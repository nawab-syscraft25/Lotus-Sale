# Gunicorn Production Configuration for High Scale
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8001"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Dynamic based on CPU cores
worker_class = "gevent"  # Async worker for better concurrency
worker_connections = 1000  # Max connections per worker
max_requests = 1000  # Restart workers after X requests (prevents memory leaks)
max_requests_jitter = 50  # Add randomness to max_requests
preload_app = True  # Load app before forking workers (saves memory)

# Worker timeout and keep-alive
timeout = 30  # Worker timeout in seconds
keepalive = 5  # Keep-alive connections

# SSL (if needed)
# keyfile = "/path/to/ssl/key.pem"
# certfile = "/path/to/ssl/cert.pem"

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "lotus-chatbot-api"

# Server mechanics
daemon = False  # Set to True for production daemon mode
pidfile = "logs/gunicorn.pid"
user = None  # Set to specific user in production
group = None  # Set to specific group in production
tmp_upload_dir = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance tuning
worker_tmp_dir = "/dev/shm" if os.path.exists("/dev/shm") else None  # Use RAM for temp files
forwarded_allow_ips = "*"  # Configure for your load balancer
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

# Monitoring hooks
def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal."""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")
