# Documentación Completa - Brujería Content Generator
## Migración de WordPress a Python + FastAPI + React

---

## 📋 Resumen Ejecutivo

**Proyecto Actual:** Plugin de WordPress para generación automática de contenido SEO usando IA  
**Objetivo:** Migrar a una aplicación web moderna con Python + FastAPI + React  
**Dominio:** Generación de contenido sobre brujería, esoterismo y magia  
**API Principal:** DeepSeek AI para generación de contenido humanizado  

---

## 🏗️ Arquitectura Actual (WordPress)

### Estructura de Archivos
```
brujeria-content-generator/
├── brujeria-content-generator.php     # Plugin principal
├── includes/                          # Clases PHP
│   ├── class-bcg-config.php          # Configuración
│   ├── class-bcg-keywords.php        # Gestión de keywords
│   ├── class-bcg-api.php             # API DeepSeek
│   ├── class-bcg-admin.php           # Panel admin
│   ├── class-bcg-scheduler.php       # Programador automático
│   ├── class-bcg-queue.php           # Cola de tareas
│   └── class-bcg-title-optimizer.php # Optimización títulos
├── templates/                         # Vistas PHP
│   ├── admin-dashboard.php
│   ├── admin-settings.php
│   ├── keywords-list.php
│   ├── admin-scheduler.php
│   └── content-generation.php
├── assets/                           # Frontend
│   ├── css/
│   ├── js/
│   └── admin.js
├── cron-diagnostics.php             # Herramientas diagnóstico
├── trigger-cron.php                 # Activación manual
└── debug-cron.php                   # Debug sistema
```

---

## 🗄️ Estructura de Base de Datos

### Tablas Principales

#### 1. `bcg_keywords`
```sql
CREATE TABLE bcg_keywords (
    id int(11) NOT NULL AUTO_INCREMENT,
    keyword varchar(255) NOT NULL,
    status enum('available','used','reserved') DEFAULT 'available',
    post_id int(11) DEFAULT NULL,
    priority int(11) DEFAULT 0,
    search_volume int(11) DEFAULT 0,
    competition varchar(20) DEFAULT 'unknown',
    category varchar(100) DEFAULT NULL,
    notes text DEFAULT NULL,
    created_at datetime DEFAULT CURRENT_TIMESTAMP,
    updated_at datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    used_at datetime DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY keyword (keyword)
);
```

#### 2. `bcg_logs`
```sql
CREATE TABLE bcg_logs (
    id int(11) NOT NULL AUTO_INCREMENT,
    type varchar(50) NOT NULL,
    message text NOT NULL,
    data longtext DEFAULT NULL,
    created_at datetime DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY type (type),
    KEY created_at (created_at)
);
```

#### 3. `bcg_queue`
```sql
CREATE TABLE bcg_queue (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    keyword_id BIGINT UNSIGNED NOT NULL,
    scheduled_for DATETIME NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    attempts TINYINT UNSIGNED NOT NULL DEFAULT 0,
    last_error TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
```

#### 4. `bcg_keyword_analytics`
```sql
CREATE TABLE bcg_keyword_analytics (
    id int(11) NOT NULL AUTO_INCREMENT,
    keyword_id int(11) NOT NULL,
    post_id int(11) DEFAULT NULL,
    search_volume int(11) DEFAULT 0,
    competition_score decimal(3,2) DEFAULT 0.00,
    ranking_position int(11) DEFAULT NULL,
    click_through_rate decimal(5,2) DEFAULT 0.00,
    conversion_rate decimal(5,2) DEFAULT 0.00,
    last_updated datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
```

---

## 🔧 Funcionalidades Principales

### 1. **Gestión de Keywords**
- **Importación masiva:** Texto, CSV, JSON
- **Categorización automática:** Por tipo de contenido
- **Sistema de prioridades:** 5 niveles
- **Prevención de canibalización:** Verificación automática
- **Estados:** available, used, reserved
- **Métricas:** Volumen de búsqueda, competencia

### 2. **Generación de Contenido IA**
- **API:** DeepSeek Chat Completions
- **Humanización avanzada:** Técnicas anti-detección IA
- **Optimización SEO:** Densidad keywords, estructura H1-H6
- **Tipos de contenido:** Posts, páginas, artículos especializados
- **Longitud variable:** 500-2000 palabras
- **Estilos:** Informativo, persuasivo, narrativo, etc.

### 3. **Programador Automático**
- **Intervalos:** 5min, 15min, 30min, hourly, daily, twicedaily
- **Límites diarios:** Configurable por usuario
- **Cola de tareas:** Sistema de queue con reintentos
- **Horarios específicos:** Configuración de hora exacta
- **Notificaciones:** Email alerts

### 4. **Optimización SEO**
- **Títulos competitivos:** Análisis de SERPs
- **Meta descripciones:** Generación automática
- **Interlinking automático:** Enlaces internos contextuales
- **Estructura de headings:** H1-H6 optimizada
- **Densidad de keywords:** Control 1.5-2.5%

### 5. **Generación de Imágenes**
- **APIs soportadas:** OpenAI DALL-E, Google Gemini, SDXL
- **Formatos:** WebP, PNG, JPG
- **SEO:** Alt text y títulos automáticos
- **Posicionamiento:** Automático o manual
- **Cache:** Sistema de almacenamiento local

### 6. **Sistema de Monitoreo**
- **Estadísticas de uso:** Generaciones diarias, errores
- **Logs detallados:** Todas las operaciones
- **Diagnósticos:** Herramientas de debug
- **Alertas:** Límites de API, errores críticos

---

## 🔄 Flujos de Trabajo

### Flujo de Generación Manual
1. Usuario selecciona keyword desde dashboard
2. Configura parámetros (tipo, longitud, estilo)
3. Sistema verifica canibalización
4. Genera prompt optimizado
5. Llama a DeepSeek API
6. Procesa y humaniza contenido
7. Crea post en WordPress
8. Genera imágenes (opcional)
9. Aplica interlinking automático
10. Marca keyword como usada

### Flujo de Generación Automática
1. Cron job ejecuta según programación
2. Verifica límites diarios
3. Obtiene keywords de la cola
4. Procesa cada keyword secuencialmente
5. Maneja errores y reintentos
6. Actualiza estadísticas
7. Envía notificaciones
8. Reprograma siguiente ejecución

### Flujo de Gestión de Keywords
1. Importación masiva desde archivo/texto
2. Validación y limpieza de datos
3. Verificación de duplicados
4. Asignación de categorías automática
5. Cálculo de prioridades
6. Inserción en base de datos
7. Actualización de estadísticas

---

## ⚙️ Configuraciones del Sistema

### API Settings
```php
'api_key' => '',                    // DeepSeek API Key
'api_endpoint' => 'https://api.deepseek.com/v1/chat/completions',
'model' => 'deepseek-chat',
'max_tokens' => 2000,
'temperature' => 0.7,
```

### Content Generation
```php
'default_word_count' => 800,
'content_language' => 'es',
'writing_style' => 'profesional',
'keyword_density_target' => 2.5,
'auto_publish' => false,
'auto_interlinking' => true,
```

### Scheduling
```php
'auto_schedule' => false,
'schedule_interval' => 'daily',
'schedule_time' => '09:00',
'max_posts_per_day' => 3,
'email_notifications' => true,
```

### Image Generation
```php
'openai_api_key' => '',
'openai_model' => 'dall-e-3',
'enable_image_generation' => false,
'num_images' => 3,
'image_placement' => 'auto',
```

---

## 🎯 Arquitectura Propuesta (Python + FastAPI + React)

### Stack Tecnológico

#### Backend (Python + FastAPI)
```python
# Dependencias principales
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
pydantic==2.5.0
celery==5.3.4
redis==5.0.1
openai==1.3.7
requests==2.31.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

#### Frontend (React + Next.js)
```json
{
  "dependencies": {
    "next": "14.0.3",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "@tanstack/react-query": "5.8.4",
    "axios": "1.6.2",
    "tailwindcss": "3.3.6",
    "@headlessui/react": "1.7.17",
    "react-hook-form": "7.48.2",
    "recharts": "2.8.0",
    "react-table": "7.8.0"
  }
}
```

#### Base de Datos
```yaml
PostgreSQL: 15+
Redis: 7.0+ (Cache y Celery)
```

### Estructura del Proyecto
```
brujeria-content-generator/
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── api/                     # Endpoints API
│   │   │   ├── v1/
│   │   │   │   ├── keywords.py
│   │   │   │   ├── content.py
│   │   │   │   ├── scheduler.py
│   │   │   │   ├── analytics.py
│   │   │   │   └── auth.py
│   │   ├── core/                    # Configuración
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/                  # Modelos SQLAlchemy
│   │   │   ├── keyword.py
│   │   │   ├── content.py
│   │   │   ├── user.py
│   │   │   └── analytics.py
│   │   ├── schemas/                 # Pydantic Schemas
│   │   │   ├── keyword.py
│   │   │   ├── content.py
│   │   │   └── user.py
│   │   ├── services/                # Lógica de negocio
│   │   │   ├── ai_service.py
│   │   │   ├── keyword_service.py
│   │   │   ├── content_service.py
│   │   │   ├── scheduler_service.py
│   │   │   └── image_service.py
│   │   ├── tasks/                   # Celery Tasks
│   │   │   ├── content_generation.py
│   │   │   ├── image_generation.py
│   │   │   └── analytics.py
│   │   └── utils/                   # Utilidades
│   │       ├── seo_utils.py
│   │       ├── text_utils.py
│   │       └── validators.py
│   ├── alembic/                     # Migraciones DB
│   ├── requirements.txt
│   └── main.py
├── frontend/                        # React Frontend
│   ├── src/
│   │   ├── components/             # Componentes React
│   │   │   ├── dashboard/
│   │   │   ├── keywords/
│   │   │   ├── content/
│   │   │   ├── scheduler/
│   │   │   └── common/
│   │   ├── pages/                  # Páginas Next.js
│   │   │   ├── dashboard.tsx
│   │   │   ├── keywords.tsx
│   │   │   ├── content.tsx
│   │   │   └── settings.tsx
│   │   ├── hooks/                  # Custom Hooks
│   │   ├── services/               # API Calls
│   │   ├── store/                  # Estado global
│   │   ├── types/                  # TypeScript Types
│   │   └── utils/
│   ├── public/
│   ├── package.json
│   └── next.config.js
├── docker-compose.yml              # Desarrollo local
├── Dockerfile.backend
├── Dockerfile.frontend
└── README.md
```

---

## 🗄️ Modelos de Datos (SQLAlchemy)

### Keyword Model
```python
class Keyword(Base):
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), unique=True, index=True, nullable=False)
    status = Column(Enum(KeywordStatus), default=KeywordStatus.AVAILABLE)
    priority = Column(Integer, default=0)
    search_volume = Column(Integer, default=0)
    competition = Column(String(20), default="unknown")
    category = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    used_at = Column(DateTime)
    
    # Relaciones
    content_items = relationship("Content", back_populates="keyword")
    analytics = relationship("KeywordAnalytics", back_populates="keyword")
```

### Content Model
```python
class Content(Base):
    __tablename__ = "content"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    meta_description = Column(String(160))
    content_type = Column(String(50), default="post")
    word_count = Column(Integer)
    status = Column(Enum(ContentStatus), default=ContentStatus.DRAFT)
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    
    # Relaciones
    keyword = relationship("Keyword", back_populates="content_items")
    user = relationship("User", back_populates="content_items")
    images = relationship("ContentImage", back_populates="content")
```

### User Model
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    api_key_deepseek = Column(String(255))
    api_key_openai = Column(String(255))
    daily_limit = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    content_items = relationship("Content", back_populates="user")
    usage_stats = relationship("UsageStats", back_populates="user")
```

---

## 🔌 API Endpoints (FastAPI)

### Keywords Endpoints
```python
# GET /api/v1/keywords/
# POST /api/v1/keywords/
# GET /api/v1/keywords/{keyword_id}
# PUT /api/v1/keywords/{keyword_id}
# DELETE /api/v1/keywords/{keyword_id}
# POST /api/v1/keywords/bulk-import
# GET /api/v1/keywords/stats
# POST /api/v1/keywords/{keyword_id}/mark-used
```

### Content Generation Endpoints
```python
# POST /api/v1/content/generate
# GET /api/v1/content/
# GET /api/v1/content/{content_id}
# PUT /api/v1/content/{content_id}
# DELETE /api/v1/content/{content_id}
# POST /api/v1/content/{content_id}/publish
# GET /api/v1/content/stats
```

### Scheduler Endpoints
```python
# GET /api/v1/scheduler/status
# POST /api/v1/scheduler/configure
# POST /api/v1/scheduler/start
# POST /api/v1/scheduler/stop
# GET /api/v1/scheduler/queue
# POST /api/v1/scheduler/queue/add
# DELETE /api/v1/scheduler/queue/{item_id}
```

### Analytics Endpoints
```python
# GET /api/v1/analytics/dashboard
# GET /api/v1/analytics/keywords
# GET /api/v1/analytics/content
# GET /api/v1/analytics/usage
# GET /api/v1/analytics/performance
```

---

## 🎨 Componentes React

### Dashboard Components
```typescript
// components/dashboard/DashboardStats.tsx
interface DashboardStatsProps {
  totalKeywords: number;
  availableKeywords: number;
  usedKeywords: number;
  dailyGenerated: number;
  monthlyGenerated: number;
}

// components/dashboard/RecentActivity.tsx
// components/dashboard/QuickActions.tsx
// components/dashboard/UsageChart.tsx
```

### Keywords Components
```typescript
// components/keywords/KeywordList.tsx
// components/keywords/KeywordForm.tsx
// components/keywords/KeywordImport.tsx
// components/keywords/KeywordStats.tsx
// components/keywords/KeywordFilters.tsx
```

### Content Components
```typescript
// components/content/ContentGenerator.tsx
// components/content/ContentList.tsx
// components/content/ContentEditor.tsx
// components/content/ContentPreview.tsx
// components/content/ContentSettings.tsx
```

### Scheduler Components
```typescript
// components/scheduler/SchedulerConfig.tsx
// components/scheduler/SchedulerStatus.tsx
// components/scheduler/QueueManager.tsx
// components/scheduler/SchedulerLogs.tsx
```

---

## 🔄 Servicios y Tareas Asíncronas

### AI Service
```python
class AIService:
    def __init__(self):
        self.deepseek_client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1"
        )
    
    async def generate_content(
        self, 
        keyword: str, 
        content_type: str, 
        word_count: int,
        style: str = "professional"
    ) -> ContentResponse:
        # Implementación de generación
        pass
    
    async def generate_title(
        self, 
        keyword: str, 
        competitors: List[str]
    ) -> str:
        # Análisis competitivo de títulos
        pass
    
    async def optimize_content(
        self, 
        content: str, 
        keyword: str
    ) -> OptimizedContent:
        # Optimización SEO
        pass
```

### Celery Tasks
```python
@celery_app.task
def generate_content_task(keyword_id: int, user_id: int):
    """Tarea asíncrona para generar contenido"""
    # Implementación
    pass

@celery_app.task
def generate_images_task(content_id: int):
    """Tarea asíncrona para generar imágenes"""
    # Implementación
    pass

@celery_app.task
def scheduled_content_generation():
    """Tarea programada para generación automática"""
    # Implementación
    pass
```

---

## 🔒 Autenticación y Seguridad

### JWT Authentication
```python
# Configuración JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Middleware de autenticación
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Verificación de tokens
    pass
```

### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/content/generate")
@limiter.limit("10/minute")
async def generate_content(request: Request):
    # Endpoint con límite de rate
    pass
```

---

## 📊 Monitoreo y Analytics

### Métricas Clave
- **Generaciones por día/mes**
- **Tiempo promedio de generación**
- **Tasa de éxito/error**
- **Uso de API (tokens consumidos)**
- **Keywords más utilizadas**
- **Rendimiento por categoría**
- **Calidad del contenido (métricas SEO)**

### Logging
```python
import structlog

logger = structlog.get_logger()

# Logs estructurados
logger.info(
    "content_generated",
    keyword_id=keyword.id,
    user_id=user.id,
    word_count=content.word_count,
    generation_time=elapsed_time
)
```

---

## 🚀 Plan de Migración

### Fase 1: Configuración Base (Semana 1-2)
1. **Setup del entorno de desarrollo**
   - Docker containers (PostgreSQL, Redis, FastAPI, React)
   - Configuración de Celery para tareas asíncronas
   - Setup de Next.js con TypeScript

2. **Modelos de datos**
   - Migración de esquemas de WordPress a SQLAlchemy
   - Configuración de Alembic para migraciones
   - Seeders con datos de prueba

### Fase 2: Backend Core (Semana 3-4)
1. **API Authentication**
   - Sistema de usuarios con JWT
   - Middleware de autenticación
   - Rate limiting

2. **Keywords Management**
   - CRUD completo de keywords
   - Importación masiva
   - Sistema de categorías y prioridades

3. **AI Integration**
   - Servicio de DeepSeek API
   - Generación de contenido
   - Optimización SEO

### Fase 3: Frontend Base (Semana 5-6)
1. **Dashboard principal**
   - Estadísticas en tiempo real
   - Gráficos con Recharts
   - Acciones rápidas

2. **Gestión de Keywords**
   - Lista con filtros y búsqueda
   - Formularios de creación/edición
   - Importación masiva con drag & drop

3. **Generación de Contenido**
   - Formulario de generación
   - Preview en tiempo real
   - Editor de contenido

### Fase 4: Funcionalidades Avanzadas (Semana 7-8)
1. **Scheduler System**
   - Configuración de programación
   - Cola de tareas con Celery
   - Monitoreo de ejecuciones

2. **Image Generation**
   - Integración con OpenAI DALL-E
   - Gestión de imágenes
   - Optimización automática

3. **Analytics Dashboard**
   - Métricas detalladas
   - Reportes exportables
   - Alertas automáticas

### Fase 5: Optimización y Deploy (Semana 9-10)
1. **Performance**
   - Caching con Redis
   - Optimización de queries
   - CDN para assets estáticos

2. **Testing**
   - Tests unitarios (pytest)
   - Tests de integración
   - Tests E2E (Playwright)

3. **Deployment**
   - Configuración de producción
   - CI/CD con GitHub Actions
   - Monitoreo con Sentry

---

## 💰 Estimación de Costos

### Desarrollo (10 semanas)
- **Backend Developer:** $4,000 - $6,000
- **Frontend Developer:** $3,500 - $5,000
- **DevOps/Deploy:** $1,000 - $1,500
- **Testing & QA:** $1,000 - $1,500
- **Total:** $9,500 - $14,000

### Infraestructura Mensual
- **VPS/Cloud:** $50 - $100
- **Database:** $20 - $50
- **Redis:** $15 - $30
- **CDN:** $10 - $25
- **Monitoring:** $20 - $40
- **Total:** $115 - $245/mes

### APIs Externas
- **DeepSeek:** $0.14 per 1M tokens
- **OpenAI DALL-E:** $0.040 per image
- **Otros servicios:** Variable

---

## 🎯 Ventajas de la Migración

### Técnicas
- **Performance:** 5-10x más rápido que WordPress
- **Escalabilidad:** Microservicios, load balancing
- **Mantenibilidad:** Código más limpio y testeable
- **Flexibilidad:** APIs REST para integraciones
- **Seguridad:** Mejor control de acceso y validación

### Funcionales
- **UX moderna:** Interfaz responsive y rápida
- **Real-time:** Updates en tiempo real
- **Mobile-first:** Optimizado para dispositivos móviles
- **Extensibilidad:** Fácil agregar nuevas funcionalidades
- **Analytics:** Métricas más detalladas

### Operacionales
- **Deploy:** Automatizado con CI/CD
- **Monitoring:** Logs estructurados y alertas
- **Backup:** Estrategias automatizadas
- **Updates:** Sin downtime
- **Multi-tenant:** Soporte para múltiples usuarios

---

## 📝 Próximos Pasos

1. **Validar requerimientos** con stakeholders
2. **Setup del entorno** de desarrollo local
3. **Crear repositorio** con estructura base
4. **Implementar MVP** con funcionalidades core
5. **Testing** y refinamiento
6. **Deploy** a producción
7. **Migración de datos** desde WordPress
8. **Training** y documentación para usuarios

---

## 📚 Recursos Adicionales

### Documentación Técnica
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryproject.org/)

### Herramientas de Desarrollo
- **IDE:** VS Code con extensiones Python/TypeScript
- **API Testing:** Postman/Insomnia
- **Database:** pgAdmin para PostgreSQL
- **Monitoring:** Grafana + Prometheus

---

**Documento creado:** $(date)  
**Versión:** 1.0  
**Autor:** Documentación automática del sistema actual  
**Propósito:** Facilitar migración a stack moderno Python + FastAPI + React