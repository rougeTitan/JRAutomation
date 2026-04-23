import re
from datetime import datetime
from typing import Dict, List, Optional

class JobEmailParser:
    """Parse job-related emails and extract structured information"""
    
    def __init__(self):
        self.tech_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node.js', 'nodejs', 'django', 'flask', 'spring', 'springboot',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'k8s',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
            'git', 'jenkins', 'ci/cd', 'terraform', 'ansible',
            'rest', 'restful', 'api', 'graphql', 'microservices',
            'html', 'css', 'tailwind', 'bootstrap', 'sass',
            'machine learning', 'ml', 'ai', 'deep learning', 'nlp',
            'data science', 'pandas', 'numpy', 'tensorflow', 'pytorch',
            'c++', 'c#', '.net', 'ruby', 'rails', 'php', 'laravel',
            'go', 'golang', 'rust', 'scala', 'kotlin', 'swift',
            'devops', 'agile', 'scrum', 'jira', 'confluence'
        ]
        
        self.location_patterns = [
            r'(?:location|based in|office in|located in)[\s:]+([A-Z][a-zA-Z\s,]+(?:NY|CA|TX|FL|IL|PA|OH|GA|NC|MI|NJ|VA|WA|MA|AZ|TN|IN|MO|MD|WI|MN|CO|AL|SC|LA|KY|OR|OK|CT|UT|IA|NV|AR|MS|KS|NM|NE|WV|ID|HI|NH|ME|RI|MT|DE|SD|ND|AK|VT|WY|DC))',
            r'\b([A-Z][a-zA-Z\s]+,\s*(?:NY|CA|TX|FL|IL|PA|OH|GA|NC|MI|NJ|VA|WA|MA|AZ|TN|IN|MO|MD|WI|MN|CO|AL|SC|LA|KY|OR|OK|CT|UT|IA|NV|AR|MS|KS|NM|NE|WV|ID|HI|NH|ME|RI|MT|DE|SD|ND|AK|VT|WY|DC))\b',
            r'(?:remote|hybrid|on-site|onsite|work from home)',
        ]
        
        self.job_title_patterns = [
            r'(?:position|role|opening|opportunity|job)[\s:]+(.+?)(?:\||at|with|\n|$)',
            r'(?:hiring|seeking|looking for)[\s:]+(.+?)(?:\||at|with|\n|$)',
            r'^([A-Z][a-zA-Z\s/]+(?:Engineer|Developer|Analyst|Manager|Architect|Designer|Scientist|Specialist|Lead|Director|Consultant))',
        ]
    
    def extract_email_from_sender(self, sender: str) -> Optional[str]:
        """Extract email address from sender field"""
        email_match = re.search(r'<([^>]+)>', sender)
        if email_match:
            return email_match.group(1)
        
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', sender)
        if email_match:
            return email_match.group(0)
        
        return None
    
    def extract_name_from_sender(self, sender: str) -> Optional[str]:
        """Extract name from sender field"""
        name_match = re.match(r'^([^<@]+)', sender)
        if name_match:
            name = name_match.group(1).strip()
            if name and not any(char.isdigit() for char in name):
                return name
        return None
    
    def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers from text"""
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',
            r'\+1[-.]?\d{3}[-.]?\d{3}[-.]?\d{4}'
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            phones.extend(matches)
        
        return list(set(phones))
    
    def extract_social_links(self, text: str) -> Dict[str, str]:
        """Extract social media links"""
        social = {}
        
        linkedin_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9-]+)', text, re.IGNORECASE)
        if linkedin_match:
            social['linkedin'] = f"https://linkedin.com/in/{linkedin_match.group(1)}"
        
        twitter_match = re.search(r'twitter\.com/([a-zA-Z0-9_]+)', text, re.IGNORECASE)
        if twitter_match:
            social['twitter'] = f"https://twitter.com/{twitter_match.group(1)}"
        
        github_match = re.search(r'github\.com/([a-zA-Z0-9-]+)', text, re.IGNORECASE)
        if github_match:
            social['github'] = f"https://github.com/{github_match.group(1)}"
        
        return social
    
    def extract_job_title(self, subject: str, body: str) -> Optional[str]:
        """Extract job title from email"""
        for pattern in self.job_title_patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                if len(title) > 5 and len(title) < 100:
                    return title
        
        for pattern in self.job_title_patterns:
            match = re.search(pattern, body[:500], re.IGNORECASE | re.MULTILINE)
            if match:
                title = match.group(1).strip()
                if len(title) > 5 and len(title) < 100:
                    return title
        
        return None
    
    def extract_technologies(self, text: str) -> List[str]:
        """Extract technologies/skills from text"""
        found_tech = []
        text_lower = text.lower()
        
        for tech in self.tech_keywords:
            pattern = r'\b' + re.escape(tech) + r'\b'
            if re.search(pattern, text_lower):
                found_tech.append(tech.title())
        
        return list(set(found_tech))
    
    def extract_location(self, text: str) -> Optional[str]:
        """Extract job location from text"""
        for pattern in self.location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(0).strip()
                return location
        
        return None
    
    def extract_salary(self, text: str) -> Optional[str]:
        """Extract salary information if present"""
        salary_patterns = [
            r'\$\d{2,3}[,\d]*[kK]?\s*[-–]\s*\$\d{2,3}[,\d]*[kK]?',
            r'\$\d{2,3}[,\d]*[kK]?\s*(?:per year|annually|/year|/yr)',
            r'\d{2,3}[,\d]*[kK]?\s*[-–]\s*\d{2,3}[,\d]*[kK]?\s*(?:USD|dollars)'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def extract_experience_level(self, text: str) -> Optional[str]:
        """Extract experience level requirement"""
        text_lower = text.lower()
        
        if re.search(r'\b(?:senior|sr\.|lead|principal|staff)\b', text_lower):
            return 'Senior'
        elif re.search(r'\b(?:mid-level|mid level|intermediate)\b', text_lower):
            return 'Mid-Level'
        elif re.search(r'\b(?:junior|jr\.|entry|entry-level|entry level)\b', text_lower):
            return 'Junior/Entry-Level'
        elif re.search(r'\b\d+\+?\s*years?\s*(?:of\s*)?experience\b', text_lower):
            exp_match = re.search(r'\b(\d+)\+?\s*years?\s*(?:of\s*)?experience\b', text_lower)
            if exp_match:
                years = int(exp_match.group(1))
                if years >= 7:
                    return 'Senior'
                elif years >= 3:
                    return 'Mid-Level'
                else:
                    return 'Junior/Entry-Level'
        
        return 'Not Specified'
    
    def generate_summary(self, body: str, subject: str = '', max_length: int = 400) -> str:
        """Generate an intelligent summary focused on key decision points"""
        cleaned = re.sub(r'<[^>]+>', '', body)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        important_phrases = [
            r'(?:job description|role|position|opportunity)[^.!?]{20,200}[.!?]',
            r'(?:responsibilities|duties|you will)[^.!?]{30,250}[.!?]',
            r'(?:requirements|qualifications|must have|looking for)[^.!?]{30,250}[.!?]',
            r'(?:benefits|compensation|salary|package)[^.!?]{20,200}[.!?]',
            r'(?:apply|interested|contact|next steps)[^.!?]{20,150}[.!?]'
        ]
        
        summary_parts = []
        text_lower = cleaned.lower()
        
        for pattern in important_phrases:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches[:1]:
                start_idx = text_lower.find(match.lower())
                if start_idx >= 0:
                    original_text = cleaned[start_idx:start_idx + len(match)].strip()
                    if original_text and len(original_text) > 20:
                        summary_parts.append(original_text)
        
        if summary_parts:
            summary = ' '.join(summary_parts)[:max_length]
            if len(' '.join(summary_parts)) > max_length:
                summary = summary[:summary.rfind(' ')] + '...'
            return summary
        
        sentences = [s.strip() for s in re.split(r'[.!?]+', cleaned) if len(s.strip()) > 20]
        if sentences:
            summary = '. '.join(sentences[:3]) + '.'
            if len(summary) > max_length:
                summary = summary[:max_length]
                summary = summary[:summary.rfind(' ')] + '...'
            return summary
        
        return cleaned[:max_length] + '...' if len(cleaned) > max_length else cleaned
    
    def parse_job_email(self, email_details: Dict) -> Dict:
        """Parse a job email and extract all relevant information"""
        subject = email_details.get('subject', '')
        body = email_details.get('body', '') + ' ' + email_details.get('snippet', '')
        sender = email_details.get('from', '')
        full_text = f"{subject} {body}"
        
        sender_email = self.extract_email_from_sender(sender)
        sender_name = self.extract_name_from_sender(sender)
        
        job_info = {
            'email_id': email_details.get('id'),
            'subject': subject,
            'date': email_details.get('date'),
            'job_title': self.extract_job_title(subject, body) or 'Not Extracted',
            'sender': {
                'name': sender_name or 'Unknown',
                'email': sender_email or 'Unknown',
                'full': sender,
                'phone': self.extract_phone_numbers(body),
                'social_media': self.extract_social_links(body)
            },
            'location': self.extract_location(full_text) or 'Not Specified',
            'technologies': self.extract_technologies(full_text),
            'salary': self.extract_salary(body),
            'experience_level': self.extract_experience_level(full_text),
            'summary': self.generate_summary(body, subject, 400),
            'raw_snippet': email_details.get('snippet', '')[:200]
        }
        
        return job_info
