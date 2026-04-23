#!/bin/bash
# Monitoring script for Job Email Analyzer

echo "============================================================"
echo "Job Email Analyzer - System Monitor"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check web service status
echo -e "${YELLOW}Web Dashboard Service:${NC}"
if systemctl is-active --quiet job-analyzer; then
    echo -e "  Status: ${GREEN}RUNNING${NC}"
    echo "  Uptime: $(systemctl show job-analyzer --property=ActiveEnterTimestamp | cut -d'=' -f2)"
else
    echo -e "  Status: ${RED}STOPPED${NC}"
fi

# Check memory usage
echo ""
echo -e "${YELLOW}Memory Usage:${NC}"
free -h | grep -E 'Mem|Swap'

# Check disk usage
echo ""
echo -e "${YELLOW}Disk Usage:${NC}"
df -h / | tail -n 1

# Check CPU load
echo ""
echo -e "${YELLOW}CPU Load:${NC}"
uptime

# Check recent analysis
echo ""
echo -e "${YELLOW}Last Email Analysis:${NC}"
if [ -f ~/job-analyzer/job_analysis.json ]; then
    LAST_RUN=$(stat -c %y ~/job-analyzer/job_analysis.json | cut -d'.' -f1)
    JOBS=$(grep -o '"job_emails_found": [0-9]*' ~/job-analyzer/job_analysis.json | grep -o '[0-9]*')
    echo "  Last run: $LAST_RUN"
    echo "  Jobs found: $JOBS"
else
    echo "  No analysis data found"
fi

# Check next scheduled analysis
echo ""
echo -e "${YELLOW}Next Scheduled Analysis:${NC}"
systemctl list-timers job-analyzer-daily.timer --no-pager | grep job-analyzer-daily

# Check recent logs
echo ""
echo -e "${YELLOW}Recent Logs (last 5 lines):${NC}"
journalctl -u job-analyzer -n 5 --no-pager

# Check network connectivity
echo ""
echo -e "${YELLOW}Network Connectivity:${NC}"
if curl -s --head http://localhost:5000 > /dev/null; then
    echo -e "  Local dashboard: ${GREEN}ACCESSIBLE${NC}"
else
    echo -e "  Local dashboard: ${RED}NOT ACCESSIBLE${NC}"
fi

# Check port 5000
echo ""
echo -e "${YELLOW}Port Status:${NC}"
sudo netstat -tlnp | grep 5000 || echo "  Port 5000 not listening"

echo ""
echo "============================================================"
