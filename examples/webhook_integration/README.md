"""
CVG Neuron -- Webhook Receiver Setup Example
(c) Clearview Geographic LLC -- MIT License

Shows how to configure CVG Neuron's webhook receiver endpoints
and how to register them with external services (GitHub, Azure DevOps).

This is a companion to the webhook client example.
"""

# ── Webhook Endpoint Reference ────────────────────────────────────────────────
#
# Neuron exposes these webhook endpoints at /api/webhook/*:
#
#   GET  /api/webhook/              -- Webhook service info
#   POST /api/webhook/github        -- GitHub events (push, PR, release, workflow)
#   POST /api/webhook/azure-devops  -- Azure DevOps events (build, release, PR)
#   POST /api/webhook/deploy        -- Generic deployment notifications
#
# All webhook events are fed into Neuron's edge connector as intelligence
# payloads, triggering cognitive processing and persistent memory storage.


# ── GitHub Webhook Configuration ──────────────────────────────────────────────
#
# To configure a GitHub webhook:
#
# 1. Go to your GitHub repository → Settings → Webhooks → Add webhook
# 2. Set Payload URL to: http://<neuron-host>:8808/api/webhook/github
# 3. Set Content type to: application/json
# 4. Set Secret to a strong random string (recommended for production)
# 5. Select events: Push, Pull requests, Releases, Workflow runs
# 6. Click "Add webhook"
#
# Example GitHub webhook secret configuration in Neuron's .env:
#   GITHUB_WEBHOOK_SECRET=your-secret-here
#
# Without a secret, GitHub webhooks are accepted in dev mode (no auth).


# ── Azure DevOps Service Hook Configuration ────────────────────────────────────
#
# To configure an Azure DevOps service hook:
#
# 1. Go to Project Settings → Service Hooks → Create subscription
# 2. Select "Web hook" as the service
# 3. Configure triggers:
#    - Build completed
#    - Release created
#    - Pull request created/updated
#    - Code pushed
# 4. Set URL to: http://<neuron-host>:8808/api/webhook/azure-devops
# 5. Click "Finish"


# ── Generic Deployment Webhook ────────────────────────────────────────────────
#
# Any CI/CD system can send deployment notifications:
#
#   curl -X POST http://<neuron-host>:8808/api/webhook/deploy \
#     -H "Content-Type: application/json" \
#     -d '{
#       "app_name": "my-service",
#       "status": "success",
#       "environment": "production",
#       "commit_sha": "abc123",
#       "branch": "main",
#       "repository": "myorg/myrepo"
#     }'
#
# Status values: success | failed | in_progress
# Failed deployments trigger high-priority alerts in Neuron's edge connector.


# ── Webhook Event Flow ────────────────────────────────────────────────────────
#
# 1. External system sends webhook POST to Neuron
# 2. Neuron verifies authentication (HMAC for GitHub, optional for others)
# 3. Event is routed to the appropriate handler by event type
# 4. Handler extracts key data (repo, branch, status, commits, etc.)
# 5. Event is packaged as an IntelligencePayload
# 6. Payload is auto-registered with the edge connector (first use)
# 7. Edge connector ingests the payload into Neuron's memory
# 8. High-priority events (>=7) trigger immediate cognitive processing
# 9. Alerts always trigger immediate cognitive processing


# ── Testing Webhooks Locally ──────────────────────────────────────────────────
#
# Use the included neuron_webhook_client.py to test:
#
#   from neuron_webhook_client import NeuronWebhookClient
#   client = NeuronWebhookClient("http://localhost:8808")
#
#   # Test deployment notification
#   result = client.send_deploy("test-app", "success", "development")
#   print(result)
#
#   # Test GitHub push
#   result = client.send_github_push(
#       repo_full_name="myorg/myrepo",
#       ref="refs/heads/main",
#       commits=[{"id": "abc123", "message": "test"}],
#       pusher_name="testuser",
#       head_commit_id="abc123",
#       head_commit_message="test commit",
#   )
#   print(result)


# ── Security Considerations ────────────────────────────────────────────────────
#
# 1. Always use HTTPS in production (via reverse proxy like Caddy or nginx)
# 2. Set GITHUB_WEBHOOK_SECRET to enable HMAC-SHA256 verification
# 3. Use network-level firewall rules to restrict webhook source IPs
# 4. Neuron's edge connector validates payload freshness (5-minute window)
# 5. All webhook events are logged for audit purposes
