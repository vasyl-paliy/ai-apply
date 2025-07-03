"""Email service for sending job applications and automated emails."""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import asyncio
from jinja2 import Environment, FileSystemLoader
from loguru import logger

from ..config import settings


class EmailService:
    """Service for sending emails with job applications and notifications."""
    
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email
        self.from_name = settings.from_name
        
        # Setup Jinja2 for email templates
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
    
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and authenticate SMTP connection."""
        try:
            if self.smtp_port == 465:
                # SSL connection
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                # TLS connection
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls(context=ssl.create_default_context())
            
            server.login(self.smtp_username, self.smtp_password)
            return server
            
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise
    
    async def send_job_application_email(
        self,
        to_email: str,
        to_name: Optional[str],
        job_title: str,
        company_name: str,
        cover_letter: str,
        user_profile: Dict[str, Any],
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send a job application email with cover letter and resume."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = f"Application for {job_title} - {user_profile['full_name']}"
            
            # Create email body
            email_body = self._create_application_email_body(
                to_name=to_name,
                job_title=job_title,
                company_name=company_name,
                cover_letter=cover_letter,
                user_profile=user_profile
            )
            
            msg.attach(MIMEText(email_body, 'html'))
            
            # Add attachments (resume, portfolio, etc.)
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Send email
            with self._create_smtp_connection() as server:
                server.send_message(msg)
                
            logger.info(f"Job application email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send job application email: {e}")
            return False
    
    async def send_follow_up_email(
        self,
        to_email: str,
        to_name: Optional[str],
        job_title: str,
        company_name: str,
        user_profile: Dict[str, Any],
        application_date: datetime,
        follow_up_type: str = "initial"  # initial, second, final
    ) -> bool:
        """Send a follow-up email for a job application."""
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = f"Following up on {job_title} Application - {user_profile['full_name']}"
            
            # Create follow-up email body
            email_body = self._create_follow_up_email_body(
                to_name=to_name,
                job_title=job_title,
                company_name=company_name,
                user_profile=user_profile,
                application_date=application_date,
                follow_up_type=follow_up_type
            )
            
            msg.attach(MIMEText(email_body, 'html'))
            
            # Send email
            with self._create_smtp_connection() as server:
                server.send_message(msg)
                
            logger.info(f"Follow-up email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send follow-up email: {e}")
            return False
    
    async def send_notification_email(
        self,
        to_email: str,
        subject: str,
        message: str,
        notification_type: str = "info"  # info, success, warning, error
    ) -> bool:
        """Send a notification email to the user."""
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Create notification email body
            email_body = self._create_notification_email_body(
                message=message,
                notification_type=notification_type
            )
            
            msg.attach(MIMEText(email_body, 'html'))
            
            # Send email
            with self._create_smtp_connection() as server:
                server.send_message(msg)
                
            logger.info(f"Notification email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification email: {e}")
            return False
    
    async def send_daily_summary_email(
        self,
        to_email: str,
        user_name: str,
        summary_data: Dict[str, Any]
    ) -> bool:
        """Send daily summary email with application statistics."""
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = f"Daily Job Application Summary - {datetime.now().strftime('%B %d, %Y')}"
            
            # Create summary email body
            email_body = self._create_daily_summary_email_body(
                user_name=user_name,
                summary_data=summary_data
            )
            
            msg.attach(MIMEText(email_body, 'html'))
            
            # Send email
            with self._create_smtp_connection() as server:
                server.send_message(msg)
                
            logger.info(f"Daily summary email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send daily summary email: {e}")
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message."""
        try:
            file_path = attachment['path']
            filename = attachment.get('filename', Path(file_path).name)
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Determine attachment type
            if filename.endswith('.pdf'):
                part = MIMEApplication(file_data, _subtype='pdf')
            elif filename.endswith(('.doc', '.docx')):
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file_data)
                encoders.encode_base64(part)
            else:
                part = MIMEApplication(file_data)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment}: {e}")
    
    def _create_application_email_body(
        self,
        to_name: Optional[str],
        job_title: str,
        company_name: str,
        cover_letter: str,
        user_profile: Dict[str, Any]
    ) -> str:
        """Create HTML email body for job application."""
        try:
            template = self.jinja_env.get_template('job_application.html')
            return template.render(
                to_name=to_name or "Hiring Manager",
                job_title=job_title,
                company_name=company_name,
                cover_letter=cover_letter,
                user_profile=user_profile
            )
        except Exception:
            # Fallback to simple template
            return self._create_simple_application_email_body(
                to_name, job_title, company_name, cover_letter, user_profile
            )
    
    def _create_simple_application_email_body(
        self,
        to_name: Optional[str],
        job_title: str,
        company_name: str,
        cover_letter: str,
        user_profile: Dict[str, Any]
    ) -> str:
        """Create simple HTML email body for job application."""
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .content {{ padding: 20px; }}
                .signature {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Job Application: {job_title}</h2>
                <p>Dear {to_name or 'Hiring Manager'},</p>
            </div>
            
            <div class="content">
                <p>I am writing to express my interest in the {job_title} position at {company_name}.</p>
                
                <div style="margin: 20px 0; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
                    {cover_letter.replace('\n', '<br>')}
                </div>
                
                <p>I have attached my resume for your review. I look forward to hearing from you soon.</p>
                
                <div class="signature">
                    <p>Best regards,<br>
                    <strong>{user_profile['full_name']}</strong><br>
                    {user_profile.get('phone', '')}<br>
                    {user_profile.get('email', '')}<br>
                    {user_profile.get('linkedin_url', '')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_follow_up_email_body(
        self,
        to_name: Optional[str],
        job_title: str,
        company_name: str,
        user_profile: Dict[str, Any],
        application_date: datetime,
        follow_up_type: str
    ) -> str:
        """Create HTML email body for follow-up."""
        days_ago = (datetime.now() - application_date).days
        
        if follow_up_type == "initial":
            subject_line = f"Following up on my {job_title} application"
            opening = f"I wanted to follow up on my application for the {job_title} position that I submitted {days_ago} days ago."
        elif follow_up_type == "second":
            subject_line = f"Continued interest in {job_title} position"
            opening = f"I am following up again regarding my application for the {job_title} position at {company_name}."
        else:  # final
            subject_line = f"Final follow-up on {job_title} application"
            opening = f"This is my final follow-up regarding my application for the {job_title} position."
        
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .content {{ padding: 20px; }}
                .signature {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <div class="content">
                <p>Dear {to_name or 'Hiring Manager'},</p>
                
                <p>{opening}</p>
                
                <p>I remain very interested in this opportunity and would welcome the chance to discuss how my skills and experience can contribute to {company_name}'s success.</p>
                
                <p>Please let me know if you need any additional information from me.</p>
                
                <div class="signature">
                    <p>Best regards,<br>
                    <strong>{user_profile['full_name']}</strong><br>
                    {user_profile.get('phone', '')}<br>
                    {user_profile.get('email', '')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_notification_email_body(
        self,
        message: str,
        notification_type: str
    ) -> str:
        """Create HTML email body for notifications."""
        colors = {
            "info": "#17a2b8",
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545"
        }
        
        color = colors.get(notification_type, "#17a2b8")
        
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .notification {{ padding: 20px; border-left: 4px solid {color}; background-color: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="notification">
                <h3 style="color: {color}; margin-top: 0;">AutoApply AI Notification</h3>
                <p>{message}</p>
            </div>
        </body>
        </html>
        """
    
    def _create_daily_summary_email_body(
        self,
        user_name: str,
        summary_data: Dict[str, Any]
    ) -> str:
        """Create HTML email body for daily summary."""
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .summary {{ padding: 20px; background-color: #f8f9fa; border-radius: 5px; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat {{ text-align: center; padding: 15px; background-color: white; border-radius: 5px; }}
                .stat-number {{ font-size: 24px; font-weight: bold; color: #007bff; }}
            </style>
        </head>
        <body>
            <div class="summary">
                <h2>Daily Summary - {datetime.now().strftime('%B %d, %Y')}</h2>
                <p>Hello {user_name},</p>
                
                <p>Here's your daily job application summary:</p>
                
                <div class="stats">
                    <div class="stat">
                        <div class="stat-number">{summary_data.get('applications_sent', 0)}</div>
                        <div>Applications Sent</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{summary_data.get('new_matches', 0)}</div>
                        <div>New Job Matches</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{summary_data.get('responses_received', 0)}</div>
                        <div>Responses Received</div>
                    </div>
                </div>
                
                <p>Keep up the great work! Your AutoApply AI is working hard for you.</p>
            </div>
        </body>
        </html>
        """
    
    async def test_connection(self) -> bool:
        """Test SMTP connection."""
        try:
            with self._create_smtp_connection() as server:
                server.noop()
            return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False 