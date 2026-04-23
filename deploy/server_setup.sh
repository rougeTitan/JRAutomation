#!/bin/bash
# Server Setup Script for EC2 Instance
# Run this on your EC2 instance after transferring files

set -e

echo "============================================================"
echo "Job Email Analyzer - Server Setup"
echo "============================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

echo ""
echo -e "${YELLOW}Installing Python and dependencies...${NC}"
sudo apt install -y python3 python3-pip python3-venv git nginx

echo ""
echo -e "${YELLOW}Creating virtual environment...${NC}"
cd ~/job-analyzer
python3 -m venv venv
source venv/bin/activate

echo ""
echo -e "${YELLOW}Installing Python packages...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo -e "${GREEN}✓ Server setup complete!${NC}"
echo ""
echo "============================================================"
echo "Next Steps:"
echo "============================================================"
echo ""
echo "1. Setup systemd services (auto-start):"
echo "   cd ~/job-analyzer/deploy"
echo "   sudo bash setup_services.sh"
echo ""
echo "2. Setup Nginx reverse proxy (optional but recommended):"
echo "   sudo bash setup_nginx.sh"
echo ""
echo "3. Authenticate with Gmail (first time only):"
echo "   python3 job_analyzer.py"
echo ""
echo "4. Start web dashboard manually (or use systemd service):"
echo "   python3 web_ui.py"
echo ""
echo "============================================================"
