#!/bin/bash
# Initialize HashiCorp Vault for AI Agents
# This script sets up Vault with all necessary secrets and policies

set -e

export VAULT_ADDR='http://localhost:8200'
export VAULT_TOKEN='your-root-token'

echo "Initializing Vault for AI Agents Platform..."

# Enable KV secrets engine
echo "Enabling KV secrets engine..."
vault secrets enable -version=2 -path=secret kv

# Create secrets paths
echo "Creating secret paths..."

# Anthropic API Keys (use different keys for different agent tiers if needed)
vault kv put secret/agents/anthropic \
    api_key="sk-ant-your-api-key-here" \
    backup_api_key="sk-ant-your-backup-api-key-here"

# Database credentials
vault kv put secret/agents/database \
    host="postgres-service" \
    port="5432" \
    database="agents_db" \
    username="agents_admin" \
    password="your-secure-password-here"

# Redis credentials
vault kv put secret/agents/redis \
    host="redis-service" \
    port="6379" \
    password="your-redis-password"

# JWT signing key for API authentication
vault kv put secret/agents/auth \
    jwt_secret="your-jwt-secret-key" \
    encryption_key="your-encryption-key"

# External service API keys
vault kv put secret/agents/external \
    slack_webhook="https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
    pagerduty_key="your-pagerduty-key" \
    datadog_api_key="your-datadog-key"

# Create policies for agents
echo "Creating Vault policies..."

# Agent read policy
vault policy write agent-read -<<EOF
path "secret/data/agents/*" {
  capabilities = ["read", "list"]
}
path "secret/metadata/agents/*" {
  capabilities = ["list"]
}
EOF

# Admin policy
vault policy write agent-admin -<<EOF
path "secret/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
path "sys/policies/*" {
  capabilities = ["read", "list"]
}
EOF

# Enable Kubernetes auth method
echo "Enabling Kubernetes authentication..."
vault auth enable kubernetes

# Configure Kubernetes auth
vault write auth/kubernetes/config \
    kubernetes_host="https://kubernetes.default.svc" \
    kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
    token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token

# Create role for agents
vault write auth/kubernetes/role/agent-role \
    bound_service_account_names=agent-service-account \
    bound_service_account_namespaces=ai-agents \
    policies=agent-read \
    ttl=24h

echo "✓ Vault initialization complete!"
echo ""
echo "Next steps:"
echo "1. Update Kubernetes secrets with Vault token"
echo "2. Configure agents to use Vault for secret retrieval"
echo "3. Rotate the root token and store securely"
