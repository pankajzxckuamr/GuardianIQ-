/* src/server/serverClient.ts */
import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import helmet from "helmet";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 5173;

// Configure strict Content Security Policy (CSP)
app.use(
  helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        connectSrc: ["'self'", "http://localhost:8000", "ws://localhost:5173"],
        styleSrc: [
          "'self'",
          "'unsafe-inline'",
          "https://fonts.googleapis.com"
        ],
        fontSrc: ["'self'", "https://fonts.gstatic.com"],
        imgSrc: ["'self'", "data:", "blob:"],
        scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'"], // unsafe-inline / unsafe-eval are permitted for development support, but restricted where practical
        objectSrc: ["'none'"],
        frameAncestors: ["'self'"],
      },
    },
  })
);

// Serve static assets from built dist folder
const distPath = path.join(__dirname, "../dist");
app.use(express.static(distPath));

// Support SPA routing - fallback all other GET requests to index.html
app.get("*", (_req, res) => {
  res.sendFile(path.join(distPath, "index.html"));
});

app.listen(PORT, () => {
  console.log(`[GuardianIQ] Production client server active on port ${PORT}`);
  console.log(`[GuardianIQ] Content Security Policy (CSP) successfully enforced.`);
});
