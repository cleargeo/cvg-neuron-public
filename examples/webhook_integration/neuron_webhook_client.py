"""
CVG Neuron -- Webhook Integration Examples
(c) Clearview Geographic LLC -- MIT License

Demonstrates how to send webhook events to CVG Neuron's webhook receiver.
Neuron's webhook endpoints accept events from GitHub, Azure DevOps, and
any CI/CD system, feeding them into the edge connector intelligence pipeline.

Webhook receiver URL: http://<neuron-host>:8808/api/webhook/
"""

import json
import hashlib
import hmac
import urllib.request
import urllib.error
from typing import Any, Dict, Optional


class NeuronWebhookClient:
    """
    Client for sending webhook events to CVG Neuron.

    Supports:
    - GitHub webhooks (push, PR, release, workflow events)
    - Azure DevOps service hooks (build, release, PR events)
    - Generic deployment notifications

    Example:
        client = NeuronWebhookClient("http://localhost:8808")
        client.send_deploy("my-app", "success", "production", commit_sha="abc123")
    """

    def __init__(self, base_url: str, github_secret: str = ""):
        self.base_url = base_url.rstrip("/")
        self.github_secret = github_secret

    # ── Generic Deployment ──────────────────────────────────────────────────

    def send_deploy(
        self,
        app_name: str,
        status: str,
        environment: str = "production",
        commit_sha: Optional[str] = None,
        branch: Optional[str] = None,
        repository: Optional[str] = None,
        deployed_by: Optional[str] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """
        Send a deployment notification to Neuron.

        Args:
            app_name: Application or service name
            status: Deployment status (success, failed, in_progress)
            environment: Target environment (production, staging, development)
            commit_sha: Git commit SHA
            branch: Git branch name
            repository: Repository name
            deployed_by: Who/what triggered the deployment
            message: Optional status message
            metadata: Optional extra data

        Returns:
            Neuron's response dict

        Example:
            client.send_deploy(
                app_name="cvg-neuron",
                status="success",
                environment="production",
                commit_sha="abc123def456",
                branch="main",
                repository="cleargeo/CVG-Neuron",
            )
        """
        payload = {
            "app_name": app_name,
            "status": status,
            "environment": environment,
            "commit_sha": commit_sha,
            "branch": branch,
            "repository": repository,
            "deployed_by": deployed_by,
            "message": message,
            "metadata": metadata or {},
        }
        return self._post("/api/webhook/deploy", payload)

    # ── GitHub Webhooks ─────────────────────────────────────────────────────

    def send_github_push(
        self,
        repo_full_name: str,
        ref: str,
        commits: list,
        pusher_name: str,
        head_commit_id: str = "",
        head_commit_message: str = "",
    ) -> dict:
        """
        Send a GitHub push event to Neuron.

        Args:
            repo_full_name: e.g. "cleargeo/CVG-Neuron"
            ref: e.g. "refs/heads/main"
            commits: List of commit dicts with 'id' and 'message'
            pusher_name: GitHub username of the pusher
            head_commit_id: SHA of the head commit
            head_commit_message: Commit message

        Returns:
            Neuron's response dict
        """
        payload = {
            "repository": {"full_name": repo_full_name},
            "ref": ref,
            "commits": commits,
            "pusher": {"name": pusher_name},
            "head_commit": {
                "id": head_commit_id,
                "message": head_commit_message,
            },
        }
        headers = {"X-GitHub-Event": "push"}
        if self.github_secret:
            body = json.dumps(payload).encode()
            signature = "sha256=" + hmac.new(
                self.github_secret.encode(), body, hashlib.sha256
            ).hexdigest()
            headers["X-Hub-Signature-256"] = signature
        return self._post("/api/webhook/github", payload, headers)

    def send_github_pr(
        self,
        repo_full_name: str,
        action: str,
        pr_number: int,
        title: str,
        author: str,
        head_branch: str,
        base_branch: str,
    ) -> dict:
        """
        Send a GitHub pull request event to Neuron.

        Args:
            repo_full_name: e.g. "cleargeo/CVG-Neuron"
            action: PR action (opened, closed, synchronize, reopened)
            pr_number: PR number
            title: PR title
            author: GitHub username
            head_branch: Source branch
            base_branch: Target branch

        Returns:
            Neuron's response dict
        """
        payload = {
            "action": action,
            "pull_request": {
                "number": pr_number,
                "title": title,
                "user": {"login": author},
                "head": {"ref": head_branch},
                "base": {"ref": base_branch},
            },
            "repository": {"full_name": repo_full_name},
        }
        headers = {"X-GitHub-Event": "pull_request"}
        return self._post("/api/webhook/github", payload, headers)

    def send_github_workflow(
        self,
        repo_full_name: str,
        action: str,
        workflow_name: str,
        conclusion: str,
        run_id: int,
        branch: str = "",
        head_sha: str = "",
    ) -> dict:
        """
        Send a GitHub workflow run event to Neuron.

        Args:
            repo_full_name: e.g. "cleargeo/CVG-Neuron"
            action: Workflow action (completed, requested)
            workflow_name: Name of the workflow
            conclusion: Workflow conclusion (success, failure, cancelled)
            run_id: GitHub workflow run ID
            branch: Branch the workflow ran on
            head_sha: Commit SHA

        Returns:
            Neuron's response dict
        """
        payload = {
            "action": action,
            "workflow_run": {
                "name": workflow_name,
                "conclusion": conclusion,
                "id": run_id,
                "head_branch": branch,
                "head_sha": head_sha,
            },
            "repository": {"full_name": repo_full_name},
        }
        headers = {"X-GitHub-Event": "workflow_run"}
        return self._post("/api/webhook/github", payload, headers)

    # ── Azure DevOps Webhooks ────────────────────────────────────────────────

    def send_azure_build(
        self,
        project_name: str,
        build_number: str,
        status: str,
        result: str,
        definition_name: str = "",
    ) -> dict:
        """
        Send an Azure DevOps build completed event to Neuron.

        Args:
            project_name: Azure DevOps project name
            build_number: Build number
            status: Build status (completed, succeeded, failed)
            result: Build result (succeeded, failed, canceled)
            definition_name: Build pipeline name

        Returns:
            Neuron's response dict
        """
        payload = {
            "eventType": "build.complete",
            "resource": {
                "build": {
                    "buildNumber": build_number,
                    "status": status,
                    "result": result,
                    "definition": {"name": definition_name},
                }
            },
            "resourceContainers": {
                "project": {"name": project_name}
            },
        }
        return self._post("/api/webhook/azure-devops", payload)

    def send_azure_release(
        self,
        release_name: str,
        environment_name: str,
        environment_status: str,
    ) -> dict:
        """
        Send an Azure DevOps release created event to Neuron.

        Args:
            release_name: Release name
            environment_name: Target environment name
            environment_status: Environment status

        Returns:
            Neuron's response dict
        """
        payload = {
            "eventType": "ms.vss-release.release-created-event",
            "resource": {
                "release": {"name": release_name},
                "environment": {
                    "name": environment_name,
                    "status": environment_status,
                },
            },
        }
        return self._post("/api/webhook/azure-devops", payload)

    # ── Internal ─────────────────────────────────────────────────────────────

    def _post(
        self,
        path: str,
        payload: dict,
        extra_headers: Optional[dict] = None,
    ) -> dict:
        """Send a POST request to Neuron."""
        url = f"{self.base_url}{path}"
        body = json.dumps(payload).encode()
        headers = {"Content-Type": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            return {"status": "error", "http": exc.code, "detail": exc.read().decode()}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}


# ── Usage Examples ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    client = NeuronWebhookClient("http://localhost:8808")

    # Example 1: Deployment notification
    print("=== Deployment Notification ===")
    result = client.send_deploy(
        app_name="cvg-neuron",
        status="success",
        environment="production",
        commit_sha="abc123def456",
        branch="main",
        repository="cleargeo/CVG-Neuron",
        message="Integration enhancement sweep",
    )
    print(json.dumps(result, indent=2))

    # Example 2: GitHub push
    print("\n=== GitHub Push ===")
    result = client.send_github_push(
        repo_full_name="cleargeo/CVG-Neuron",
        ref="refs/heads/main",
        commits=[{"id": "abc123", "message": "feat: webhook integration"}],
        pusher_name="alexzelenski",
        head_commit_id="abc123def456789",
        head_commit_message="feat: webhook integration layer",
    )
    print(json.dumps(result, indent=2))

    # Example 3: GitHub PR
    print("\n=== GitHub PR ===")
    result = client.send_github_pr(
        repo_full_name="cleargeo/CVG-Neuron",
        action="opened",
        pr_number=42,
        title="Add webhook receiver layer",
        author="alexzelenski",
        head_branch="feature/webhooks",
        base_branch="master",
    )
    print(json.dumps(result, indent=2))

    # Example 4: GitHub workflow
    print("\n=== GitHub Workflow ===")
    result = client.send_github_workflow(
        repo_full_name="cleargeo/CVG-Neuron",
        action="completed",
        workflow_name="CI/CD Pipeline",
        conclusion="success",
        run_id=12345,
        branch="main",
        head_sha="abc123def456",
    )
    print(json.dumps(result, indent=2))

    # Example 5: Azure DevOps build
    print("\n=== Azure DevOps Build ===")
    result = client.send_azure_build(
        project_name="CVG-Platform",
        build_number="20260622.1",
        status="completed",
        result="succeeded",
        definition_name="CVG-Neuron-CI",
    )
    print(json.dumps(result, indent=2))
