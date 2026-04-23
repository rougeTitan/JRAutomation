import os
import pickle
import json
from datetime import datetime
from gmail_categorizer import GmailCategorizer
from job_parser import JobEmailParser

class JobAnalyzer:
    """Analyze job-related emails and generate structured reports"""
    
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        self.gmail = GmailCategorizer(credentials_file, token_file)
        self.parser = JobEmailParser()
        self.job_emails = []
        self.stats = {
            'total_processed': 0,
            'job_emails_found': 0,
            'technologies': {},
            'locations': {},
            'experience_levels': {},
            'senders': {}
        }
    
    def authenticate(self):
        """Authenticate with Gmail"""
        return self.gmail.authenticate()
    
    def fetch_and_analyze_jobs(self, max_emails=100, days_back=30, auto_delete_old=False):
        """Fetch emails and analyze job-related ones with 30-day window"""
        print(f"\n📧 Fetching up to {max_emails} emails from last {days_back} days...")
        
        if auto_delete_old:
            print(f"\n🗑️ Auto-deleting emails older than {days_back} days...")
            result = self.gmail.delete_old_emails(days_old=days_back)
            print(f"✓ Deleted {result['deleted']} old emails")
        
        messages = self.gmail.fetch_emails(max_results=max_emails, days_back=days_back)
        
        if not messages:
            print("No emails found.")
            return
        
        total = len(messages)
        self.stats['total_processed'] = total
        
        print(f"✓ Found {total} emails")
        print(f"\n🔍 Analyzing job-related emails...")
        
        for idx, message in enumerate(messages, 1):
            print(f"Processing email {idx}/{total}...", end='\r')
            
            email_details = self.gmail.get_email_details(message['id'])
            if not email_details:
                continue
            
            category = self.gmail.categorize_email(email_details)
            
            if category == 'Job Related':
                job_info = self.parser.parse_job_email(email_details)
                self.job_emails.append(job_info)
                
                for tech in job_info['technologies']:
                    self.stats['technologies'][tech] = self.stats['technologies'].get(tech, 0) + 1
                
                location = job_info['location']
                if location != 'Not Specified':
                    self.stats['locations'][location] = self.stats['locations'].get(location, 0) + 1
                
                exp_level = job_info['experience_level']
                self.stats['experience_levels'][exp_level] = self.stats['experience_levels'].get(exp_level, 0) + 1
                
                sender_email = job_info['sender']['email']
                if sender_email != 'Unknown':
                    self.stats['senders'][sender_email] = self.stats['senders'].get(sender_email, 0) + 1
        
        self.stats['job_emails_found'] = len(self.job_emails)
        print(f"\n✓ Processed {total} emails, found {self.stats['job_emails_found']} job-related emails")
    
    def generate_console_report(self):
        """Generate a console summary report"""
        print("\n" + "="*70)
        print("JOB EMAIL ANALYSIS REPORT")
        print("="*70)
        
        print(f"\n📊 Summary:")
        print(f"  • Total Emails Processed: {self.stats['total_processed']}")
        print(f"  • Job-Related Emails: {self.stats['job_emails_found']}")
        
        if self.stats['job_emails_found'] == 0:
            print("\n⚠️  No job-related emails found.")
            return
        
        print(f"\n💼 Top Job Titles:")
        job_titles = {}
        for job in self.job_emails[:10]:
            title = job['job_title']
            if title != 'Not Extracted':
                print(f"  • {title}")
        
        if self.stats['technologies']:
            print(f"\n🔧 Most Required Technologies:")
            sorted_tech = sorted(self.stats['technologies'].items(), key=lambda x: x[1], reverse=True)
            for tech, count in sorted_tech[:10]:
                print(f"  • {tech}: {count} mentions")
        
        if self.stats['locations']:
            print(f"\n📍 Top Locations:")
            sorted_locations = sorted(self.stats['locations'].items(), key=lambda x: x[1], reverse=True)
            for location, count in sorted_locations[:10]:
                print(f"  • {location}: {count} jobs")
        
        if self.stats['experience_levels']:
            print(f"\n📈 Experience Levels:")
            for level, count in sorted(self.stats['experience_levels'].items(), key=lambda x: x[1], reverse=True):
                print(f"  • {level}: {count} jobs")
        
        if self.stats['senders']:
            print(f"\n📨 Top Recruiters/Senders:")
            sorted_senders = sorted(self.stats['senders'].items(), key=lambda x: x[1], reverse=True)
            for sender, count in sorted_senders[:10]:
                print(f"  • {sender}: {count} emails")
        
        print("\n" + "="*70)
    
    def save_json_report(self, output_file=None):
        """Save detailed analysis to JSON file"""
        if output_file is None:
            output_file = os.path.join(os.path.dirname(__file__), 'data', 'job_analysis.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.stats,
            'jobs': self.job_emails
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Detailed report saved to: {output_file}")
        return output_file
    
    def get_jobs_data(self):
        """Get jobs data for web UI"""
        return {
            'statistics': self.stats,
            'jobs': self.job_emails
        }


def main():
    print("="*70)
    print("JOB EMAIL ANALYZER")
    print("="*70)
    
    analyzer = JobAnalyzer()
    
    try:
        analyzer.authenticate()
        
        max_emails = input("\nHow many emails to scan? (default: 100): ").strip()
        max_emails = int(max_emails) if max_emails else 100
        
        analyzer.fetch_and_analyze_jobs(max_emails=max_emails)
        
        analyzer.generate_console_report()
        
        analyzer.save_json_report()
        
        print("\n💡 Tip: Run 'python web_ui.py' to view results in a web interface!")
        
    except FileNotFoundError:
        print("\n✗ Error: 'credentials.json' file not found!")
        print("Please follow the setup instructions in GMAIL_SETUP.md")
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
