#!/bin/bash
# Backup script for credentials and data

BACKUP_DIR=~/job-analyzer-backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

echo "============================================================"
echo "Job Email Analyzer - Backup Script"
echo "============================================================"
echo ""

# Create backup directory
mkdir -p $BACKUP_DIR

echo "Creating backup: $BACKUP_FILE"

# Backup important files
cd ~/job-analyzer
tar -czf $BACKUP_FILE \
    credentials.json \
    token.pickle \
    job_analysis.json \
    --exclude='venv' \
    --exclude='__pycache__' \
    2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ Backup created successfully"
    echo "  Location: $BACKUP_FILE"
    echo "  Size: $(du -h $BACKUP_FILE | cut -f1)"
else
    echo "✗ Backup failed"
    exit 1
fi

# Keep only last 7 backups
echo ""
echo "Cleaning old backups (keeping last 7)..."
cd $BACKUP_DIR
ls -t backup_*.tar.gz | tail -n +8 | xargs -r rm
echo "✓ Cleanup complete"

echo ""
echo "Available backups:"
ls -lh $BACKUP_DIR/backup_*.tar.gz

echo ""
echo "To restore a backup:"
echo "  tar -xzf $BACKUP_FILE -C ~/job-analyzer"
echo ""
