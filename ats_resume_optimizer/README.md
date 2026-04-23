# ATS Resume Optimizer

Personal ATS tool: upload resume + paste job description → get score + AI-optimized resume.

## How It Works

1. **Keyword Match Score** (55% weight) – set-theory overlap between JD and resume keywords (NLTK tokenized, stemmed)
2. **Semantic Score** (45% weight) – TF-IDF cosine similarity between the two documents
3. **AI Optimization** – GPT-4o rewrites your resume to naturally include missing keywords

## Setup

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env
# Edit .env and add your OpenAI API key
uvicorn main:app --reload
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Usage

1. Drop your resume (PDF / DOCX / TXT)
2. Paste the job description
3. Click **Analyze Resume** → see ATS scores + keyword gaps
4. Click **Optimize with AI** → get rewritten resume (requires OpenAI key)
5. Review AI changes marked with `[[ ]]`, download

## Scoring

| Score | Verdict |
|-------|---------|
| ≥ 75% | 🚀 Strong Match – Interview Likely |
| 50–74% | ⚠️ Moderate Match – Needs Improvement |
| < 50% | 🗑️ Weak Match – High Rejection Risk |

## Notes
- Analysis works without OpenAI key (scoring + keyword gap only)
- AI optimization requires `OPENAI_API_KEY` in `backend/.env`
- Always review AI-generated changes before using the resume
