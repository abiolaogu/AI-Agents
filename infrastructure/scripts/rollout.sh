#!/bin/bash
# Rolling update script for agents
# Usage: ./rollout.sh [agent_id] [new_version]

set -e

AGENT_ID=$1
NEW_VERSION=${2:-latest}

if [ -z "$AGENT_ID" ]; then
    echo "Usage: ./rollout.sh [agent_id] [new_version]"
    exit 1
fi

echo "Starting rolling update for $AGENT_ID to version $NEW_VERSION"

# Update image
kubectl set image deployment/${AGENT_ID}-deployment \
    ${AGENT_ID}=ghcr.io/your-org/${AGENT_ID}:${NEW_VERSION} \
    -n ai-agents

# Watch rollout status
echo "Watching rollout status..."
kubectl rollout status deployment/${AGENT_ID}-deployment -n ai-agents

# Verify deployment
echo "Verifying deployment..."
kubectl get pods -n ai-agents -l app=${AGENT_ID}

# Run health check
POD_NAME=$(kubectl get pods -n ai-agents -l app=${AGENT_ID} -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n ai-agents $POD_NAME -- curl -f http://localhost/health

echo "✓ Rolling update complete for $AGENT_ID"
