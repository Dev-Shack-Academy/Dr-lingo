# Backend - Django REST API

Django REST Framework backend for the Medical Translation Chat System.

## Quick Start

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Setup environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start server
python manage.py runserver
```

Server runs at `http://localhost:8000`

## Project Structure

```
services/
├── api/                          # Main API application
│   ├── models/                   # Database models
│   │   ├── user.py              # Custom User with RBAC
│   │   ├── chat.py              # ChatRoom, ChatMessage
│   │   └── rag.py               # Collection, CollectionItem
│   │
│   ├── views/                    # API endpoints
│   │   ├── auth.py              # Authentication
│   │   ├── chat.py              # Chat rooms & messages
│   │   ├── rag.py               # RAG collections
│   │   └── health.py            # Health checks
│   │
│   ├── serializers/              # API serializers
│   ├── permissions.py            # RBAC permission classes
│   │
│   ├── services/                 # Business logic
│   │   ├── ai/                  # AI Provider Factory
│   │   │   ├── base.py          # Abstract base classes
│   │   │   ├── factory.py       # Provider factory
│   │   │   ├── gemini_provider.py
│   │   │   └── ollama_provider.py
│   │   └── rag_service.py       # RAG operations
│   │
│   ├── tasks/                    # Celery background tasks
│   │   ├── __init__.py          # Message bus registration (Celery signals)
│   │   ├── audio_tasks.py       # Audio transcription
│   │   ├── translation_tasks.py # Translation with caching
│   │   ├── rag_tasks.py         # Document processing
│   │   ├── assistance_tasks.py  # AI assistance
│   │   └── cleanup_tasks.py     # Maintenance tasks
│   │
│   ├── events/                   # RabbitMQ Event System
│   │   ├── bus_registry.py      # Process-local config registry
│   │   ├── message_bus_factory.py # Factory for producers/consumers
│   │   ├── access.py            # Singleton access (get_producer/consumer)
│   │   ├── events.py            # Event type constants
│   │   ├── publisher.py         # High-level publish_event()
│   │   ├── subscriber.py        # Event handlers
│   │   ├── producers/
│   │   │   ├── base.py          # BaseProducer abstract class
│   │   │   └── rabbitmq.py      # Thread-safe RabbitMQ producer
│   │   └── consumers/
│   │       ├── base.py          # BaseConsumer abstract class
│   │       └── rabbitmq.py      # Topic-based RabbitMQ consumer
│   │
│   ├── management/commands/
│   │   └── run_event_consumer.py # Event consumer command
│   │
│   └── urls.py                   # API routes
│
├── config/                       # Django configuration
│   ├── settings.py              # Main settings + MESSAGE_BUS_CONFIG
│   ├── celery.py                # Celery configuration
│   ├── urls.py                  # Root URL config
│   └── wsgi.py                  # WSGI config
│
├── manage.py                    # Django management script
├── pyproject.toml               # Poetry dependencies
└── .env                         # Environment variables
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login (returns JWT tokens)
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `GET /api/auth/me/` - Get current user
- `PUT /api/auth/profile/` - Update profile
- `POST /api/auth/change-password/` - Change password

### Chat Rooms
- `GET /api/chat-rooms/` - List chat rooms
- `POST /api/chat-rooms/` - Create chat room
- `GET /api/chat-rooms/{id}/` - Get room details
- `POST /api/chat-rooms/{id}/send_message/` - Send message
- `POST /api/chat-rooms/{id}/add_patient_context/` - Add patient context
- `GET /api/chat-rooms/{id}/get_doctor_assistance/` - Get AI assistance

### RAG Collections
- `GET /api/collections/` - List collections
- `POST /api/collections/` - Create collection
- `POST /api/collections/{id}/add_document/` - Add document
- `POST /api/collections/{id}/query/` - Query collection
- `POST /api/collections/{id}/reindex/` - Reindex collection

### Health & Tasks
- `GET /api/health/` - API health check
- `GET /api/celery/status/` - Celery status
- `GET /api/tasks/{task_id}/` - Get task status

### Admin Panel
- `/admin/` - Django admin interface

## Environment Variables

Create a `.env` file (see `.env.example`):

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (port 5435 for Docker)
DATABASE_URL=postgresql://dr-lingo_user:dr-lingo_pass@localhost:5435/dr-lingo_db

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# AI Provider (gemini or ollama)
AI_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key

# Ollama (for local AI)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TRANSLATION_MODEL=granite:latest
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest

# Redis (port 6380 for Docker)
REDIS_URL=redis://localhost:6380/1

# Celery
CELERY_BROKER_URL=redis://localhost:6380/0
CELERY_RESULT_BACKEND=redis://localhost:6380/0

# RabbitMQ (port 5673 for Docker)
RABBITMQ_URL=amqp://guest:guest@localhost:5673/
```

## Database

### PostgreSQL (Default)
```bash
# Start PostgreSQL with Docker
docker-compose up -d

# Connection string
DATABASE_URL=postgresql://dr-lingo_user:dr-lingo_pass@localhost:5432/dr-lingo_db
```

### Migrations
```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

## Common Commands

```bash
# Create superuser for admin panel
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run on different port
python manage.py runserver 8001

# Django shell
python manage.py shell

# Run tests
pytest

# Celery worker (all queues)
celery -A config worker -l info -Q default,audio,translation,rag,assistance,maintenance

# Celery beat (scheduled tasks)
celery -A config beat -l info

# Event consumer (RabbitMQ)
python manage.py run_event_consumer
```

## Adding New Features

### 1. Create a Model

```python
# api/models.py
from django.db import models

class YourModel(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
```

### 2. Create a Serializer

```python
# api/serializers.py
from rest_framework import serializers
from .models import YourModel

class YourModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = YourModel
        fields = '__all__'
```

### 3. Create a ViewSet

```python
# api/views.py
from rest_framework import viewsets
from .models import YourModel
from .serializers import YourModelSerializer

class YourModelViewSet(viewsets.ModelViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
```

### 4. Register the Route

```python
# api/urls.py
from rest_framework.routers import DefaultRouter
from .views import YourModelViewSet

router = DefaultRouter()
router.register(r'yourmodels', YourModelViewSet)
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## Django Admin

Register models in `api/admin.py`:

```python
from django.contrib import admin
from .models import YourModel

@admin.register(YourModel)
class YourModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
```

Access at `http://localhost:8000/admin/`

## Dependencies

Managed with Poetry in `pyproject.toml`:

### Core
- `django` - Web framework
- `djangorestframework` - REST API toolkit
- `django-cors-headers` - CORS support
- `psycopg2-binary` - PostgreSQL adapter
- `python-decouple` - Environment variables
- `dj-database-url` - Database URL parsing

### Development
- `pytest` - Testing framework
- `pytest-django` - Django testing
- `ipython` - Enhanced Python shell
- `pre-commit` - Git hooks

## Code Quality

### Linting & Formatting
```bash
# Run Ruff linter
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Pre-commit Hooks
```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test
pytest api/tests/test_models.py
```

## Troubleshooting

### Port Already in Use
```bash
# Find process
lsof -i :8000

# Use different port
python manage.py runserver 8001
```

### Database Connection Error
```bash
# Check PostgreSQL is running
docker-compose ps

# Restart database
docker-compose restart postgres
```

### Migration Issues
```bash
# Reset migrations (development only!)
python manage.py migrate api zero
python manage.py migrate
```

### Module Not Found
```bash
# Reinstall dependencies
poetry install

# Activate environment
poetry shell
```

## Production Deployment

### Settings to Change
```python
# config/settings.py
DEBUG = False
SECRET_KEY = 'strong-random-secret-key'
ALLOWED_HOSTS = ['your-domain.com']
```

### Use Production Server
```bash
# Install gunicorn
poetry add gunicorn

# Run with gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Static Files
```bash
# Collect static files
python manage.py collectstatic
```

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Poetry Documentation](https://python-poetry.org/docs/)

## Need Help?

- Check the main [README.md](../README.md)
- See [LOCAL_SETUP_CHECKLIST.md](../LOCAL_SETUP_CHECKLIST.md)
- Review Django error messages in terminal
- Check `config/settings.py` for configuration
