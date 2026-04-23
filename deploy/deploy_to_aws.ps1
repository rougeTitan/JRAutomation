# AWS Deployment Script for Windows
# Automates file transfer to EC2 instance

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Job Email Analyzer - AWS Deployment Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Get EC2 instance details
$EC2_IP = "34.227.79.200"
$KEY_PATH = "C:\Users\siddh\Downloads\job-email-analyzer-key-pair.pem"

if (-not (Test-Path $KEY_PATH)) {
    Write-Host "Error: Key file not found at $KEY_PATH" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Testing SSH connection..." -ForegroundColor Yellow
ssh -i $KEY_PATH -o ConnectTimeout=10 ubuntu@$EC2_IP "echo 'Connection successful'"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Cannot connect to EC2 instance. Check IP and key file." -ForegroundColor Red
    exit 1
}

Write-Host "Connection successful!" -ForegroundColor Green
Write-Host ""

# Set parent directory
$PROJECT_DIR = Split-Path -Parent $PSScriptRoot

Write-Host "Preparing files for deployment..." -ForegroundColor Yellow

# Create temporary deployment directory
$TEMP_DEPLOY = Join-Path $env:TEMP "job-analyzer-deploy"
if (Test-Path $TEMP_DEPLOY) {
    Remove-Item -Recurse -Force $TEMP_DEPLOY
}
New-Item -ItemType Directory -Path $TEMP_DEPLOY | Out-Null

# Copy necessary files
Write-Host "Copying project files..." -ForegroundColor Yellow

$FILES_TO_COPY = @(
    "gmail_categorizer.py",
    "job_parser.py",
    "job_analyzer.py",
    "web_ui.py",
    "requirements.txt",
    "templates",
    "deploy"
)

foreach ($file in $FILES_TO_COPY) {
    $source = Join-Path $PROJECT_DIR $file
    if (Test-Path $source) {
        Copy-Item -Path $source -Destination $TEMP_DEPLOY -Recurse -Force
        Write-Host "  ✓ Copied $file" -ForegroundColor Green
    }
}

# Check for credentials
$CREDS_PATH = Join-Path $PROJECT_DIR "credentials.json"
if (Test-Path $CREDS_PATH) {
    Write-Host ""
    $copy_creds = Read-Host "Copy credentials.json to server? (yes/no)"
    if ($copy_creds -eq "yes") {
        Copy-Item -Path $CREDS_PATH -Destination $TEMP_DEPLOY -Force
        Write-Host "  ✓ Copied credentials.json" -ForegroundColor Green
    }
}

# Check for token
$TOKEN_PATH = Join-Path $PROJECT_DIR "token.pickle"
if (Test-Path $TOKEN_PATH) {
    Write-Host ""
    $copy_token = Read-Host "Copy token.pickle to server? (yes/no)"
    if ($copy_token -eq "yes") {
        Copy-Item -Path $TOKEN_PATH -Destination $TEMP_DEPLOY -Force
        Write-Host "  ✓ Copied token.pickle" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Transferring files to EC2 instance..." -ForegroundColor Yellow

# Create directory on server
ssh -i $KEY_PATH ubuntu@$EC2_IP "mkdir -p ~/job-analyzer"

# Transfer files using SCP
scp -i $KEY_PATH -r "$TEMP_DEPLOY\*" ubuntu@${EC2_IP}:~/job-analyzer/

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Files transferred successfully!" -ForegroundColor Green
} else {
    Write-Host "Error: File transfer failed" -ForegroundColor Red
    exit 1
}

# Cleanup
Remove-Item -Recurse -Force $TEMP_DEPLOY

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "EC2 Instance: $EC2_IP" -ForegroundColor White
Write-Host "Files deployed to: ~/job-analyzer/" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Connect to your instance:" -ForegroundColor White
Write-Host "   ssh -i $KEY_PATH ubuntu@$EC2_IP" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Run the server setup script:" -ForegroundColor White
Write-Host "   cd ~/job-analyzer/deploy" -ForegroundColor Gray
Write-Host "   bash server_setup.sh" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Access your dashboard at:" -ForegroundColor White
Write-Host "   http://${EC2_IP}:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

# Ask if user wants to SSH now
$ssh_now = Read-Host "Connect to EC2 instance now? (yes/no)"
if ($ssh_now -eq "yes") {
    ssh -i $KEY_PATH ubuntu@$EC2_IP
}
