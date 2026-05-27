import express from 'express';
import helmet from 'helmet';
import compression from 'compression';
import { createProxyMiddleware } from 'http-proxy-middleware';
import path from 'path';
import fs from 'fs';

const app = express();
const PORT = process.env.PORT || 3000;
const PROXY_API = process.env.PROXY_API === 'true';
const VITE_API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Enable gzip compression for better performance
app.use(compression());

// Enforce Content Security Policy via Helmet
app.use(
  helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        connectSrc: ["'self'", VITE_API_BASE_URL],
        scriptSrc: ["'self'"], // No unsafe-inline or unsafe-eval in production
        styleSrc: ["'self'", "'unsafe-inline'"], // Transitional for Google Fonts
        fontSrc: ["'self'"],
        imgSrc: ["'self'", 'data:'],
        objectSrc: ["'none'"],
        frameAncestors: ["'self'"],
      },
    },
  })
);

// Proxy /api requests to backend if PROXY_API is enabled
if (PROXY_API) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: VITE_API_BASE_URL,
      changeOrigin: true,
    })
  );
}

// Determine dist path robustly
// Using process.cwd() ensures it works regardless of ESM/CommonJS transpilation context
// as long as the server is started from the project root.
const distPath = path.join(process.cwd(), 'dist');

if (!fs.existsSync(distPath)) {
  console.warn(`[WARNING] Static directory not found: ${distPath}`);
  console.warn(`[WARNING] Did you forget to run 'npm run build' for the frontend?`);
}

// Serve static assets from the Vite build output
app.use(express.static(distPath));

// Catch-all route to return index.html for SPA routing
app.get('*', (req, res) => {
  res.sendFile(path.join(distPath, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`\n======================================================`);
  console.log(`[GuardianIQ] Production Server Started`);
  console.log(`======================================================`);
  console.log(`PORT: ${PORT}`);
  console.log(`CSP:  Enforced via Helmet`);
  console.log(`API Proxy: ${PROXY_API ? `Enabled (Target: ${VITE_API_BASE_URL})` : 'Disabled'}`);
  console.log(`\nServing static files from: ${distPath}`);
});
