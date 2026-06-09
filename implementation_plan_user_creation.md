# Implementation Plan: Automatic Login Credentials for Registry Users

## Goal
Bridge the gap between the Governance Registry and the Authentication system. Whenever a new user is registered via the "Users & Roles" UI, the system will automatically provision an authentication account so the user can log in immediately.

## Open Questions
None.

## Proposed Changes

### Backend Components

#### [MODIFY] [backend/app/modules/registry/services.py](file:///d:/GuardianIQ--1/backend/app/modules/registry/services.py)
Update the `create_user` function.
- **Before creating the `GuardianUser`**, check if an authentication `User` already exists for the given email.
- **If not**, create a new `User` record in the authentication system:
  - Set the password to a default value: `Admin@1234!`
  - Extract the `role_code` from the provided Registry Role ID.
  - Find the matching Authentication Role and assign it to the new `User`.
- Commit both the auth `User` and the `GuardianUser` in the same database session so they stay perfectly in sync.

#### [MODIFY] [backend/app/modules/registry/repositories.py](file:///d:/GuardianIQ--1/backend/app/modules/registry/repositories.py)
Ensure that the `create_user` logic shares the SQLAlchemy `db` session with the newly added Authentication user code.

## Verification Plan
1. Start the application.
2. Go to **Registry > Users & Roles** on the frontend.
3. Click **+ Register User** and create a brand new user.
4. Log out.
5. Attempt to log in with the newly created user's email and the default password `Admin@1234!`.
6. Verify successful login.
