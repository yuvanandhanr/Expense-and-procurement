"""
Gunicorn Configuration.

Configures the Gunicorn WSGI/ASGI server for production deployment on AWS ECS/EKS.
Optimizes worker processes, keeps connections alive for ALBs, and configures stdout/stderr logging.
"""

import multiprocessing
import os

# Port and binding IP configuration
port = os.getenv("PORT", "8000")
bind = f"0.0.0.0:{port}"

# Determine worker count based on CPU allocation or setting
cores = multiprocessing.cpu_count()
workers = int(os.getenv("WEB_CONCURRENCY", str((cores * 2) + 1)))

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
