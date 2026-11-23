"""
Gunicorn Configuration.

Configures the Gunicorn WSGI/ASGI server for production deployment on AWS ECS/EKS.
Optimizes worker processes, keeps connections alive for ALBs, and configures stdout/stderr logging.
"""

import multiprocessing
import os

# Port and binding IP configuration
# Bind to Render's dynamic PORT as well as fallback ports 8000 and 10000 so reverse proxy connects immediately
port = os.getenv("PORT", "10000")
bind = list({f"0.0.0.0:{port}", "0.0.0.0:8000", "0.0.0.0:10000"})

# Determine worker count based on CPU allocation or setting
# Set conservative default of 1 worker for container environments (Render/ECS) to prevent memory exhaustion (512MB limit)
workers = int(os.getenv("WEB_CONCURRENCY", "1"))

# Uvicorn worker class for ASGI application serving
worker_class = "uvicorn.workers.UvicornWorker"

# Load Balancer (ALB) compatibility settings
# Keepalive should exceed the load balancer idle timeout (default AWS ALB timeout is 60s)
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "300"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "300"))

# Logging: Output directly to standard out/err to facilitate AWS CloudWatch ingestion
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "INFO").lower()

# Process naming
proc_name = "enterprise-api"
