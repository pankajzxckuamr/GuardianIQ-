# Implementation Plan - SMTP Email Notifications with Dynamic Reply-To

Enable actual email notifications to be sent to designated workflow approvers (e.g., `trynewthings247forfun@gmail.com` for Aayush Barapatre) instead of falling back to logging them to `notifications.log`, with a dynamic `Reply-To` header pointing to the workflow owner's email.

## User Review Required
> [!IMPORTANT]
> To send emails via Gmail SMTP, you must configure a sending email address (e.g., a service or personal Gmail account) and generate a **Google App Password**. Do not use your primary Google account password as it will be rejected by Google's SMTP security policies.
> Setting the `Reply-To` header to the workflow owner's email allows the designated approver to click "Reply" in their email client and communicate directly with the owner, even though the email is dispatched securely from the system's verified sending address.

## Proposed Changes

### 1. Notifications Module

#### [MODIFY] [notifications.py](file:///c:/Users/aayus/desktop/GuardianIQ--1/backend/app/modules/registry/notifications.py)
- Update `send_workflow_approval_notification` signature to accept `owner_email: Optional[str] = None`.
- In SMTP mode, set the `Reply-To` header if `owner_email` is provided:
  ```python
  if owner_email:
      msg['Reply-To'] = owner_email
  ```
- In log fallback mode, log the `Reply-To` header as well.

### 2. Workflow Services

#### [MODIFY] [services.py](file:///c:/Users/aayus/desktop/GuardianIQ--1/backend/app/modules/registry/services.py)
- Update calls to `send_workflow_approval_notification` inside `create_workflow` and `update_workflow` to fetch `owner.email` and pass it as the fourth argument.

### 3. Configuration

#### [MODIFY] [.env](file:///c:/Users/aayus/desktop/GuardianIQ--1/backend/.env)
Add SMTP configuration keys:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-sender-email@gmail.com
SMTP_PASSWORD=your-16-character-app-password
```

## Verification Plan

### Manual Verification
1. Register a new workflow with Aayush Barapatre (`trynewthings247forfun@gmail.com`) set as the approver.
2. Confirm that an email is successfully received at `trynewthings247forfun@gmail.com`.
3. Open the email in the client and click "Reply". Verify that the recipient address defaults to the workflow owner's email address (e.g. `admin@guardianiq.com`) instead of the platform SMTP sending address.
4. Check the console and `backend/logs` to ensure no SMTP errors are logged.
