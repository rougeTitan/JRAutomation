# Gmail Email Categorizer - Setup Guide

## Overview
This tool connects to your Gmail account, reads your emails, categorizes them automatically, and generates a detailed report. You can then take actions like deleting emails by category.

## 🔧 Setup Instructions

### Step 1: Install Dependencies

```bash
cd gmail_automation
pip install -r requirements.txt
```

### Step 2: Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Gmail API**:
   - Click on "Enable APIs and Services"
   - Search for "Gmail API"
   - Click "Enable"

### Step 3: Create OAuth 2.0 Credentials

1. In Google Cloud Console, go to **APIs & Services > Credentials**
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. If prompted, configure the OAuth consent screen:
   - User Type: **External**
   - App name: `Gmail Email Categorizer`
   - User support email: Your email
   - Developer contact: Your email
   - Click **Save and Continue**
   - Skip Scopes, Test Users, and Summary
4. Create OAuth Client ID:
   - Application type: **Desktop app**
   - Name: `Gmail Categorizer`
   - Click **Create**
5. Download the JSON file
6. **Rename it to `credentials.json`** and place it in the `gmail_automation` folder

### Step 4: Run the Tool

```bash
python gmail_categorizer.py
```

On first run:
- A browser window will open
- Sign in to your Google account
- Click **"Allow"** to grant permissions
- The tool will save authentication token for future use

## 📧 Features

### Automatic Categorization
Emails are automatically sorted into these categories:

- **Job Related** - Job postings, recruiter emails, LinkedIn notifications
- **Finance/Trading** - Stock alerts, market updates, trading notifications
- **Tech Updates/Informational** - Newsletters, tech blogs, updates
- **Social Media** - Facebook, Twitter, Instagram notifications
- **Shopping/Orders** - Amazon, purchase receipts, shipping updates
- **Promotional/Marketing** - Sales, discounts, marketing emails
- **Automated/Notifications** - System-generated emails
- **Other/Uncategorized** - Everything else

### Report Generation
The tool creates:
- Console summary with email counts per category
- Detailed JSON report (`email_report.json`) with all email metadata
- Preview of first 5 emails in each category

### Email Management
After categorization, you can:
- Delete all emails in a specific category
- Export detailed reports
- Review categories before taking action

## 🔐 Security Notes

- `credentials.json` - Your OAuth credentials (keep private)
- `token.pickle` - Authentication token (automatically generated)
- **Add both to `.gitignore`** to prevent accidental commits
- The tool only requests necessary permissions (read/modify emails)

## 📊 Usage Example

```bash
$ python gmail_categorizer.py

How many emails to process? (default: 100): 50

📧 Fetching and processing up to 50 emails...
✓ Found 50 emails to process
✓ Processed 50 emails successfully

============================================================
EMAIL CATEGORIZATION REPORT
============================================================

Finance/Trading: 12 emails
------------------------------------------------------------
  • AAPL Alert: Price Movement Detected...
    From: alerts@tradealerts.com
  ... and 11 more emails

Job Related: 8 emails
------------------------------------------------------------
  • Software Engineer Position - TechCorp...
    From: recruiter@techcorp.com
  ... and 7 more emails

Promotional/Marketing: 25 emails
------------------------------------------------------------
  • Limited Time Offer: 50% OFF...
    From: marketing@store.com
  ... and 24 more emails

============================================================
TOTAL EMAILS PROCESSED: 50
============================================================

What would you like to do next?
1. Delete emails by category
2. Export detailed report
3. Exit
```

## 🚀 Advanced Usage

### Customize Categories
Edit the `categorize_email()` method in `gmail_categorizer.py` to add your own keyword rules.

### Filter by Query
Modify the `fetch_emails()` call to use Gmail search syntax:
```python
categorizer.fetch_emails(max_results=100, query='is:unread')
```

### Automated Cleanup
Create a scheduled script to run daily and auto-delete promotional emails:
```python
categorizer = GmailCategorizer()
categorizer.authenticate()
categorizer.process_emails(max_emails=100)
categorizer.delete_emails_by_category('Promotional/Marketing')
```

## 🛠️ Troubleshooting

**Error: credentials.json not found**
- Make sure you downloaded and renamed the OAuth credentials file
- Place it in the `gmail_automation` folder

**Authentication fails**
- Delete `token.pickle` and re-authenticate
- Check that Gmail API is enabled in Google Cloud Console

**Missing emails**
- Increase `max_emails` parameter
- Check if emails are archived (not in inbox)

## ⚠️ Important Notes

- First run requires browser authentication
- Token expires periodically - re-authenticate when prompted
- Deleted emails go to Trash (recoverable for 30 days)
- Process emails in batches to avoid API rate limits
