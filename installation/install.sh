#!/bin/bash
# One-Command Installation for AI Agents Platform
# Installs everything needed to run the platform locally

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
    _    ___      _                    _
   / \  |_ _|    / \   __ _  ___ _ __ | |_ ___
  / _ \  | |    / _ \ / _` |/ _ \ '_ \| __/ __|
 / ___ \ | |   / ___ \ (_| |  __/ | | | |_\__ \
/_/   \_\___| /_/   \_\__, |\___|_| |_|\__|___/
                      |___/
         Platform Installation Script
EOF
echo -e "${NC}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AI Agents Platform - Installation${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose installed${NC}"

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.template .env
    echo -e "${YELLOW}⚠ Please edit .env and add your ANTHROPIC_API_KEY${NC}"
    echo -e "${YELLOW}   Then run this script again.${NC}"
    exit 0
fi

# Load environment variables
source .env

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your-api-key-here" ]; then
    echo -e "${RED}Error: ANTHROPIC_API_KEY not set in .env file${NC}"
    echo -e "${YELLOW}Please edit .env and add your Anthropic API key${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Configuration loaded${NC}"
echo ""

# Create required directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p logs ssl scan-results

# Generate Prometheus config if not exists
if [ ! -f "prometheus.yml" ]; then
    echo -e "${YELLOW}Creating Prometheus configuration...${NC}"
    cat > prometheus.yml << 'PROMEOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'agents'
    static_configs:
      - targets: ['business-plan-agent:8209']
    metrics_path: '/metrics'
PROMEOF
fi

# Generate Nginx config if not exists
if [ ! -f "nginx.conf" ]; then
    echo -e "${YELLOW}Creating Nginx configuration...${NC}"
    cat > nginx.conf << 'NGINXEOF'
events {
    worker_connections 1024;
}

http {
    upstream agents {
        server business-plan-agent:8209;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://agents;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /consul {
            proxy_pass http://consul:8500;
        }

        location /vault {
            proxy_pass http://vault:8200;
        }
    }
}
NGINXEOF
fi

# Generate database init script
if [ ! -f "init-db.sql" ]; then
    echo -e "${YELLOW}Creating database initialization script...${NC}"
    cat > init-db.sql << 'SQLEOF'
-- AI Agents Platform Database Schema

CREATE TABLE IF NOT EXISTS agents (
    agent_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_requests (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    task_description TEXT NOT NULL,
    response TEXT,
    tokens_used INTEGER,
    processing_time_ms FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

CREATE INDEX idx_agent_requests_agent_id ON agent_requests(agent_id);
CREATE INDEX idx_agent_requests_created_at ON agent_requests(created_at);

-- Insert sample agent
INSERT INTO agents (agent_id, name, category, version)
VALUES ('business_plan_agent_009', 'Business Plan Agent', 'business_ops', '1.0.0')
ON CONFLICT (agent_id) DO NOTHING;
SQLEOF
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Installation${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Pull required images
echo -e "${YELLOW}[1/4] Pulling Docker images...${NC}"
docker-compose -f docker-compose.full.yml pull

# Build agent images
echo -e "${YELLOW}[2/4] Building agent images...${NC}"
echo -e "${BLUE}Building business-plan-agent...${NC}"
docker-compose -f docker-compose.full.yml build business-plan-agent

# Start services
echo -e "${YELLOW}[3/4] Starting services...${NC}"
docker-compose -f docker-compose.full.yml up -d

# Wait for services to be healthy
echo -e "${YELLOW}[4/4] Waiting for services to be ready...${NC}"
echo -e "${BLUE}This may take 30-60 seconds...${NC}"

# Wait for database
echo -n "Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker-compose -f docker-compose.full.yml exec -T postgres pg_isready -U $DB_USER > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for Redis
echo -n "Waiting for Redis..."
for i in {1..30}; do
    if docker-compose -f docker-compose.full.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for agent
echo -n "Waiting for Business Plan Agent..."
for i in {1..60}; do
    if curl -sf http://localhost:8209/health > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Display service URLs
echo -e "${BLUE}Service URLs:${NC}"
echo "  • API Gateway:     http://localhost"
echo "  • Business Plan:   http://localhost:8209"
echo "  • Grafana:         http://localhost:3000 (admin/$GRAFANA_PASSWORD)"
echo "  • Prometheus:      http://localhost:9090"
echo "  • Consul:          http://localhost:8500"
echo "  • Vault:           http://localhost:8200"
echo ""

# Test agent
echo -e "${BLUE}Testing agent...${NC}"
RESPONSE=$(curl -s -X POST http://localhost:8209/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Write a one-sentence business idea"}' || echo "Failed")

if [[ $RESPONSE == *"result"* ]]; then
    echo -e "${GREEN}✓ Agent is responding!${NC}"
else
    echo -e "${YELLOW}⚠ Agent may need more time to start${NC}"
fi

echo ""
echo -e "${BLUE}Quick Start:${NC}"
echo "  1. Test agent:"
echo "     curl -X POST http://localhost:8209/api/v1/execute \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"task_description\": \"Create a business plan for a coffee shop\"}'"
echo ""
echo "  2. View logs:"
echo "     docker-compose -f docker-compose.full.yml logs -f"
echo ""
echo "  3. Stop platform:"
echo "     docker-compose -f docker-compose.full.yml down"
echo ""

echo -e "${GREEN}Documentation:${NC}"
echo "  • User Guide:      docs/training/03_ENDUSER_TRAINING_MANUAL.md"
echo "  • Developer Guide: docs/training/02_DEVELOPER_TRAINING_MANUAL.md"
echo "  • Admin Guide:     docs/training/01_ADMIN_TRAINING_MANUAL.md"
echo ""

echo -e "${GREEN}Happy automating! 🚀${NC}"
