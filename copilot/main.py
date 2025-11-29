import os
import json
import uuid
import threading
import logging
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable is not set. Add it to the environment or .env")

client = Groq(api_key=API_KEY)

app = FastAPI(title="Security Chatbot API", version="1.0")

# In-memory session store (ephemeral)
# sessions: session_id -> {"src": str, "messages": [ {"role": "system"/"user"/"assistant", "content": "..."} ]}
sessions: Dict[str, Dict[str, Any]] = {}
_sessions_lock = threading.Lock()

class ChatRequest(BaseModel):
    src: str
    context: Dict[str, Any] = {}
    session_id: Optional[str] = None
    user_message: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

def build_system_prompt(src: str, context: Dict[str, Any]) -> str:
    src = src.strip()
    if src == "Pipeline Integration":
        gh = context.get("github_actions", {})
        gl = context.get("gitlab_ci", {})
        jn = context.get("jenkins_pipeline", {})
        bb = context.get("bitbucket_pipelines", {})
        return (
            "You are an expert CI/CD assistant. You are provided four concrete pipeline snippets "
            "(GitHub Actions, GitLab CI, Jenkins, Bitbucket) purely as CONTEXT examples of a single canonical task: "
            "pulling the Aegis docker image, running a scanner container against the repository workspace, "
            "passing repository metadata via environment variables, optionally mounting a results directory, "
            "accepting an API key via an environment variable, supporting a --config-api-url option and a '--parallel' flag, "
            "and handling exit codes safely.\n\n"

            "IMPORTANT: When you later generate a snippet for a different CI (e.g., CircleCI, Azure Pipelines, Travis), "
            "the generated job MUST preserve the operational details and idioms shown in the examples. Specifically ensure the generated snippet:\n"
            "  - uses a `docker pull playerunknown23/aegis:latest || true` step before running the container (to avoid CI failures on pull errors),\n"
            "  - uses `set -euo pipefail` (or the CI-equivalent robust shell flags) in script blocks to fail on errors, unset variables, or pipe failures,\n"
            "  - mounts the repository workspace into the container as read-only (where applicable) and mounts a results directory as read-write,\n"
            "  - passes repository metadata environment variables (repository path/name, ref/branch, commit SHA) into the container, using idiomatic secret/variable syntax for the target CI,\n"
            "  - injects the API credential via an environment variable named `AEGIS_API_KEY` (or the CI's secret-ref mechanism) and documents how to configure that secret in the CI,\n"
            "  - conditionally includes `--config-api-url` only when CONFIG_API_URL is set (use the target CI's conditional/templating idiom),\n"
            "  - includes the `--parallel` flag when running the scanner and preserves exit-code semantics (fail the job if scanner returns non-zero unless the examples explicitly show `|| true`),\n"
            "  - prints or logs the scanner exit code where appropriate (as in the Jenkins example) and returns that exit code from the job where the examples do so.\n\n"

            "ON THE INITIAL TURN (when you receive ONLY context and no user_message): DO NOT perform analysis or generate a snippet. "
            "Instead, ask exactly ONE short clarifying question and then stop. The exact question to ask is:\n\n"
            "\"Which CI/CD system (other than GitHub Actions, GitLab, Jenkins, or Bitbucket) would you like a snippet for?\"\n\n"

            "Use the four provided snippets only to learn the required behavior and semantics. Do NOT offer the original four pipelines as outputs. "
            "After the user replies with a target CI (e.g., CircleCI, Azure Pipelines, Travis CI), produce a single ready-to-paste pipeline snippet "
            "in that target CI's idiomatic syntax that reproduces the same behavior and semantics as the provided examples. When you generate the snippet, ensure it:\n\n"
            " - pulls the Aegis image (playerunknown23/aegis:latest) and runs it against the repo workspace\n"
            " - mounts the repository workspace as read-only and a results directory as read-write when applicable\n"
            " - passes repository metadata env vars (repository name/path, ref/branch, commit SHA)\n"
            " - uses environment variable AEGIS_API_KEY and includes CONFIG_API_URL conditionally if present\n"
            " - includes the '--parallel' flag and preserves exit code semantics\n"
            " - uses idiomatic secret/variable references for the chosen CI\n\n"

            "When producing the snippet, output EXACTLY one fenced code block containing the snippet and include a 1–3 line note after the code explaining where to paste it and which secrets/variables to set. "
            "Keep the snippet minimal, idiomatic for the target CI, and ready to paste before the build stage.\n\n"

            # embed the exact provided snippets (every line will appear here via the context variables)
            f"GitHub Actions example (context):\n```\n{gh.get('run', '')}\n```\n\n"
            f"GitLab CI example (context):\n```\n{json.dumps(gl.get('security-scan', gl), indent=2)}\n```\n\n"
            f"Jenkins pipeline example (context):\n```\n{chr(10).join(jn.get('steps', []))}\n```\n\n"
            f"Bitbucket pipeline example (context):\n```\n{chr(10).join(bb.get('script', []))}\n```\n\n"
        )

    elif src == "Vuln Scan":
        return (
            "You are a security code analysis assistant. The user has provided a vulnerable code snippet "
            "and a proposed fix as context. On the initial turn (when you receive only context and no user_message), "
            "DO NOT perform analysis or provide a fixed snippet. Instead, ask **one short clarifying question** "
            "that prompts the user to describe the visible problem or error they are encountering with the proposed fix. "
            "Do not include any analysis, explanation, or corrected code in this initial reply — wait for the user's answer.\n\n"
            "When the user replies describing the problem or error, then perform a step-by-step analysis comparing the vulnerable "
            "and proposed fixed code, point out any remaining issues, and provide a corrected, secure code snippet and testing tips.\n\n"
            f"Vulnerable code (context):\n```python\n{context.get('code_snippet', '')}\n```\n\n"
            f"Proposed fix (context):\n```python\n{context.get('fixed_code', '')}\n```\n\n"
            "Important: On the initial message ask exactly one brief question like: "
            "\"What problem or error are you seeing when you run the fixed snippet?\""
        )

    elif src == "Full Repo Scan":
        scan_report = context.get("scan_report", context)
        return (
            "You are a software security assistant. You get the results of a full repository security scan from the context"
            "ON THE INITIAL TURN (when you receive ONLY context and no user_message): ask exactly ONE short clarifying question about what the user wants to know from the scan results, and then stop. "
            "The exact question to ask is:\n\n"
            "\"What specific information or insights are you looking for from the security scan results?\"\n\n"
            "When the user replies with their information needs, provide a detailed analysis of the scan"
            "Analyze the findings, explain the impact, and provide clear step-by-step remediation actions.\n\n"
            f"Scan report (JSON):\n```\n{json.dumps(scan_report, indent=2)}\n```\n"
        )

    else:
        return (
        "You are a helpful, concise, and technically knowledgeable assistant. "
        "The user may ask questions about CI/CD, application security, DevSecOps, pipelines, vulnerabilities, or code fixes. "
        "Do your best to answer clearly, with minimal assumptions. Include code snippets where appropriate. "
        "If the question is unrelated to security or DevOps, you may still help in a general programming context."
    )

def extract_reply_from_result(result: Any) -> Optional[str]:
    try:
        choices = getattr(result, "choices", None)
        if choices:
            first = choices[0]
            msg = getattr(first, "message", None)
            if msg is not None:
                content = getattr(msg, "content", None)
                if content:
                    return content
            if isinstance(first, dict):
                if "message" in first and isinstance(first["message"], dict):
                    return first["message"].get("content")
                if "text" in first:
                    return first.get("text")
        if isinstance(result, dict):
            return result.get("output") or result.get("text") or None
    except Exception as e:
        logger.debug("extract_reply_from_result error: %s", e)
    return None

def create_session(initial_messages: List[Dict[str, str]], src: str) -> str:
    sid = str(uuid.uuid4())
    with _sessions_lock:
        sessions[sid] = {"src": src, "messages": list(initial_messages)}
    logger.info("Created session %s for src=%s", sid, src)
    return sid

def append_to_session(sid: str, role: str, content: str) -> None:
    with _sessions_lock:
        if sid not in sessions:
            raise KeyError("Session not found")
        sessions[sid]["messages"].append({"role": role, "content": content})

def get_session_messages(sid: str) -> List[Dict[str, str]]:
    with _sessions_lock:
        if sid not in sessions:
            raise KeyError("Session not found")
        return list(sessions[sid]["messages"])

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Behavior:
      - If session_id provided: treat as follow-up. Append user_message, send full history to Groq, append assistant reply.
      - If no session_id: build system prompt from src/context, optionally include user_message, create session, call Groq.
    """
    if not req.src:
        raise HTTPException(status_code=400, detail="src is required")

    try:
        if req.session_id:
            sid = req.session_id
            try:
                # ensure session exists
                _ = get_session_messages(sid)
            except KeyError:
                raise HTTPException(status_code=404, detail="Session ID not found")

            if not req.user_message:
                raise HTTPException(status_code=400, detail="For follow-up turns include user_message")

            # append user message and take full history
            append_to_session(sid, "user", req.user_message)
            messages = get_session_messages(sid)

        else:
            # new session: build system prompt including context
            system_prompt = build_system_prompt(req.src, req.context or {})
            messages = [{"role": "system", "content": system_prompt}]
            if req.user_message:
                messages.append({"role": "user", "content": req.user_message})

            sid = create_session(messages, req.src)

        # Call Groq - SDK doesn't accept session_id, so we send full history every time
        try:
            result = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
            )
        except Exception as e:
            logger.exception("Groq API call failed")
            raise HTTPException(status_code=500, detail=f"Groq API error: {str(e)}")

        reply = extract_reply_from_result(result)
        if not reply:
            try:
                if isinstance(result, dict):
                    reply = result["choices"][0]["message"]["content"]
            except Exception:
                reply = None

        if not reply:
            logger.debug("Full Groq result: %s", str(result))
            raise HTTPException(status_code=500, detail="Empty response from Groq API")

        # store assistant reply and return
        append_to_session(sid, "assistant", reply)

        return ChatResponse(response=reply, session_id=sid)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in chat endpoint")
        raise HTTPException(status_code=500, detail=str(e))
