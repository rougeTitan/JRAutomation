import os
import json
import re
from bs4 import BeautifulSoup


def _load_env():
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ.setdefault(key.strip(), val.strip())


_load_env()

_TECH_PATTERNS = [
    ('Java',         r'\bjava\b(?!\s*script)', True),
    ('Python',       r'\bpython\b', True),
    ('JavaScript',   r'\bjavascript\b', True),
    ('TypeScript',   r'\btypescript\b', True),
    ('React',        r'\breact\.?js\b|\breact\b', True),
    ('Angular',      r'\bangular\b', True),
    ('Vue.js',       r'\bvue\.?js\b', True),
    ('Node.js',      r'\bnode\.?js\b', True),
    ('Spring Boot',  r'\bspring\s*boot\b', True),
    ('Spring',       r'\bspring\b', False),
    ('AWS',          r'\baws\b', True),
    ('Azure',        r'\bazure\b', True),
    ('GCP',          r'\bgcp\b|\bgoogle\s+cloud\b', True),
    ('Docker',       r'\bdocker\b', True),
    ('Kubernetes',   r'\bkubernetes\b|\bk8s\b', True),
    ('SQL',          r'\bsql\b', True),
    ('PostgreSQL',   r'\bpostgresql\b|\bpostgres\b', True),
    ('MySQL',        r'\bmysql\b', True),
    ('MongoDB',      r'\bmongodb\b', True),
    ('Redis',        r'\bredis\b', True),
    ('Kafka',        r'\bkafka\b', True),
    ('Microservices',r'\bmicroservices?\b', True),
    ('REST API',     r'\brest(?:ful)?\s*(?:api)?\b', True),
    ('GraphQL',      r'\bgraphql\b', True),
    ('Jenkins',      r'\bjenkins\b', True),
    ('Git',          r'\bgit\b', True),
    ('CI/CD',        r'\bci\s*/\s*cd\b|\bcicd\b', True),
    ('Agile',        r'\bagile\b', True),
    ('Scrum',        r'\bscrum\b', True),
    ('Terraform',    r'\bterraform\b', True),
    ('Linux',        r'\blinux\b', True),
    ('Hibernate',    r'\bhibernate\b', True),
    ('Spark',        r'\bapache\s*spark\b|\bspark\b', True),
    ('Golang',       r'\bgolang\b|\bgo\s+lang\b', True),
    ('C#',           r'\bc#\b|\b\.net\b', True),
]


def _clean_body(html_or_text: str) -> str:
    try:
        text = BeautifulSoup(html_or_text, 'html.parser').get_text(separator='\n')
    except Exception:
        text = re.sub(r'<[^>]+>', ' ', html_or_text)
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'[ \t]+', ' ', text)).strip()


def _extract_skills(text: str):
    seen, found = set(), []
    tl = text.lower()
    for name, pat, primary in _TECH_PATTERNS:
        if primary and name not in seen and re.search(pat, tl, re.IGNORECASE):
            found.append(name)
            seen.add(name)
    return found


def _extract_bullets(text: str, section_keywords: list, max_bullets: int = 6) -> list:
    pattern = r'(?:' + '|'.join(section_keywords) + r')[^:\n]*[:\n]+((?:(?:[ \t]*[•\-*\d.]+[ \t]+[^\n]+\n?)+))'
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return []
    bullets = []
    for line in m.group(1).split('\n'):
        line = re.sub(r'^[\s•\-*\d.]+', '', line).strip()
        if len(line) > 20:
            bullets.append(line)
    return bullets[:max_bullets]


def _regex_extract(body: str, subject: str) -> dict:
    clean = _clean_body(body)
    tl = clean.lower()
    skills = _extract_skills(clean)
    exp_m = re.search(r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)', tl)
    years = (exp_m.group(1) + '+') if exp_m else 'Not specified'
    sal_m = re.search(r'\$[\d,]+\s*[-–]\s*\$[\d,]+|\$[\d,]+[kK]?\s*(?:per\s*year|annually|/yr)', clean, re.I)
    work_type = 'Remote' if 'remote' in tl else 'Hybrid' if 'hybrid' in tl else 'Onsite'
    title = re.split(r'\|\||[|/]', subject)[0].strip()
    responsibilities = _extract_bullets(clean, ['responsibilit', 'you will', 'duties', 'role involves'])
    requirements = _extract_bullets(clean, ['requirements?', 'qualifications?', 'must have', 'looking for'])
    notes = (
        f"Emphasize experience with {', '.join(skills[:5])}. "
        f"The role expects {years} of experience. "
        "Quantify achievements and include matching keywords for ATS optimization."
    ) if skills else "Tailor your Professional Summary to mirror the job description language."
    return {
        'role_title': title,
        'company': 'See email',
        'location': 'See email',
        'work_type': work_type,
        'experience_years': years,
        'required_skills': skills[:10],
        'nice_to_have_skills': [],
        'key_responsibilities': responsibilities,
        'requirements': requirements,
        'compensation': sal_m.group(0) if sal_m else None,
        'resume_tailoring_notes': notes,
        'ai_powered': False,
    }


def summarize_job(body: str, subject: str) -> dict:
    _load_env()
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not api_key or api_key.startswith('your_'):
        return _regex_extract(body, subject)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        clean_body = _clean_body(body)[:8000]
        prompt = (
            f"Analyze this recruiter email and return ONLY valid JSON (no markdown).\n\n"
            f"Subject: {subject}\n\nEmail:\n{clean_body}\n\n"
            'Return JSON with keys: role_title, company, location, work_type (Remote|Hybrid|Onsite), '
            'experience_years, required_skills (array), nice_to_have_skills (array), '
            'key_responsibilities (array of concise bullets), requirements (array), '
            'compensation (string or null), resume_tailoring_notes (2-3 sentences on what to '
            'highlight for ATS and which keywords to include).'
        )
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.1,
            response_format={'type': 'json_object'},
        )
        result = json.loads(response.choices[0].message.content)
        result['ai_powered'] = True
        return result
    except Exception as e:
        result = _regex_extract(body, subject)
        result['ai_error'] = str(e)
        return result


def _highlight_wrap(content: str, role: str = '') -> str:
    """Wrap modified resume content with a visible amber highlight + dismiss button"""
    label = f'\u270f AI Tailored{" for: " + role if role else ""}'
    remove_js = (
        "var w=this.closest('.ai-hl');"
        "w.outerHTML=w.querySelector('ul').outerHTML;"
    )
    return (
        '<div class="ai-hl" style="'
        'background:#fffbeb;'
        'border:2px solid #f59e0b;'
        'border-radius:6px;'
        'padding:12px 14px 8px;'
        'position:relative;'
        'margin:4px 0;'
        '">'
        f'<span style="'
        f'position:absolute;top:-11px;left:10px;'
        f'background:#f59e0b;color:#1a1100;'
        f'font-size:7.5pt;font-weight:700;'
        f'padding:1px 10px;border-radius:999px;'
        f'font-family:Arial,sans-serif;letter-spacing:0.3px;'
        f'">{label}</span>'
        f'<button onclick="{remove_js}" title="Remove highlight" style="'
        f'position:absolute;top:-11px;right:10px;'
        f'background:#ef4444;color:#fff;border:none;'
        f'border-radius:999px;font-size:7.5pt;font-weight:700;'
        f'padding:1px 8px;cursor:pointer;font-family:Arial,sans-serif;'
        f'line-height:1.4;">\u00d7 Remove</button>'
        + content +
        '</div>'
    )


def generate_tailored_resume(resume_html: str, job_summary: dict) -> str:
    _load_env()
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    role = job_summary.get('role_title', 'Software Engineer')
    company = job_summary.get('company', '')
    company_label = f' @ {company}' if company and company not in ('Not mentioned', 'See email') else ''
    skills = job_summary.get('required_skills', [])

    banner = (
        '<div style="position:fixed;top:0;left:0;right:0;background:#1a3a6b;color:#fff;'
        'padding:6px 16px;font-size:9pt;z-index:9999;display:flex;justify-content:space-between;align-items:center;">'
        f'<span>📄 Tailored for: <strong>{role}</strong>{company_label}</span>'
        '<button onclick="window.print()" style="background:#fff;color:#1a3a6b;border:none;'
        'padding:3px 12px;border-radius:4px;cursor:pointer;font-weight:700;font-size:9pt;">'
        'Print / Save PDF</button></div><div style="height:34px"></div>'
    )

    def _apply_no_ai_highlights(src_html: str) -> str:
        """Highlight matched skills in existing summary + wrap with review box."""
        notes = job_summary.get('resume_tailoring_notes', '')
        notes_block = (
            f'<div style="background:#eff6ff;border-left:3px solid #3b82f6;'
            f'padding:6px 10px;margin-bottom:8px;font-size:8pt;color:#1e3a8a;font-family:Arial,sans-serif;">'
            f'<strong>Tailoring Notes:</strong> {notes}</div>'
        ) if notes else ''

        def _mark_skills(html_ul: str) -> str:
            result = html_ul
            for sk in skills:
                result = re.sub(
                    r'(?i)(' + re.escape(sk) + r')',
                    r'<mark style="background:#fef08a;padding:0 2px;border-radius:2px;">\1</mark>',
                    result
                )
            return result

        pat = r'(<div class="summary">\s*)(<ul>.*?</ul>)(\s*</div>)'

        def _replace(m):
            marked_ul = _mark_skills(m.group(2))
            label = f'\u270f Review & Tailor{" \u2014 " + role if role else ""}'
            remove_js = (
                "var w=this.closest('.ai-hl');"
                "w.outerHTML=w.querySelector('ul').outerHTML;"
            )
            wrapped = (
                '<div class="ai-hl" style="'
                'background:#fffbeb;border:2px solid #f59e0b;border-radius:6px;'
                'padding:12px 14px 8px;position:relative;margin:4px 0;">'
                f'<span style="position:absolute;top:-11px;left:10px;background:#f59e0b;'
                f'color:#1a1100;font-size:7.5pt;font-weight:700;padding:1px 10px;'
                f'border-radius:999px;font-family:Arial,sans-serif;">{label}</span>'
                f'<button onclick="{remove_js}" title="Remove highlight" style="'
                f'position:absolute;top:-11px;right:10px;background:#ef4444;color:#fff;'
                f'border:none;border-radius:999px;font-size:7.5pt;font-weight:700;'
                f'padding:1px 8px;cursor:pointer;font-family:Arial,sans-serif;">\u00d7 Remove</button>'
                + notes_block + marked_ul +
                '</div>'
            )
            return m.group(1) + wrapped + m.group(3)

        out = re.sub(pat, _replace, src_html, flags=re.DOTALL)
        out = out.replace(
            '<div class="section-title">Professional Summary</div>',
            '<div class="section-title">Professional Summary '
            '<span style="font-size:7pt;font-weight:700;background:#f59e0b;color:#1a1100;'
            'padding:1px 8px;border-radius:999px;vertical-align:middle;'
            'font-family:Arial,sans-serif;margin-left:6px;">\u270f REVIEW NEEDED'
            '<button onclick="this.parentElement.remove()" title="Dismiss" style="'
            'background:none;border:none;color:#1a1100;font-weight:900;font-size:8pt;'
            'cursor:pointer;margin-left:4px;padding:0;line-height:1;">\u00d7</button>'
            '</span></div>'
        )
        return out.replace('</body>', banner + '\n</body>')

    if not api_key or api_key.startswith('your_'):
        return _apply_no_ai_highlights(resume_html)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        responsibilities = job_summary.get('key_responsibilities', [])
        requirements = job_summary.get('requirements', [])
        notes = job_summary.get('resume_tailoring_notes', '')
        prompt = (
            f"You are a professional resume writer. Generate a tailored Professional Summary "
            f"as HTML <ul> bullets for this job application.\n\n"
            f"Job: {role}{company_label}\n"
            f"Required Skills: {', '.join(skills)}\n"
            f"Key Responsibilities: {chr(10).join('- ' + r for r in responsibilities[:5])}\n"
            f"Requirements: {chr(10).join('- ' + r for r in requirements[:4])}\n"
            f"Notes: {notes}\n\n"
            "Candidate: 7+ years Software Engineer — Java, Spring Boot, Kafka, Angular, "
            "Node.js, React, AWS, Docker, Kubernetes, Microservices, CI/CD, PostgreSQL, MongoDB.\n\n"
            "Output ONLY the HTML <ul>...</ul> with 5-7 <li> bullets. "
            "First bullet leads with the target role. Include ATS keywords. Each bullet ≤2 sentences."
        )
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3,
        )
        new_ul = response.choices[0].message.content.strip()
        highlighted = _highlight_wrap(new_ul, role)
        pattern = r'(<div class="summary">\s*)<ul>.*?</ul>(\s*</div>)'
        new_html = re.sub(pattern, r'\g<1>' + highlighted + r'\2', resume_html, flags=re.DOTALL)
        new_html = new_html.replace(
            '<div class="section-title">Professional Summary</div>',
            '<div class="section-title">Professional Summary '
            '<span style="font-size:7pt;font-weight:700;background:#f59e0b;color:#1a1100;'
            'padding:1px 8px;border-radius:999px;vertical-align:middle;'
            'font-family:Arial,sans-serif;margin-left:6px;">\u270f MODIFIED'
            '<button onclick="this.parentElement.remove()" title="Dismiss" style="'
            'background:none;border:none;color:#1a1100;font-weight:900;font-size:8pt;'
            'cursor:pointer;margin-left:4px;padding:0;line-height:1;">\u00d7</button>'
            '</span></div>'
        )
        return new_html.replace('</body>', banner + '\n</body>')
    except Exception as e:
        print(f"Tailored resume error (falling back to highlight mode): {e}")
        return _apply_no_ai_highlights(resume_html)
