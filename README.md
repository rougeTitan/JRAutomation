# Job Search Automation Platform

An AI-powered job search automation suite — parse recruiter emails, generate tailored resumes, and send smart replies, all from a single web dashboard.

---

## Project Structure

```
gmail_automation/
├── gmail_agent/                 Gmail analyzer + AI dashboard
│   ├── web_ui.py                Flask backend (API server)
│   ├── gmail_categorizer.py     Gmail API: fetch, categorize, send emails
│   ├── job_analyzer.py          Job extraction and classification
│   ├── job_summarizer.py        AI job summarization + tailored resume gen (OpenAI)
│   ├── email_responder.py       AI email reply generation (Groq + Llama 3.1 8B)
│   ├── templates/index.html     Apple-inspired web dashboard UI
│   ├── data/job_analysis.json   Cached job analysis results
│   └── .env                     API keys (not committed to Git)
├── ats_resume_optimizer/        ATS keyword scorer + GPT-4o resume optimizer
├── myResume/                    Your base resume (HTML)
├── resources/                   Resume research dataset
├── job_targets/                 S&P500 job scraper + resume matcher
├── deploy/                      AWS deployment scripts
├── requirements.txt
└── README.md
```

---

## Features

### 📧 Gmail Email Analyzer
- Fetches and categorizes up to 100 recruiter emails via Gmail API
- Extracts job title, company, location, salary, technologies, experience level
- Full email body extraction (no truncation) for accurate AI analysis
- One-click email deletion and 30-day cleanup

### 🤖 AI Job Analysis (OpenAI GPT-4o-mini)
- Structured job summary: role, company, location, work type, compensation
- Required vs nice-to-have skills extraction
- Key responsibilities and requirements parsing
- Resume tailoring notes specific to each job

### 📄 Tailored Resume Generation
- Rewrites professional summary bullets to match each job's requirements
- Highlights added/changed content with amber visual markers
- Dismiss-able highlight banners
- Download as HTML or Print to PDF directly from browser
- Falls back to keyword highlighting when no API key is set

### ✉️ AI Email Reply (Groq + Llama 3.1 8B)
- Generates professional, role-specific reply emails with one click
- 100–150 word emails highlighting matching skills
- Full compose modal: editable To, Subject, Body fields
- AI badge shown when Groq generates the reply
- Template fallback when no Groq key is available
- Regenerate button to get a fresh AI draft
- **Attach Tailored Resume** checkbox — auto-generates and attaches `Siddhesh_DilipKumar_[Role].html`
- Sends via Gmail API in the original thread
- Card turns grey with "Replied" label after sending

### 🎨 Apple-Inspired UI
- Inter font (Google Fonts) + `-apple-system` font stack (SF Pro on Apple devices)
- `#f5f5f7` Apple page background
- Dark charcoal-to-navy header gradient
- Floating white cards with 16–18px border radius and subtle shadows
- Job cards: staggered `fadeSlideUp` entrance animation, `translateY(-3px)` hover lift
- Apple-blue `#0071e3` accent color throughout
- Focus rings and input borders match Apple design language
- Thin 5px custom scrollbar
- All buttons: `scale(0.96)` press feedback micro-interaction
- 22px radius modals with cinematic box-shadows
- Slide panel with `cubic-bezier` easing

---

## API Keys Required

Create `gmail_agent/.env` with:

```env
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here
```

- **OpenAI** (`gpt-4o-mini`) — AI job summarization + tailored resume rewriting
- **Groq** (`llama-3.1-8b-instant`) — Fast, lightweight email reply generation

> Both keys are optional. The app falls back to regex-based highlighting when keys are absent.

---

## Quick Start

```powershell
# Install dependencies
pip install -r requirements.txt

# Start the Gmail dashboard (http://localhost:5000)
python gmail_agent/web_ui.py
```

Then open **http://localhost:5000** in your browser.

### Gmail OAuth Setup (first run only)
1. Place `credentials.json` (from Google Cloud Console) in `gmail_agent/`
2. Run the server — a browser window will open for OAuth consent
3. `token.pickle` is saved automatically for future runs

---

## Dashboard Workflow

1. **Refresh** → fetches latest recruiter emails from Gmail
2. **AI Analyze** → extracts structured job info with GPT-4o-mini
3. **Tailor Resume** → generates a resume with highlighted matching content
4. **Reply** → AI drafts a professional reply, optionally attaches the tailored resume, sends via Gmail

---

## All API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Dashboard UI |
| `GET` | `/api/jobs` | Get all analyzed jobs |
| `GET` | `/api/stats` | Get statistics |
| `GET` | `/api/resume` | Get base resume HTML |
| `POST` | `/api/refresh` | Fetch + analyze latest emails |
| `POST` | `/api/delete-email` | Delete a single email |
| `POST` | `/api/cleanup-old` | Delete emails older than 30 days |
| `POST` | `/api/jobs/<id>/summarize` | AI-summarize a job email |
| `POST` | `/api/jobs/<id>/tailor-resume` | Generate tailored resume HTML |
| `POST` | `/api/jobs/<id>/draft-reply` | Generate AI email draft (Groq) |
| `POST` | `/api/jobs/<id>/send-reply` | Send reply via Gmail API |

---

## Other Modules

| Module | What | How to run |
|--------|------|------------|
| `ats_resume_optimizer/` | ATS keyword scoring + GPT-4o resume optimization | `uvicorn main:app` (port 8000) + `npm run dev` (port 5173) |
| `resources/` | 1000 GitHub resume dataset + deep analysis | `python resources/collect_resumes.py` |
| `job_targets/` | S&P500 job scraper + resume matcher | `python job_targets/scrape_jobs.py` |
| `deploy/` | AWS infrastructure scripts | see `deploy/README.md` |

---

## Dependencies

```
groq>=0.9.0
google-auth==2.23.0
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.100.0
flask==3.0.0
flask-cors==4.0.0
openai>=1.0.0
```

---

## Security Notes

- `gmail_agent/.env` is **not committed to Git** — add it to `.gitignore`
- `credentials.json` and `token.pickle` should also be in `.gitignore`
- Never hardcode API keys in source files

