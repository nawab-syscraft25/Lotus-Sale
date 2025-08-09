from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import uuid
from chat import chat_with_agent

# Create FastAPI app
app = FastAPI(
    title="Lotus Electronics Chatbot API",
    description="Official Lotus Electronics chatbot API for customer support and product search",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: dict
    session_id: str
    status: str = "success"

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="Lotus Electronics Chatbot API",
        version="1.0.0"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return HealthResponse(
        status="healthy",
        service="Lotus Electronics Chatbot API", 
        version="1.0.0"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint for Lotus Electronics chatbot
    
    Args:
        request: ChatRequest containing message and optional session_id
        
    Returns:
        ChatResponse with bot response and session information
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Validate input
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get response from chatbot
        bot_response = chat_with_agent(request.message.strip(), session_id)
        
        # Parse the JSON response
        try:
            response_data = json.loads(bot_response)
        except json.JSONDecodeError:
            # Fallback if response isn't valid JSON
            response_data = {
                "answer": bot_response,
                "end": "How else can I help you with Lotus Electronics products?"
            }
        
        return ChatResponse(
            response=response_data,
            session_id=session_id,
            status="success"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        error_response = {
            "answer": f"I'm sorry, there was a technical issue: {str(e)}. Please try again in a moment.",
            "end": "Is there anything else I can help you with from our electronics collection?"
        }
        
        return ChatResponse(
            response=error_response,
            session_id=request.session_id or "error_session",
            status="error"
        )

@app.get("/sessions/{session_id}/clear")
async def clear_session(session_id: str):
    """Clear conversation history for a specific session"""
    try:
        from chat import redis_memory
        if hasattr(redis_memory, 'clear_user_messages'):
            redis_memory.clear_user_messages(session_id)
            return {"status": "success", "message": f"Session {session_id} cleared"}
        else:
            return {"status": "info", "message": "No persistent memory configured"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")

@app.get("/sessions/stats")
async def get_active_sessions():
    """Get statistics about active sessions"""
    try:
        from chat import redis_memory
        if hasattr(redis_memory, 'get_active_users'):
            active_users = redis_memory.get_active_users()
            return {
                "status": "success",
                "active_sessions": len(active_users),
                "sessions": active_users[:10]  # Return first 10 for privacy
            }
        else:
            return {"status": "info", "message": "No persistent memory configured"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
