# Makefile para Autopublicador Web
# Facilita las tareas comunes de desarrollo y despliegue

.PHONY: help install setup dev prod clean test lint format docker-dev docker-prod logs backup

# Variables
PYTHON := python3
PIP := pip3
NPM := npm
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_DEV := docker-compose -f docker-compose.dev.yml
BACKEND_DIR := backend
FRONTEND_DIR := frontend

# Colores para output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Ayuda por defecto
help: ## Mostrar esta ayuda
	@echo "$(BLUE)🔮 Autopublicador Web - Comandos Disponibles$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Ejemplos de uso:$(NC)"
	@echo "  make install     # Instalar todas las dependencias"
	@echo "  make dev         # Iniciar entorno de desarrollo"
	@echo "  make docker-dev  # Iniciar con Docker (desarrollo)"
	@echo "  make test        # Ejecutar tests"

# Instalación y configuración
install: ## Instalar todas las dependencias
	@echo "$(BLUE)📦 Instalando dependencias...$(NC)"
	@$(MAKE) install-backend
	@$(MAKE) install-frontend
	@echo "$(GREEN)✅ Instalación completada$(NC)"

install-backend: ## Instalar dependencias del backend
	@echo "$(BLUE)📦 Instalando dependencias de Python...$(NC)"
	@cd $(BACKEND_DIR) && $(PYTHON) -m venv venv
	@cd $(BACKEND_DIR) && source venv/bin/activate && $(PIP) install --upgrade pip
	@cd $(BACKEND_DIR) && source venv/bin/activate && $(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Backend instalado$(NC)"

install-frontend: ## Instalar dependencias del frontend
	@echo "$(BLUE)📦 Instalando dependencias de Node.js...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) install
	@echo "$(GREEN)✅ Frontend instalado$(NC)"

setup: ## Configuración inicial completa
	@echo "$(BLUE)⚙️ Configuración inicial...$(NC)"
	@$(MAKE) install
	@$(MAKE) setup-env
	@$(MAKE) setup-db
	@echo "$(GREEN)✅ Configuración completada$(NC)"

setup-env: ## Configurar archivos de entorno
	@echo "$(BLUE)⚙️ Configurando archivos .env...$(NC)"
	@if [ ! -f $(BACKEND_DIR)/.env ]; then \
		cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env; \
		echo "$(YELLOW)⚠️ Configura las API keys en $(BACKEND_DIR)/.env$(NC)"; \
	fi
	@if [ ! -f $(FRONTEND_DIR)/.env.local ]; then \
		echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > $(FRONTEND_DIR)/.env.local; \
		echo "NEXT_PUBLIC_APP_NAME=Autopublicador Web" >> $(FRONTEND_DIR)/.env.local; \
	fi
	@echo "$(GREEN)✅ Archivos .env configurados$(NC)"

setup-db: ## Configurar base de datos
	@echo "$(BLUE)🗄️ Configurando base de datos...$(NC)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && alembic upgrade head
	@cd $(BACKEND_DIR) && source venv/bin/activate && $(PYTHON) -c "from app.core.init_db import init_db; import asyncio; asyncio.run(init_db())"
	@echo "$(GREEN)✅ Base de datos configurada$(NC)"

verify: ## Verificar instalación completa
	@echo "$(BLUE)🔍 Verificando instalación...$(NC)"
	@$(PYTHON) scripts/verify_installation.py

verify-quick: ## Verificación rápida (solo estructura)
	@echo "$(BLUE)🔍 Verificación rápida...$(NC)"
	@if [ -d "$(BACKEND_DIR)" ] && [ -d "$(FRONTEND_DIR)" ]; then \
		echo "$(GREEN)✅ Estructura básica OK$(NC)"; \
	else \
		echo "$(RED)❌ Estructura del proyecto incompleta$(NC)"; \
	fi

# Desarrollo
dev: ## Iniciar entorno de desarrollo (backend + frontend)
	@echo "$(BLUE)🚀 Iniciando entorno de desarrollo...$(NC)"
	@echo "$(YELLOW)Abriendo terminales separadas...$(NC)"
	@osascript -e 'tell app "Terminal" to do script "cd $(PWD) && make dev-backend"'
	@sleep 2
	@osascript -e 'tell app "Terminal" to do script "cd $(PWD) && make dev-frontend"'

dev-backend: ## Iniciar solo el backend
	@echo "$(BLUE)🚀 Iniciando backend en http://localhost:8000$(NC)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Iniciar solo el frontend
	@echo "$(BLUE)🚀 Iniciando frontend en http://localhost:3000$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run dev

# Docker
docker-dev: ## Iniciar con Docker (desarrollo)
	@echo "$(BLUE)🐳 Iniciando servicios de desarrollo con Docker...$(NC)"
	@$(DOCKER_COMPOSE_DEV) up -d
	@echo "$(GREEN)✅ Servicios iniciados:$(NC)"
	@echo "  📊 PostgreSQL: localhost:5433"
	@echo "  🔴 Redis: localhost:6380"
	@echo "  🗄️ Adminer: http://localhost:8080"
	@echo "  📊 Redis Commander: http://localhost:8081"

docker-prod: ## Iniciar con Docker (producción)
	@echo "$(BLUE)🐳 Iniciando en modo producción...$(NC)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Aplicación iniciada en http://localhost$(NC)"

docker-build: ## Construir imágenes Docker
	@echo "$(BLUE)🔨 Construyendo imágenes Docker...$(NC)"
	@$(DOCKER_COMPOSE) build

docker-stop: ## Detener servicios Docker
	@echo "$(YELLOW)🛑 Deteniendo servicios Docker...$(NC)"
	@$(DOCKER_COMPOSE) down
	@$(DOCKER_COMPOSE_DEV) down

docker-clean: ## Limpiar contenedores y volúmenes Docker
	@echo "$(RED)🧹 Limpiando Docker...$(NC)"
	@$(DOCKER_COMPOSE) down -v --remove-orphans
	@$(DOCKER_COMPOSE_DEV) down -v --remove-orphans
	@docker system prune -f

# Testing
test: ## Ejecutar todos los tests
	@echo "$(BLUE)🧪 Ejecutando tests...$(NC)"
	@$(MAKE) test-backend
	@$(MAKE) test-frontend

test-backend: ## Ejecutar tests del backend
	@echo "$(BLUE)🧪 Tests de Python...$(NC)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && pytest tests/ -v

test-frontend: ## Ejecutar tests del frontend
	@echo "$(BLUE)🧪 Tests de React...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) test

test-coverage: ## Ejecutar tests con coverage
	@echo "$(BLUE)📊 Tests con coverage...$(NC)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && pytest tests/ --cov=app --cov-report=html
	@echo "$(GREEN)📊 Reporte en $(BACKEND_DIR)/htmlcov/index.html$(NC)"

# Linting y formateo
lint: ## Ejecutar linting
	@echo "$(BLUE)🔍 Ejecutando linting...$(NC)"
	@$(MAKE) lint-backend
	@$(MAKE) lint-frontend

lint-backend: ## Linting del backend
	@echo "$(BLUE)🔍 Linting Python...$(NC)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && flake8 app/
	@cd $(BACKEND_DIR) && source venv/bin/activate && mypy app/

lint-frontend: ## Linting del frontend
	@echo "$(BLUE)🔍 Linting React...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run lint

format: ## Formatear código
	@echo "$(BLUE)✨ Formateando código...$(NC)"
	@$(MAKE) format-backend
	@$(MAKE) format-frontend

format-backend: ## Formatear código Python
	@echo "$(BLUE)✨ Formateando Python...$(NC)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && black app/
	@cd $(BACKEND_DIR) && source venv/bin/activate && isort app/

format-frontend: ## Formatear código React
	@echo "$(BLUE)✨ Formateando React...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run format

# Base de datos
db-migrate: ## Crear nueva migración
	@echo "$(BLUE)🗄️ Creando migración...$(NC)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && alembic revision --autogenerate -m "$(msg)"

db-upgrade: ## Aplicar migraciones
	@echo "$(BLUE)🗄️ Aplicando migraciones...$(NC)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && alembic upgrade head

db-downgrade: ## Revertir migración
	@echo "$(YELLOW)🗄️ Revirtiendo migración...$(NC)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && alembic downgrade -1

db-reset: ## Resetear base de datos
	@echo "$(RED)🗄️ Reseteando base de datos...$(NC)"
	@cd $(BACKEND_DIR) && source venv/bin/activate && alembic downgrade base
	@cd $(BACKEND_DIR) && source venv/bin/activate && alembic upgrade head
	@$(MAKE) setup-db

# Logs
logs: ## Ver logs de Docker
	@$(DOCKER_COMPOSE) logs -f

logs-backend: ## Ver logs del backend
	@$(DOCKER_COMPOSE) logs -f backend

logs-frontend: ## Ver logs del frontend
	@$(DOCKER_COMPOSE) logs -f frontend

# Backup
backup: ## Crear backup de la base de datos
	@echo "$(BLUE)💾 Creando backup...$(NC)"
	@mkdir -p backups
	@docker exec autopublicador_db pg_dump -U autopublicador_user autopublicador > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup creado en backups/$(NC)"

restore: ## Restaurar backup (usar: make restore file=backup.sql)
	@echo "$(BLUE)📥 Restaurando backup...$(NC)"
	@docker exec -i autopublicador_db psql -U autopublicador_user -d autopublicador < $(file)
	@echo "$(GREEN)✅ Backup restaurado$(NC)"

# Limpieza
clean: ## Limpiar archivos temporales
	@echo "$(BLUE)🧹 Limpiando archivos temporales...$(NC)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name ".pytest_cache" -delete
	@find . -type f -name ".coverage" -delete
	@rm -rf $(BACKEND_DIR)/htmlcov
	@rm -rf $(FRONTEND_DIR)/.next
	@rm -rf $(FRONTEND_DIR)/out
	@echo "$(GREEN)✅ Limpieza completada$(NC)"

# Información del sistema
status: ## Mostrar estado del sistema
	@echo "$(BLUE)📊 Estado del Sistema$(NC)"
	@echo ""
	@echo "$(GREEN)🔧 Herramientas:$(NC)"
	@$(PYTHON) --version 2>/dev/null || echo "$(RED)❌ Python no encontrado$(NC)"
	@node --version 2>/dev/null || echo "$(RED)❌ Node.js no encontrado$(NC)"
	@docker --version 2>/dev/null || echo "$(RED)❌ Docker no encontrado$(NC)"
	@echo ""
	@echo "$(GREEN)📁 Estructura:$(NC)"
	@ls -la | grep -E '^d.*backend|^d.*frontend|^-.*docker-compose'
	@echo ""
	@echo "$(GREEN)🌐 URLs:$(NC)"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

info: ## Mostrar información del proyecto
	@echo "$(BLUE)🔮 Autopublicador Web$(NC)"
	@echo "Plataforma de generación de contenido con IA"
	@echo ""
	@echo "$(GREEN)📋 Características:$(NC)"
	@echo "  ✨ Generación de contenido con IA"
	@echo "  🖼️ Generación de imágenes"
	@echo "  🔍 Análisis de keywords"
	@echo "  ⏰ Programación automática"
	@echo "  📊 Analytics avanzados"
	@echo ""
	@echo "$(GREEN)🛠️ Stack Tecnológico:$(NC)"
	@echo "  Backend:  Python + FastAPI"
	@echo "  Frontend: React + Next.js"
	@echo "  DB:       PostgreSQL + Redis"
	@echo "  AI:       DeepSeek + OpenAI"