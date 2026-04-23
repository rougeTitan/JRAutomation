#!/bin/bash
# Setup UFW Firewall

set -e

echo "============================================================"
echo "Setting up UFW Firewall"
echo "============================================================"
echo ""

# Install UFW if not present
sudo apt install -y ufw

echo "Configuring firewall rules..."

# Reset to defaults
sudo ufw --force reset

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (critical - don't lock yourself out!)
sudo ufw allow 22/tcp comment 'SSH'

# Allow HTTP
sudo ufw allow 80/tcp comment 'HTTP'

# Allow HTTPS
sudo ufw allow 443/tcp comment 'HTTPS'

# Allow Flask (if not using Nginx)
sudo ufw allow 5000/tcp comment 'Flask Web UI'

# Enable firewall
echo ""
echo "Enabling firewall..."
sudo ufw --force enable

# Show status
echo ""
echo "============================================================"
echo "✓ Firewall configured successfully!"
echo "============================================================"
echo ""
sudo ufw status verbose

echo ""
echo "============================================================"
echo "Security Notes:"
echo "============================================================"
echo "• SSH is allowed from anywhere (port 22)"
echo "• For better security, restrict SSH to your IP:"
echo "  sudo ufw delete allow 22/tcp"
echo "  sudo ufw allow from YOUR_IP to any port 22"
echo ""
echo "• HTTP/HTTPS are open for web access"
echo "• All other incoming ports are blocked by default"
echo "============================================================"
