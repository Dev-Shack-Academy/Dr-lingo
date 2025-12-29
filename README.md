# Medical Translation Chat System

A real-time medical translation platform enabling seamless communication between healthcare providers and patients across language barriers. Features AI-powered translation, cultural context awareness, and RAG-enhanced medical knowledge.

## Features

- **Real-time Translation**: Instant bidirectional translation between 15+ languages
- **Voice Support**: Speech-to-text and text-to-speech capabilities
- **Knowledge Base**: Global reference data (medical terminology, language guides, cultural context) used for ALL translations
- **Patient Context**: Per-patient details (medical history, cultural background) linked to specific chat rooms
- **RAG Integration**: Context-aware responses combining Knowledge Base and Patient Context
- **Cultural Sensitivity**: AI considers cultural context for appropriate translations
- **Role-Based Access**: Patient, Doctor, and Admin roles with appropriate permissions
- **Admin Panel**: Full management of users, chat rooms, Knowledge Base, and Patient Context

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Backend | Django 5, Django REST Framework |
| Database | PostgreSQL |
| AI Providers | Google Gemini, Ollama (local) |
| Task Queue | Celery + Redis |
| Event Bus | RabbitMQ |
| Auth | JWT (SimpleJWT) |

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
│   │   └── events/        # RabbitMQ event system
│   │       ├── bus_registry.py      # Process-local config
│   │       ├── message_bus_factory.py # Producer/consumer factory
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

### 1. Start Infrastructure Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5435)
- Redis (port 6380)
- RabbitMQ (port 5673, management UI: 15673)

### 2. Setup Backend

```bash
cd services

# Install dependencies
poetry install

# Copy environment file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run migrations
poetry run python manage.py migrate

# Create admin user
poetry run python manage.py createsuperuser
```

### 3. Setup Frontend

```bash
cd client

# Install dependencies
npm install

# Build for production
npm run build
```

### 4. Start All Services

You'll need multiple terminals:

**Terminal 1 - Django Server:**
```bash
cd services
poetry run python manage.py runserver
```

**Terminal 2 - Celery Worker:**
```bash
cd services
poetry run celery -A config worker -l info -Q default,audio,translation,rag,assistance,maintenance
```

**Terminal 3 - Celery Beat (scheduled tasks):**
```bash
cd services
poetry run celery -A config beat -l info
```

**Terminal 4 - Event Consumer (optional):**
```bash
cd services
poetry run python manage.py run_event_consumer
```

**Terminal 5 - Frontend Dev Server:**
```bash
cd client
npm run dev
```

## Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000/api/ |
| Django Admin | http://localhost:8000/admin/ |
| API Docs (Swagger) | http://localhost:8000/api/docs/swagger/ |
| RabbitMQ Management | http://localhost:15673 (guest/guest) |

## Environment Variables

### Backend (`services/.env`)

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://dr-lingo_user:dr-lingo_pass@localhost:5435/dr-lingo_db

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174

# AI Provider (gemini or ollama)
AI_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key

# Ollama (for local AI)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TRANSLATION_MODEL=granite:latest
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest

# Redis
REDIS_URL=redis://localhost:6380/1

# Celery
CELERY_BROKER_URL=redis://localhost:6380/0
CELERY_RESULT_BACKEND=redis://localhost:6380/0

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5673/
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

### Chat
- `GET /api/chat/rooms/` - List chat rooms
- `POST /api/chat/rooms/` - Create chat room
- `GET /api/chat/rooms/{id}/messages/` - Get messages
- `POST /api/chat/rooms/{id}/send/` - Send message

### RAG Collections (Knowledge Base & Patient Context)
- `GET /api/rag/collections/` - List all collections
- `GET /api/rag/collections/?collection_type=knowledge_base` - List Knowledge Bases
- `GET /api/rag/collections/?collection_type=patient_context` - List Patient Contexts
- `POST /api/rag/collections/` - Create collection (specify `collection_type`)
- `POST /api/rag/collections/{id}/items/` - Add document to collection
- `POST /api/rag/collections/{id}/query/` - Query collection

### Admin
- `GET /api/admin/users/` - List users
- `POST /api/admin/users/` - Create user
- `PUT /api/admin/users/{id}/` - Update user
- `DELETE /api/admin/users/{id}/` - Delete user

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

# Celery worker
poetry run celery -A config worker -l info

# Celery beat
poetry run celery -A config beat -l info
```

### Frontend
```bash
cd client

# Dev server
npm run dev

# Build
npm run build

# Lint
npm run lint

# Format
npm run format
```

### Docker
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Reset database
docker-compose down -v
docker-compose up -d
```

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
