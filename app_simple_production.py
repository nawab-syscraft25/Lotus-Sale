# Simplified Production Flask App
import os
import time
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory, g

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")

# Configuration
app.config.update({
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production'),
})

# Import your existing modules
from chat import chat_with_agent, redis_memory
from tools.product_search_tool import ProductSearchTool
import json

# Initialize the product search tool
search_tool = ProductSearchTool()

# Request tracking
request_count = 0
active_requests = 0

# Middleware for request timing and logging
@app.before_request
def before_request():
    global request_count, active_requests
    request_count += 1
    active_requests += 1
    
    g.start_time = time.time()
    g.request_id = f'req_{int(time.time()*1000)}_{request_count}'
    
    logger.info(
        f"Request started - ID: {g.request_id}, Method: {request.method}, "
        f"Path: {request.path}, Remote: {request.remote_addr}, "
        f"Active: {active_requests}"
    )

@app.after_request
def after_request(response):
    global active_requests
    active_requests -= 1
    
    duration = time.time() - g.start_time
    
    logger.info(
        f"Request completed - ID: {getattr(g, 'request_id', 'unknown')}, "
        f"Status: {response.status_code}, Duration: {duration:.3f}s, "
        f"Active: {active_requests}"
    )
    
    # Add response headers
    response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
    response.headers['X-Response-Time'] = f'{duration:.3f}s'
    
    return response

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "error": "Internal server error",
        "message": "We're experiencing high traffic. Please try again shortly."
    }), 500

@app.errorhandler(503)
def service_unavailable(error):
    logger.error(f"Service unavailable: {str(error)}")
    return jsonify({
        "error": "Service temporarily unavailable",
        "message": "Service is temporarily unavailable. Please try again later."
    }), 503

# Routes
@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

@app.route("/", methods=["GET"])
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
                "total_requests": request_count,
                "active_requests": active_requests,
                "active_users": len(redis_memory.get_active_users())
            }
        }
        
        logger.info(f"Health check success: {health_data}")
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }), 503

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    """Enhanced chat endpoint with better error handling and monitoring"""
    try:
        if request.method == "OPTIONS":
            response = jsonify({"status": "ok"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "*")
            response.headers.add('Access-Control-Allow-Methods', "*")
            return response

        # Simple rate limiting check
        if active_requests > 50:  # Limit concurrent requests
            logger.warning(f"Too many active requests: {active_requests}")
            return jsonify({
                "error": "Server busy",
                "message": "Too many requests. Please wait a moment and try again."
            }), 503

        # Validate API key
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != "nawabkhan":
            logger.warning(f"Unauthorized access from {request.remote_addr}")
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
            f"Chat request - Session: {session_id[:8]}..., "
            f"Message length: {len(user_message)}, Request ID: {g.request_id}"
        )

        # Process with timeout
        start_time = time.time()
        
        try:
            # Call your existing chat function
            result = chat_with_agent(user_message, session_id)
            
            processing_time = time.time() - start_time
            logger.info(
                f"Chat response generated - Session: {session_id[:8]}..., "
                f"Processing time: {processing_time:.3f}s, Request ID: {g.request_id}"
            )

            # Add CORS headers
            response = jsonify({"response": result})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "*")
            response.headers.add("Access-Control-Allow-Methods", "*")
            
            return response

        except Exception as chat_error:
            logger.error(
                f"Chat processing error - Session: {session_id[:8]}..., "
                f"Error: {str(chat_error)}, Request ID: {g.request_id}"
            )
            
            return jsonify({
                "error": "Chat processing failed",
                "message": "I'm experiencing high traffic. Please try again shortly."
            }), 500

    except Exception as e:
        logger.error(
            f"Chat endpoint error: {str(e)}, "
            f"Request ID: {getattr(g, 'request_id', 'unknown')}"
        )
        
        return jsonify({
            "error": "Internal server error",
            "message": "We're experiencing technical difficulties. Please try again."
        }), 500

@app.route("/status")
def status():
    """Service status endpoint"""
    try:
        active_users = len(redis_memory.get_active_users())
        
        return jsonify({
            "service": "Lotus Electronics Chatbot",
            "status": "operational",
            "metrics": {
                "total_requests": request_count,
                "active_requests": active_requests,
                "active_users": active_users
            },
            "timestamp": time.time(),
            "version": "1.0.0"
        })
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return jsonify({
            "service": "Lotus Electronics Chatbot",
            "status": "degraded",
            "error": str(e),
            "timestamp": time.time()
        }), 503

if __name__ == "__main__":
    # Development server (not for production)
    logger.info("Starting Lotus Electronics Chatbot API...")
    app.run(debug=True, host="0.0.0.0", port=8001)
