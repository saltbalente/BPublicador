# 🔮 Autopublicador Web - Plataforma de Generación de Contenido con IA

> **Plataforma completa para la generación automática de contenido SEO sobre brujería, esoterismo y magia usando Inteligencia Artificial**

## 📋 Descripción

Esta es una plataforma web moderna desarrollada con **Python + FastAPI + React** que permite la generación automática de contenido optimizado para SEO usando IA. La plataforma incluye análisis de keywords, detección de canibalización, generación de imágenes con IA, programación automática y analytics detallados.

### 🎯 Características Principales

- ✨ **Generación de Contenido con IA** - DeepSeek y OpenAI
- 🖼️ **Generación de Imágenes** - DALL-E 3 integrado
- 🔍 **Análisis de Keywords** - Detección de canibalización
- ⏰ **Programador Automático** - Publicación programada
- 📊 **Analytics Avanzados** - Métricas y reportes detallados
- 🔒 **Sistema de Autenticación** - JWT con roles de usuario
- 🚀 **API REST Completa** - Documentación automática
- 📱 **Interfaz Web Moderna** - Dashboard intuitivo

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Servicios IA  │
│   (React)       │◄──►│   (FastAPI)     │◄──►│ DeepSeek/OpenAI │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │   Base de       │    │     Redis       │
│   Analytics     │    │   Datos         │    │   (Cache)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python 3.9+
- Node.js 18+
- PostgreSQL (recomendado) o SQLite
- Redis
- API Keys de DeepSeek y OpenAI

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd autopublicador-web
```

### 2. Configurar Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones
```

### 3. Configurar Base de Datos

```bash
# Ejecutar migraciones
alembic upgrade head

# Crear usuario administrador (opcional)
python -c "from app.core.init_db import init_db; init_db()"
```

### 4. Configurar Frontend

```bash
cd ../frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env.local
# Editar .env.local con la URL del backend
```

### 5. Ejecutar la Aplicación

#### Backend
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm run dev
```

## 🔧 Configuración de Variables de Entorno

### Backend (.env)

```env
# API Keys (OBLIGATORIAS)
DEEPSEEK_API_KEY=tu_deepseek_api_key_aqui
OPENAI_API_KEY=tu_openai_api_key_aqui

# Base de Datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/autopublicador
REDIS_URL=redis://localhost:6379/0

# Seguridad
SECRET_KEY=tu-clave-secreta-muy-segura
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
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Autopublicador Web
```

## 📚 Uso de la Plataforma

### 1. Dashboard Principal

El dashboard muestra:
- Estadísticas generales
- Keywords disponibles/usadas
- Contenido generado recientemente
- Métricas de rendimiento
- Estado del programador automático

### 2. Gestión de Keywords

#### Importar Keywords
```bash
# Formato CSV
keyword,priority,category
"tarot amor",5,"tarot"
"hechizos dinero",4,"hechizos"
"rituales luna llena",3,"rituales"
```

#### Análisis de Canibalización
- Detección automática de keywords similares
- Análisis de densidad semántica
- Recomendaciones de optimización

### 3. Generación de Contenido

#### Manual
1. Seleccionar keyword
2. Configurar parámetros (longitud, estilo, etc.)
3. Generar contenido
4. Revisar y editar
5. Publicar o programar

#### Automática
1. Configurar programador
2. Establecer intervalos y límites
3. Activar generación automática
4. Monitorear resultados

### 4. Generación de Imágenes

- Generación automática basada en contenido
- Múltiples estilos disponibles
- Optimización SEO de alt text
- Gestión de imágenes destacadas

## 🔌 API Endpoints

### Autenticación
```
POST /api/v1/auth/login
POST /api/v1/auth/register
POST /api/v1/auth/refresh
```

### Keywords
```
GET    /api/v1/keywords/
POST   /api/v1/keywords/
PUT    /api/v1/keywords/{id}
DELETE /api/v1/keywords/{id}
POST   /api/v1/keywords/bulk-import
```

### Análisis de Keywords
```
POST /api/v1/keyword-analysis/analyze-cannibalization
POST /api/v1/keyword-analysis/analyze-seo-potential
POST /api/v1/keyword-analysis/bulk-analyze
```

### Contenido
```
GET  /api/v1/content/
POST /api/v1/content/generate
PUT  /api/v1/content/{id}
POST /api/v1/content/{id}/publish
```

### Generación de Imágenes
```
POST /api/v1/images/generate
POST /api/v1/images/generate-for-content
POST /api/v1/images/bulk-generate
```

### Programador
```
GET  /api/v1/scheduler/status
POST /api/v1/scheduler/configure
POST /api/v1/scheduler/start
POST /api/v1/scheduler/stop
```

### Analytics
```
GET /api/v1/analytics/dashboard
GET /api/v1/analytics/keywords
GET /api/v1/analytics/content
GET /api/v1/analytics/performance
```

## 📊 Servicios Principales

### 1. ContentGenerator
- Integración con DeepSeek y OpenAI
- Optimización SEO automática
- Múltiples estilos de escritura
- Control de densidad de keywords

### 2. KeywordAnalyzer
- Análisis de similitud semántica
- Detección de canibalización
- Estimación de dificultad SEO
- Recomendaciones automáticas

### 3. ImageGenerator
- Generación con DALL-E 3
- Múltiples estilos y tamaños
- Optimización automática de alt text
- Gestión de almacenamiento

### 4. SchedulerService
- Programación flexible
- Cola de tareas con reintentos
- Límites configurables
- Monitoreo en tiempo real

### 5. AnalyticsService
- Métricas detalladas
- Reportes exportables
- Tendencias y comparaciones
- Alertas automáticas

## 🔒 Seguridad

- **Autenticación JWT** con refresh tokens
- **Rate limiting** configurable
- **Validación de datos** con Pydantic
- **Sanitización** de contenido
- **Logs de auditoría** completos

## 📈 Monitoreo y Logs

### Logs Estructurados
```python
logger.info(
    "content_generated",
    keyword_id=keyword.id,
    user_id=user.id,
    word_count=content.word_count,
    generation_time=elapsed_time
)
```

### Métricas Clave
- Generaciones por día/mes
- Tiempo promedio de generación
- Tasa de éxito/error
- Uso de tokens de API
- Rendimiento por keyword

## 🚀 Despliegue en Producción

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/autopublicador
    depends_on:
      - db
      - redis
  
  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=https://api.tudominio.com
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=autopublicador
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
  
  redis:
    image: redis:7-alpine
```

### Variables de Producción
```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://...
SECRET_KEY=clave-super-segura-de-produccion
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## 📝 Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

- **Documentación**: `/docs` (Swagger UI automático)
- **Issues**: GitHub Issues
- **Email**: soporte@tudominio.com

## 🔮 Roadmap

- [ ] Integración con más proveedores de IA
- [ ] Editor WYSIWYG avanzado
- [ ] Plantillas de contenido personalizables
- [ ] Integración con WordPress/CMS
- [ ] App móvil
- [ ] Análisis de competencia automático
- [ ] SEO scoring en tiempo real
- [ ] Integración con Google Analytics

---

**Desarrollado con ❤️ para la comunidad de creadores de contenido esotérico**