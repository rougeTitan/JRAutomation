import os
import pickle
import base64
import json
from datetime import datetime, timedelta
from collections import defaultdict
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailCategorizer:
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.creds = None
        self.categories = defaultdict(list)
        
    def authenticate(self, force_refresh=False):
        """Authenticate with Gmail API with automatic token refresh.
        Cloud-safe: loads token/credentials from environment variables when
        GMAIL_TOKEN_B64 / GMAIL_CREDENTIALS_JSON are set (Railway, Render, etc.)
        """
        creds = None

        # ── 1. Load token ──────────────────────────────────────────────────
        token_b64 = os.environ.get('GMAIL_TOKEN_B64')
        if token_b64 and not force_refresh:
            try:
                creds = pickle.loads(base64.b64decode(token_b64))
                print("✓ Token loaded from environment variable")
            except Exception as e:
                print(f"⚠️  Error loading token from env: {e}")
                creds = None
        elif os.path.exists(self.token_file) and not force_refresh:
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                print(f"⚠️  Error loading token: {e}. Generating new token...")
                creds = None

        # ── 2. Refresh or re-auth if needed ───────────────────────────────
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("🔄 Refreshing expired token...")
                    creds.refresh(Request())
                    print("✓ Token refreshed successfully")
                except Exception as e:
                    print(f"⚠️  Token refresh failed: {e}. Re-authenticating...")
                    creds = None

            if not creds:
                # ── Load credentials.json from env var or file ──
                creds_json = os.environ.get('GMAIL_CREDENTIALS_JSON')
                if creds_json:
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                        tmp.write(creds_json)
                        tmp_path = tmp.name
                    flow = InstalledAppFlow.from_client_secrets_file(tmp_path, SCOPES)
                    os.unlink(tmp_path)
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                print("🔑 Starting OAuth authentication...")
                creds = flow.run_local_server(port=0)

            # ── 3. Save token (file if writable, log b64 for cloud) ───────
            try:
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
                print("✓ Token saved successfully")
            except Exception as e:
                print(f"⚠️  Warning: Could not save token to file: {e}")

            # Print new base64 token so it can be updated in cloud env vars
            if token_b64:
                new_b64 = base64.b64encode(pickle.dumps(creds)).decode()
                print(f"🔑 Update GMAIL_TOKEN_B64 env var with: {new_b64[:40]}...")

        self.creds = creds
        self.service = build('gmail', 'v1', credentials=creds)
        print("✓ Successfully authenticated with Gmail API")
        return self.service
    
    def _ensure_authenticated(self):
        """Ensure credentials are valid before making API calls"""
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                    self.service = build('gmail', 'v1', credentials=self.creds)
                    with open(self.token_file, 'wb') as token:
                        pickle.dump(self.creds, token)
                except Exception as e:
                    print(f"⚠️  Auto-refresh failed, re-authenticating: {e}")
                    self.authenticate(force_refresh=True)
            else:
                self.authenticate()
        return True
    
    def fetch_emails(self, max_results=100, query='', days_back=None):
        """Fetch emails from inbox with optional date filtering"""
        self._ensure_authenticated()
        
        try:
            search_query = query
            if days_back:
                cutoff_date = datetime.now() - timedelta(days=days_back)
                date_str = cutoff_date.strftime('%Y/%m/%d')
                search_query = f"{query} after:{date_str}" if query else f"after:{date_str}"
            
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=search_query
            ).execute()
            
            messages = results.get('messages', [])
            print(f"✓ Found {len(messages)} emails to process")
            return messages
        except HttpError as error:
            if error.resp.status == 401:
                print('🔄 Authentication expired, refreshing...')
                self.authenticate(force_refresh=True)
                return self.fetch_emails(max_results, query, days_back)
            print(f'✗ An error occurred: {error}')
            return []
    
    def get_email_details(self, msg_id):
        """Get detailed information about an email"""
        self._ensure_authenticated()
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown')
            
            body = self._get_email_body(message['payload'])
            
            return {
                'id': msg_id,
                'subject': subject,
                'from': sender,
                'date': date,
                'body': body,
                'snippet': message.get('snippet', '')
            }
        except HttpError as error:
            print(f'✗ Error fetching email {msg_id}: {error}')
            return None
    
    def _get_email_body(self, payload):
        """Extract email body from payload"""
        body = ""
        
        if 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html' and 'data' in part['body'] and not body:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        
        return body[:500]
    
    def get_email_full_body(self, msg_id: str) -> dict:
        """Fetch full email with complete body (no truncation) for AI analysis"""
        self._ensure_authenticated()
        try:
            message = self.service.users().messages().get(
                userId='me', id=msg_id, format='full'
            ).execute()
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            sender  = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            date    = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            body    = self._extract_full_body(message['payload'])
            return {'id': msg_id, 'subject': subject, 'from': sender,
                    'date': date, 'body': body, 'snippet': message.get('snippet', '')}
        except HttpError as error:
            print(f'✗ Error fetching full email {msg_id}: {error}')
            return None

    def _extract_full_body(self, payload) -> str:
        """Recursively extract complete email body without truncation"""
        body = ''
        if payload.get('body', {}).get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
        elif 'parts' in payload:
            for part in payload['parts']:
                mime = part.get('mimeType', '')
                if mime == 'text/plain' and part.get('body', {}).get('data'):
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
                    break
                elif mime == 'text/html' and part.get('body', {}).get('data') and not body:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
                elif mime.startswith('multipart/') and not body:
                    body = self._extract_full_body(part)
        return body

    def send_email(self, to: str, subject: str, body: str,
                   reply_to_msg_id: str = None,
                   attachment_name: str = None, attachment_content: bytes = None) -> bool:
        """Send an email via Gmail API with optional attachment"""
        import base64 as _b64
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email import encoders as _enc

        if attachment_name and attachment_content:
            msg = MIMEMultipart()
            msg['to'] = to
            msg['subject'] = subject
            if reply_to_msg_id:
                msg['In-Reply-To'] = reply_to_msg_id
                msg['References'] = reply_to_msg_id
            msg.attach(MIMEText(body, 'plain'))
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment_content if isinstance(attachment_content, bytes)
                             else attachment_content.encode('utf-8'))
            _enc.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{attachment_name}"')
            msg.attach(part)
        else:
            msg = MIMEText(body)
            msg['to'] = to
            msg['subject'] = subject
            if reply_to_msg_id:
                msg['In-Reply-To'] = reply_to_msg_id
                msg['References'] = reply_to_msg_id

        raw = _b64.urlsafe_b64encode(msg.as_bytes()).decode()
        send_body = {'raw': raw}
        if reply_to_msg_id:
            try:
                orig = self.service.users().messages().get(
                    userId='me', id=reply_to_msg_id, format='minimal'
                ).execute()
                thread_id = orig.get('threadId')
                if thread_id:
                    send_body['threadId'] = thread_id
            except Exception:
                pass
        result = self.service.users().messages().send(userId='me', body=send_body).execute()
        return bool(result.get('id'))

    def categorize_email(self, email_details):
        """Categorize email based on content using keyword matching"""
        subject = email_details['subject'].lower()
        body = email_details['body'].lower()
        snippet = email_details['snippet'].lower()
        sender = email_details['from'].lower()
        
        content = f"{subject} {snippet} {body}"
        
        job_keywords = ['job', 'career', 'hiring', 'opportunity', 'interview', 'resume', 'recruiter', 'position', 'application', 'linkedin']
        tech_keywords = ['update', 'newsletter', 'blog', 'article', 'technology', 'software', 'development', 'coding', 'programming', 'github', 'stack overflow']
        finance_keywords = ['stock', 'trade', 'alert', 'market', 'investment', 'portfolio', 'price', 'financial', 'dividend', 'earnings']
        social_keywords = ['facebook', 'twitter', 'instagram', 'notification', 'friend request', 'commented', 'liked', 'shared']
        shopping_keywords = ['order', 'shipped', 'delivery', 'purchase', 'receipt', 'amazon', 'ebay', 'payment', 'invoice']
        promotional_keywords = ['sale', 'discount', 'offer', 'deal', 'promo', 'unsubscribe', 'marketing', 'advertise']
        
        if any(keyword in content for keyword in job_keywords):
            return 'Job Related'
        elif any(keyword in content for keyword in finance_keywords):
            return 'Finance/Trading'
        elif any(keyword in content for keyword in tech_keywords):
            return 'Tech Updates/Informational'
        elif any(keyword in content for keyword in social_keywords):
            return 'Social Media'
        elif any(keyword in content for keyword in shopping_keywords):
            return 'Shopping/Orders'
        elif any(keyword in content for keyword in promotional_keywords):
            return 'Promotional/Marketing'
        elif 'noreply' in sender or 'no-reply' in sender:
            return 'Automated/Notifications'
        else:
            return 'Other/Uncategorized'
    
    def process_emails(self, max_emails=100):
        """Process and categorize emails"""
        print(f"\n📧 Fetching and processing up to {max_emails} emails...")
        
        messages = self.fetch_emails(max_results=max_emails)
        
        if not messages:
            print("No emails found.")
            return
        
        total = len(messages)
        for idx, message in enumerate(messages, 1):
            print(f"Processing email {idx}/{total}...", end='\r')
            
            email_details = self.get_email_details(message['id'])
            if email_details:
                category = self.categorize_email(email_details)
                self.categories[category].append(email_details)
        
        print(f"\n✓ Processed {total} emails successfully")
    
    def generate_report(self, output_file=None):
        """Generate categorization report"""
        if output_file is None:
            output_file = os.path.join(os.path.dirname(__file__), 'data', 'email_report.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        print(f"\n📊 Generating Email Report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_emails': sum(len(emails) for emails in self.categories.values()),
            'categories': {}
        }
        
        print("\n" + "="*60)
        print("EMAIL CATEGORIZATION REPORT")
        print("="*60)
        
        for category in sorted(self.categories.keys()):
            emails = self.categories[category]
            count = len(emails)
            
            report['categories'][category] = {
                'count': count,
                'emails': [
                    {
                        'id': e['id'],
                        'subject': e['subject'],
                        'from': e['from'],
                        'date': e['date']
                    } for e in emails
                ]
            }
            
            print(f"\n{category}: {count} emails")
            print("-" * 60)
            for email in emails[:5]:
                print(f"  • {email['subject'][:50]}...")
                print(f"    From: {email['from'][:50]}")
            
            if count > 5:
                print(f"  ... and {count - 5} more emails")
        
        print("\n" + "="*60)
        print(f"TOTAL EMAILS PROCESSED: {report['total_emails']}")
        print("="*60)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Detailed report saved to: {output_file}")
        return report
    
    def delete_email_by_id(self, email_id):
        """Delete a single email by ID"""
        self._ensure_authenticated()
        
        try:
            self.service.users().messages().delete(
                userId='me',
                id=email_id
            ).execute()
            return True
        except HttpError as error:
            if error.resp.status == 401:
                print('🔄 Authentication expired, refreshing...')
                self.authenticate(force_refresh=True)
                return self.delete_email_by_id(email_id)
            print(f'✗ Error deleting email {email_id}: {error}')
            return False
    
    def delete_emails_by_ids(self, email_ids):
        """Delete multiple emails by their IDs"""
        self._ensure_authenticated()
        
        deleted = 0
        failed = []
        
        for email_id in email_ids:
            try:
                self.service.users().messages().delete(
                    userId='me',
                    id=email_id
                ).execute()
                deleted += 1
            except HttpError as error:
                if error.resp.status == 401:
                    print('🔄 Authentication expired, refreshing...')
                    self.authenticate(force_refresh=True)
                    try:
                        self.service.users().messages().delete(
                            userId='me',
                            id=email_id
                        ).execute()
                        deleted += 1
                        continue
                    except:
                        pass
                failed.append(email_id)
                print(f'✗ Error deleting email {email_id}: {error}')
        
        return {'deleted': deleted, 'failed': failed}
    
    def delete_old_emails(self, days_old=30):
        """Delete emails older than specified days"""
        self._ensure_authenticated()
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        date_str = cutoff_date.strftime('%Y/%m/%d')
        query = f"before:{date_str}"
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                maxResults=500,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            if not messages:
                print(f"✓ No emails older than {days_old} days found")
                return {'deleted': 0, 'failed': []}
            
            print(f"Found {len(messages)} emails older than {days_old} days")
            email_ids = [msg['id'] for msg in messages]
            return self.delete_emails_by_ids(email_ids)
            
        except HttpError as error:
            print(f'✗ Error fetching old emails: {error}')
            return {'deleted': 0, 'failed': []}
    
    def delete_emails_by_category(self, category_name):
        """Delete all emails in a specific category"""
        if category_name not in self.categories:
            print(f"✗ Category '{category_name}' not found")
            return
        
        emails = self.categories[category_name]
        count = len(emails)
        
        print(f"\n⚠️  About to delete {count} emails from category '{category_name}'")
        confirm = input("Type 'DELETE' to confirm: ")
        
        if confirm != 'DELETE':
            print("✗ Deletion cancelled")
            return
        
        deleted = 0
        for email in emails:
            try:
                self.service.users().messages().delete(
                    userId='me',
                    id=email['id']
                ).execute()
                deleted += 1
                print(f"Deleted {deleted}/{count} emails...", end='\r')
            except HttpError as error:
                print(f"\n✗ Error deleting email {email['id']}: {error}")
        
        print(f"\n✓ Successfully deleted {deleted} emails from '{category_name}'")
    
    def get_category_summary(self):
        """Get a summary of categories"""
        summary = {}
        for category, emails in self.categories.items():
            summary[category] = len(emails)
        return summary


def main():
    print("="*60)
    print("GMAIL EMAIL CATEGORIZER")
    print("="*60)
    
    categorizer = GmailCategorizer()
    
    try:
        categorizer.authenticate()
        
        max_emails = input("\nHow many emails to process? (default: 100): ").strip()
        max_emails = int(max_emails) if max_emails else 100
        
        categorizer.process_emails(max_emails=max_emails)
        
        categorizer.generate_report()
        
        print("\n" + "="*60)
        print("What would you like to do next?")
        print("1. Delete emails by category")
        print("2. Export detailed report")
        print("3. Exit")
        print("="*60)
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            summary = categorizer.get_category_summary()
            print("\nAvailable categories:")
            for idx, (cat, count) in enumerate(summary.items(), 1):
                print(f"{idx}. {cat} ({count} emails)")
            
            cat_name = input("\nEnter category name to delete: ").strip()
            categorizer.delete_emails_by_category(cat_name)
        elif choice == '2':
            filename = input("Enter report filename (default: data/email_report.json): ").strip()
            filename = filename if filename else None
            categorizer.generate_report(filename)
        
        print("\n✓ Done! Check 'gmail_agent/data/email_report.json' for detailed results.")
        
    except FileNotFoundError:
        print("\n✗ Error: 'credentials.json' file not found!")
        print("Please follow the setup instructions in GMAIL_SETUP.md")
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")


if __name__ == '__main__':
    main()
