# 🚀 AWS EC2 Deployment Guide - Job Email Analyzer

Complete guide to deploy your Job Email Analyzer on AWS EC2 Free Tier.

## 📋 Prerequisites

- AWS Account (sign up at https://aws.amazon.com)
- Gmail API credentials (`credentials.json`) - already configured
- Basic terminal/SSH knowledge

## 💰 Cost Estimate

**Free Tier (First 12 months):**
- EC2 t2.micro: FREE (750 hours/month)
- EBS Storage 30GB: FREE
- Data Transfer 15GB/month: FREE

**After Free Tier:** ~$10-12/month

---

## 🎯 Deployment Steps

### Step 1: Launch EC2 Instance

1. **Login to AWS Console**: https://console.aws.amazon.com/
2. **Go to EC2 Dashboard**: Services → EC2
3. **Launch Instance**:
   - Click **"Launch Instance"**
   - **Name**: `job-email-analyzer`

4. **Choose AMI**:
   - Select **"Ubuntu Server 22.04 LTS"** (Free tier eligible)

5. **Instance Type**:
   - Select **"t2.micro"** (1 vCPU, 1GB RAM) - Free tier eligible

6. **Key Pair**:
   - Click **"Create new key pair"**
   - Name: `job-analyzer-key`
   - Type: RSA
   - Format: `.pem` (for Mac/Linux) or `.ppk` (for Windows/PuTTY)
   - Click **"Create key pair"** and save file securely

7. **Network Settings**:
   - ✅ Allow SSH traffic from: **My IP** (more secure)
   - ✅ Allow HTTP traffic from: **Anywhere** (0.0.0.0/0)
   - ✅ Allow HTTPS traffic from: **Anywhere** (0.0.0.0/0)
   - Click **"Edit"** and add custom rule:
     - Type: **Custom TCP**
     - Port: **5000**
     - Source: **Anywhere** (0.0.0.0/0)
     - Description: Flask Web UI

8. **Configure Storage**:
   - Size: **8 GB** (Free tier allows up to 30GB)
   - Type: **gp3** (General Purpose SSD)

9. **Advanced Details** (Optional):
   - Leave defaults

10. **Launch**:
    - Review and click **"Launch instance"**
    - Wait 2-3 minutes for instance to start

### Step 2: Connect to Your Instance

**Get Instance Details:**
1. Go to EC2 Dashboard → Instances
2. Select your instance
3. Copy **"Public IPv4 address"** (e.g., 3.85.123.45)

**Windows Users (Using PowerShell/CMD):**
```powershell
# Navigate to where you saved the key
cd Downloads

# Set proper permissions (if needed)
icacls job-analyzer-key.pem /inheritance:r
icacls job-analyzer-key.pem /grant:r "%username%":"(R)"

# Connect via SSH
ssh -i job-analyzer-key.pem ubuntu@YOUR_PUBLIC_IP
```

**Mac/Linux Users:**
```bash
# Set proper permissions
chmod 400 job-analyzer-key.pem

# Connect
ssh -i job-analyzer-key.pem ubuntu@YOUR_PUBLIC_IP
```

Type `yes` when prompted about fingerprint.

### Step 3: Server Setup (Automated)

Once connected to your EC2 instance, run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv git

# Install nginx (web server for production)
sudo apt install -y nginx

# Create application directory
mkdir -p ~/job-analyzer
cd ~/job-analyzer
```

### Step 4: Transfer Your Project Files

**Option A: Use the deployment script (Recommended)**

On your **local machine** (Windows):
```powershell
cd "c:\Trade Alerts\gmail_automation\deploy"
.\deploy_to_aws.ps1
# Follow prompts for IP address and key file location
```

**Option B: Manual SCP Transfer**

On your **local machine**:
```powershell
# Navigate to gmail_automation folder
cd "c:\Trade Alerts\gmail_automation"

# Transfer files (replace YOUR_PUBLIC_IP and path to key)
scp -i C:\path\to\job-analyzer-key.pem -r . ubuntu@YOUR_PUBLIC_IP:~/job-analyzer/

# Transfer credentials separately (important!)
scp -i C:\path\to\job-analyzer-key.pem credentials.json ubuntu@YOUR_PUBLIC_IP:~/job-analyzer/
```

### Step 5: Server Configuration (On EC2)

```bash
# Navigate to project
cd ~/job-analyzer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set proper permissions
chmod +x deploy/*.sh
```

### Step 6: Initial Gmail Authentication

**IMPORTANT**: Gmail OAuth requires browser authentication on first run.

**Method 1: SSH Port Forwarding (Recommended)**

On your **local machine**, create a new SSH connection with port forwarding:

```powershell
ssh -i job-analyzer-key.pem -L 5000:localhost:5000 ubuntu@YOUR_PUBLIC_IP
```

Then on the EC2 instance:
```bash
cd ~/job-analyzer
source venv/bin/activate
python3 job_analyzer.py
# Browser will open on your LOCAL machine for authentication
```

**Method 2: Temporary Public Access**

```bash
# Run analyzer to generate auth URL
python3 job_analyzer.py
# Copy the URL shown, paste in your browser, complete auth
# token.pickle will be created
```

After authentication, you can close this connection.

### Step 7: Setup Systemd Services (Auto-start)

Run the setup script:
```bash
cd ~/job-analyzer/deploy
sudo bash setup_services.sh
```

This creates two services:
- **job-analyzer.service**: Runs web dashboard 24/7
- **job-analyzer-daily.timer**: Runs email analysis daily at 9 AM

**Manual Service Commands:**
```bash
# Start web dashboard
sudo systemctl start job-analyzer

# Enable auto-start on boot
sudo systemctl enable job-analyzer

# Check status
sudo systemctl status job-analyzer

# View logs
sudo journalctl -u job-analyzer -f

# Restart service
sudo systemctl restart job-analyzer
```

### Step 8: Configure Nginx (Production Web Server)

```bash
cd ~/job-analyzer/deploy
sudo bash setup_nginx.sh
```

This configures Nginx as a reverse proxy for better performance and security.

### Step 9: Access Your Dashboard

**Via Public IP:**
```
http://YOUR_PUBLIC_IP:5000
```

**Or with Nginx (port 80):**
```
http://YOUR_PUBLIC_IP
```

---

## 🔒 Security Best Practices

### 1. **Restrict SSH Access**

Edit security group to allow SSH only from your IP:
1. EC2 Dashboard → Security Groups
2. Select your instance's security group
3. Edit Inbound Rules
4. SSH rule: Change source to **"My IP"**

### 2. **Use Environment Variables for Credentials**

```bash
# On EC2 instance
cd ~/job-analyzer
nano .env
```

Add:
```
GMAIL_CREDENTIALS_FILE=/home/ubuntu/job-analyzer/credentials.json
GMAIL_TOKEN_FILE=/home/ubuntu/job-analyzer/token.pickle
```

### 3. **Setup Firewall (UFW)**

```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 5000/tcp # Flask (if not using Nginx)
sudo ufw enable
sudo ufw status
```

### 4. **Setup SSL/HTTPS (Optional but Recommended)**

If you have a domain name:
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
```

---

## 📊 Monitoring & Maintenance

### Check Application Status
```bash
# Web dashboard status
sudo systemctl status job-analyzer

# Daily analyzer timer
sudo systemctl status job-analyzer-daily.timer

# View logs
sudo journalctl -u job-analyzer -n 100
```

### View Analysis Results
```bash
cd ~/job-analyzer
cat job_analysis.json | python3 -m json.tool | less
```

### Manual Email Analysis
```bash
cd ~/job-analyzer
source venv/bin/activate
python3 job_analyzer.py
```

### Update Application
```bash
cd ~/job-analyzer
git pull  # if using git
sudo systemctl restart job-analyzer
```

---

## 🔧 Troubleshooting

### Dashboard Not Loading

1. **Check service status:**
   ```bash
   sudo systemctl status job-analyzer
   ```

2. **Check logs:**
   ```bash
   sudo journalctl -u job-analyzer -n 50
   ```

3. **Restart service:**
   ```bash
   sudo systemctl restart job-analyzer
   ```

### Port 5000 Not Accessible

1. **Verify security group allows port 5000**
2. **Check firewall:**
   ```bash
   sudo ufw status
   ```
3. **Ensure service is running:**
   ```bash
   sudo netstat -tlnp | grep 5000
   ```

### Gmail Authentication Issues

1. **Re-authenticate:**
   ```bash
   cd ~/job-analyzer
   rm token.pickle
   python3 job_analyzer.py
   ```

2. **Use port forwarding method** (see Step 6)

### Out of Memory

If t2.micro runs out of memory, add swap:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 💡 Optimization Tips

### 1. **Reduce Email Scan Frequency**

Edit daily timer:
```bash
sudo nano /etc/systemd/system/job-analyzer-daily.timer
# Change OnCalendar=daily to weekly/monthly
sudo systemctl daemon-reload
```

### 2. **Enable Response Compression**

Already configured in nginx setup for faster loading.

### 3. **Setup CloudWatch Monitoring**

Monitor EC2 metrics:
- CPU utilization
- Network traffic
- Disk usage

Access at: AWS Console → CloudWatch → Dashboards

---

## 💰 Cost Management

### Monitor Your Usage

1. **AWS Billing Dashboard**: https://console.aws.amazon.com/billing/
2. **Set Billing Alerts**:
   - Go to CloudWatch → Billing → Create Alarm
   - Set threshold: $10/month
   - Get email when approaching limit

### Reduce Costs

1. **Stop instance when not needed:**
   ```bash
   # From AWS Console or CLI
   aws ec2 stop-instances --instance-ids i-1234567890abcdef0
   ```

2. **Schedule auto-shutdown:**
   ```bash
   # Add to crontab on EC2
   crontab -e
   # Add: 0 2 * * * sudo shutdown -h now
   # (Shuts down at 2 AM daily)
   ```

3. **Use CloudWatch for auto-stop/start**

---

## 🎓 Learning Resources

**AWS Fundamentals:**
- EC2 Documentation: https://docs.aws.amazon.com/ec2/
- Free Tier Details: https://aws.amazon.com/free/

**System Administration:**
- Systemd Services: https://www.freedesktop.org/software/systemd/man/systemd.service.html
- Nginx Configuration: https://nginx.org/en/docs/

---

## 📝 Quick Reference Commands

```bash
# Service Management
sudo systemctl start job-analyzer       # Start dashboard
sudo systemctl stop job-analyzer        # Stop dashboard
sudo systemctl restart job-analyzer     # Restart dashboard
sudo systemctl status job-analyzer      # Check status

# View Logs
sudo journalctl -u job-analyzer -f      # Follow logs live
sudo journalctl -u job-analyzer -n 100  # Last 100 lines

# Application
cd ~/job-analyzer && source venv/bin/activate
python3 job_analyzer.py                 # Run analysis manually
python3 web_ui.py                       # Start web UI manually

# System
df -h                                   # Check disk space
free -m                                 # Check memory
top                                     # CPU usage
```

---

## ✅ Deployment Checklist

- [ ] AWS account created
- [ ] EC2 instance launched (t2.micro)
- [ ] Security group configured (ports 22, 80, 5000)
- [ ] SSH key downloaded and secured
- [ ] Connected to instance via SSH
- [ ] System updated
- [ ] Python and dependencies installed
- [ ] Project files transferred
- [ ] Virtual environment created
- [ ] Python packages installed
- [ ] Gmail authentication completed
- [ ] Systemd services configured
- [ ] Services enabled and started
- [ ] Nginx configured (optional)
- [ ] Firewall configured
- [ ] Dashboard accessible
- [ ] Billing alerts set up

---

**Deployment Complete! 🎉**

Your Job Email Analyzer is now running 24/7 on AWS EC2.

Access your dashboard at: `http://YOUR_PUBLIC_IP:5000`
