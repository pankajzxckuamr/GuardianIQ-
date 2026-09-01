# ==============================================================================
# GuardianIQ Gunicorn + Uvicorn Production Configuration
# ==============================================================================

import multiprocessing
import os

# Server socket
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
# For CPU bound or I/O bound async FastAPI applications:
workers = int(os.getenv("WEB_CONCURRENCY", (multiprocessing.cpu_count() * 2) + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = int(os.getenv("WEB_TIMEOUT", 120))
keepalive = int(os.getenv("WEB_KEEPALIVE", 5))

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s µs'

# Process naming
proc_name = "guardianiq_api"

# Graceful shutdown
graceful_timeout = 30
