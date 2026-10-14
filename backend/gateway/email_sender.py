"""
Special Agent - Secure Email Dispatcher
Sends approved job applications directly from Jubayer's Gmail to recruiters with audit logging.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from dotenv import load_dotenv
from backend.database.db import log_outreach, update_application_status

load_dotenv()

class EmailDispatcher:
    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SMTP_USER", "jubayerahmadaistudio@gmail.com")

    @property
    def app_password(self) -> str:
        return os.getenv("SMTP_APP_PASSWORD", "").replace(" ", "").strip()

    def verify_smtp_credentials(self) -> Dict[str, Any]:
        """Verifies Gmail SMTP TLS login without sending an email."""
        pwd = self.app_password
        if not pwd:
            return {"authenticated": False, "message": "SMTP_APP_PASSWORD not set"}

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                server.login(self.sender_email, pwd)
            return {"authenticated": True, "message": "Gmail SMTP Authentication Successful!"}
        except Exception as e:
            return {"authenticated": False, "message": f"SMTP Authentication Error: {str(e)}"}

    def send_application_email(self, application_id: int, recipient_email: str, subject: str, body: str) -> Dict[str, Any]:
        """Sends application email to recruiter after operator approval."""
        pwd = self.app_password
        if not recipient_email or "@" not in recipient_email:
            return {"success": False, "message": "Invalid recipient email"}

        if not pwd:
            log_outreach(
                application_id=application_id,
                recipient_email=recipient_email,
                action="email_approved_dry_run",
                status="success",
                details="Application approved by operator. Queued in dry-run mode (Waiting for Gmail App Password)."
            )
            update_application_status(application_id, "sent")
            return {
                "success": True,
                "mode": "dry_run",
                "message": f"প্রপোজাল সফলভাবে অনুমোদিত হয়েছে এবং কিউতে রাখা হয়েছে! (প্রাপক: {recipient_email})"
            }

        try:
            msg = MIMEMultipart()
            msg["From"] = f"Jubayer <{self.sender_email}>"
            msg["To"] = recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                server.starttls()
                server.login(self.sender_email, pwd)
                server.send_message(msg)

            log_outreach(
                application_id=application_id,
                recipient_email=recipient_email,
                action="email_sent",
                status="success",
                details="Delivered directly via Gmail SMTP."
            )
            update_application_status(application_id, "sent")
            return {"success": True, "mode": "live", "message": f"ইমেইল সরাসরি পাঠানো সম্পন্ন হয়েছে! ({recipient_email})"}
        except Exception as e:
            err_msg = str(e)
            log_outreach(
                application_id=application_id,
                recipient_email=recipient_email,
                action="email_failed",
                status="failure",
                details=err_msg
            )
            return {"success": False, "message": f"ইমেইল পাঠাতে সমস্যা: {err_msg}"}

email_dispatcher = EmailDispatcher()
