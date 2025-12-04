# Backend - Django REST API

Django REST Framework backend for the hackathon project.

## Quick Start

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Setup environment
cp .env.example .env

# Run migrations
python manage.py migrate

# Seed sample data
python manage.py seed_data

# Start server
python manage.py runserver
```

Server runs at `http://localhost:8000`

## Project Structure

```
backend/
├── api/                      # Main API application
│   ├── models.py            # Database models
│   ├── serializers.py       # API serializers
│   ├── views.py             # API endpoints
│   ├── urls.py              # API routes
│   ├── admin.py             # Django admin config
│   └── management/
│       └── commands/
│           └── seed_data.py # Sample data seeding
│
├── config/                   # Django configuration
│   ├── settings.py          # Main settings
│   ├── urls.py              # Root URL config
│   ├── wsgi.py              # WSGI config
│   └── asgi.py              # ASGI config
│
├── manage.py                # Django management script
├── pyproject.toml           # Poetry dependencies
└── .env                     # Environment variables
```

## API Endpoints

### Items API
- `GET /api/items/` - List all items
- `POST /api/items/` - Create new item
- `GET /api/items/{id}/` - Get specific item
- `PUT /api/items/{id}/` - Update item
- `PATCH /api/items/{id}/` - Partial update
- `DELETE /api/items/{id}/` - Delete item

### Health Check
- `GET /api/health/` - API health check

### Admin Panel
- `/admin/` - Django admin interface

## Environment Variables

Create a `.env` file with:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://hackathon_user:hackathon_pass@localhost:5432/hackathon_db

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Database

### PostgreSQL (Default)
```bash
# Start PostgreSQL with Docker
docker-compose up -d

# Connection string
DATABASE_URL=postgresql://hackathon_user:hackathon_pass@localhost:5432/hackathon_db
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

# Seed sample data
python manage.py seed_data

# Run development server
python manage.py runserver

# Run on different port
python manage.py runserver 8001

# Django shell
python manage.py shell

# Run tests
pytest
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
