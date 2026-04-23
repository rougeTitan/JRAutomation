# 📦 AWS Deployment Package

Complete automation scripts for deploying Job Email Analyzer to AWS EC2.

## 📁 Files in This Directory

### Documentation
- **`AWS_DEPLOYMENT_GUIDE.md`** - Complete step-by-step deployment guide (START HERE)
- **`quick_deploy.md`** - Quick reference for experienced users
- **`README.md`** - This file

### Windows Deployment Scripts
- **`deploy_to_aws.ps1`** - PowerShell script to transfer files to EC2

### Linux Server Setup Scripts
- **`server_setup.sh`** - Initial server configuration
- **`setup_services.sh`** - Configure systemd auto-start services
- **`setup_nginx.sh`** - Setup Nginx reverse proxy
- **`setup_firewall.sh`** - Configure UFW firewall

### Maintenance Scripts
- **`monitor.sh`** - System monitoring dashboard
- **`backup.sh`** - Backup credentials and data

## 🚀 Quick Start

### Step 1: Launch EC2 Instance
Follow AWS_DEPLOYMENT_GUIDE.md Step 1 to create your EC2 instance.

### Step 2: Deploy
**From your Windows machine:**
```powershell
cd "c:\Trade Alerts\gmail_automation\deploy"
.\deploy_to_aws.ps1
```

### Step 3: Setup Server
**SSH to your EC2 instance:**
```bash
ssh -i your-key.pem ubuntu@YOUR_PUBLIC_IP
cd ~/job-analyzer/deploy
bash server_setup.sh
sudo bash setup_services.sh
sudo bash setup_nginx.sh
sudo bash setup_firewall.sh
```

### Step 4: Access
Visit: `http://YOUR_PUBLIC_IP`

## 📚 Documentation Order

1. **`AWS_DEPLOYMENT_GUIDE.md`** - Full deployment tutorial
2. **`quick_deploy.md`** - Quick reference once you know the process

## 🔧 Maintenance

### Monitor System
```bash
bash ~/job-analyzer/deploy/monitor.sh
```

### Backup Data
```bash
bash ~/job-analyzer/deploy/backup.sh
```

### View Logs
```bash
sudo journalctl -u job-analyzer -f
```

### Restart Service
```bash
sudo systemctl restart job-analyzer
```

## 💰 Cost

- **Free Tier (12 months):** $0/month
- **After Free Tier:** ~$10-12/month

## 🆘 Troubleshooting

See AWS_DEPLOYMENT_GUIDE.md → Troubleshooting section

Common issues:
- Dashboard not loading → Check security group allows port 5000
- Service won't start → Check logs: `sudo journalctl -u job-analyzer -n 50`
- Out of memory → Add swap space (see guide)

## 🔒 Security Notes

- Store `.pem` key file securely
- Restrict SSH to your IP in security group
- Setup SSL/HTTPS for production use
- Use environment variables for secrets
- Enable UFW firewall

## 📊 What Gets Deployed

```
~/job-analyzer/
├── gmail_categorizer.py
├── job_parser.py
├── job_analyzer.py
├── web_ui.py
├── requirements.txt
├── templates/
│   └── index.html
├── credentials.json (you provide)
├── token.pickle (generated)
└── deploy/
    └── (all these scripts)
```

## ✅ Deployment Checklist

- [ ] EC2 instance launched
- [ ] Security group configured
- [ ] SSH key downloaded
- [ ] Files deployed via `deploy_to_aws.ps1`
- [ ] Server setup complete
- [ ] Services configured
- [ ] Nginx setup (optional)
- [ ] Firewall enabled
- [ ] Gmail authenticated
- [ ] Dashboard accessible
- [ ] Billing alerts configured

---

**Need Help?** See `AWS_DEPLOYMENT_GUIDE.md` for detailed instructions.
