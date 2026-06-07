import logging
import os
import smtplib
from email.message import EmailMessage
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_workflow_approval_notification(workflow_name: str, approver_email: str, owner_name: str) -> None:
    """
    Sends an email alert for workflow approval.
    """
    subject = f"Action Required: Approve Workflow '{workflow_name}'"
    body = f"Hello,\n\nUser '{owner_name}' has requested your approval for the workflow '{workflow_name}'.\nPlease review and approve at your earliest convenience."
    
    logger.info(f"[EMAIL NOTIFICATION ATTEMPT] To: {approver_email} | Subject: {subject}")
    
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT", 587)
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    if smtp_server and smtp_user and smtp_pass:
        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = approver_email

            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            logger.info("Email successfully sent via SMTP.")
            return
        except Exception as e:
            logger.error(f"Failed to send SMTP email: {e}")
            # Fallback to file logging if SMTP fails
    else:
        logger.warning("SMTP credentials not fully configured in .env. Falling back to log file notification.")

    # Fallback / Log File
    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "notifications.log")
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"--- EMAIL ALERT ---\nTo: {approver_email}\nSubject: {subject}\nBody: {body}\n\n")
    except Exception as e:
        logger.error(f"Failed to write notification log: {e}")
