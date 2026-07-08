# Implementation Plan - Integrate Tailwind CSS in Frontend

This plan outlines the steps to install and configure Tailwind CSS in the frontend react-vite project. This will restore the styling and layout for Phase 2 pages (such as Schedule Approvals, Run History, and Authorization Simulator) which are currently built using Tailwind classes but lack the Tailwind compiler.

## Proposed Changes

### Configuration Files

#### [NEW] [tailwind.config.js](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/tailwind.config.js)
- Create a Tailwind configuration file targeting all `.tsx` and `.ts` source files.

#### [NEW] [postcss.config.js](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/postcss.config.js)
- Configure PostCSS to compile Tailwind and Autoprefixer.

#### [MODIFY] [package.json](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/package.json)
- Add `tailwindcss`, `postcss`, and `autoprefixer` to devDependencies.

### Style Sheets

#### [MODIFY] [global.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/styles/global.css)
- Import Tailwind's base, components, and utilities layers alongside existing custom styles.

---

## Verification Plan

### Automated Steps
- Run `npm install` to install the dependencies.
- Start/restart the frontend development server using `npm run dev` to verify compilation.

### Manual Verification
- View the UI pages (especially **Authorization Simulator** and **Schedule Approvals**) in the browser.
- Verify that inputs have borders and background styling, checkboxes are styled and aligned, cards display on grid columns, and Tailwind utility classes compile correctly.
