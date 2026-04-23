import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
        _client = OpenAI(api_key=api_key)
    return _client


SYSTEM_PROMPT = """You are an expert resume writer and ATS optimization specialist.
Your task is to rewrite the provided resume so it:
1. Naturally incorporates the MISSING keywords from the job description
2. Aligns phrasing and terminology with the job description
3. Keeps all factual information accurate – DO NOT invent experience or skills
4. Uses strong action verbs and quantifiable achievements where possible
5. Maintains a clean, ATS-parseable structure (no tables, columns, or graphics)
6. Returns the full rewritten resume as plain text, preserving all sections
7. Highlights added/changed content by wrapping it in [[ ]] markers so the user can review

Return ONLY the rewritten resume text. No extra commentary."""


def optimize_resume(resume_text: str, jd_text: str, missing_keywords: list[str]) -> str:
    client = _get_client()

    missing_kw_str = ", ".join(missing_keywords[:30]) if missing_keywords else "None identified"

    user_prompt = f"""JOB DESCRIPTION:
{jd_text}

MISSING KEYWORDS TO INCORPORATE:
{missing_kw_str}

ORIGINAL RESUME:
{resume_text}

Rewrite the resume above to better match the job description."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=4096,
    )

    return response.choices[0].message.content.strip()
