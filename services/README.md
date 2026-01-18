# Backend - Django REST API

Django REST Framework backend for the Medical Translation Chat System.

## Quick Start

```bash
# Install dependencies
poetry install

# Install TTS dependencies (requires Python <3.12)
poetry add "TTS>=0.22.0" --python ">=3.11,<3.12"
poetry add torchcodec

# Activate virtual environment
poetry shell

# Setup environment
cp .env.example .env
# Edit .env - set AI_PROVIDER=ollama

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start server
python manage.py runserver
```

Server runs at `http://localhost:8000`

## Running Celery

For optimal performance, run two separate Celery workers:

**Option A: Two Workers (Recommended for TTS)**
```bash
# Terminal 1 - Main worker (translation, rag, etc.)
poetry run celery -A config worker -l INFO -Q default,translation,rag,assistance,maintenance -c 4

# Terminal 2 - Audio/TTS worker (single process)
poetry run celery -A config worker -l INFO -Q audio -c 1
```

**Option B: Single Worker (Simpler)**
```bash
poetry run celery -A config worker -l INFO -Q default,audio,translation,rag,assistance,maintenance -c 1
```

> **Note:** TTS uses the XTTS v2 model (~1.8GB) which is not thread-safe. The audio queue should run with `-c 1` to prevent model conflicts.

**Optional Services:**
```bash
# Celery beat (scheduled tasks)
poetry run celery -A config beat -l INFO

# Flower (monitoring)
poetry run celery -A config flower --port=5555
```

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
│   │   │   ├── ollama_provider.py
│   │   │   └── prompts/         # Versioned prompts
│   │   │       ├── translation/ # V1, V2 translation prompts
│   │   │       ├── completion.py
│   │   │       └── transcription.py
│   │   └── rag/                 # RAG Service (versioned)
│   │       ├── base.py          # BaseRAGService, RAGVersion
│   │       ├── factory.py       # get_rag_service, get_translation_context
│   │       ├── v1.py            # Character-based chunking
│   │       └── v2.py            # Sentence-based chunking + filtering
│   │
│   ├── tasks/                    # Celery background tasks
│   │   ├── __init__.py          # Message bus registration (Celery signals)
│   │   ├── audio_tasks.py       # Audio transcription
│   │   ├── translation_tasks.py # Translation with caching
│   │   ├── tts_tasks.py         # Text-to-speech generation
│   │   ├── pdf_tasks.py         # PDF processing with OCR
│   │   ├── rag_tasks.py         # Document processing
│   │   ├── dataset_tasks.py     # Hugging Face dataset import
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
│   │   ├── channels_bridge.py   # RabbitMQ → WebSocket bridge
│   │   ├── producers/
│   │   │   ├── base.py          # BaseProducer abstract class
│   │   │   └── rabbitmq.py      # Thread-safe RabbitMQ producer
│   │   └── consumers/
│   │       ├── base.py          # BaseConsumer abstract class
│   │       └── rabbitmq.py      # Topic-based RabbitMQ consumer
│   │
│   ├── consumers/                # WebSocket Consumers
│   │   ├── __init__.py          # Consumer exports
│   │   └── chat.py              # Real-time chat WebSocket consumer
│   │
│   ├── management/commands/
│   │   ├── consume_events.py # Event consumer command
│   │   └── run_websocket_server.py # Daphne WebSocket server
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

### RAG Optimization
The system generates query embeddings **once** and reuses them across all relevant collections (Global Knowledge Base + Patient Context + Linked KBs) during a single request. This prevents CPU overload and ensures fast response times even when querying multiple vector stores.

### Health & Tasks
- `GET /api/health/` - API health check
- `GET /api/config/ai/` - Get AI configuration (models, providers)
- `GET /api/celery/status/` - Celery worker status
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

# Database (Docker - port 5435)
DATABASE_URL=postgresql://dr-lingo_user:dr-lingo_pass@localhost:5435/dr-lingo_db

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# AI Provider (ollama or gemini)
AI_PROVIDER=ollama

# Ollama (Local AI - Recommended)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TRANSLATION_MODEL=zongwei/gemma3-translator:4b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:v1.5

# Gemini (Cloud AI - Optional)
# AI_PROVIDER=gemini
# GEMINI_API_KEY=your-gemini-api-key

# Redis (Docker - port 6380)
REDIS_URL=redis://localhost:6380/1

# Celery
CELERY_BROKER_URL=redis://localhost:6380/0
CELERY_RESULT_BACKEND=redis://localhost:6380/0

# RabbitMQ (Docker - port 5673)
RABBITMQ_URL=amqp://guest:guest@localhost:5673/

# Whisper (Docker or Local)
WHISPER_API_URL=http://localhost:9000
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

# Event consumer with WebSocket server (recommended)
python manage.py consume_events

# Import Hugging Face dataset into RAG knowledge base
python manage.py import_hf_dataset --lang zul
```

## Importing Hugging Face Datasets

The `import_hf_dataset` command allows you to pull South African language datasets from Hugging Face and create RAG knowledge base collections.

### Supported Languages

| Code | Language |
|------|----------|
| zul | isiZulu |
| sot | Sesotho |
| xho | isiXhosa |
| afr | Afrikaans |
| nso | Sepedi |
| tsn | Setswana |
| ssw | siSwati |
| ven | Tshivenda |
| nbl | isiNdebele |
| tso | Xitsonga |

### Usage Examples

**Management Command (Synchronous):**
```bash
# Import isiZulu dataset
python manage.py import_hf_dataset --lang zul

# Import Sesotho dataset with custom collection name
python manage.py import_hf_dataset --lang sot --collection "Sesotho Medical Terms"

# Import specific split (train or dev_test)
python manage.py import_hf_dataset --lang zul --split dev_test

# Use streaming mode for large datasets
python manage.py import_hf_dataset --lang zul --streaming

# Limit number of items (useful for testing)
python manage.py import_hf_dataset --lang zul --limit 100

# Process embeddings asynchronously with Celery
python manage.py import_hf_dataset --lang zul --async

# With Hugging Face authentication (for private datasets)
python manage.py import_hf_dataset --lang zul --hf-token YOUR_HF_TOKEN
```

**Celery Tasks (Asynchronous):**
```python
from api.tasks import import_hf_dataset_async, import_all_hf_languages

# Import single language in background
import_hf_dataset_async.delay(
    lang_code="zul",
    collection_name="isiZulu Medical Data",
    limit=100
)

# Import all 10 South African languages
import_all_hf_languages.delay(split="train", limit=500)
```

### Events Published

| Event | When | Payload |
|-------|------|---------|
| `dataset.import_started` | Import begins | lang_code, lang_name, collection_name, split |
| `dataset.import_completed` | Import finishes | collection_id, created, skipped, errors |
| `dataset.import_failed` | Import fails | lang_code, error |
| `dataset.batch_import_started` | Batch import begins | languages, split, limit |

### Prerequisites

**1. Request Dataset Access (Required - Gated Dataset):**

The `za-african-next-voices` dataset is gated on Hugging Face. You must request access first:

1. Visit: https://huggingface.co/datasets/dsfsi-anv/za-african-next-voices
2. Click "Access repository" button
3. Accept the dataset terms/license
4. Wait for approval (usually instant)

**2. Get Hugging Face Token:**

1. Go to: https://huggingface.co/settings/tokens
2. Create a new token with "Read" permission
3. Add to your `.env` file: `HF_TOKEN=your_token_here`

**3. Install Dependencies:**
```bash
pip install datasets[audio]==3.6.0
pip install huggingface-hub
```

Or with Poetry:
```bash
poetry install
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
- Review Django error messages in terminal
- Check `config/settings.py` for configuration
