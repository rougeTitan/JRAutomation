#!/bin/bash
# Setup Nginx reverse proxy

set -e

echo "============================================================"
echo "Setting up Nginx Reverse Proxy"
echo "============================================================"
echo ""

# Get EC2 public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

echo "Detected Public IP: $PUBLIC_IP"
echo ""

# Create nginx configuration
echo "Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/job-analyzer > /dev/null <<EOF
server {
    listen 80;
    server_name $PUBLIC_IP;

    client_max_body_size 10M;

    # Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support (if needed in future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files (if any)
    location /static {
        alias /home/ubuntu/job-analyzer/static;
        expires 30d;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable site
echo "Enabling site..."
sudo ln -sf /etc/nginx/sites-available/job-analyzer /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
echo ""
echo "Testing Nginx configuration..."
sudo nginx -t

# Restart nginx
echo "Restarting Nginx..."
sudo systemctl restart nginx
sudo systemctl enable nginx

echo ""
echo "============================================================"
echo "✓ Nginx configured successfully!"
echo "============================================================"
echo ""
echo "Your dashboard is now accessible at:"
echo "  http://$PUBLIC_IP"
echo ""
echo "Direct Flask access (port 5000) still works:"
echo "  http://$PUBLIC_IP:5000"
echo ""
echo "Health check:"
echo "  http://$PUBLIC_IP/health"
echo ""
echo "============================================================"
echo "Optional: Setup SSL/HTTPS"
echo "============================================================"
echo ""
echo "If you have a domain name, you can setup free SSL with:"
echo "  sudo apt install certbot python3-certbot-nginx"
echo "  sudo certbot --nginx -d yourdomain.com"
echo ""
echo "============================================================"
