# DevShack Academy - Production Environment Makefile
# Run commands from the project root directory

.PHONY: help setup build up down restart logs shell migrate test clean rebuild

# Colors for output
GREEN := \033[0;32m
NC := \033[0m

# Default values for seed command
YEARS ?= 2
COHORTS ?= 4

help:
	@echo "$(GREEN)Dr-Lingo - Docker Commands$(NC)"
	@echo ""
	@echo "Setup:"
	@echo "  make setup           - Initial setup (copy env files)"
	@echo "  make build           - Build all Docker images"
	@echo "  make up              - Start all services"
	@echo "  make down            - Stop all services"
	@echo ""
	@echo "Development:"
	@echo "  make dev             - Start development environment"
	@echo "  make dev-down        - Stop development environment"
	@echo "  make logs            - View all logs"
	@echo "  make logs-api        - View API logs"
	@echo "  make logs-ws         - View WebSocket logs"
	@echo "  make shell           - Open shell in services container"
	@echo ""
	@echo "Database:"
	@echo "  make migrate         - Run migrations"
	@echo "  make makemigrations  - Create migrations"
	@echo "  make superuser       - Create superuser"
	@echo "  make db-reset        - Flush all data and re-migrate"
	@echo "  make db-nuke         - DROP and recreate database"
	@echo "  make dbshell         - Open database shell"
	@echo "  make backup          - Backup database"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean           - Remove containers and volumes"
	@echo "  make rebuild         - Rebuild everything"
	@echo "  make ps              - Show running containers"
	@echo "  make health          - Check service health"
	@echo ""
	@echo "AI Models:"
	@echo "  make ollama-pull     - Pull Ollama AI models (granite3.3:8b, nomic-embed-text)"
	@echo "  make ollama-list     - List installed Ollama models"
	@echo "  make piper-download  - Download Piper TTS voice models (en, es, af)"
	@echo "  make piper-list      - List installed Piper TTS models"
	@echo ""
	@echo "HuggingFace Datasets:"
	@echo "  make hf-import-zulu          - Import isiZulu language dataset"
	@echo "  make hf-import-xhosa         - Import isiXhosa language dataset"
	@echo "  make hf-import-sotho         - Import Sesotho language dataset"
	@echo "  make hf-import-afrikaans     - Import Afrikaans language dataset"
	@echo "  make hf-import-aligned       - Import English-Afrikaans aligned translations"
	@echo "  make hf-import-kb-zulu       - Import isiZulu Knowledge Base Projection"
	@echo "  make hf-import-kb-xhosa      - Import isiXhosa Knowledge Base Projection"
	@echo "  make hf-import-all           - Import all South African language datasets"


# Setup

setup:
	@echo "Setting up environment..."
	@cp -n .env.prod.example .env.prod 2>/dev/null || true
	@cp -n services/.env.example services/.env 2>/dev/null || true
	@cp -n client/.env.example client/.env 2>/dev/null || true
	@echo "$(GREEN)Setup complete! Edit .env.prod with your configuration.$(NC)"


# Production Commands

# Ollama Model Management
ollama-pull:
	@echo "Pulling Ollama models (this may take 10-30 minutes)..."
	docker exec dr-lingo_ollama_prod ollama pull zongwei/gemma3-translator:4b
	docker exec dr-lingo_ollama_prod ollama pull nomic-embed-text:v1.5
	@echo "$(GREEN)Ollama models ready!$(NC)"

ollama-pull-afc:
	@echo "pulling afc model "
	docker exec dr-lingo_ollama_prod ollama pull AeroCorp/afm:expert_13_medical

ollama-list:
	@echo "Installed Ollama models:"
	docker exec dr-lingo_ollama_prod ollama list

# Piper TTS Model Management
piper-download:
	@echo "Downloading Piper TTS models..."
	mkdir -p services/media/piper_models
	@echo "Downloading English voice (required)..."
	wget -q --show-progress -P services/media/piper_models https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
	wget -q --show-progress -P services/media/piper_models https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
	@echo "Downloading Spanish voice..."
	wget -q --show-progress -P services/media/piper_models https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx
	wget -q --show-progress -P services/media/piper_models https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx.json
	@echo "$(GREEN)Piper TTS models downloaded!$(NC)"
	@echo "Note: Afrikaans and other SA languages use English voice as fallback (no native Piper voices available)"

piper-list:
	@echo "Installed Piper TTS models:"
	@ls -lh services/media/piper_models/*.onnx 2>/dev/null || echo "No models found. Run 'make piper-download' first."

build:
	docker compose -f docker-compose.prod.yml build


up:
	docker compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)Services starting... Check with 'make ps'$(NC)"
	docker restart dr-lingo_nginx_prod


down:
	docker compose -f docker-compose.prod.yml down

restart:
	docker compose -f docker-compose.prod.yml restart

logs:
	docker compose -f docker-compose.prod.yml logs -f

logs-api:
	docker compose -f docker-compose.prod.yml logs -f services

logs-ws:
	docker compose -f docker-compose.prod.yml logs -f channels

logs-events:
	docker compose -f docker-compose.prod.yml logs -f event_consumer

logs-nginx:
	docker compose -f docker-compose.prod.yml logs -f nginx


# Development Commands

dev:
	docker compose up -d
	@echo "$(GREEN)Development containers started (postgres, redis, rabbitmq)$(NC)"
	@echo "Run 'docker compose -f docker-compose.prod.yml exec services poetry run python manage.py runserver_ws' to start Django"

dev-down:
	docker compose down

dev-logs:
	docker compose logs -f


# Shell Access

shell:
	docker compose -f docker-compose.prod.yml exec services /bin/bash

shell-db:
	docker compose -f docker-compose.prod.yml exec db psql -U dr-lingo_user -d dr-lingo_db


# Database Commands (Production - Docker)

migrate:
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py migrate

makemigrations:
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py makemigrations

superuser:
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py createsuperuser

db-reset:
	@echo "$(GREEN)Resetting database - this will DELETE ALL DATA!$(NC)"
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py flush --noinput
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py migrate
	@echo "$(GREEN)Database reset complete. Run 'make seed' to add test data.$(NC)"

db-nuke:
	@echo "$(GREEN)Nuking database - dropping and recreating!$(NC)"
	docker compose -f docker-compose.prod.yml exec db psql -U dr-lingo_user -d postgres -c "DROP DATABASE IF EXISTS dr-lingo_db;"
	docker compose -f docker-compose.prod.yml exec db psql -U dr-lingo_user -d postgres -c "CREATE DATABASE dr-lingo_db;"
	@echo "$(GREEN)Database nuked and recreated. Run 'make migrate.$(NC)"

dbshell:
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py dbshell

backup:
	@echo "Creating database backup..."
	@docker compose -f docker-compose.prod.yml exec -T db pg_dump -U dr-lingo_user dr-lingo_db > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup created!$(NC)"


# Maintenance

ps:
	docker compose -f docker-compose.prod.yml ps

stats:
	docker stats --no-stream

clean:
	docker compose -f docker-compose.prod.yml down -v
	docker compose down -v
	@echo "$(GREEN)Cleaned up containers and volumes$(NC)"

rebuild:
	docker compose -f docker-compose.prod.yml down
	docker compose -f docker-compose.prod.yml build --no-cache
	docker compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)Rebuild complete!$(NC)"

collectstatic:
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py collectstatic --noinput

test:
	docker compose -f docker-compose.prod.yml exec services poetry run pytest

health:
	@echo "Checking service health..."
	@curl -sf http://localhost/api/health/ && echo "$(GREEN)API: OK$(NC)" || echo "API: FAILED"
	@curl -sf http://localhost/health && echo "$(GREEN)Nginx: OK$(NC)" || echo "Nginx: FAILED"


# Quick Commands for Local Development

run-api:
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py runserver_ws

run-client:
	cd client && yarn dev

install:
	docker compose -f docker-compose.prod.yml exec services poetry install
	cd client && yarn install

# Local development database commands (using poetry)
dev-migrate:
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py migrate

dev-makemigrations:
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py makemigrations

dev-superuser:
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py createsuperuser

dev-seed:
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py seed_prod_data

dev-seed-clear:
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py seed_prod_data --clear

dev-seed-demo:
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py seed_data

dev-shell:
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py shell


# HuggingFace Dataset Import Commands
# These import South African language datasets for RAG-enhanced translation

# Single language imports (dsfsi-anv/za-african-next-voices)
hf-import-zulu:
	@echo "Importing isiZulu dataset from HuggingFace..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_hf_dataset --lang zul --limit 500 --async
	@echo "$(GREEN)isiZulu dataset imported!$(NC)"

hf-import-xhosa:
	@echo "Importing isiXhosa dataset from HuggingFace..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_hf_dataset --lang xho --limit 500
	@echo "$(GREEN)isiXhosa dataset imported!$(NC)"

hf-import-sotho:
	@echo "Importing Sesotho dataset from HuggingFace..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_hf_dataset --lang sot --limit 500
	@echo "$(GREEN)Sesotho dataset imported!$(NC)"

hf-import-afrikaans:
	@echo "Importing Afrikaans dataset from HuggingFace..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_hf_dataset --lang afr --limit 500
	@echo "$(GREEN)Afrikaans dataset imported!$(NC)"

hf-import-sepedi:
	@echo "Importing Sepedi dataset from HuggingFace..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_hf_dataset --lang nso --limit 500
	@echo "$(GREEN)Sepedi dataset imported!$(NC)"

hf-import-setswana:
	@echo "Importing Setswana dataset from HuggingFace..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_hf_dataset --lang set --limit 500
	@echo "$(GREEN)Setswana dataset imported!$(NC)"

# Aligned translations (EdinburghNLP/south-african-lang-id)
hf-import-aligned:
	@echo "Importing English-Afrikaans aligned translations..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_aligned_translations --languages english afrikaans --limit 500
	@echo "$(GREEN)Aligned translations imported!$(NC)"

hf-import-aligned-xhosa:
	@echo "Importing English-Xhosa aligned translations..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_aligned_translations --languages english xhosa --limit 500
	@echo "$(GREEN)English-Xhosa aligned translations imported!$(NC)"

# Knowledge Base Projection (sello-ralethe/Knowledge_Base_Projection)
hf-import-kb-zulu:
	@echo "Importing isiZulu Knowledge Base Projection..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_knowledge_base_projection --lang zul --limit 500
	@echo "$(GREEN)isiZulu Knowledge Base imported!$(NC)"

hf-import-kb-xhosa:
	@echo "Importing isiXhosa Knowledge Base Projection..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_knowledge_base_projection --lang xho --limit 500
	@echo "$(GREEN)isiXhosa Knowledge Base imported!$(NC)"

hf-import-kb-sotho:
	@echo "Importing Sesotho Knowledge Base Projection..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_knowledge_base_projection --lang sot --limit 500
	@echo "$(GREEN)Sesotho Knowledge Base imported!$(NC)"

hf-import-kb-sepedi:
	@echo "Importing Sepedi Knowledge Base Projection..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_knowledge_base_projection --lang nso --limit 500
	@echo "$(GREEN)Sepedi Knowledge Base imported!$(NC)"

# Import all datasets (comprehensive)
hf-import-all:
	@echo "$(GREEN)Importing all South African language datasets...$(NC)"
	@echo "This may take 30-60 minutes depending on your connection and AI provider."
	@echo ""
	@echo "Step 1/6: Importing aligned translations..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_aligned_translations --languages english afrikaans --limit 500
	@echo ""
	@echo "Step 2/6: Importing isiZulu dataset..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_hf_dataset --lang zul --limit 300
	@echo ""
	@echo "Step 3/6: Importing isiXhosa dataset..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_hf_dataset --lang xho --limit 300
	@echo ""
	@echo "Step 4/6: Importing Afrikaans dataset..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_hf_dataset --lang afr --limit 300
	@echo ""
	@echo "Step 5/6: Importing isiZulu Knowledge Base..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_knowledge_base_projection --lang zul --limit 300
	@echo ""
	@echo "Step 6/6: Importing isiXhosa Knowledge Base..."
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_knowledge_base_projection --lang xho --limit 300
	@echo ""
	@echo "$(GREEN)All datasets imported successfully!$(NC)"

# Docker production versions (run inside container)
hf-import-all-docker:
	@echo "$(GREEN)Importing all datasets in Docker container...$(NC)"
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_aligned_translations --languages english afrikaans --limit 500
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_hf_dataset --lang zul --limit 300
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_hf_dataset --lang xho --limit 300
	docker compose -f docker-compose.prod.yml exec services poetry run python manage.py import_hf_dataset --lang afr --limit 300
	@echo "$(GREEN)All datasets imported!$(NC)"
