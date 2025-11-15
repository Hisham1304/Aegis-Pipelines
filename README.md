# Integrating Aegis Security Scanner

This guide provides the necessary steps and code snippets to integrate the Aegis security scanner into your CI/CD pipelines.

## 🚀 Getting Started (Universal Prerequisites)

Before you begin, you must have the following from your Aegis dashboard:

1.  **Aegis API Key:** A unique API key to authenticate with the Aegis service.
2.  **Config API URL:** If you use quality gates, you will also need the configuration API URL.

You must store these as secure environment variables (secrets) in your CI/CD platform's settings. The scanner will read them from the environment.

* `AEGIS_API_KEY`: Your scanner API key.
* `CONFIG_API_URL`: Your quality gate configuration URL.

---
## JENKINS
### Prerequisites

* The Jenkins agent (or node) must have Docker installed and configured.
* Store your `AEGIS_API_KEY` and `CONFIG_API_URL` as **String Credentials in Jenkins** (e.g., with IDs `aegis_api_key` and `config_api_url`).

### Jenkinsfile Snippet

This snippet is a complete `stage` that you can copy and paste into the `stages` block of your `Jenkinsfile`:

```groovy
stage('Run Security Scan (Docker)') {
      steps {
        withCredentials([
          string(credentialsId: 'aegis_api_key', variable: 'AEGIS_API_KEY'),
          string(credentialsId: 'config_api_url', variable: 'CONFIG_API_URL')
        ]) {
          sh '''
            set -euo pipefail
            echo "Pulling Aegis image..."
            docker pull playerunknown23/aegis:latest || true 
            echo "Running Aegis scanner container..."
            SCANNER_EXIT=0
            # Set config arg only if variable is not empty
            if [ -n "${CONFIG_API_URL:-}" ]; then
              CONFIG_ARG="--config-api-url=${CONFIG_API_URL}"
            else
              CONFIG_ARG=""
            fi
            docker run --rm \
              -v "${WORKSPACE}:/app/target:ro" \
              -v "${WORKSPACE}/results:/app/results:rw" \
              -e AEGIS_API_KEY="${AEGIS_API_KEY}" \
              -e CONFIG_API_URL="${CONFIG_API_URL}" \
              -e GITHUB_REPOSITORY="${JOB_NAME}" \
              -e GITHUB_REF="${BRANCH_NAME:-unknown-ref}" \
              -e GITHUB_SHA="${GIT_COMMIT:-unknown-sha}" \
              playerunknown23/aegis:latest \
              /app/target \
              --api-key "${AEGIS_API_KEY}" \
              ${CONFIG_ARG} \
              --parallel || SCANNER_EXIT=$? 
            echo "Aegis exit code: $SCANNER_EXIT"
            exit $SCANNER_EXIT
          '''
        }
      }
    }
```
---
## GITLAB
### Prerequisites

* Ensure your GitLab runner is configured to support Docker-in-Docker.
* Store your `AEGIS_API_KEY` and `CONFIG_API_URL` as **CI/CD Variables** in your GitLab project settings (mark them as "Masked").

### .gitlab-ci.yml Snippet

This snippet is a complete `job` definition that can be added to your .gitlab-ci.yml file. It uses a Docker-in-Docker (DinD) setup.

```yaml
stages:
  - scan

variables:
  DOCKER_TLS_CERTDIR: ""

security-scan:
  stage: test
  image: docker:24.0.5
  services:
    - name: docker:24.0.5-dind
      alias: docker
  script:
    - echo "=== Pulling Aegis image ==="
    - docker pull playerunknown23/aegis:latest || true
    - echo "=== Running Aegis scanner ==="
    - |
      set -euo pipefail
      if [ -n "${CONFIG_API_URL:-}" ]; then
        CONFIG_ARG="--config-api-url=${CONFIG_API_URL}"
      else
        CONFIG_ARG=""
      fi
      docker run --rm \
        -v "$CI_PROJECT_DIR":/app/target:ro \
        -v "$CI_PROJECT_DIR/results":/app/results:rw \
        -e AEGIS_API_KEY="$AEGIS_API_KEY" \
        -e CONFIG_API_URL="$CONFIG_API_URL" \
        -e GITHUB_REPOSITORY="$CI_PROJECT_PATH" \
        -e GITHUB_REF="$CI_COMMIT_REF_NAME" \
        -e GITHUB_SHA="$CI_COMMIT_SHA" \
        playerunknown23/aegis:latest \
        /app/target \
        --api-key "$AEGIS_API_KEY" \
        $CONFIG_ARG \
        --parallel
  # Set allow_failure: true if you do not want this job 
  # to block your pipeline on a failed quality gate.
  allow_failure: false
```
---
## BITBUCKET
### Prerequisites

* Enable the `docker` service for the pipeline.
* Store your `AEGIS_API_KEY` and `CONFIG_API_URL` as **Repository variables** in your Bitbucket repository settings (mark them as "Secured")

### bitbucket-pipelines.yml snippet

This snippet is a complete `step` that can be added to your bitbucket-pipelines.yml file.

```yaml
- step:
        name: "Aegis - pull & run"
        services:
          - docker
        script:
          - set -euo pipefail
          - docker pull playerunknown23/aegis:latest
          # Run the scanner
          # The "|| true" at the end prevents this command 
          # from failing the pipeline if vulnerabilities are found.
          # Remove "|| true" if you want the pipeline to fail.
          - |
            docker run --rm \
              -v "$BITBUCKET_CLONE_DIR":/app/target:ro \
              -v "$BITBUCKET_CLONE_DIR/results":/app/results:rw \
              -e AEGIS_API_KEY="$AEGIS_API_KEY" \
              -e CONFIG_API_URL="$CONFIG_API_URL" \
              -e GITHUB_REPOSITORY="$BITBUCKET_REPO_FULL_NAME" \
              -e GITHUB_REF="$BITBUCKET_BRANCH" \
              -e GITHUB_SHA="$BITBUCKET_COMMIT" \
              playerunknown23/aegis:latest \
              /app/target \
              --api-key "$AEGIS_API_KEY" \
              ${CONFIG_API_URL:+--config-api-url "$CONFIG_API_URL"} \
              --parallel || true
```




