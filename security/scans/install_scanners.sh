#!/bin/bash
# Install security scanning tools

echo "Installing Security Scanning Tools..."

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Detected Linux OS"

    # Trivy (container vulnerability scanner)
    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
    echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
    sudo apt-get update
    sudo apt-get install trivy

    # Gitleaks (secrets scanner)
    wget https://github.com/zricethezav/gitleaks/releases/download/v8.18.0/gitleaks_8.18.0_linux_x64.tar.gz
    tar -xzf gitleaks_8.18.0_linux_x64.tar.gz
    sudo mv gitleaks /usr/local/bin/

elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS"

    # Install Homebrew if not present
    if ! command -v brew &> /dev/null; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    # Install tools via Homebrew
    brew install trivy
    brew install gitleaks
    brew install kubesec
fi

# Python-based tools (works on all OS)
pip3 install safety bandit

echo "✓ Security scanning tools installed"
echo ""
echo "Installed tools:"
echo "- Trivy: Docker image vulnerability scanner"
echo "- Safety: Python dependency security checker"
echo "- Bandit: Python code security analyzer"
echo "- Gitleaks: Secrets detection tool"
echo "- Kubesec: Kubernetes security scanner"
