# PocketLLM Backend

FastAPI-based backend service for PocketLLM, implementing the architecture from HW3.

## Architecture

The backend follows a service-based architecture with the following components:

- **APIGateway**: FastAPI routers for authentication, chat, and admin endpoints
- **AuthService**: User authentication and JWT token management
- **SessionService**: Chat session and message history management
- **CacheManager**: Redis-based caching for LLM responses
- **ModelInferenceService**: LLM inference orchestration with caching
- **LLMEngine**: llama.cpp wrapper for model inference
- **MonitoringService**: System metrics and telemetry

## Directory Structure

```
backend/
├── main.py                    # FastAPI application entry point
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── auth/
│   └── service.py            # Authentication service
├── routers/                  # API route handlers
│   ├── auth_router.py        # Auth API endpoints
│   ├── chat_router.py        # Chat API endpoints
│   └── admin_router.py       # Admin API endpoints
├── services/                 # Business logic layer
│   ├── session_service.py    # Session management
│   ├── cache_service.py      # Redis cache manager
│   ├── llm_service.py        # LLM inference
│   └── monitoring_service.py # System monitoring
├── schemas/                  # Pydantic data models
│   ├── auth.py               # Auth data models
│   ├── chat.py               # Chat data models
│   └── admin.py              # Admin data models
└── utils/                    # Utilities and dependencies
    └── dependencies.py       # FastAPI dependencies
```

## Setup Instructions

### 1. Create Python Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. (Optional) Download LLM Model

Download a GGUF model file and place it in the `models/` directory:

```bash
mkdir -p ../models
# Download model (example using wget)
# wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf -O ../models/tinyllama-1.1b-chat-q4.gguf
```

**Note**: The backend will run in "mock mode" if no model is available.

### 5. (Optional) Start Redis

For caching functionality, start Redis:

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install Redis locally
sudo apt install redis-server  # Ubuntu/Debian
brew install redis             # macOS
```

**Note**: The backend will work without Redis, but caching will be disabled.

### 6. Run the Backend

```bash
# Development mode (with auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python main.py
```

The server will start on `http://localhost:8000`

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Default Users

The backend creates two default users for testing:

- **Regular User**:
  - Username: `user1`
  - Password: `password123`

- **Admin User**:
  - Username: `admin`
  - Password: `admin123`

## API Endpoints

### Authentication
- `POST /auth/login` - User login, returns JWT token
- `GET /auth/test` - Test auth service

### Chat
- `POST /chat` - Send message and get LLM response
- `GET /chat/history` - Get user's chat sessions
- `GET /chat/history/{session_id}` - Get specific session
- `DELETE /chat/history/{session_id}` - Delete session

### Admin (requires admin role)
- `GET /admin/metrics` - System metrics
- `POST /admin/cache/flush` - Flush cache
- `GET /admin/model/info` - Model configuration
- `GET /admin/cache/stats` - Cache statistics
- `GET /admin/sessions/count` - Session count

### Health
- `GET /` - Root endpoint
- `GET /health` - Health check

## Example Usage

### 1. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "password123"}'
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "...",
  "username": "user1",
  "is_admin": false
}
```

### 2. Send Chat Message

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"prompt": "Hello, how are you?"}'
```

### 3. Get Chat History

```bash
curl -X GET http://localhost:8000/chat/history \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Admin: Get Metrics

```bash
curl -X GET http://localhost:8000/admin/metrics \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## Configuration

Key environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_PATH` | Path to GGUF model file | `./models/tinyllama-1.1b-chat-q4.gguf` |
| `SECRET_KEY` | JWT secret key | `dev-secret-key-change-in-production` |
| `REDIS_HOST` | Redis server host | `localhost` |
| `ENABLE_CACHE` | Enable/disable caching | `True` |
| `MODEL_N_THREADS` | CPU threads for inference | `4` |

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when implemented)
pytest
```

### Code Structure

The backend follows the HW3 architecture:

1. **API Gateway** ([main.py](main.py)): FastAPI application with CORS, routers
2. **Services** ([services/](services/)): Business logic layer
3. **Auth** ([auth/](auth/)): Authentication and authorization
4. **Schemas** ([schemas/](schemas/)): Pydantic data models
5. **Utils** ([utils/](utils/)): Dependencies and utilities

## Troubleshooting

### Redis Connection Error

If you see "Redis connection failed", either:
1. Start Redis: `docker run -d -p 6379:6379 redis:7-alpine`
2. Or disable caching: Set `ENABLE_CACHE=False` in `.env`

### Model Not Found

If you see "Model file not found":
1. Download a GGUF model file
2. Place it in `../models/` directory
3. Update `MODEL_PATH` in `.env`

The backend will run in mock mode without a model.

### Import Errors

Make sure you're in the virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Next Steps

1. Implement Next.js API Routes (BFF layer) in `/frontend/app/api/`
2. Connect frontend to backend via BFF
3. Add WebSocket support for streaming responses
4. Add database for persistent storage (replace in-memory stores)
5. Add proper logging and monitoring
6. Add unit and integration tests
