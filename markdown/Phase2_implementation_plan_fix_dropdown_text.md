# Implementation Plan - Fix Dropdown Text Visibility

Fix the option text visibility in HTML `<select>` dropdown elements across the application. When select elements are clicked in the dark theme dashboard, option lists often default to a white background while the option text inherits the parent's light-colored/white font, resulting in invisible (white-on-white) option values.

## Proposed Changes

### Frontend Styles

#### [MODIFY] [globals.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/styles/globals.css)
- Add a global CSS rule for `select option` to specify a dark background color and high-contrast text color:
  ```css
  select option {
    background-color: var(--bg-secondary, #121824);
    color: var(--text-primary, #f8fafc);
  }
  ```
  This serves as a global fallback for all standard selects across the entire application (Registry pages, custom forms, etc.).

#### [MODIFY] [phase2Shared.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/phase2Shared.module.css)
- Add explicit option styling targeting CSS-scoped selects (`.filterSelect` and `.formControl`):
  ```css
  .filterSelect option,
  .formControl option {
    background-color: var(--bg-secondary, #121824);
    color: var(--text-primary, #f8fafc);
  }
  ```
  This ensures selects styled with CSS modules render dropdown options with correct background and text colors:
  - [CreateScheduleWizard.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/CreateScheduleWizard.tsx) (now using `formControl` from phase 2 shared styling)
  - [WorkflowSchedulerDashboard.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/WorkflowSchedulerDashboard.tsx)
  - [RunHistoryPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/RunHistoryPage.tsx)
  - [AgentAssignmentMatrix.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/AgentAssignmentMatrix.tsx)
  - [AuthorizationSimulator.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/AuthorizationSimulator.tsx)

## Verification Plan

### Manual Verification
1. Run the frontend development server: `npm run dev` in `frontend/`.
2. Go to "Create Workflow Schedule" (`/workflow-scheduler/new` or via dashboard wizard link) and click on dropdowns like **Workflow**, **Agent**, **Model**, etc. Confirm options are visible.
3. Open "Agent Assignments" and click **Add Assignment**. Click the **Agent**, **Model**, or **Execution Mode** dropdowns; confirm options are visible.
4. Open the filters on the "Workflow Scheduler" or "Run History" pages. Confirm filter dropdowns render visible options.
5. Go to "Authorization Simulator" and click the selects for **Subject Type**, **Object Type**, and **Action Code**. Confirm option lists render visible text.
