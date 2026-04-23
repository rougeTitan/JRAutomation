const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions';
const MODEL = 'llama-3.1-8b-instant';

// ── Generate a professional email reply ───────────────────────────────────
export async function generateEmailReply(apiKey, { jobSummary, emailBody, senderName }) {
  const systemPrompt = `You are a professional job seeker writing concise, tailored email replies to recruiters. 
Write 100-150 word replies that are professional, enthusiastic, and highlight relevant skills.`;

  const userPrompt = `Write a professional reply to this recruiter email.

Recruiter email snippet:
${emailBody.slice(0, 800)}

Job details:
- Role: ${jobSummary.role || 'Not specified'}
- Company: ${jobSummary.company || 'Not specified'}
- Required skills: ${(jobSummary.required_skills || []).join(', ')}

Write a reply email body only (no subject line, no headers). Be concise, 100-150 words.`;

  const res = await fetch(GROQ_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
      max_tokens: 300,
      temperature: 0.7,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `Groq API error ${res.status}`);
  }

  const data = await res.json();
  return data.choices[0].message.content.trim();
}

// ── Analyze a job email and extract structured info ───────────────────────
export async function analyzeJobEmail(apiKey, emailBody) {
  const prompt = `Extract structured job information from this recruiter email. 
Return ONLY valid JSON with these fields:
{
  "role": "job title",
  "company": "company name", 
  "location": "city/remote",
  "work_type": "remote/hybrid/onsite",
  "salary": "salary range or null",
  "experience": "years required",
  "required_skills": ["skill1", "skill2"],
  "nice_skills": ["skill1"],
  "summary": "2 sentence summary"
}

Email:
${emailBody.slice(0, 2000)}`;

  const res = await fetch(GROQ_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 500,
      temperature: 0.1,
      response_format: { type: 'json_object' },
    }),
  });

  if (!res.ok) throw new Error(`Groq API error ${res.status}`);
  const data = await res.json();

  try {
    return JSON.parse(data.choices[0].message.content);
  } catch {
    return null;
  }
}
