# 📧 Job Email Analyzer - Standalone Project

A complete standalone tool to automate job search by analyzing Gmail emails, extracting job details, and presenting them in a beautiful web dashboard.

## 🎯 What This Does

This tool solves a critical problem: **sorting through hundreds of recruiter emails efficiently**.

**Features:**
- ✅ Connects to Gmail via API (secure OAuth2)
- ✅ Scans and categorizes emails automatically
- ✅ **Parses job-related emails** to extract:
  - Job title
  - Recruiter/sender information (name, email, phone, LinkedIn)
  - Job description summary
  - Required technologies/skills
  - Location (city, state, remote/hybrid)
  - Experience level (Junior/Mid/Senior)
  - Salary information (if available)
- ✅ **Web Dashboard** with:
  - Statistics overview
  - Interactive charts
  - Filterable job listings
  - CSV export capability
  - Technology trends
  - Recruiter tracking

## 📁 Project Structure

```
gmail_automation/
├── gmail_categorizer.py      # Gmail API integration
├── job_parser.py              # Intelligent job email parser
├── job_analyzer.py            # Main analysis engine
├── web_ui.py                  # Flask web server
├── templates/
│   └── index.html             # Dashboard UI
├── requirements.txt           # Python dependencies
├── credentials.json           # Gmail API credentials (you create this)
├── token.pickle              # Auth token (auto-generated)
├── job_analysis.json         # Generated report data
├── run_analyzer.bat          # Windows launcher for CLI
├── run_web_ui.bat            # Windows launcher for web UI
├── GMAIL_SETUP.md            # Detailed setup guide
└── PROJECT_README.md         # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd gmail_automation
pip install -r requirements.txt
```

Or use the automated launcher:
```bash
run_analyzer.bat
```

### 2. Setup Gmail API Credentials

**Follow the detailed guide in `GMAIL_SETUP.md`**, but here's the summary:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download as `credentials.json` and place in this folder
5. Add yourself as a test user in OAuth consent screen

### 3. Run the Analyzer

**Option A: Command Line**
```bash
python job_analyzer.py
```

**Option B: Windows Launcher**
```bash
run_analyzer.bat
```

This will:
- Authenticate with Gmail (first time only)
- Scan your emails
- Extract job information
- Generate `job_analysis.json`
- Display console report

### 4. View in Web Dashboard

**Option A: Command Line**
```bash
python web_ui.py
```

**Option B: Windows Launcher**
```bash
run_web_ui.bat
```

Then open: **http://localhost:5000**

## 📊 Dashboard Features

### Statistics Cards
- Total emails processed
- Job opportunities found
- Unique technologies mentioned
- Unique recruiters/senders

### Interactive Charts
- Experience level distribution (pie chart)
- Top 10 technologies (bar chart)

### Filters
- Search by keyword
- Filter by technology
- Filter by experience level

### Job Listings Display
Each job shows:
- ✅ Job title (parsed from email)
- ✅ Recruiter name, email, phone
- ✅ Location
- ✅ Experience level badge
- ✅ Summary of job description
- ✅ Technology tags
- ✅ Salary (if mentioned)
- ✅ Date received
- ✅ Social media links (LinkedIn, etc.)

### Export
- Download filtered results as CSV
- Import into spreadsheets or other tools

## 🎨 How It Works

### 1. Email Categorization (`gmail_categorizer.py`)
Uses keyword matching to categorize emails into:
- Job Related
- Finance/Trading
- Tech Updates
- Promotional
- Social Media
- Shopping
- Automated/Notifications
- Other

### 2. Job Parsing (`job_parser.py`)
Uses regex patterns and NLP techniques to extract:
- **Job titles** - Pattern matching on common title formats
- **Technologies** - Keyword matching against 50+ tech terms
- **Locations** - Pattern matching for US cities/states and remote indicators
- **Experience levels** - Analyzing seniority keywords and years of experience
- **Contact info** - Email, phone, social media links
- **Summaries** - First few sentences of job description

### 3. Analysis & Reporting (`job_analyzer.py`)
- Aggregates statistics
- Tracks trends (most common tech, locations, recruiters)
- Generates JSON report
- Provides console summary

### 4. Web Dashboard (`web_ui.py` + `templates/index.html`)
- Modern responsive design with Tailwind CSS
- Real-time filtering and search
- Interactive charts with Chart.js
- Clean, professional UI

## 🔒 Privacy & Security

- ✅ All authentication via Google OAuth2
- ✅ Credentials stored locally only
- ✅ No data sent to third parties
- ✅ `.gitignore` protects sensitive files
- ✅ Read-only access to emails (with modify for deletion)

## 💡 Use Cases

### Job Search Automation
1. Run analyzer weekly to scan new job emails
2. Review dashboard to find relevant opportunities
3. Filter by preferred technologies
4. Export to spreadsheet for tracking
5. Identify most active recruiters

### Market Intelligence
- See which technologies are most in-demand
- Track salary ranges by role
- Identify hiring hotspots (locations)
- Analyze recruiter patterns

### Email Management
- Quickly identify spam recruiters
- Delete irrelevant job emails in bulk
- Keep only opportunities matching your criteria

## 🛠️ Customization

### Add Custom Technologies
Edit `job_parser.py` line 10-20 to add your tech stack:
```python
self.tech_keywords = [
    'python', 'java', 'your_custom_tech', ...
]
```

### Modify Categorization Rules
Edit `gmail_categorizer.py` line 95-115 to adjust keyword matching

### Change UI Theme
Edit `templates/index.html` - Uses Tailwind CSS classes

## 📝 Example Workflow

```bash
# Step 1: Analyze emails (first time or when you want fresh data)
python job_analyzer.py
# > How many emails to scan? 200
# > [Processing...]
# > ✓ Found 87 job-related emails
# > Report saved to job_analysis.json

# Step 2: Launch web dashboard
python web_ui.py
# > Dashboard available at http://localhost:5000

# Step 3: Browse and filter jobs in your browser
# Step 4: Export CSV for further analysis
# Step 5: Use data for job applications
```

## 🔧 Troubleshooting

### "credentials.json not found"
- Follow `GMAIL_SETUP.md` to create OAuth credentials
- Make sure file is named exactly `credentials.json`
- Place it in the `gmail_automation` folder

### "Access blocked: gmailAutomation has not completed verification"
- Add yourself as a test user in Google Cloud Console
- OAuth consent screen → Test users → Add your email

### "Module not found" errors
- Run: `pip install -r requirements.txt`
- Or use `run_analyzer.bat` which auto-installs

### No data in dashboard
- Run `job_analyzer.py` first to generate data
- Check that `job_analysis.json` exists

## 📈 Future Enhancements

Potential additions:
- AI-powered job matching based on your resume
- Email auto-responder for recruiters
- Integration with job tracking tools
- Automated application submission
- Salary negotiation insights
- Cover letter generation

## 🤝 Support

This is a standalone project created specifically for automating job search email management.

## 📄 License

Free to use and modify for personal use.

---

**Built with:** Python, Flask, Gmail API, Tailwind CSS, Chart.js
**Created:** 2026
**Purpose:** Streamline job search by automating email analysis
