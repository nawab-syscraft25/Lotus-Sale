# app.py (production-ready, without /search endpoints)

import os
import logging
import json
from flask import Flask, request, jsonify, render_template, send_from_directory

# Import your modules
from chat import chat_with_agent, redis_memory
from tools.product_search_tool import ProductSearchTool

# Create Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,  # change to WARNING in production if too verbose
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize tools
search_tool = ProductSearchTool()


# ---------- Routes ---------- #

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)


@app.route("/", methods=["GET"])
def index():
    return render_template("chat.html")


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    try:
        redis_memory.redis_client.ping()
        pinecone_status = "connected" if search_tool.is_available else "disconnected"
        return jsonify({
            "status": "healthy",
            "service": "Lotus Electronics Chatbot",
            "redis": "connected",
            "search_methods": {"pinecone_vector": pinecone_status},
            "active_users": len(redis_memory.get_active_users())
        })
    except Exception as e:
        logger.exception("Health check failed")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    payload = request.get_json(force=True)
    message = payload.get("message")
    session_id = payload.get("session_id", "default_session")

    if not message:
        return jsonify({"error": "Missing 'message' in request"}), 400

    try:
        ai_reply = chat_with_agent(message, session_id)
        data = json.loads(ai_reply)
        return jsonify({"status": "success", "data": data})
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return jsonify({"error": "Invalid JSON response from agent"}), 500
    except Exception as e:
        logger.exception("Error in chat_with_agent")
        return jsonify({"error": str(e)}), 500


# ---------- Entrypoint ---------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    app.run(host="0.0.0.0", port=port, debug=False)
