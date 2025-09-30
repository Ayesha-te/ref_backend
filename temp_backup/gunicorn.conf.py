"""
Gunicorn configuration optimized for Neon database connections
"""
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# Worker processes
# Keep worker count low to avoid exceeding Neon's connection limit (~50 pooled connections)
workers = int(os.environ.get('GUNICORN_WORKERS', '2'))
worker_class = "sync"  # Use sync workers instead of async to avoid connection leaks
worker_connections = 1000
max_requests = 200  # Restart workers after 200 requests to prevent memory leaks
max_requests_jitter = 50  # Add randomness to prevent all workers restarting at once

# Threading
threads = int(os.environ.get('GUNICORN_THREADS', '4'))

# Timeout
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'nexocart-backend'

# Server mechanics
preload_app = True  # Load application code before forking workers
enable_stdio_inheritance = True

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190