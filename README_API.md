# Lotus Electronics Chatbot Web API

A production-ready FastAPI web service for the Lotus Electronics chatbot with Redis memory and product search capabilities.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Redis Server

Make sure Redis is running on your system:

```bash
# On Windows (if Redis is installed)
redis-server

# On Linux/Mac
sudo systemctl start redis
# or
redis-server
```

### 3. Run the API Server

#### Development (Uvicorn)
```bash
# Option 1: Direct command
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Use the startup script
# Windows:
start_uvicorn.bat
# Linux/Mac:
bash start_uvicorn.sh
```

#### Production (Gunicorn)
```bash
# Option 1: Direct command
gunicorn main:app --bind 0.0.0.0:8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Option 2: Use the startup script
# Windows:
start_gunicorn.bat
# Linux/Mac:
bash start_gunicorn.sh
```

### 4. Access the API

- **API Server**: http://localhost:8000
- **Interactive Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 📋 API Endpoints

### Health Check
```
GET /health
```
Returns server health status.

### Chat Endpoint
```
POST /chat
```

**Request Body:**
```json
{
  "message": "Show me Samsung smartphones under 25000",
  "session_id": "user123" // optional
}
```

**Response:**
```json
{
  "response": {
    "answer": "I found some great Samsung smartphones under ₹25000...",
    "products": [
      {
        "product_name": "Samsung Galaxy A14",
        "product_mrp": "₹16,499",
        "product_url": "https://...",
        "product_image": "https://...",
        "features": ["6.6 Display", "50MP Camera"]
      }
    ],
    "end": "Would you like to see more options?"
  },
  "session_id": "user123",
  "status": "success"
}
```

### Session Management
```
GET /sessions/{session_id}/clear    # Clear session history
GET /sessions/stats                 # Get active session stats
```

## 🧪 Testing

### 1. Python Test Script
```bash
python test_api.py
```

Choose between:
1. **Automated test** - Runs predefined test scenarios
2. **Interactive test** - Manual chat testing

### 2. Web Interface
Open `chat_client.html` in your browser for a user-friendly chat interface.

### 3. cURL Examples
```bash
# Health check
curl http://localhost:8000/health

# Send chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me laptops under 50k", "session_id": "test_user"}'

# Clear session
curl http://localhost:8000/sessions/test_user/clear
```

## ⚙️ Configuration

### Environment Variables
Set these in your environment or startup scripts:

```bash
# Required
export GOOGLE_API_KEY="your_google_api_key_here"

# Optional
export TAVILY_API_KEY="your_tavily_api_key_here"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="0"
```

### Server Configuration

#### Uvicorn (Development)
- **Host**: 0.0.0.0 (accepts connections from any IP)
- **Port**: 8000
- **Reload**: Enabled (auto-restarts on code changes)
- **Log Level**: Info

#### Gunicorn (Production)
- **Workers**: 4 (adjust based on CPU cores)
- **Worker Class**: uvicorn.workers.UvicornWorker
- **Max Requests**: 1000 (worker restart threshold)
- **Timeout**: 30 seconds
- **Keep Alive**: 2 seconds

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───▶│   FastAPI Web    │───▶│   Chat Agent    │
│  (Web/Mobile)   │    │      API         │    │  (LangGraph)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                        ┌──────────────────┐    ┌─────────────────┐
                        │   Redis Memory   │    │ Product Search  │
                        │   (Sessions)     │    │   (Pinecone)    │
                        └──────────────────┘    └─────────────────┘
```

## 🔧 Development

### File Structure
```
├── main.py                 # FastAPI application
├── chat.py                 # Core chatbot logic
├── tools/
│   └── product_search_tool.py  # Product search integration
├── requirements.txt        # Dependencies
├── start_uvicorn.bat/sh   # Development startup scripts
├── start_gunicorn.bat/sh  # Production startup scripts
├── test_api.py            # API testing script
├── chat_client.html       # Web testing interface
└── README.md              # This file
```

### Adding New Endpoints
1. Add route handlers to `main.py`
2. Define request/response models with Pydantic
3. Update the test scripts
4. Document in this README

## 🚨 Error Handling

The API includes comprehensive error handling for:
- **Redis connection issues** - Falls back to no-memory mode
- **Chat processing errors** - Returns user-friendly error messages
- **Validation errors** - Returns detailed field validation issues
- **Rate limiting** - Can be configured with middleware

## 📊 Monitoring

### Health Checks
- **Basic**: `GET /health` - Simple status check
- **Detailed**: `GET /` - Service information

### Logging
- **Uvicorn**: Built-in request logging
- **Gunicorn**: Access and error logs to stdout
- **Application**: Redis connection status, chat processing logs

### Performance Monitoring
For production, consider adding:
- **Prometheus metrics** with prometheus_client
- **Request tracking** with middleware
- **Error monitoring** with Sentry

## 🔒 Security Considerations

### For Production:
1. **CORS**: Configure `allow_origins` properly
2. **API Keys**: Use environment variables, not hardcoded values
3. **Rate Limiting**: Add rate limiting middleware
4. **HTTPS**: Use reverse proxy (nginx) with SSL
5. **Authentication**: Add JWT or session-based auth if needed

### Example nginx configuration:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🐛 Troubleshooting

### Common Issues:

1. **Redis Connection Failed**
   - Make sure Redis server is running: `redis-server`
   - Check connection settings in `chat.py`

2. **API Key Errors**
   - Verify GOOGLE_API_KEY is set correctly
   - Check API quotas and limits

3. **Port Already in Use**
   - Change port: `--port 8001`
   - Kill existing process: `lsof -ti:8000 | xargs kill`

4. **Import Errors**
   - Install dependencies: `pip install -r requirements.txt`
   - Check Python version compatibility

### Debug Mode:
```bash
# Enable debug logging
uvicorn main:app --log-level debug

# View detailed errors
python -c "from main import app; print(app.openapi())"
```

## 📈 Scaling

### Horizontal Scaling:
- Run multiple instances behind a load balancer
- Use shared Redis instance for session storage
- Consider database connection pooling

### Vertical Scaling:
- Increase Gunicorn workers: `--workers 8`
- Optimize Redis memory settings
- Monitor CPU and memory usage

---

**🏪 Lotus Electronics Chatbot API v1.0.0**  
*Your trusted partner for all electronics needs*
