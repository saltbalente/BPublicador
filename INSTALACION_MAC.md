# 🍎 Guía de Instalación para Mac

> **Guía completa para configurar el Autopublicador Web en macOS**

## 📋 Prerrequisitos

Antes de comenzar, asegúrate de tener instalado:

### 1. Homebrew (Gestor de paquetes para Mac)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Python 3.9+
```bash
brew install python@3.11
# Verificar instalación
python3 --version
```

### 3. Node.js 18+
```bash
brew install node@18
# Verificar instalación
node --version
npm --version
```

### 4. Git
```bash
brew install git
# Verificar instalación
git --version
```

### 5. PostgreSQL (Opcional, recomendado para producción)
```bash
brew install postgresql@15
brew services start postgresql@15
```

### 6. Redis (Opcional, para cache)
```bash
brew install redis
brew services start redis
```

## 🚀 Instalación Rápida

### Opción 1: Usando Makefile (Recomendado)

```bash
# 1. Clonar el repositorio
git clone https://github.com/saltbalente/BPublicador.git
cd BPublicador

# 2. Instalación completa automática
make setup

# 3. Iniciar en modo desarrollo
make dev
```

### Opción 2: Instalación Manual

```bash
# 1. Clonar el repositorio
git clone https://github.com/saltbalente/BPublicador.git
cd BPublicador

# 2. Configurar backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones (ver sección de configuración)

# 4. Configurar base de datos
alembic upgrade head
python -c "from app.core.init_db import init_db; import asyncio; asyncio.run(init_db())"

# 5. Configurar frontend
cd ../frontend
npm install

# 6. Crear archivo de configuración del frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8001" > .env.local
echo "NEXT_PUBLIC_APP_NAME=Autopublicador Web" >> .env.local
```

## ⚙️ Configuración de Variables de Entorno

### Backend (.env)

Edita el archivo `backend/.env` con tus configuraciones:

```env
# API Keys (OBLIGATORIAS para funcionalidad completa)
DEEPSEEK_API_KEY=tu_deepseek_api_key_aqui
OPENAI_API_KEY=tu_openai_api_key_aqui
GEMINI_API_KEY=tu_gemini_api_key_aqui

# Base de Datos (SQLite por defecto, PostgreSQL recomendado)
DATABASE_URL=sqlite:///./autopublicador.db
# Para PostgreSQL:
# DATABASE_URL=postgresql://usuario:password@localhost:5432/autopublicador

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0

# Seguridad
SECRET_KEY=tu-clave-secreta-muy-segura-cambia-esto
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configuración de Contenido
DEFAULT_CONTENT_PROVIDER=deepseek
CONTENT_LANGUAGE=es
WRITING_STYLE=profesional

# Generación de Imágenes
ENABLE_IMAGE_GENERATION=true
DALLE_MODEL=dall-e-3
MAX_IMAGES_PER_CONTENT=5

# Programador
ENABLE_SCHEDULER=true
MAX_DAILY_POSTS=10

# Configuración de desarrollo
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=info
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_APP_NAME=Autopublicador Web
```

## 🏃‍♂️ Ejecutar la Aplicación

### Opción 1: Usando Makefile

```bash
# Iniciar todo (abre terminales separadas)
make dev

# O iniciar servicios por separado
make dev-backend    # Backend en http://localhost:8001
make dev-frontend   # Frontend en http://localhost:3000
```

### Opción 2: Manual

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## 🐳 Usando Docker (Alternativa)

```bash
# Servicios de desarrollo (PostgreSQL + Redis)
make docker-dev

# Aplicación completa en Docker
make docker-prod
```

## 🔧 Verificación de la Instalación

### 1. Verificar Backend
```bash
curl http://localhost:8001/ping
# Debería responder: {"status":"ok"}
```

### 2. Verificar Frontend
Abrir en el navegador: http://localhost:3000

### 3. Verificar API
Abrir en el navegador: http://localhost:8001/docs
(Documentación automática de la API)

## 🧪 Ejecutar Tests

```bash
# Todos los tests
make test

# Solo backend
make test-backend

# Solo frontend
make test-frontend

# Tests con coverage
make test-coverage
```

## 🔍 Solución de Problemas Comunes

### Error: "Command not found: python3"
```bash
# Instalar Python con Homebrew
brew install python@3.11
# Agregar al PATH si es necesario
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Error: "Permission denied" al instalar dependencias
```bash
# Usar pip con --user o asegurar que el venv esté activado
source backend/venv/bin/activate
pip install -r requirements.txt
```

### Error: "Port already in use"
```bash
# Encontrar y terminar proceso que usa el puerto
lsof -ti:8001 | xargs kill -9
# O cambiar el puerto en la configuración
```

### Error de base de datos
```bash
# Resetear base de datos
cd backend
source venv/bin/activate
rm -f autopublicador.db  # Solo si usas SQLite
alembic upgrade head
python -c "from app.core.init_db import init_db; import asyncio; asyncio.run(init_db())"
```

### Error: "Module not found"
```bash
# Reinstalar dependencias
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 📱 Acceso a la Aplicación

Una vez que todo esté funcionando:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **Documentación API**: http://localhost:8001/docs
- **Admin Panel**: http://localhost:8001/admin (si está configurado)

## 🔑 Obtener API Keys

### DeepSeek API
1. Visita: https://platform.deepseek.com/
2. Crea una cuenta
3. Genera una API key
4. Agrega créditos a tu cuenta

### OpenAI API
1. Visita: https://platform.openai.com/
2. Crea una cuenta
3. Ve a API Keys
4. Genera una nueva key
5. Agrega método de pago

### Gemini API (Google)
1. Visita: https://makersuite.google.com/
2. Crea una cuenta de Google Cloud
3. Habilita la API de Gemini
4. Genera una API key

## 🚀 Siguientes Pasos

1. **Configurar API Keys**: Sin estas, la generación de contenido no funcionará
2. **Importar Keywords**: Usa el panel de admin para cargar tus keywords
3. **Configurar Categorías**: Organiza tu contenido
4. **Probar Generación**: Genera tu primer contenido
5. **Configurar Programador**: Para automatización

## 📚 Comandos Útiles

```bash
# Ver todos los comandos disponibles
make help

# Limpiar instalación
make clean

# Formatear código
make format

# Linting
make lint

# Backup de base de datos
make backup

# Ver logs
make logs
```

## 🆘 Soporte

Si tienes problemas:

1. Revisa los logs: `make logs`
2. Verifica que todos los servicios estén corriendo
3. Consulta la documentación en `/docs`
4. Abre un issue en GitHub

---

**¡Listo! Tu Autopublicador Web debería estar funcionando en tu Mac** 🎉