# 🚀 Quick Deploy Guide (TL;DR)

For experienced users who want to deploy quickly.

## 1️⃣ Launch EC2 Instance

```
• AMI: Ubuntu Server 22.04 LTS
• Instance Type: t2.micro (Free Tier)
• Key Pair: Create new, save .pem file
• Security Group: Allow ports 22, 80, 5000
• Storage: 8GB gp3
```

## 2️⃣ Deploy Files

**From Windows:**
```powershell
cd "c:\Trade Alerts\gmail_automation\deploy"
.\deploy_to_aws.ps1
# Enter IP and key path when prompted
```

## 3️⃣ Setup Server

**SSH to EC2:**
```bash
ssh -i your-key.pem ubuntu@YOUR_PUBLIC_IP
```

**Run setup:**
```bash
cd ~/job-analyzer/deploy
bash server_setup.sh
sudo bash setup_services.sh
sudo bash setup_nginx.sh
sudo bash setup_firewall.sh
```

## 4️⃣ Authenticate Gmail

**SSH with port forwarding:**
```bash
ssh -i your-key.pem -L 5000:localhost:5000 ubuntu@YOUR_PUBLIC_IP
```

**On EC2:**
```bash
cd ~/job-analyzer
source venv/bin/activate
python3 job_analyzer.py
# Complete OAuth in browser on your local machine
```

## 5️⃣ Access Dashboard

```
http://YOUR_PUBLIC_IP
```

**Done! 🎉**

---

## Useful Commands

```bash
# Check status
sudo systemctl status job-analyzer

# View logs
sudo journalctl -u job-analyzer -f

# Restart service
sudo systemctl restart job-analyzer

# Run analysis manually
sudo systemctl start job-analyzer-daily

# Monitor system
bash ~/job-analyzer/deploy/monitor.sh

# Backup
bash ~/job-analyzer/deploy/backup.sh
```

## Cost

- **Year 1:** FREE (AWS Free Tier)
- **After Year 1:** ~$10-12/month

## Support

See `AWS_DEPLOYMENT_GUIDE.md` for detailed documentation.
