import re, os, sys, json

resume_path = os.path.join(os.path.dirname(__file__), '..', 'myResume', 'Siddhesh_DilipKumar_Resume.html')
html = open(resume_path, encoding='utf-8').read()

pat = r'(<div class="summary">\s*)(<ul>.*?</ul>)(\s*</div>)'
result = re.search(pat, html, re.DOTALL)
print("resume file length:", len(html))
print("summary div present:", '<div class="summary">' in html)
print("pattern match:", result is not None)

if result:
    print("group(2) snippet:", result.group(2)[:100])
else:
    # find what the summary div actually looks like
    idx = html.find('class="summary"')
    print("summary context:", repr(html[idx-10:idx+120]))

# Now test the full function with a fake job summary
sys.path.insert(0, os.path.dirname(__file__))
from job_summarizer import generate_tailored_resume

fake_summary = {
    'role_title': 'Senior Java Developer',
    'company': 'Test Corp',
    'required_skills': ['Java', 'Spring Boot', 'Kafka', 'AWS', 'Docker'],
    'resume_tailoring_notes': 'Highlight Java and Spring Boot microservices experience. Emphasize AWS cloud deployment skills.',
    'key_responsibilities': [],
    'requirements': [],
}

output = generate_tailored_resume(html, fake_summary)
print("\nOutput length:", len(output))
print("amber highlight present:", 'ai-hl' in output)
print("REVIEW NEEDED badge:", 'REVIEW NEEDED' in output)
print("mark tag present:", '<mark' in output)
print("banner present:", 'Tailored for' in output)

out_path = os.path.join(os.path.dirname(__file__), '..', 'myResume', 'debug_tailored.html')
open(out_path, 'w', encoding='utf-8').write(output)
print("\nWrote debug output to:", out_path)
