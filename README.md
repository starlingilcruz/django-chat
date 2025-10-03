# django-chat

Real-time chat application built with Django, Channels, and Redis Streams.

## Features

- **Real-time messaging** via WebSockets using Django Channels
- **Redis Streams** for fast message storage and retrieval
- **PostgreSQL** for user and conversation management
- **JWT Authentication** with secure password validation
- **Rate limiting** to prevent message spam
- **JSON logging** for production monitoring
- **Health checks** for infrastructure monitoring
- **Comprehensive test suite** with pytest
- **CI/CD** with GitHub Actions

## Tech Stack

- Python 3.9+
- Django 4.2
- Django REST Framework
- Django Channels 4
- Redis 7 (Streams)
- PostgreSQL 16
- Daphne (ASGI server)
- Docker & Docker Compose

## Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd django-chat
   ```

2. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

3. **Update environment variables** in `.env`:
   ```env
   DJANGO_SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   POSTGRES_DB=djangochat
   POSTGRES_USER=djangochat
   POSTGRES_PASSWORD=change-me
   POSTGRES_HOST=db
   POSTGRES_PORT=5432

   REDIS_URL=redis://redis:6379/0
   ```

4. **Start services**
   ```bash
   docker-compose up -d
   ```

5. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

6. **Create superuser** (optional)
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

7. **Access the application**
   - API: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - Health Check: http://localhost:8000/healthz

## Local Development Setup

1. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

4. **Start PostgreSQL and Redis**
   ```bash
   docker-compose up -d db redis
   ```

5. **Run migrations**
   ```bash
   export DJANGO_SETTINGS_MODULE=djangochat.settings.dev
   python manage.py migrate
   ```

6. **Run development server**
   ```bash
   daphne -b 0.0.0.0 -p 8000 djangochat.asgi:application
   ```

## API Endpoints

### Authentication

- **POST** `/api/v1/auth/signup` - Register a new user
  ```json
  {
    "email": "user@example.com",
    "username": "username",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }
  ```

- **POST** `/api/v1/auth/login` - Login user
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePass123!"
  }
  ```

### Conversations

- **GET** `/api/v1/conversations/` - List user's conversations
- **POST** `/api/v1/conversations/` - Create a new conversation
  ```json
  {
    "name": "My Chat Room",
    "participant_ids": [1, 2, 3]
  }
  ```
- **GET** `/api/v1/conversations/{id}/` - Get conversation details
- **POST** `/api/v1/conversations/{id}/add_participant` - Add participant (admin only)
  ```json
  {
    "user_id": 4
  }
  ```

### Messages

- **GET** `/api/v1/conversations/{id}/messages?from={message_id}&limit=50` - Get message history

## WebSocket Usage

Connect to: `ws://localhost:8000/ws/conversations/{conversation_id}/`

### Authentication
Include JWT token in query string or headers (implementation-specific).

### Send Message
```json
{
  "type": "message.send",
  "content": "Hello, world!"
}
```

### Receive Message
```json
{
  "type": "message",
  "message": {
    "id": "1234567890-0",
    "user_id": 1,
    "user_email": "user@example.com",
    "user_name": "John Doe",
    "content": "Hello, world!",
    "conversation_id": "uuid"
  }
}
```

### Error Response
```json
{
  "type": "error",
  "code": "THROTTLED",
  "message": "You are sending messages too quickly"
}
```

## Rate Limiting

Messages are rate-limited to prevent spam:
- **Limit**: 10 messages per 60 seconds per user per conversation
- **Error Code**: `THROTTLED`

Adjust in `messaging/throttle.py`:
```python
message_throttler = MessageThrottler(max_messages=10, window_seconds=60)
```

## Validation Rules

### User Registration
- **First Name**: 1-50 characters
- **Last Name**: 1-50 characters
- **Email**: Valid RFC email, unique
- **Password**:
  - Minimum 10 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 digit
  - At least 1 special character

### Messages
- **Content**: 1-2000 characters

## Health Check

**GET** `/healthz`

Returns:
```json
{
  "status": "healthy",
  "checks": {
    "postgres": true,
    "redis": true
  }
}
```

- **200 OK**: All services healthy
- **503 Service Unavailable**: One or more services unhealthy

## Testing

Run tests locally:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

## Logging

JSON-formatted logs include:
- Request/response details
- User ID and conversation ID
- Status codes and latency
- Error stack traces

Configure log level in settings:
```python
LOGGING = {
    "root": {
        "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    }
}
```

## Security

### Production Settings
- Set `DEBUG=False`
- Use strong `DJANGO_SECRET_KEY`
- Configure `ALLOWED_HOSTS`
- Enable SSL: `SECURE_SSL_REDIRECT=True`
- Set `SESSION_COOKIE_SECURE=True`
- Set `CSRF_COOKIE_SECURE=True`

### WebSocket Security
- AllowedHostsOriginValidator enabled
- Authentication required for all connections
- Participant membership verified

## Project Structure

```
django-chat/
├── djangochat/          # Project settings and config
│   ├── settings/        # Settings by environment (base, dev, prod, test)
│   ├── asgi.py          # ASGI application
│   └── urls.py          # Main URL routing
├── accounts/            # User authentication
├── conversations/       # Conversation management
├── messaging/           # WebSocket consumer, Redis Streams, throttling
├── common/              # Health checks, shared utilities
├── tests/               # Test suite
├── docker/              # Docker configuration
├── .github/             # CI/CD workflows
├── docker-compose.yml   # Docker services
├── Dockerfile           # Application image
└── pyproject.toml       # Python dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License
