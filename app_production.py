# Enhanced Production Flask App with Scaling Features
import os
import time
import logging
from functools import wraps
from flask import Flask, request, jsonify, render_template, send_from_directory, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from prometheus_flask_exporter import PrometheusMetrics
import redis
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")

# Configuration
app.config.update({
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production'),
    'REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
    'CACHE_DEFAULT_TIMEOUT': 300,
    'RATELIMIT_STORAGE_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/2'),
})

# Initialize extensions
cache = Cache(app)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri=app.config['RATELIMIT_STORAGE_URL']
)
limiter.init_app(app)

# Initialize Prometheus metrics
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')

# Static metrics for monitoring
chat_requests_total = metrics.counter(
    'chat_requests_total', 'Total chat requests', labels={'status': lambda: getattr(g, 'status', 'unknown')}
)

chat_response_time = metrics.histogram(
    'chat_response_time_seconds', 'Chat response time in seconds'
)

# Import your existing modules
from chat import chat_with_agent, redis_memory
from tools.product_search_tool import ProductSearchTool
import json

# Initialize the product search tool
search_tool = ProductSearchTool()

# Middleware for request timing and logging
@app.before_request
def before_request():
    g.start_time = time.time()
    g.request_id = request.headers.get('X-Request-ID', f'req_{int(time.time()*1000)}')
    
    logger.info(
        "request_started",
        method=request.method,
        path=request.path,
        remote_addr=get_remote_address(),
        user_agent=request.headers.get('User-Agent'),
        request_id=g.request_id
    )

@app.after_request
def after_request(response):
    duration = time.time() - g.start_time
    g.status = response.status_code
    
    logger.info(
        "request_completed",
        status_code=response.status_code,
        duration=duration,
        request_id=getattr(g, 'request_id', 'unknown')
    )
    
    # Add response headers
    response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
    response.headers['X-Response-Time'] = f'{duration:.3f}s'
    
    return response

# Error handlers
@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning("rate_limit_exceeded", remote_addr=get_remote_address())
    return jsonify({
        "error": "Rate limit exceeded",
        "message": "Too many requests. Please wait before trying again.",
        "retry_after": str(e.retry_after)
    }), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error("internal_server_error", error=str(error))
    return jsonify({
        "error": "Internal server error",
        "message": "We're experiencing high traffic. Please try again shortly."
    }), 500

@app.errorhandler(503)
def service_unavailable(error):
    logger.error("service_unavailable", error=str(error))
    return jsonify({
        "error": "Service temporarily unavailable",
        "message": "Service is temporarily unavailable. Please try again later."
    }), 503

# Caching decorator
def cached_response(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f"{f.__name__}:{hash(str(args) + str(kwargs))}"
            result = cache.get(cache_key)
            if result is None:
                result = f(*args, **kwargs)
                cache.set(cache_key, result, timeout=timeout)
            return result
        return decorated_function
    return decorator

# Routes
@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

@app.route("/", methods=["GET"])
@cached_response(timeout=3600)  # Cache homepage for 1 hour
def index():
    return render_template("chat.html")

@app.route("/health", methods=["GET"])
def health():
    """Comprehensive health check endpoint"""
    try:
        # Test Redis connection
        redis_start = time.time()
        redis_memory.redis_client.ping()
        redis_duration = time.time() - redis_start
        
        # Check search tool availability
        pinecone_status = "connected" if search_tool.is_available else "disconnected"
        api_status = "available" if search_tool.api_available else "unavailable"
        
        # System metrics
        import psutil
        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent(interval=1)
        
        health_data = {
            "status": "healthy",
            "service": "Lotus Electronics Chatbot",
            "timestamp": time.time(),
            "version": "1.0.0",
            "components": {
                "redis": {
                    "status": "connected",
                    "response_time": f"{redis_duration:.3f}s"
                },
                "search_methods": {
                    "pinecone_vector": pinecone_status,
                    "lotus_api": api_status
                }
            },
            "metrics": {
                "active_users": len(redis_memory.get_active_users()),
                "memory_usage": f"{memory_usage}%",
                "cpu_usage": f"{cpu_usage}%"
            }
        }
        
        logger.info("health_check_success", **health_data)
        return jsonify(health_data)
        
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }), 503

@app.route("/chat", methods=["POST", "OPTIONS"])
@limiter.limit("30 per minute")  # Rate limiting for chat endpoint
@chat_response_time.time()  # Prometheus timing
def chat():
    """Enhanced chat endpoint with better error handling and monitoring"""
    try:
        if request.method == "OPTIONS":
            response = jsonify({"status": "ok"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "*")
            response.headers.add('Access-Control-Allow-Methods', "*")
            return response

        # Validate API key
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != "nawabkhan":
            logger.warning("unauthorized_access", remote_addr=get_remote_address())
            return jsonify({"error": "Unauthorized"}), 401

        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        user_message = data.get("message", "").strip()
        session_id = data.get("session_id", "")

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        if not session_id:
            return jsonify({"error": "Session ID is required"}), 400

        logger.info(
            "chat_request",
            session_id=session_id,
            message_length=len(user_message),
            request_id=g.request_id
        )

        # Process with timeout
        start_time = time.time()
        
        try:
            # Call your existing chat function
            result = chat_with_agent(user_message, session_id)
            
            processing_time = time.time() - start_time
            logger.info(
                "chat_response_generated",
                session_id=session_id,
                processing_time=processing_time,
                request_id=g.request_id
            )

            # Add CORS headers
            response = jsonify({"response": result})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "*")
            response.headers.add("Access-Control-Allow-Methods", "*")
            
            g.status = 200
            return response

        except Exception as chat_error:
            logger.error(
                "chat_processing_error",
                session_id=session_id,
                error=str(chat_error),
                request_id=g.request_id
            )
            
            g.status = 500
            return jsonify({
                "error": "Chat processing failed",
                "message": "I'm experiencing high traffic. Please try again shortly."
            }), 500

    except Exception as e:
        logger.error(
            "chat_endpoint_error",
            error=str(e),
            request_id=getattr(g, 'request_id', 'unknown')
        )
        
        g.status = 500
        return jsonify({
            "error": "Internal server error",
            "message": "We're experiencing technical difficulties. Please try again."
        }), 500

# Additional monitoring endpoints
@app.route("/metrics")
def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return metrics.generate_latest()

@app.route("/status")
@cached_response(timeout=60)  # Cache for 1 minute
def status():
    """Service status endpoint"""
    try:
        active_users = len(redis_memory.get_active_users())
        
        return jsonify({
            "service": "Lotus Electronics Chatbot",
            "status": "operational",
            "active_users": active_users,
            "timestamp": time.time(),
            "version": "1.0.0"
        })
    except Exception as e:
        logger.error("status_check_failed", error=str(e))
        return jsonify({
            "service": "Lotus Electronics Chatbot",
            "status": "degraded",
            "error": str(e),
            "timestamp": time.time()
        }), 503

if __name__ == "__main__":
    # Development server (not for production)
    app.run(debug=True, host="0.0.0.0", port=8001)
