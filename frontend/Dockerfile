# ==============================================================================
# GuardianIQ Frontend Dockerfile (Multi-stage Build with Nginx)
# ==============================================================================

# Stage 1: Build the React/Vite SPA
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies (cached if package files do not change)
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build argument for API base URL during static compilation
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Run build
RUN npm run build

# Stage 2: Serve optimized static files via Nginx Alpine
FROM nginx:alpine AS runner

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
