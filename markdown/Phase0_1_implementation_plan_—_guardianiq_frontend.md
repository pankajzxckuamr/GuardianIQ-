# Implementation Plan — GuardianIQ Frontend Foundation

This plan outlines the complete architectural design and step-by-step implementation strategy for the **GuardianIQ / SignalMDM frontend foundation**. The frontend is built using **React, Vite, TypeScript, and Vanilla CSS** (strictly conforming to the no-inline-styles rule and decentralized service architecture), fully integrated with the existing FastAPI backend's contracts, auth flow, and response wrappers.

---

## User Review Required

> [!IMPORTANT]
> **Authentication & CORS Contracts**
> 1. The FastAPI backend auth endpoints (/api/auth/login) use standard `OAuth2PasswordRequestForm` dependencies, which expect form-data (`application/x-www-form-urlencoded` body containing `username` and `password`). The frontend login service will map standard JSON fields to `URLSearchParams` to ensure seamless integration.
> 2. The backend uses a dual-layered auth scheme:
>    - Returns `access_token` and `refresh_token` at the root and in the `data` wrapper for OAuth2 compatibility.
>    - The frontend will store the tokens in-memory (or in browser session storage) and configure all fetch modules to include `credentials: "include"`, ensuring browser cookies are fully transmitted for session persistence.
> 3. CORS settings in the FastAPI backend currently permit `http://localhost:3000`, `http://localhost:5173`, `http://localhost:5174`, `http://127.0.0.1:3000`, and `http://127.0.0.1:5173`. We will run the Vite development server on `http://localhost:5173`.

> [!TIP]
> **Decentralized API Service Rules**
> To prevent dependency cycles and maintain a strict separation of concerns, the frontend will contain **no centralized API singleton** (e.g. no global `apiClient.ts`). Instead, each domain-specific folder (`services/auth`, `services/health`, `services/tenants`, etc.) will own its fetch client, request/response headers, error parsers, and endpoints.
> They will share common utility helpers from `services/shared/` to inject `X-Request-ID` and `X-Device-ID` (device fingerprint).

---

## Open Questions

> [!NOTE]
> None. The backend contracts are well-defined in the repository (`app/main.py`, `app/modules/auth/routes.py`, `app/core/middleware.py`). We will build a production-grade integration that exactly aligns with the database model, request wrapper, and health contracts.

---

## Proposed Changes

We will construct the exact folder structure requested. The files will be created in logical, dependent order (types and utilities first, services next, then UI components, routing, pages, and finally server-side packaging).

### 1. Project Scaffolding and Configurations

#### [NEW] [package.json](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/package.json)
- Full production `package.json` with scripts: `dev`, `build`, `serve`, `typecheck`, `lint`.
- Dependencies: `react`, `react-dom`, `react-router-dom`, `lucide-react` (for icons).
- DevDependencies: `typescript`, `@types/react`, `@types/react-dom`, `vite`, `eslint`, `@typescript-eslint/parser`, `@typescript-eslint/eslint-plugin`, `express` (for the production serve script), `@types/express`, `helmet`.

#### [NEW] [tsconfig.json](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/tsconfig.json)
- Strict TypeScript configuration (`"strict": true`, `"noImplicitAny": true`, `"strictNullChecks": true`, `"moduleResolution": "node"`).

#### [NEW] [vite.config.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/vite.config.ts)
- Vite configuration with port `5173` and path alias setups if needed.

#### [NEW] [.env](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/.env)
- Environment setup matching `.env.example`.

---

### 2. Styling System

We will construct a CSS system with absolute separation from React components, avoiding any inline styling.

#### [NEW] [theme.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/styles/theme.css)
- CSS custom properties (variables) for dark-theme palette, typography (Inter), spacing scales, glassmorphism layers, micro-animations, and transition timings.

#### [NEW] [globals.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/styles/globals.css)
- Reset rules, typography setups, scrollbars, global focus ring accessibility, and responsive core layout utilities.

#### [NEW] [app.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/styles/app.css)
- Main application structure styling, layout containers, and side-nav / header wrappers.

#### [NEW] [login.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/styles/pages/login.css)
- Glassmorphic card styling, input focus lines, gradient glows, and active loading animations.

#### [NEW] [dashboard.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/styles/pages/dashboard.css)
- Dashboard layout grid, key performance indicators (KPI) cards, table animations, and search filter wrappers.

#### [NEW] [health.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/styles/pages/health.css)
- Connection monitor, database uptime card, environment variables display, and raw JSON response inspection grid.

---

### 3. Core Types and Shared Services

#### [NEW] [api.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/types/api.ts)
- Strictly typed envelopes matching FastAPI's `StandardResponse` (`status`, `request_id`, `message`, `data`).

#### [NEW] [auth.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/types/auth.ts)
- Strictly typed `User`, `Role`, `Permission`, and login response shapes.

#### [NEW] [common.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/types/common.ts)
- Utility types for pagination, navigation, and theme toggling.

#### [NEW] [requestId.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/shared/requestId.ts)
- Generates or tracks `X-Request-ID` to send with API requests and retrieve in response handlers.

#### [NEW] [deviceId.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/shared/deviceId.ts)
- Securely computes/fetches a stable device fingerprint (`X-Device-ID`) and caches it in persistent storage.

#### [NEW] [serviceErrors.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/shared/serviceErrors.ts)
- Custom errors representing HTTP 401 (Unauthorized), 403 (Forbidden), 422 (Validation), Network, and Timeout. Captures `request_id` and raw backend messages.

---

### 4. Decentralized Feature Services

#### [NEW] [authService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/auth/authService.ts) and [authTypes.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/auth/authTypes.ts)
- Independent fetcher for `/api/auth/login` (URL-encoded payload, generates stable session fingerpring), `/api/auth/logout`, and `/api/auth/me`.

#### [NEW] [healthService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/health/healthService.ts) and [healthTypes.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/health/healthTypes.ts)
- Feeds off `/api/health` and `/api/health/db`. Parses response wrappers and captures timing metrics.

#### [NEW] [tenantService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/tenants/tenantService.ts) and [tenantTypes.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/tenants/tenantTypes.ts)
- Services for `/api/tenants` (placeholder integration indicating tenant structure).

#### [NEW] [foundationService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/foundation/foundationService.ts) and [foundationTypes.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/foundation/foundationTypes.ts)
- Services for `/api/foundation/*` models.

#### [NEW] [auditService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/audit/auditService.ts) and [auditTypes.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/audit/auditTypes.ts)
- Real/simulated module to query backend audit trails at `/api/audit/*`.

---

### 5. Utilities

#### [NEW] [storage.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/utils/storage.ts)
- Typesafe interfaces for `localStorage` and `sessionStorage`.

#### [NEW] [errors.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/utils/errors.ts)
- Maps complex backend exception details (including nesting FastAPI fields) into human-readable prompts.

#### [NEW] [dates.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/utils/dates.ts)
- Formatting helpers for high-precision epoch and ISO-8601 timestamps returned in the audit trail.

---

### 6. Contexts & Hooks

#### [NEW] [AuthContext.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/context/AuthContext.tsx)
- Provides `currentUser`, `loading`, `login()`, `logout()`, `refreshSession()`, `isAuthenticated()`, and active `roles`/`permissions` checking utilities.

#### [NEW] [useAuth.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/hooks/useAuth.ts)
- Quick wrapper for auth contexts.

#### [NEW] [useTheme.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/hooks/useTheme.ts)
- Manage active theme tokens on the browser `document` root.

---

### 7. Reusable UI Components

Every UI component is strictly typed, has independent styling, handles accessibility properties, and contains NO inline style attributes.

- **Button**: Custom variant actions (primary, secondary, danger, ghost), loader support.
- **Card**: Glassmorphic wrapper containing header, body, footer.
- **Table**: Fully formatted, striped tabular list with customizable headers and actions.
- **Badge**: Tiny color tag for RBAC indicators or health status tags.
- **Loader**: Visual spinning progress indicators.
- **Modal**: Accessible dialogue layer with escape listeners and backdrop overlay.
- **EmptyState**: Visual feedback when data grids are vacant.
- **PageHeader**: Unified component with breadcrumb support, action buttons, and subtitles.
- **FormField**: Beautiful labeled input grid with dynamic backend validation error displays.
- **Toast**: Floating alert notification manager.

---

### 8. Routing, Navigation, & Pages

#### [NEW] [ProtectedRoute.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/routes/ProtectedRoute.tsx)
- RBAC guards based on user roles and specific permissions. Gracefully redirects to `/login` or `/unauthorized`.

#### [NEW] [AppRouter.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/routes/AppRouter.tsx)
- Router mapping for `/login`, `/dashboard`, `/health`, `/unauthorized`, and standard `*` fallback.

#### [NEW] [App.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/app/App.tsx)
- Bootstraps context providers, layouts, global configurations, and Toast overlays.

#### [NEW] [LoginPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/LoginPage.tsx)
- Form layout, handles backend error responses, displays current Request IDs on failure.

#### [NEW] [DashboardPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/DashboardPage.tsx)
- Fully functional grid displaying quick stats (system health, user roles, permission level details, audit log mock, active tenants).

#### [NEW] [FoundationHealthPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/FoundationHealthPage.tsx)
- Connection test module connecting directly to `/api/health` and `/api/health/db`. Real-time latency tracking.

#### [NEW] [UnauthorizedPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/UnauthorizedPage.tsx)
- Error display when users try to view areas beyond their credentials level.

#### [NEW] [NotFoundPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/NotFoundPage.tsx)
- Interactive and animated 404 display.

---

### 9. Server client for Production Serving

#### [NEW] [serverClient.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/server/serverClient.ts)
- Express server supporting SPA catch-all routing (`/*` to `index.html`), Helmet CSP setup, gzip compression, and direct static directory serving.

---

## Verification Plan

### Automated Build & Lint Check
- **Commands**:
  - `npm run typecheck` (validates TypeScript compilation and contract interfaces)
  - `npm run build` (compiles and packages application assets into `dist/`)
  - Run linting checks using standard configuration scripts.

### Manual Integration Verification
1. Start the FastAPI backend server inside `backend/` using its startup shell or command, or ensure it is running at `http://localhost:8000`.
2. Start the Vite development server using `npm run dev` at `http://localhost:5173`.
3. Open `http://localhost:5173/health` to confirm the green status of FastAPI API and Database connections.
4. Attempt a login at `http://localhost:5173/login` using standard credentials, inspect the console/network tabs to ensure `X-Request-ID` and `X-Device-ID` headers are sent.
5. Verify that `/dashboard` displays details matching the logged-in user retrieved from `/api/auth/me`.
