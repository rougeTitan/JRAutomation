#!/bin/bash
# Setup systemd services for auto-start

set -e

echo "============================================================"
echo "Setting up Systemd Services"
echo "============================================================"
echo ""

# Get current user and home directory
USER=$(whoami)
HOME_DIR=$(eval echo ~$USER)
PROJECT_DIR="$HOME_DIR/job-analyzer"

# Create web dashboard service
echo "Creating job-analyzer web service..."
sudo tee /etc/systemd/system/job-analyzer.service > /dev/null <<EOF
[Unit]
Description=Job Email Analyzer Web Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/web_ui.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create daily analysis service
echo "Creating job-analyzer daily analysis service..."
sudo tee /etc/systemd/system/job-analyzer-daily.service > /dev/null <<EOF
[Unit]
Description=Job Email Analyzer - Daily Analysis
After=network.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=/bin/bash -c 'echo "100" | $PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/job_analyzer.py'
EOF

# Create timer for daily analysis
echo "Creating daily analysis timer..."
sudo tee /etc/systemd/system/job-analyzer-daily.timer > /dev/null <<EOF
[Unit]
Description=Job Email Analyzer - Daily Analysis Timer
Requires=job-analyzer-daily.service

[Timer]
OnCalendar=daily
OnCalendar=09:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Reload systemd
echo ""
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable services
echo "Enabling services..."
sudo systemctl enable job-analyzer.service
sudo systemctl enable job-analyzer-daily.timer

# Start services
echo "Starting web dashboard service..."
sudo systemctl start job-analyzer.service

echo "Starting daily analysis timer..."
sudo systemctl start job-analyzer-daily.timer

echo ""
echo "============================================================"
echo "✓ Services configured successfully!"
echo "============================================================"
echo ""
echo "Service Status:"
echo "============================================================"
sudo systemctl status job-analyzer.service --no-pager -l
echo ""
echo "Timer Status:"
echo "============================================================"
sudo systemctl status job-analyzer-daily.timer --no-pager -l
echo ""
echo "============================================================"
echo "Useful Commands:"
echo "============================================================"
echo "View web dashboard logs:   sudo journalctl -u job-analyzer -f"
echo "Restart web dashboard:     sudo systemctl restart job-analyzer"
echo "Stop web dashboard:        sudo systemctl stop job-analyzer"
echo "Check timer schedule:      systemctl list-timers"
echo "Run analysis manually:     sudo systemctl start job-analyzer-daily"
echo "============================================================"
