import logging
import os

logger = logging.getLogger(__name__)

def send_workflow_approval_notification(workflow_name: str, approver_email: str, owner_name: str) -> None:
    """
    Sends a mock Email-only alert for workflow approval and logs it to a file.
    """
    subject = f"Action Required: Approve Workflow '{workflow_name}'"
    body = f"Hello,\n\nUser '{owner_name}' has requested your approval for the workflow '{workflow_name}'.\nPlease review and approve at your earliest convenience."
    
    print(f"[EMAIL NOTIFICATION SENT] To: {approver_email} | Subject: {subject}")
    logger.info(f"[EMAIL NOTIFICATION SENT] To: {approver_email} | Subject: {subject}")
    
    # Append to logs/notifications.log
    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "notifications.log")
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"--- EMAIL ALERT ---\nTo: {approver_email}\nSubject: {subject}\nBody: {body}\n\n")
    except Exception as e:
        logger.error(f"Failed to write notification log: {e}")
