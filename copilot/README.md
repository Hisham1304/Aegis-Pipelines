##PIPELINE INTEGRATION:

###1: Initial Request:
```
{
  "src": "Pipeline Integration",
  "context": {
    "github_actions": {
      "name": "Run Aegis Security Scan",
      "run": "docker run --rm \\n  -v ${{ github.workspace }}:/app/target \\n  -e GITHUB_REPOSITORY=${{ github.repository }} \\n  -e GITHUB_REF=${{ github.ref }} \\n  -e GITHUB_SHA=${{ github.sha }} \\n  playerunknown23/aegis:latest \\n  /app/target \\n  --api-key aegis_LJvDFv7nhDBxNOac7AcWJoVoR9T79t6A \\n  --config-api-url https://config-api-mja3.onrender.com \\n  --parallel"
    },
    "gitlab_ci": {
      "stages": [
        "scan"
      ],
      "variables": {
        "DOCKER_TLS_CERTDIR": ""
      },
      "security-scan": {
        "stage": "scan",
        "image": "docker:24.0.5",
        "services": [
          {
            "name": "docker:24.0.5-dind",
            "alias": "docker"
          }
        ],
        "script": [
          "echo \"=== Pulling Aegis image ===\"",
          "docker pull playerunknown23/aegis:latest || true",
          "echo \"=== Running Aegis scanner ===\"",
          "set -euo pipefail",
          "if [ -n \"${CONFIG_API_URL:-}\" ]; then CONFIG_ARG=\"--config-api-url=${CONFIG_API_URL}\"; else CONFIG_ARG=\"\"; fi",
          "docker run --rm \\",
          "  -v \"$CI_PROJECT_DIR\":/app/target:ro \\",
          "  -v \"$CI_PROJECT_DIR/results\":/app/results:rw \\",
          "  -e AEGIS_API_KEY=\"$AEGIS_API_KEY\" \\",
          "  -e CONFIG_API_URL=\"$CONFIG_API_URL\" \\",
          "  -e GITHUB_REPOSITORY=\"$CI_PROJECT_PATH\" \\",
          "  -e GITHUB_REF=\"$CI_COMMIT_REF_NAME\" \\",
          "  -e GITHUB_SHA=\"$CI_COMMIT_SHA\" \\",
          "  playerunknown23/aegis:latest \\",
          "  /app/target \\",
          "  --api-key \"$AEGIS_API_KEY\" \\",
          "  $CONFIG_ARG \\",
          "  --parallel"
        ],
        "allow_failure": false
      }
    },
    "jenkins_pipeline": {
      "stage": "Run Security Scan (Docker)",
      "steps": [
        "withCredentials([string(credentialsId: 'aegis_api_key', variable: 'AEGIS_API_KEY'), string(credentialsId: 'config_api_url', variable: 'CONFIG_API_URL')]) {",
        "  sh '''",
        "    set -euo pipefail",
        "    echo \"Pulling Aegis image...\"",
        "    docker pull playerunknown23/aegis:latest || true",
        "    echo \"Running Aegis scanner container...\"",
        "    SCANNER_EXIT=0",
        "    if [ -n \"${CONFIG_API_URL:-}\" ]; then CONFIG_ARG=\"--config-api-url=${CONFIG_API_URL}\"; else CONFIG_ARG=\"\"; fi",
        "    docker run --rm \\",
        "      -v \"${WORKSPACE}:/app/target:ro\" \\",
        "      -v \"${WORKSPACE}/results:/app/results:rw\" \\",
        "      -e AEGIS_API_KEY=\"${AEGIS_API_KEY}\" \\",
        "      -e CONFIG_API_URL=\"${CONFIG_API_URL}\" \\",
        "      -e GITHUB_REPOSITORY=\"${JOB_NAME}\" \\",
        "      -e GITHUB_REF=\"${BRANCH_NAME:-unknown-ref}\" \\",
        "      -e GITHUB_SHA=\"${GIT_COMMIT:-unknown-sha}\" \\",
        "      playerunknown23/aegis:latest \\",
        "      /app/target \\",
        "      --api-key \"${AEGIS_API_KEY}\" \\",
        "      ${CONFIG_ARG} \\",
        "      --parallel || SCANNER_EXIT=$?",
        "    echo \"Aegis exit code: $SCANNER_EXIT\"",
        "    exit $SCANNER_EXIT",
        "  '''",
        "}"
      ]
    },
    "bitbucket_pipelines": {
      "step": "Aegis - pull & run",
      "services": [
        "docker"
      ],
      "script": [
        "set -euo pipefail",
        "docker pull playerunknown23/aegis:latest",
        "docker run --rm \\",
        "  -v \"$BITBUCKET_CLONE_DIR\":/app/target:ro \\",
        "  -e AEGIS_API_KEY=\"$AEGIS_API_KEY\" \\",
        "  -e CONFIG_API_URL=\"$CONFIG_API_URL\" \\",
        "  -e GITHUB_REPOSITORY=\"$BITBUCKET_REPO_FULL_NAME\" \\",
        "  -e GITHUB_REF=\"$BITBUCKET_BRANCH\" \\",
        "  -e GITHUB_SHA=\"$BITBUCKET_COMMIT\" \\",
        "  playerunknown23/aegis:latest \\",
        "  /app/target \\",
        "  --api-key \"$AEGIS_API_KEY\" \\",
        "  ${CONFIG_API_URL:+--config-api-url \"$CONFIG_API_URL\"} \\",
        "  --parallel || true"
      ]
    }
  }
}
```
###expected response:
```
{
  "response": "Which CI/CD system (other than GitHub Actions, GitLab, Jenkins, or Bitbucket) would you like a snippet for?",
  "session_id": "1f2dca3b-430f-487c-b777-6e2646486283"
}
```
###2: Follow up with the response: (copy & paste the previous session id here)
```
{
  "src": "Pipeline Integration",
  "context": {},
  "session_id": "1f2dca3b-430f-487c-b777-6e2646486283",
  "user_message": "CircleCI please — provide a config.yml snippet"
}
```
###expected response:
```
{
  "response": "```yml\nversion: 2.1\njobs:\n  aegis-scan:\n    docker:\n      - image: cimg/docker:20.10.17\n    steps:\n      - checkout\n      - run: \n          name: Pull Aegis image\n          command: docker pull playerunknown23/aegis:latest || true\n      - run: \n          name: Run Aegis scanner\n          command: |\n            set -euo pipefail\n            if [ -n \"${CONFIG_API_URL}\" ]; then CONFIG_ARG=\"--config-api-url=${CONFIG_API_URL}\"; else CONFIG_ARG=\"\"; fi\n            docker run --rm \\\n              -v \"${PWD}:/app/target:ro\" \\\n              -v \"${PWD}/results:/app/results:rw\" \\\n              -e AEGIS_API_KEY=\"$AEGIS_API_KEY\" \\\n              -e CONFIG_API_URL=\"${CONFIG_API_URL}\" \\\n              -e GITHUB_REPOSITORY=\"${CIRCLE_PROJECT_REPONAME}\" \\\n              -e GITHUB_REF=\"${CIRCLE_BRANCH}\" \\\n              -e GITHUB_SHA=\"${CIRCLE_SHA1}\" \\\n              playerunknown23/aegis:latest \\\n              /app/target \\\n              --api-key \"$AEGIS_API_KEY\" \\\n              $CONFIG_ARG \\\n              --parallel\n          exit_code: 1  # Fail the job on non-zero exit code\nworkflows:\n  aegis-scan-workflow:\n    jobs:\n      - aegis-scan\n```\nNote: To use this snippet, store your AEGIS_API_KEY as a CircleCI project environment variable, and optionally set CONFIG_API_URL if needed. Paste this snippet into your `.circleci/config.yml` file.",
  "session_id": "1f2dca3b-430f-487c-b777-6e2646486283"
}
```
and further requests in src: "Pipeline Integration" can follow the above request while copy pasting the session_id.

##VULN SCAN:
###1: Intial Request:
```
{
  "src": "Vuln Scan",
  "context": {
    "code_snippet": "import os\n\nfilename = request.args.get('filename')\n# Unsafe! User can pass 'test.txt; rm -rf /'\nos.system(f'cat {filename}')",
    "description": "OS Command Injection. A filename provided by a user is used to build a shell command with string concatenation.",
    "fixed_code": "import os\nimport subprocess\n\nfilename = request.args.get('filename')\nos.system(['cat', filename])",
    "fix_description": "Attempted using list args but still using os.system."
  }
}
```
###expected response:
```
{
  "response": "What problem or error are you seeing when you run the fixed snippet?",
  "session_id": "6d74c337-05c9-4c52-9934-ec823d4375ea"
}
```
###2: Follow up with the response: (copy & paste the previous session id here)
```
{
  "src": "Vuln Scan",
  "context": {},
  "session_id": "6d74c337-05c9-4c52-9934-ec823d4375ea",
  "user_message": "I get TypeError: os.system() takes a string argument."
}
```
###expected response:
```
{
  "response": "## Step-by-step analysis of the problem:\n\n1. **Understanding the error**: The error `TypeError: os.system() takes a string argument` indicates that the `os.system()` function is expecting a string argument but is receiving a different type, in this case, a list.\n2. **Analyzing the proposed fix**: The proposed fix is trying to pass a list of arguments to `os.system()`, which is incorrect. The correct function to use when passing multiple arguments is `subprocess.run()` or other related functions from the `subprocess` module.\n3. **Identifying the vulnerability**: The original code was vulnerable to shell injection attacks because it directly concatenated user input into a shell command. The proposed fix attempts to address this but incorrectly uses `os.system()` with a list.\n4. ............................................ **Test with a filename that contains special characters**: Ensure that filenames with special characters are handled correctly and do not cause shell injection vulnerabilities.",
  "session_id": "6d74c337-05c9-4c52-9934-ec823d4375ea"
}
```
and further requests in src: "Vuln Scan" can follow the above request while copy pasting the session_id.

##FULL REPO SCAN: 
(whatever data and information we have, have it under "scan_report":{} . then the scan_report will be inside our context parameter)
###1: Initial Request:
```
{
  "src": "Full Repo Scan",
  "context": {
    "scan_report": {
      "summary": "Found 3 issues",
      "vulnerabilities": [
        { "file": "src/auth.py", "issue": "Hardcoded secret", "severity": "high", "line": 12 },
        { "file": "src/db.py", "issue": "SQL concatenation", "severity": "high", "line": 45 },
        { "file": "scripts/deploy.sh", "issue": "World-writable file", "severity": "medium", "line": 3 }
      ]
    }
  }
}
```
###expected response:
```
{
  "response": "What specific information or insights are you looking for from the security scan results?",
  "session_id": "aa195c07-6428-4459-94b9-ea57698661da"
}
```
###2: Follow up with the response: (copy & paste the previous session id here)
```
{
  "src": "Full Repo Scan",
  "context": {},
  "session_id": "PASTE_SESSION_ID_HERE",
  "user_message": "Please prioritize the issues and give step-by-step remediations for the top two high-severity findings."
}
```
###expected response:
```
{
  "response": "Based on the scan report, I've prioritized the issues and will provide step-by-step remediation actions for the top two high-severity findings.\n\n**Priority Order:**\n\n1. Hardcoded secret in `src/auth.py` (High Severity)\n2. SQL concatenation in `src/db.py` (High Severity)\n3. World-writable file in `scripts/deploy.sh` (Medium Severity)\n\n**Remediation for High-Severity Findings:**\n\n### 1. Hardcoded secret in `src/auth.py`\n\n* **Issue:** A hardcoded secret is found in `src/auth.py` at line 12, which poses a significant risk to the security of your application.\n* **Impact:** An attacker can exploit this vulnerability to gain unauthorized access to sensitive data or systems.\n* **Remediation Steps:**\n\t1. **Remove the hardcoded secret**: .........................................................................................query.bindparams(name=user_input)\n```\n\nBy following these remediation steps, you can address the high-severity findings and significantly improve the security of your application.",
  "session_id": "aa195c07-6428-4459-94b9-ea57698661da"
}
```
and further requests in src: "Vuln Scan" can follow the above request while copy pasting the session_id.

##FREEFORM: 
(this is used when the user just wants to directly interact with chatbot and the request does not come from a particular src. here the "src": "value can be anything here apart from Freeform)
###1: Initial Request:
```
{
  "src": "Freeform",
  "context": {},
  "user_message": "How can I mask secrets in CI logs for CircleCI?"
}
```
###expected response:
```
{
  "response":"......"
  "session_id":"49fd3899-760a-4210-8b1a-39f3325f5472"
}
```
###2: Follow up with the response: (copy & paste the previous session id here)
```
{
  "src": "Freeform",
  "context": {},
  "session_id": "PASTE_SESSION_ID_HERE",
  "user_message": "Show an example for CircleCI to mask 'AEGIS_API_KEY' in logs."
}
```