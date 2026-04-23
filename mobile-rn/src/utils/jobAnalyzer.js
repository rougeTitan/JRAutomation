// Port of gmail_agent/job_analyzer.py + job_summarizer.py logic to JavaScript
// Used as a fallback when no API key is set, or as a pre-filter before AI analysis

const JOB_KEYWORDS = {
  frontend: ['react', 'vue', 'angular', 'javascript', 'typescript', 'css', 'html', 'next.js', 'svelte'],
  backend: ['python', 'node', 'java', 'go', 'rust', 'django', 'fastapi', 'express', 'spring'],
  data: ['sql', 'pandas', 'numpy', 'spark', 'kafka', 'airflow', 'dbt', 'tableau', 'power bi'],
  ml: ['pytorch', 'tensorflow', 'scikit-learn', 'llm', 'nlp', 'computer vision', 'mlops'],
  devops: ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'ci/cd', 'terraform', 'jenkins'],
  mobile: ['swift', 'kotlin', 'react native', 'flutter', 'ios', 'android'],
};

const REMOTE_PATTERNS = [/\bremote\b/i, /\bwork from home\b/i, /\bwfh\b/i];
const HYBRID_PATTERNS = [/\bhybrid\b/i, /\bflexible\b/i];
const SALARY_PATTERNS = [
  /\$\s*(\d{2,3})[kK]?\s*[-–]\s*\$?\s*(\d{2,3})[kK]?/,
  /(\d{2,3}),?000\s*[-–]\s*(\d{2,3}),?000/,
  /salary[:\s]+\$?([\d,]+)/i,
];
const EXPERIENCE_PATTERNS = [
  /(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience/i,
  /(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)/i,
];

// ── Quick regex-based extraction (no API key needed) ───────────────────────
export function quickAnalyze(email) {
  const text = `${email.subject} ${email.body}`.toLowerCase();

  return {
    id: email.id,
    threadId: email.threadId,
    subject: email.subject,
    from: email.from,
    date: email.date,
    snippet: email.snippet,
    role: extractRole(email.subject, email.body),
    company: extractCompany(email.from, email.body),
    location: extractLocation(email.body),
    work_type: extractWorkType(text),
    salary: extractSalary(email.body),
    experience: extractExperience(email.body),
    required_skills: extractSkills(text),
    ai_analyzed: false,
  };
}

function extractRole(subject, body) {
  const patterns = [
    /(?:role|position|title)[:\s]+([^\n,]+)/i,
    /(?:hiring|looking for|seeking)\s+(?:a|an)?\s+([^\n,]+)/i,
    /([A-Z][a-zA-Z\s]+(?:Engineer|Developer|Analyst|Manager|Lead|Architect|Scientist|Designer))/,
  ];
  for (const p of patterns) {
    const m = subject.match(p) || body.match(p);
    if (m) return m[1].trim().slice(0, 60);
  }
  return subject.slice(0, 60);
}

function extractCompany(from, body) {
  const emailDomain = from.match(/@([a-zA-Z0-9-]+)\./)?.[1];
  const companyPattern = body.match(/(?:at|with|for|join)\s+([A-Z][a-zA-Z\s&.,]+?)(?:\s+is|\s+are|\s+has|\.|,)/);
  return companyPattern?.[1]?.trim() || (emailDomain ? emailDomain.charAt(0).toUpperCase() + emailDomain.slice(1) : 'Unknown');
}

function extractLocation(body) {
  const m = body.match(/(?:location|based in|office in)[:\s]+([^\n,]+)/i)
    || body.match(/([A-Z][a-zA-Z]+,\s*[A-Z]{2}(?:\s+\d{5})?)/);
  return m?.[1]?.trim() || 'Not specified';
}

function extractWorkType(text) {
  if (REMOTE_PATTERNS.some(p => p.test(text))) return 'Remote';
  if (HYBRID_PATTERNS.some(p => p.test(text))) return 'Hybrid';
  return 'Onsite';
}

function extractSalary(body) {
  for (const p of SALARY_PATTERNS) {
    const m = body.match(p);
    if (m) return m[0].trim();
  }
  return null;
}

function extractExperience(body) {
  for (const p of EXPERIENCE_PATTERNS) {
    const m = body.match(p);
    if (m) return `${m[1]}${m[2] ? `-${m[2]}` : '+'} years`;
  }
  return null;
}

function extractSkills(text) {
  const found = [];
  for (const skills of Object.values(JOB_KEYWORDS)) {
    for (const skill of skills) {
      if (text.includes(skill.toLowerCase()) && !found.includes(skill)) {
        found.push(skill);
      }
    }
  }
  return found.slice(0, 10);
}

// ── Category label ─────────────────────────────────────────────────────────
export function categorizeRole(skills = []) {
  const s = skills.map(x => x.toLowerCase());
  if (s.some(x => JOB_KEYWORDS.ml.includes(x))) return 'ML/AI';
  if (s.some(x => JOB_KEYWORDS.data.includes(x))) return 'Data';
  if (s.some(x => JOB_KEYWORDS.frontend.includes(x))) return 'Frontend';
  if (s.some(x => JOB_KEYWORDS.backend.includes(x))) return 'Backend';
  if (s.some(x => JOB_KEYWORDS.devops.includes(x))) return 'DevOps';
  if (s.some(x => JOB_KEYWORDS.mobile.includes(x))) return 'Mobile';
  return 'General';
}
