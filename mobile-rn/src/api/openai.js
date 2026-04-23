const OPENAI_URL = 'https://api.openai.com/v1/chat/completions';
const MODEL = 'gpt-4o-mini';

// ── Deep job analysis with GPT-4o-mini ────────────────────────────────────
export async function analyzeJobDeep(apiKey, emailBody) {
  const prompt = `You are an expert job analyst. Extract detailed structured information from this recruiter email.
Return ONLY valid JSON:
{
  "role": "exact job title",
  "company": "company name",
  "location": "city, state or Remote",
  "work_type": "Remote | Hybrid | Onsite",
  "salary_min": null,
  "salary_max": null,
  "experience_years": null,
  "required_skills": ["skill1", "skill2"],
  "nice_skills": ["skill1"],
  "responsibilities": ["resp1", "resp2"],
  "benefits": ["benefit1"],
  "summary": "2 sentence summary of the role",
  "resume_tailoring_notes": "specific advice to tailor resume for this role"
}

Recruiter email:
${emailBody.slice(0, 3000)}`;

  const res = await fetch(OPENAI_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 800,
      temperature: 0.1,
      response_format: { type: 'json_object' },
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `OpenAI error ${res.status}`);
  }

  const data = await res.json();
  try {
    return JSON.parse(data.choices[0].message.content);
  } catch {
    return null;
  }
}

// ── Tailor resume bullets for a specific job ──────────────────────────────
export async function tailorResumeBullets(apiKey, { resumeBullets, jobSummary }) {
  const prompt = `You are a professional resume writer. Rewrite these resume bullet points to better match the job requirements.
Keep the same number of bullets. Keep them truthful. Return ONLY the rewritten bullets as a JSON array of strings.

Job Role: ${jobSummary.role}
Required Skills: ${(jobSummary.required_skills || []).join(', ')}
Resume Tailoring Notes: ${jobSummary.resume_tailoring_notes || ''}

Current bullets:
${resumeBullets.map((b, i) => `${i + 1}. ${b}`).join('\n')}`;

  const res = await fetch(OPENAI_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 600,
      temperature: 0.3,
      response_format: { type: 'json_object' },
    }),
  });

  if (!res.ok) throw new Error(`OpenAI error ${res.status}`);
  const data = await res.json();
  try {
    const parsed = JSON.parse(data.choices[0].message.content);
    return Array.isArray(parsed) ? parsed : parsed.bullets || [];
  } catch {
    return resumeBullets;
  }
}
