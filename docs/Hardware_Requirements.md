# Hardware Requirements

## Minimum Requirements (Dev/Test)
- **CPU**: 4 Cores (Modern Intel/AMD/ARM)
- **RAM**: 8 GB
- **Storage**: 20 GB SSD
- **Network**: Broadband Internet connection

## Recommended Requirements (Production - Small Scale)
- **CPU**: 8 Cores
- **RAM**: 16 GB
- **Storage**: 100 GB NVMe SSD
- **Network**: 1 Gbps Ethernet

## Recommended Requirements (Production - Enterprise Scale)
For supporting 50+ concurrent agents and high-throughput event streaming:
- **Orchestration Node**:
    - CPU: 16 Cores
    - RAM: 32 GB
- **Redpanda Cluster**:
    - 3 Nodes
    - CPU: 4 Cores per node
    - RAM: 16 GB per node
    - Storage: High-performance NVMe (RAID 10 recommended)
- **Database (PostgreSQL)**:
    - Managed DBaaS instance (e.g., AWS RDS db.r6g.xlarge)

## Software Prerequisites
- **OS**: Linux (Ubuntu 22.04 LTS recommended) or macOS (for dev)
- **Container Runtime**: Docker Engine 24.0+ & Docker Compose
- **Python**: 3.9+
