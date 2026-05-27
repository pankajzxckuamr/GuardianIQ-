# GuardianIQ Frontend Production Server

The GuardianIQ frontend includes a custom Node.js Express server (`src/server/serverClient.ts`) optimized for production environments. 

## Features
- Serves the compiled SPA (`dist/` folder).
- Catch-all routing (`*` -> `index.html`) for React Router.
- Enforces strict security via **Helmet**, including a Content Security Policy (CSP).
- Optional API Proxy via `http-proxy-middleware`.
- Gzip compression via `compression`.

## Running in Production

To run the production server, simply use the npm serve script from the `frontend` root:

```bash
# This will build both the frontend bundle (dist) and the server (dist-server) before starting the app.
npm run serve
```

### Environment Variables

The server respects the following environment variables:

- `PORT`: The port to listen on (Default: `3000`)
- `PROXY_API`: Set to `true` to proxy `/api/*` requests to the backend. Useful if you are not putting the frontend and backend behind an Nginx reverse proxy. (Default: `false`)
- `VITE_API_BASE_URL`: The backend target URL if `PROXY_API` is enabled. Also used in the CSP `connect-src` directive. (Default: `http://localhost:8000`)

### Example Docker/PM2 Start Command

If running directly in production via PM2:

```bash
export PROXY_API=true
export VITE_API_BASE_URL=http://api.guardianiq.internal
npm run build
npm run build:server
NODE_ENV=production pm2 start dist-server/serverClient.js --name "giq-frontend"
```

## Security (Content Security Policy)

The server enforces the following strict CSP:
- `default-src 'self'`
- `connect-src 'self' <VITE_API_BASE_URL>`
- `script-src 'self'` (No inline scripts or eval permitted)
- `style-src 'self' 'unsafe-inline'` (Allows transitional inline styles, e.g., Google Fonts)
- `img-src 'self' data:`
- `object-src 'none'`
- `frame-ancestors 'self'`
