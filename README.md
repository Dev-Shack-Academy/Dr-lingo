# Full Stack Application - React + Django

A production-ready full-stack application featuring a React client with Vite and Django REST API services, with full end-to-end integration already configured.

## Overview

This project provides a complete development environment for building modern web applications with:

- Pre-configured React client with Vite for fast development
- Pre-configured Django REST API backend
- PostgreSQL database with Docker support
- Working CRUD example (Items)
- CORS fully configured for client-server communication
- Automated code quality checks with pre-commit hooks
- Swagger/OpenAPI documentation for the API

## Project Structure

```
/
├── client/                      # React frontend application
│   ├── src/
│   │   ├── api/                 # API client and services
│   │   │   ├── ApiClient.ts
│   │   │   ├── HttpClient.ts
│   │   │   ├── routes.ts
│   │   │   └── services/
│   │   ├── components/          # React components
│   │   ├── types/               # TypeScript type definitions
│   │   ├── App.tsx              # Main application component
│   │   └── main.tsx             # Application entry point
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.js
│   ├── eslint.config.js
│   ├── tailwind.config.js
│   └── .prettierrc
│
├── services/                    # Django backend application
│   ├── api/                     # Main API application
│   │   ├── models.py            # Database models
│   │   ├── serializers.py       # Data serializers
│   │   ├── views.py             # API endpoints
│   │   ├── urls.py              # API routes
│   │   └── management/
│   │       └── commands/        # Custom management commands
│   ├── config/                  # Django configuration
│   │   ├── settings.py          # Django settings
│   │   ├── urls.py              # Root URL configuration
│   │   └── wsgi.py
│   ├── manage.py                # Django management script
│   ├── pyproject.toml           # Poetry dependencies
│   └── poetry.lock
│
├── docker-compose.yml           # PostgreSQL database setup
├── .pre-commit-config.yaml      # Pre-commit hooks configuration
└── README.md                    # This file
```

## Prerequisites

Before starting development, ensure the following tools are installed:

| Tool | Version | Installation |
|------|---------|--------------|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| Poetry | Latest | `curl -sSL https://install.python-poetry.org \| python3 -` |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| Docker | Latest | [docker.com](https://www.docker.com/get-started) |
| Docker Compose | Latest | Included with Docker Desktop |
| Git | Latest | [git-scm.com](https://git-scm.com/) |

Verify installations:
```bash
python --version
poetry --version
node --version
docker --version
git --version
```

## Quick Setup

Follow these steps to get the full stack running locally:

### 1. Start the Database

```bash
docker-compose up -d
```

Verify the PostgreSQL container is running:
```bash
docker-compose ps
```

Database credentials:
- Host: localhost
- Port: 5432
- Database: hackathon_db
- User: hackathon_user
- Password: hackathon_pass

### 2. Setup Backend Services

```bash
cd services

# Install Python dependencies
poetry install

# Activate virtual environment
poetry shell

# Copy environment configuration
cp .env.example .env

# Run database migrations
python manage.py migrate

# Seed database with sample data (optional)
python manage.py seed_data

# Start development server
python manage.py runserver
```

Backend services will be available at: `http://localhost:8000`

Test the API: `http://localhost:8000/api/items/`

Swagger documentation: `http://localhost:8000/api/docs/swagger/`

### 3. Setup Frontend Client

Open a new terminal and run:

```bash
cd client

# Install JavaScript dependencies
npm install

# Start development server
npm run dev
```

Frontend client will be available at: `http://localhost:5173`

### 4. Install Pre-commit Hooks

Pre-commit hooks automatically run code formatting and linting checks before each commit:

```bash
pip install pre-commit

# Install git hooks
pre-commit install

# Run on all files to verify setup
pre-commit run --all-files
```

This ensures:
- ESLint and Prettier checks on frontend code
- Python linting with Ruff
- YAML/JSON validation
- Private key detection

## Configuration

### Environment Variables

**Frontend** (`client/.env`):
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

**Backend** (`services/.env`):
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DATABASE_URL=postgresql://hackathon_user:hackathon_pass@localhost:5432/hackathon_db
```

For SQLite development without Docker:
```env
DATABASE_URL=sqlite:///db.sqlite3
```

## Daily Development Workflow

### Terminal 1 - Backend Services

```bash
cd services
poetry shell
python manage.py runserver
```

Server runs on: `http://localhost:8000`

### Terminal 2 - Frontend Client

```bash
cd client
npm run dev
```

Client runs on: `http://localhost:5173`

### Terminal 3 - Database (if needed)

```bash
# View database logs
docker-compose logs -f postgres

# Stop database
docker-compose down

# Start database
docker-compose up -d
```

## API Documentation

### Swagger/OpenAPI

Access interactive API documentation at: `http://localhost:8000/api/docs/swagger/`

Alternative documentation formats:
- ReDoc: `http://localhost:8000/api/docs/redoc/`
- OpenAPI Schema: `http://localhost:8000/api/docs/schema/`

### Items Endpoints

The application includes a complete CRUD example for items:

```
GET    /api/items/           List all items
POST   /api/items/           Create new item
GET    /api/items/{id}/      Get specific item
PUT    /api/items/{id}/      Update item
DELETE /api/items/{id}/      Delete item
```

Example response:
```json
{
  "id": 1,
  "name": "Sample Item",
  "description": "This is a sample item",
  "created_at": "2025-12-04T09:00:00Z"
}
```

## Extending the Application

### Adding a New Backend Endpoint

1. Define model in `services/api/models.py`:
```python
class CustomModel(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
```

2. Create serializer in `services/api/serializers.py`:
```python
class CustomModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomModel
        fields = '__all__'
```

3. Create viewset in `services/api/views.py`:
```python
class CustomModelViewSet(viewsets.ModelViewSet):
    queryset = CustomModel.objects.all()
    serializer_class = CustomModelSerializer
```

4. Register route in `services/api/urls.py`:
```python
router.register(r'custom', CustomModelViewSet)
```

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Adding a New Frontend Component

1. Add API service in `client/src/api/services/`:
```typescript
export const getCustomData = async () => {
  return apiClient.get('/custom/');
};
```

2. Create component in `client/src/components/`:
```typescript
import { useState, useEffect } from 'react';
import { getCustomData } from '../api/services/customService';

export function CustomComponent() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCustomData()
      .then(response => setData(response.data))
      .catch(error => console.error('Error:', error))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {/* Render your data */}
    </div>
  );
}
```

3. Use component in `client/src/App.tsx`:
```typescript
import { CustomComponent } from './components/CustomComponent';

export function App() {
  return <CustomComponent />;
}
```

## Database Management

### PostgreSQL Container

View database logs:
```bash
docker-compose logs postgres
```

Access PostgreSQL CLI:
```bash
docker exec -it hackathon_postgres psql -U hackathon_user -d hackathon_db
```

Reset database:
```bash
docker-compose down -v
docker-compose up -d
cd services
python manage.py migrate
python manage.py seed_data
```

### Django Admin Interface

Access at: `http://localhost:8000/admin/`

To register models in admin (`services/api/admin.py`):
```python
from django.contrib import admin
from .models import CustomModel

admin.site.register(CustomModel)
```

## Code Quality

### Pre-commit Hooks

Automatically run before each commit. Includes:

**Frontend:**
- ESLint - Identifies and fixes code quality issues
- Prettier - Formats code consistently

**Backend:**
- Ruff - Fast Python linting and formatting

**General:**
- YAML/JSON validation
- Private key detection
- Trailing whitespace removal
- End of file fixer

See [PRE_COMMIT_GUIDE.md](PRE_COMMIT_GUIDE.md) for detailed documentation.

### Manual Code Checks

Frontend:
```bash
cd client
npm run lint      # Check for issues
npm run format    # Format code
```

Backend:
```bash
cd services
poetry shell
ruff check .      # Check code
ruff format .     # Format code
```

## Troubleshooting

### CORS Errors

If you see CORS errors in the browser console:

1. Verify `CORS_ALLOWED_ORIGINS` in `services/.env`
2. Ensure the URL matches your client's address
3. Restart the backend server

### Port Already in Use

Port 8000 (backend):
```bash
python manage.py runserver 8001  # Use different port
```

Port 5173 (frontend):
Vite automatically tries the next available port (5174, 5175, etc.)

### Database Connection Failed

Check if PostgreSQL is running:
```bash
docker-compose ps

# Restart if needed
docker-compose down
docker-compose up -d
```

### Dependencies Issues

Backend:
```bash
cd services
poetry install --no-cache
```

Frontend:
```bash
cd client
rm -rf node_modules package-lock.json
npm install
```

### Module Not Found

Backend:
```bash
cd services
poetry shell
python manage.py migrate
```

Frontend:
```bash
cd client
npm install
```

## Architecture

### Frontend Stack
- React 19 - UI framework
- TypeScript - Type safety
- Vite - Build tool
- Tailwind CSS - Styling
- React Router - Navigation
- Axios - HTTP client

### Backend Stack
- Django 4.2+ - Web framework
- Django REST Framework - API framework
- PostgreSQL - Database
- drf-yasg - Swagger/OpenAPI documentation
- django-cors-headers - CORS support

### Development Tools
- Poetry - Python package management
- ESLint - JavaScript linting
- Prettier - Code formatting
- Ruff - Python linting
- Pre-commit - Git hooks

## Testing

### Backend Tests

```bash
cd services
python manage.py test
```

### Frontend Tests

```bash
cd client
npm test
```

## Deployment

### Frontend Build

```bash
cd client
npm run build
```

Static files are generated in `dist/` directory. Deploy to any static hosting service (Vercel, Netlify, etc.).

### Backend Deployment

1. Set environment variables for production:
```bash
DEBUG=False
SECRET_KEY=<strong-random-key>
ALLOWED_HOSTS=your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com
```

2. Use production WSGI server:
```bash
pip install gunicorn
gunicorn config.wsgi:application
```

3. Set up PostgreSQL database

4. Run migrations:
```bash
python manage.py migrate
```

## Documentation Files

- [LOCAL_SETUP_CHECKLIST.md](LOCAL_SETUP_CHECKLIST.md) - Detailed setup guide for new developers
- [DEVELOPER_SETUP_SUMMARY.md](DEVELOPER_SETUP_SUMMARY.md) - Quick reference guide
- [PRE_COMMIT_GUIDE.md](PRE_COMMIT_GUIDE.md) - Pre-commit hooks documentation
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current project status

## Common Commands Reference

### Backend

```bash
# Start development server
python manage.py runserver

# Create admin user
python manage.py createsuperuser

# Run migrations
python manage.py migrate
python manage.py makemigrations

# Load sample data
python manage.py seed_data

# Database shell
python manage.py dbshell

# Run tests
python manage.py test
```

### Frontend

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Run linting
npm run lint

# Format code
npm run format

# Preview production build
npm run preview
```

### Docker

```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f

# Access database CLI
docker exec -it hackathon_postgres psql -U hackathon_user
```

## Support and Resources

- Django Documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- React Documentation: https://react.dev/
- Vite Documentation: https://vitejs.dev/

## License

This project is provided as-is for development and deployment purposes.
