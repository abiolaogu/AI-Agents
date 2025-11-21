#!/bin/bash
# Deployment Script for AI Agents Platform
# Usage: ./deploy.sh [environment] [mode]

set -e

ENVIRONMENT=${1:-development}
MODE=${2:-full}  # full, infra-only, agents-only

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AI Agents Platform Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Environment: $ENVIRONMENT"
echo "Mode: $MODE"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"

    commands=("kubectl" "docker" "helm")
    for cmd in "${commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            echo -e "${RED}Error: $cmd is not installed${NC}"
            exit 1
        fi
        echo "✓ $cmd installed"
    done

    echo -e "${GREEN}All prerequisites met!${NC}\n"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    echo -e "${YELLOW}Deploying infrastructure...${NC}"

    # Create namespaces
    kubectl apply -f ../kubernetes/namespace.yaml

    # Create secrets (ensure they're populated)
    echo "⚠ Make sure secrets are properly configured!"
    kubectl apply -f ../kubernetes/secrets.yaml

    # Create config maps
    kubectl apply -f ../kubernetes/configmap.yaml

    # Deploy RBAC
    kubectl apply -f ../kubernetes/rbac.yaml

    # Deploy monitoring stack
    kubectl apply -f ../kubernetes/monitoring.yaml

    # Wait for monitoring to be ready
    echo "Waiting for Prometheus to be ready..."
    kubectl wait --for=condition=ready pod -l app=prometheus -n ai-agents-monitoring --timeout=300s

    echo -e "${GREEN}✓ Infrastructure deployed${NC}\n"
}

# Function to build agent images
build_agent_images() {
    echo -e "${YELLOW}Building agent Docker images...${NC}"

    # Example: build first 10 agents
    AGENT_DIRS=(../../generated-agents/*/)
    COUNT=0

    for agent_dir in "${AGENT_DIRS[@]}"; do
        if [ $COUNT -ge 10 ]; then
            echo "Built first 10 agents for demo. Use build_all_agents.sh for all 1,500"
            break
        fi

        agent_name=$(basename "$agent_dir")
        echo "Building $agent_name..."

        docker build -t "ai-agents/$agent_name:latest" "$agent_dir"

        if [ "$ENVIRONMENT" == "production" ]; then
            docker tag "ai-agents/$agent_name:latest" "ghcr.io/your-org/$agent_name:latest"
            docker push "ghcr.io/your-org/$agent_name:latest"
        fi

        ((COUNT++))
    done

    echo -e "${GREEN}✓ Agent images built${NC}\n"
}

# Function to deploy agents
deploy_agents() {
    echo -e "${YELLOW}Deploying agents...${NC}"

    # Use the generator to create deployments
    python3 ./generate_k8s_manifests.py --environment=$ENVIRONMENT

    # Apply generated manifests
    kubectl apply -f ./generated-manifests/

    echo -e "${GREEN}✓ Agents deployed${NC}\n"
}

# Function to deploy ingress
deploy_ingress() {
    echo -e "${YELLOW}Deploying ingress...${NC}"

    kubectl apply -f ../kubernetes/ingress.yaml

    echo -e "${GREEN}✓ Ingress deployed${NC}\n"
}

# Function to verify deployment
verify_deployment() {
    echo -e "${YELLOW}Verifying deployment...${NC}"

    # Check namespace
    echo "Checking namespaces..."
    kubectl get namespaces | grep ai-agents

    # Check pods
    echo "Checking pods..."
    kubectl get pods -n ai-agents

    # Check services
    echo "Checking services..."
    kubectl get svc -n ai-agents

    # Run health checks
    echo "Running health checks..."
    python3 ./health_check.py

    echo -e "${GREEN}✓ Deployment verified${NC}\n"
}

# Main deployment flow
main() {
    check_prerequisites

    case $MODE in
        full)
            deploy_infrastructure
            build_agent_images
            deploy_agents
            deploy_ingress
            verify_deployment
            ;;
        infra-only)
            deploy_infrastructure
            ;;
        agents-only)
            build_agent_images
            deploy_agents
            verify_deployment
            ;;
        *)
            echo -e "${RED}Invalid mode: $MODE${NC}"
            echo "Valid modes: full, infra-only, agents-only"
            exit 1
            ;;
    esac

    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Access Grafana: kubectl port-forward -n ai-agents-monitoring svc/grafana 3000:3000"
    echo "2. Access Prometheus: kubectl port-forward -n ai-agents-monitoring svc/prometheus 9090:9090"
    echo "3. Test an agent: curl http://localhost:8209/health"
}

main
