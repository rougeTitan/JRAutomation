from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
import json
import os
from job_analyzer import JobAnalyzer

app = Flask(__name__)
CORS(app)

analyzer = None
AGENT_DIR  = os.path.dirname(os.path.abspath(__file__))
data_file  = os.path.join(AGENT_DIR, 'data', 'job_analysis.json')
CREDS_FILE = os.path.join(AGENT_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(AGENT_DIR, 'token.pickle')

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')


@app.route('/manifest.json')
def pwa_manifest():
    """PWA Web App Manifest"""
    return jsonify({
        "name": "Job Email Analyzer",
        "short_name": "JobAI",
        "description": "AI-powered recruiter email analyzer with tailored resume & smart replies",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f5f5f7",
        "theme_color": "#1d1d1f",
        "orientation": "portrait-primary",
        "categories": ["productivity", "business"],
        "icons": [
            {"src": "/pwa-icon/192", "sizes": "192x192", "type": "image/svg+xml", "purpose": "any maskable"},
            {"src": "/pwa-icon/512", "sizes": "512x512", "type": "image/svg+xml", "purpose": "any maskable"}
        ],
        "screenshots": [],
        "shortcuts": [
            {"name": "Refresh Emails", "url": "/?action=refresh", "description": "Fetch latest recruiter emails"}
        ]
    })


@app.route('/pwa-icon/<int:size>')
def pwa_icon(size):
    """Generate SVG app icon at requested size"""
    r = size // 5
    fs = int(size * 0.45)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
           f'<rect width="{size}" height="{size}" rx="{r}" fill="#1d1d1f"/>'
           f'<rect x="{size//8}" y="{size//8}" width="{size*3//4}" height="{size*3//4}" rx="{r//2}" fill="#0071e3"/>'
           f'<text x="50%" y="54%" text-anchor="middle" dominant-baseline="middle" '
           f'font-family="system-ui,sans-serif" font-size="{fs}" fill="white">&#x1F4BC;</text>'
           f'</svg>')
    return Response(svg, mimetype='image/svg+xml')


@app.route('/sw.js')
def service_worker():
    """PWA Service Worker — network-first for API, cache-first for shell"""
    js = """
const CACHE = 'jra-v2';
const SHELL = ['/', '/manifest.json'];

self.addEventListener('install', e => {
    e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)));
    self.skipWaiting();
});

self.addEventListener('activate', e => {
    e.waitUntil(caches.keys().then(keys =>
        Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ));
    self.clients.claim();
});

self.addEventListener('fetch', e => {
    const url = new URL(e.request.url);
    if (url.pathname.startsWith('/api/')) {
        // Network-first for all API calls
        e.respondWith(
            fetch(e.request)
                .then(r => { const c = r.clone(); caches.open(CACHE).then(ca => ca.put(e.request, c)); return r; })
                .catch(() => caches.match(e.request))
        );
    } else {
        // Cache-first for app shell
        e.respondWith(
            caches.match(e.request).then(cached => cached || fetch(e.request)
                .then(r => { const c = r.clone(); caches.open(CACHE).then(ca => ca.put(e.request, c)); return r; })
            )
        );
    }
});
"""
    return Response(js, mimetype='application/javascript',
                    headers={'Service-Worker-Allowed': '/'})

@app.route('/api/analyze', methods=['POST'])
def analyze_emails():
    """Trigger email analysis"""
    global analyzer
    
    try:
        max_emails = request.json.get('max_emails', 100) if request.json else 100
        days_back = request.json.get('days_back', 30) if request.json else 30
        auto_delete_old = request.json.get('auto_delete_old', False) if request.json else False
        
        analyzer = JobAnalyzer(credentials_file=CREDS_FILE, token_file=TOKEN_FILE)
        analyzer.authenticate()
        analyzer.fetch_and_analyze_jobs(max_emails=max_emails, days_back=days_back, auto_delete_old=auto_delete_old)
        analyzer.save_json_report(data_file)
        
        return jsonify({
            'success': True,
            'message': f'Analyzed {analyzer.stats["total_processed"]} emails',
            'data': analyzer.get_jobs_data()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_emails():
    """Refresh emails by fetching latest from Gmail"""
    global analyzer
    
    try:
        max_emails = request.json.get('max_emails', 100) if request.json else 100
        days_back = request.json.get('days_back', 30) if request.json else 30
        
        analyzer = JobAnalyzer(credentials_file=CREDS_FILE, token_file=TOKEN_FILE)
        analyzer.authenticate()
        analyzer.fetch_and_analyze_jobs(max_emails=max_emails, days_back=days_back, auto_delete_old=False)
        analyzer.save_json_report(data_file)
        
        return jsonify({
            'success': True,
            'message': f'Refreshed and analyzed {analyzer.stats["total_processed"]} emails',
            'data': analyzer.get_jobs_data()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/delete-email', methods=['POST'])
def delete_email():
    """Delete a single email by ID"""
    try:
        email_id = request.json.get('email_id')
        if not email_id:
            return jsonify({
                'success': False,
                'error': 'Email ID is required'
            }), 400
        
        from gmail_categorizer import GmailCategorizer
        gmail = GmailCategorizer(credentials_file=CREDS_FILE, token_file=TOKEN_FILE)
        gmail.authenticate()
        
        success = gmail.delete_email_by_id(email_id)
        
        if success:
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data['jobs'] = [job for job in data.get('jobs', []) if job.get('email_id') != email_id]
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            return jsonify({
                'success': True,
                'message': 'Email deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete email'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cleanup-old', methods=['POST'])
def cleanup_old_emails():
    """Delete emails older than 30 days"""
    try:
        days_old = request.json.get('days_old', 30) if request.json else 30
        
        from gmail_categorizer import GmailCategorizer
        gmail = GmailCategorizer(credentials_file=CREDS_FILE, token_file=TOKEN_FILE)
        gmail.authenticate()
        
        result = gmail.delete_old_emails(days_old=days_old)
        
        return jsonify({
            'success': True,
            'message': f'Deleted {result["deleted"]} old emails',
            'deleted': result['deleted'],
            'failed': len(result['failed'])
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get analyzed job data"""
    try:
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No data available. Run analysis first.'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get analysis statistics"""
    try:
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify({
                'success': True,
                'statistics': data.get('statistics', {}),
                'job_count': len(data.get('jobs', []))
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No data available'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

RESUME_PATH = os.path.join(os.path.dirname(AGENT_DIR), 'myResume', 'Siddhesh_DilipKumar_Resume.html')


@app.route('/api/jobs/<email_id>/summarize', methods=['POST'])
def summarize_job_endpoint(email_id):
    """Fetch full email from Gmail and extract structured job info with AI"""
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        job = next((j for j in data.get('jobs', []) if j['email_id'] == email_id), None)
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404

        from gmail_categorizer import GmailCategorizer
        gmail = GmailCategorizer(credentials_file=CREDS_FILE, token_file=TOKEN_FILE)
        gmail.authenticate()
        email_details = gmail.get_email_full_body(email_id)
        if not email_details:
            return jsonify({'success': False, 'error': 'Could not fetch email from Gmail'}), 500

        from job_summarizer import summarize_job
        summary = summarize_job(email_details['body'], email_details['subject'])

        job['ai_summary'] = summary
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/jobs/<email_id>/tailor-resume', methods=['POST'])
def tailor_resume_endpoint(email_id):
    """Generate a tailored HTML resume for this specific job"""
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        job = next((j for j in data.get('jobs', []) if j['email_id'] == email_id), None)
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404

        summary = job.get('ai_summary')
        if not summary:
            from gmail_categorizer import GmailCategorizer
            gmail = GmailCategorizer(credentials_file=CREDS_FILE, token_file=TOKEN_FILE)
            gmail.authenticate()
            email_details = gmail.get_email_full_body(email_id)
            from job_summarizer import summarize_job
            summary = summarize_job(
                email_details.get('body', '') if email_details else '',
                job.get('subject', '')
            )
            job['ai_summary'] = summary
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        if not os.path.exists(RESUME_PATH):
            return jsonify({'success': False, 'error': 'Resume file not found at ' + RESUME_PATH}), 404

        with open(RESUME_PATH, encoding='utf-8') as f:
            resume_html = f.read()

        from job_summarizer import generate_tailored_resume
        tailored_html = generate_tailored_resume(resume_html, summary)
        return jsonify({'success': True, 'resume_html': tailored_html})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/resume', methods=['GET'])
def get_base_resume():
    """Serve the base resume HTML"""
    try:
        if not os.path.exists(RESUME_PATH):
            return jsonify({'success': False, 'error': 'Resume not found'}), 404
        with open(RESUME_PATH, encoding='utf-8') as f:
            return jsonify({'success': True, 'resume_html': f.read()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/jobs/<email_id>/draft-reply', methods=['POST'])
def draft_reply_endpoint(email_id):
    """Generate an AI-drafted email reply for a job using Groq"""
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        job = next((j for j in data.get('jobs', []) if j['email_id'] == email_id), None)
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404

        summary = job.get('ai_summary')
        if not summary:
            from gmail_categorizer import GmailCategorizer
            gmail = GmailCategorizer(credentials_file=CREDS_FILE, token_file=TOKEN_FILE)
            gmail.authenticate()
            email_details = gmail.get_email_full_body(email_id)
            from job_summarizer import summarize_job
            summary = summarize_job(
                email_details.get('body', '') if email_details else '',
                job.get('subject', '')
            )
            job['ai_summary'] = summary
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        from email_responder import draft_reply
        draft = draft_reply(
            job_summary=summary,
            original_subject=job.get('subject', ''),
            sender_name=job.get('sender', {}).get('name', '')
        )
        draft['to'] = job.get('sender', {}).get('email', '')
        draft['sender_name'] = job.get('sender', {}).get('name', '')
        return jsonify({'success': True, 'draft': draft})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/jobs/<email_id>/send-reply', methods=['POST'])
def send_reply_endpoint(email_id):
    """Send an email reply via Gmail API"""
    try:
        body_data = request.json or {}
        to = body_data.get('to', '').strip()
        subject = body_data.get('subject', '').strip()
        body = body_data.get('body', '').strip()

        if not to or not body:
            return jsonify({'success': False, 'error': 'Missing to or body'}), 400

        attach_resume = body_data.get('attach_resume', False)
        attachment_name = None
        attachment_content = None

        if attach_resume:
            with open(data_file, 'r', encoding='utf-8') as f:
                data2 = json.load(f)
            job2 = next((j for j in data2.get('jobs', []) if j['email_id'] == email_id), None)
            summary2 = job2.get('ai_summary') if job2 else None
            if summary2 and os.path.exists(RESUME_PATH):
                with open(RESUME_PATH, encoding='utf-8') as f:
                    resume_html = f.read()
                from job_summarizer import generate_tailored_resume
                tailored_html = generate_tailored_resume(resume_html, summary2)
                role_slug = (summary2.get('role_title') or 'Resume').replace(' ', '_').replace('/', '_')
                attachment_name = f'Siddhesh_DilipKumar_{role_slug}.html'
                attachment_content = tailored_html.encode('utf-8')

        from gmail_categorizer import GmailCategorizer
        gmail = GmailCategorizer(credentials_file=CREDS_FILE, token_file=TOKEN_FILE)
        gmail.authenticate()
        sent = gmail.send_email(to=to, subject=subject, body=body, reply_to_msg_id=email_id,
                                attachment_name=attachment_name, attachment_content=attachment_content)

        if sent:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            job = next((j for j in data.get('jobs', []) if j['email_id'] == email_id), None)
            if job:
                job['replied'] = True
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            return jsonify({'success': True, 'message': f'Reply sent to {to}'})
        else:
            return jsonify({'success': False, 'error': 'Gmail API failed to send'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("="*70)
    print("JOB EMAIL ANALYZER - WEB INTERFACE")
    print("="*70)
    print("\n🌐 Starting web server...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("\n💡 Use the Refresh button to fetch latest emails from Gmail!")
    print("="*70 + "\n")
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port, use_reloader=False)
