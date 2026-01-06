# Medical Translation Chat System

A real-time medical translation platform enabling seamless communication between healthcare providers and patients across language barriers. Features AI-powered translation, cultural context awareness, and RAG-enhanced medical knowledge.

## Features

- **Real-time Translation**: Instant bidirectional translation between 15+ languages
- **Voice Support**: Speech-to-text (Whisper) and text-to-speech (XTTS v2) capabilities
- **Text-to-Speech**: Piper TTS for fast, lightweight audio generation
- **PDF Document Processing**: Upload and extract text from PDFs (including OCR for scanned documents)
- **Task Monitoring**: Real-time Celery task tracking and status monitoring via API
- **AI Configuration API**: Frontend fetches AI models/providers from backend for consistency
- **Knowledge Base**: Global reference data (medical terminology, language guides, cultural context) used for ALL translations
- **Patient Context**: Per-patient details (medical history, cultural background) linked to specific chat rooms
- **RAG Integration**: Context-aware responses combining Knowledge Base and Patient Context
- **Cultural Sensitivity**: AI considers cultural context for appropriate translations
- **Role-Based Access**: Patient, Doctor, and Admin roles with appropriate permissions
- **Admin Panel**: Full management of users, chat rooms, Knowledge Base, and Patient Context
- **Profile Management**: User profile settings and preferences
- **404 Handling**: Proper not-found page for improved navigation

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Backend | Django 5, Django REST Framework |
| Database | PostgreSQL |
| AI Providers | Ollama (local), Google Gemini (cloud) |
| Translation | Ollama with gemma3-translator model |
| Text-to-Speech | Piper TTS |
| Speech-to-Text | Whisper.cpp |
| Task Queue | Celery + Redis |
| Event Bus | RabbitMQ |
| WebSocket | Django Channels + Redis |
| Auth | JWT (SimpleJWT) + Django OTP |

## Project Structure

```
/
├── client/                 # React frontend
│   ├── src/
│   │   ├── api/           # API services
│   │   ├── components/    # React components
│   │   │   ├── admin/     # Admin panel components
│   │   │   └── auth/      # Authentication components
│   │   ├── contexts/      # React contexts
│   │   └── pages/         # Page components
│   └── ...
│
├── services/              # Django backend
│   ├── api/
│   │   ├── models/        # Database models
│   │   ├── views/         # API endpoints
│   │   ├── serializers/   # Data serializers
│   │   ├── services/      # Business logic
│   │   │   └── ai/        # AI provider factory
│   │   ├── tasks/         # Celery tasks (with message bus registration)
│   │   ├── consumers/     # WebSocket consumers
│   │   │   └── chat.py    # Real-time chat WebSocket
│   │   └── events/        # RabbitMQ event system
│   │       ├── bus_registry.py      # Process-local config
│   │       ├── message_bus_factory.py # Producer/consumer factory
│   │       ├── channels_bridge.py   # RabbitMQ → WebSocket bridge
│   │       ├── producers/           # Thread-safe publishers
│   │       └── consumers/           # Topic-based subscribers
│   └── config/            # Django settings
│
└── docker-compose.yml     # Infrastructure services
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Poetry (Python package manager)

## Quick Start

### 1. Start Infrastructure Services (Docker)

```bash
docker compose up -d
```

This starts:
- PostgreSQL (port 5435)
- Redis (port 6380)
- RabbitMQ (port 5673, management UI: 15672)
- Whisper STT (port 9000)

### 2. Start Ollama (Local AI)

```bash
# Start Ollama server
ollama serve

# Pull required models
ollama pull zongwei/gemma3-translator:4b
ollama pull nomic-embed-text:v1.5
```

### 3. Setup Backend

```bash
cd services

# Install dependencies
poetry install

# Copy environment file
cp .env.example .env
# Edit .env - set AI_PROVIDER=ollama

# Run migrations
poetry run python manage.py migrate

# Create admin user
poetry run python manage.py createsuperuser
```

### 4. Setup Frontend

```bash
cd client

# Install dependencies
yarn install
```

### 5. Download Piper TTS Voice Models

Piper TTS requires voice models to be downloaded manually.

Browse all available voices at: https://github.com/rhasspy/piper/blob/master/VOICES.md

```bash
# Create models directory
mkdir -p services/media/piper_models
cd services/media/piper_models

# Download English voice (required)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Download additional voices as needed (optional)
# Spanish
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx.json

# Afrikaans (native SA language support)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/af/af_ZA/google/medium/af_ZA-google-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/af/af_ZA/google/medium/af_ZA-google-medium.onnx.json
```

See `docs/TTS_SYSTEM_GUIDE.md` for the full list of available voices.

### 6. Start All Services

You'll need multiple terminals:

**Terminal 1 - Django Server:**
```bash
cd services
poetry run python manage.py runserver
```

**Terminal 2 - Celery Workers (Local - NOT Docker):**

Option A: Two separate workers (recommended for TTS):
```bash
# Terminal 2a - Main worker (translation, rag, etc.)
cd services
poetry run celery -A config worker -l INFO -Q default,translation,rag,assistance,maintenance -c 4

# Terminal 2b - Audio/TTS worker (single process to avoid model conflicts)
cd services
poetry run celery -A config worker -l INFO -Q audio -c 1
```

Option B: Single worker (simpler but slower):
```bash
cd services
poetry run celery -A config worker -l INFO -Q default,audio,translation,rag,assistance,maintenance -c 1
```

> **Note:** TTS uses the XTTS v2 model (~1.8GB) which is not thread-safe. Running the audio queue with `-c 1` ensures only one TTS task runs at a time, preventing model loading conflicts.

**Terminal 3 - Frontend Dev Server:**
```bash
cd client
yarn dev
```

**Terminal 4 - Celery Beat (Optional - Scheduled Tasks):**
```bash
cd services
poetry run celery -A config beat -l INFO
```

**Terminal 5 - Flower (Optional - Monitoring):**
```bash
cd services
poetry run celery -A config flower --port=5555
```

**Terminal 6 - Event Consumer + WebSocket Server:**
```bash
cd services
poetry run python manage.py run_event_consumer
```

This single command starts:
- Daphne WebSocket server on port 8001
- RabbitMQ event consumer
- Channels bridge (forwards events to WebSocket clients)

## Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000/api/ |
| Django Admin | http://localhost:8000/admin/ |
| API Docs (Swagger) | http://localhost:8000/api/docs/swagger/ |
| RabbitMQ Management | http://localhost:15672 (guest/guest) |
| Flower (Celery) | http://localhost:5555 |
| WebSocket | ws://localhost:8001/ws/chat/{room_id}/ |

## Environment Variables

### Backend (`services/.env`)

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Docker)
DATABASE_URL=postgresql://dr-lingo_user:dr-lingo_pass@localhost:5435/dr-lingo_db

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174

# AI Provider (ollama or gemini)
AI_PROVIDER=ollama

# Ollama (Local AI - Recommended)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TRANSLATION_MODEL=zongwei/gemma3-translator:4b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:v1.5

# Gemini (Cloud AI - Optional)
# AI_PROVIDER=gemini
# GEMINI_API_KEY=your-gemini-api-key

# Redis (Docker)
REDIS_URL=redis://localhost:6380/1

# Celery
CELERY_BROKER_URL=redis://localhost:6380/0
CELERY_RESULT_BACKEND=redis://localhost:6380/0

# RabbitMQ (Docker)
RABBITMQ_URL=amqp://guest:guest@localhost:5673/

# Whisper (Docker or Local)
WHISPER_API_URL=http://localhost:9000
```

## Supported Languages

- English, Spanish, French, German, Chinese
- Arabic, Hindi, Portuguese, Russian, Japanese
- South African: isiZulu, isiXhosa, Afrikaans, Sesotho, Setswana, Sepedi, siSwati, Tshivenda, Xitsonga, isiNdebele

## User Roles

| Role | Capabilities |
|------|-------------|
| Patient | Send messages, view own conversations |
| Doctor | Send messages, view patient context, AI assistance, RAG access |
| Admin | Full access, user management, collection management |

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login (returns JWT)
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `GET /api/auth/me/` - Get current user
- `PUT /api/auth/profile/` - Update user profile

### System
- `GET /api/health/` - Health check
- `GET /api/config/ai/` - Get AI configuration (models, providers)
- `GET /api/celery/status/` - Celery worker status
- `GET /api/tasks/{task_id}/` - Get task status

### Chat
- `GET /api/chat-rooms/` - List chat rooms
- `POST /api/chat-rooms/` - Create chat room
- `GET /api/chat-rooms/{id}/` - Get chat room details
- `GET /api/chat-rooms/{id}/messages/` - Get messages
- `POST /api/chat-rooms/{id}/send/` - Send message

### RAG Collections (Knowledge Base & Patient Context)
- `GET /api/collections/` - List all collections
- `GET /api/collections/?collection_type=knowledge_base` - List Knowledge Bases
- `GET /api/collections/?collection_type=patient_context` - List Patient Contexts
- `POST /api/collections/` - Create collection (specify `collection_type`)
- `POST /api/collections/{id}/add_document/` - Add document (supports PDF upload)
- `POST /api/collections/{id}/query/` - Query collection

### Admin
- `GET /api/users/` - List users
- `POST /api/users/` - Create user
- `PUT /api/users/{id}/` - Update user
- `DELETE /api/users/{id}/` - Delete user

## Development Commands

### Backend
```bash
cd services

# Run server
poetry run python manage.py runserver

# Make migrations
poetry run python manage.py makemigrations

# Apply migrations
poetry run python manage.py migrate

# Create superuser
poetry run python manage.py createsuperuser

# Run tests
poetry run python manage.py test

# Event consumer + WebSocket server (real-time updates)
poetry run python manage.py run_event_consumer

# Celery workers (recommended: two separate workers)
# Main worker - handles translation, rag, assistance
poetry run celery -A config worker -l INFO -Q default,translation,rag,assistance,maintenance -c 4

# Audio/TTS worker - single process for TTS model
poetry run celery -A config worker -l INFO -Q audio -c 1

# Or single worker (simpler but slower)
poetry run celery -A config worker -l INFO -Q default,audio,translation,rag,assistance,maintenance -c 1

# Celery beat (scheduled tasks)
poetry run celery -A config beat -l INFO

# Flower (monitoring)
poetry run celery -A config flower --port=5555
```

### Frontend
```bash
cd client

# Dev server
yarn dev

# Build
yarn build

# Lint
yarn lint
```

### Docker (Infrastructure Only)
```bash
# Start infrastructure services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# Reset database
docker compose down -v
docker compose up -d
```

### Ollama
```bash
# Start Ollama
ollama serve

# Pull models
ollama pull zongwei/gemma3-translator:4b
ollama pull nomic-embed-text:v1.5

# List models
ollama list
```

### Dataset Imports (RAG Knowledge Base)

Import South African language datasets from Hugging Face to enhance translation quality:

```bash
cd services

# Import language dataset (za-african-next-voices)
poetry run python manage.py import_hf_dataset --lang zul          # isiZulu
poetry run python manage.py import_hf_dataset --lang xho          # isiXhosa
poetry run python manage.py import_hf_dataset --lang afr          # Afrikaans
poetry run python manage.py import_hf_dataset --lang sot          # Sesotho
poetry run python manage.py import_hf_dataset --lang nso          # Sepedi
poetry run python manage.py import_hf_dataset --lang tsn          # Setswana

# Import Knowledge Base Projection (cross-lingual knowledge)
poetry run python manage.py import_knowledge_base_projection --lang zul
poetry run python manage.py import_knowledge_base_projection --lang xho
poetry run python manage.py import_knowledge_base_projection --lang eng

# Import aligned bilingual translations
poetry run python manage.py import_aligned_translations --languages english afrikaans
poetry run python manage.py import_aligned_translations --languages english xhosa

# Common options for all import commands
--limit 100          # Limit number of items (for testing)
--async              # Process embeddings asynchronously with Celery
--streaming          # Use streaming mode for large datasets
```

**Supported Languages:**
| Code | Language | Dataset |
|------|----------|---------|
| zul | isiZulu | All datasets |
| xho | isiXhosa | All datasets |
| afr | Afrikaans | HF dataset, Aligned translations |
| sot | Sesotho | HF dataset, KB Projection |
| nso | Sepedi | HF dataset, KB Projection |
| tsn | Setswana | HF dataset |
| ssw | siSwati | HF dataset |
| ven | Tshivenda | HF dataset |
| nbl | isiNdebele | HF dataset |
| tso | Xitsonga | HF dataset |
| eng | English | KB Projection, Aligned translations |

## RAG Architecture

The system uses a two-tier RAG (Retrieval Augmented Generation) architecture:

### Knowledge Base (Global)
- Contains reference data used for ALL translations
- Examples: Medical terminology, language guides, cultural context, regional dialects
- Managed by admins in the "Knowledge Base" section

### Patient Context (Per-Patient)
- Contains individual patient details linked to specific chat rooms
- Examples: Medical history, cultural background, communication preferences, allergies
- Can link to multiple Knowledge Bases for enhanced context
- Managed by admins in the "Patient Context" section

### How They Work Together
```
Knowledge Base (Global) ──┐
                          ├──► Patient Context ──► Chat Room ──► Translations
Knowledge Base (Global) ──┘
```

When translating messages, the system:
1. Queries the Patient Context for patient-specific information
2. Queries all linked Knowledge Bases for reference data
3. Combines both contexts to produce culturally-aware, accurate translations

## License

This project is provided as-is for development and deployment purposes.
