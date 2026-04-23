import os
import re

CANDIDATE_NAME = "Siddhesh Dilipkumar"
CANDIDATE_EMAIL = "siddheshdilipkumar@gmail.com"
CANDIDATE_PHONE = "617-697-3776"
CANDIDATE_PROFILE = (
    "7+ years Software Engineer specializing in full-stack development. "
    "Expert in Java, Spring Boot, Kafka, Angular, Node.js, React, AWS, "
    "Docker, Kubernetes, Microservices, CI/CD, PostgreSQL, MongoDB."
)


def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())


def _template_reply(role: str, company: str, sender_name: str,
                    skills: str, work_type: str, location: str) -> str:
    company_str = f" at {company}" if company and company not in ('Not mentioned', 'See email', '') else ""
    work_str = f" ({work_type})" if work_type and work_type not in ('Not specified',) else ""
    loc_str = f" in {location}" if location and location not in ('Not specified', 'See email', '') else ""
    skills_str = f"My background includes strong expertise in {skills}." if skills else ""
    first_name = sender_name.split()[0] if sender_name else "there"
    return (
        f"Hi {first_name},\n\n"
        f"Thank you for reaching out regarding the {role}{company_str}{work_str}{loc_str} opportunity. "
        f"I am very interested in this role and believe my experience is a strong match.\n\n"
        f"{skills_str}\n\n"
        f"I have attached my resume for your review and would welcome the opportunity to discuss "
        f"how my background aligns with your requirements. I am available for a call at your earliest convenience.\n\n"
        f"Best regards,\n"
        f"{CANDIDATE_NAME}\n"
        f"{CANDIDATE_EMAIL} | {CANDIDATE_PHONE}"
    )


def draft_reply(job_summary: dict, original_subject: str, sender_name: str) -> dict:
    """
    Generate a professional email reply expressing interest in the job.
    Returns dict: {subject, body, ai_powered, error?}
    """
    _load_env()
    api_key = os.environ.get('GROQ_API_KEY', '').strip()

    role = job_summary.get('role_title', 'the position')
    company = job_summary.get('company', '')
    skills_list = job_summary.get('required_skills', [])
    skills = ', '.join(skills_list[:8])
    notes = job_summary.get('resume_tailoring_notes', '')
    work_type = job_summary.get('work_type', '')
    location = job_summary.get('location', '')

    subject = original_subject if original_subject else f"Re: {role} Opportunity"
    if not subject.lower().startswith('re:'):
        subject = 'Re: ' + subject

    if not api_key or api_key.startswith('your_') or api_key.startswith('gsk_your'):
        body = _template_reply(role, company, sender_name, skills, work_type, location)
        return {'subject': subject, 'body': body, 'ai_powered': False}

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        ctx = [f"Role: {role}"]
        if company and company not in ('Not mentioned', 'See email'):
            ctx.append(f"Company: {company}")
        if skills:
            ctx.append(f"Required skills: {skills}")
        if work_type:
            ctx.append(f"Work type: {work_type}")
        if location and location not in ('Not specified', 'See email'):
            ctx.append(f"Location: {location}")
        if notes:
            ctx.append(f"Tailoring notes: {notes}")

        prompt = (
            f"Write a professional, concise email reply from {CANDIDATE_NAME} "
            f"expressing strong interest in this job opportunity.\n\n"
            f"Job details:\n" + "\n".join(ctx) + "\n\n"
            f"Candidate profile: {CANDIDATE_PROFILE}\n\n"
            f"Recruiter name: {sender_name}\n\n"
            "Rules:\n"
            "- Greet recruiter by first name\n"
            "- 1 sentence expressing specific interest in the role\n"
            "- 2-3 sentences highlighting the most relevant matching skills\n"
            "- 1 sentence mentioning attached resume and interview availability\n"
            "- Professional closing with candidate name, email, phone\n"
            "- Total length: 100-150 words\n"
            "- Output ONLY the email body, no subject line, no markdown"
        )

        response = client.chat.completions.create(
            model='llama-3.1-8b-instant',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.4,
            max_tokens=400,
        )
        body = response.choices[0].message.content.strip()
        return {'subject': subject, 'body': body, 'ai_powered': True}

    except Exception as e:
        body = _template_reply(role, company, sender_name, skills, work_type, location)
        return {'subject': subject, 'body': body, 'ai_powered': False, 'error': str(e)}
