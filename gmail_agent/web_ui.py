from flask import Flask, render_template, jsonify, request
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
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
