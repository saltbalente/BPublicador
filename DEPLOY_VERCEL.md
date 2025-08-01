# 🚀 Guía de Despliegue en Vercel

## 📋 Requisitos Previos

1. **Cuenta de GitHub** (gratuita)
2. **Cuenta de Vercel** (gratuita) - [vercel.com](https://vercel.com)
3. **APIs de IA** (al menos una):
   - OpenAI API Key (recomendado)
   - DeepSeek API Key (alternativa)
   - Google Gemini API Key (alternativa)

## 🔧 Paso 1: Preparar el Repositorio en GitHub

### 1.1 Crear Repositorio en GitHub
```bash
# Inicializar git (si no está inicializado)
git init

# Agregar todos los archivos
git add .

# Hacer commit inicial
git commit -m "🚀 Initial commit - Autopublicador Web"

# Conectar con GitHub (reemplaza con tu usuario y repo)
git remote add origin https://github.com/TU_USUARIO/autopublicador-web.git

# Subir a GitHub
git push -u origin main
```

### 1.2 Verificar Archivos Importantes
Asegúrate de que estos archivos estén en tu repositorio:
- ✅ `vercel.json` - Configuración de Vercel
- ✅ `requirements-vercel.txt` - Dependencias optimizadas
- ✅ `backend/main_vercel.py` - Aplicación optimizada para Vercel
- ✅ `backend/vercel_init.py` - Script de inicialización
- ✅ `.env.production` - Template de variables de entorno

## 🌐 Paso 2: Desplegar en Vercel

### 2.1 Conectar GitHub con Vercel
1. Ve a [vercel.com](https://vercel.com) y haz login
2. Haz clic en "New Project"
3. Conecta tu cuenta de GitHub
4. Selecciona el repositorio `autopublicador-web`
5. Haz clic en "Import"

### 2.2 Configurar Variables de Entorno
En el dashboard de Vercel, ve a **Settings > Environment Variables** y agrega:

#### 🔑 Variables Obligatorias
```bash
# Seguridad
SECRET_KEY=tu-clave-super-secreta-aqui-cambiar-por-una-real
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Base de datos
DATABASE_URL=sqlite:///./autopublicador.db

# Al menos una API de IA
OPENAI_API_KEY=sk-tu-api-key-de-openai
# O alternativamente:
# DEEPSEEK_API_KEY=tu-api-key-de-deepseek
# GEMINI_API_KEY=tu-api-key-de-gemini

# Configuración básica
ENVIRONMENT=production
DEBUG=false
AI_PROVIDER=openai
```

#### ⚙️ Variables Opcionales (Configuración Avanzada)
```bash
# Configuración de contenido
MAX_CONTENT_LENGTH=2000
DEFAULT_LANGUAGE=es
DEFAULT_STYLE=profesional
KEYWORD_DENSITY=medium

# Configuración de IA
OPENAI_MODEL=gpt-3.5-turbo
MAX_TOKENS=1500
TEMPERATURE=0.7

# Generación de imágenes
IMAGE_GENERATION_ENABLED=true
IMAGE_PROVIDER=openai
DALLE_MODEL=dall-e-3
IMAGE_SIZE=1024x1024

# Analíticas
ANALYTICS_ENABLED=true
ANALYTICS_RETENTION_DAYS=90

# Rate limiting
RATE_LIMIT_ENABLED=true
REQUESTS_PER_MINUTE=60
```

### 2.3 Desplegar
1. Haz clic en "Deploy"
2. Espera a que termine el despliegue (2-5 minutos)
3. ¡Tu aplicación estará disponible en una URL como `https://tu-proyecto.vercel.app`!

## 🎯 Paso 3: Configuración Post-Despliegue

### 3.1 Verificar Funcionamiento
1. Visita tu URL de Vercel
2. Deberías ver la página de bienvenida del Autopublicador
3. Ve a `/dashboard` para acceder al panel de control
4. Ve a `/docs` para ver la documentación de la API

### 3.2 Credenciales por Defecto
- **Email:** admin@autopublicador.com
- **Password:** admin123

⚠️ **IMPORTANTE:** Cambia estas credenciales inmediatamente después del primer login.

### 3.3 Configurar Dominio Personalizado (Opcional)
1. En Vercel, ve a **Settings > Domains**
2. Agrega tu dominio personalizado
3. Configura los DNS según las instrucciones de Vercel

## 🔄 Paso 4: Actualizaciones Automáticas

### 4.1 Configurar Auto-Deploy
Vercel automáticamente desplegará cada vez que hagas push a la rama `main`:

```bash
# Hacer cambios en tu código
git add .
git commit -m "✨ Nueva funcionalidad"
git push origin main
```

### 4.2 Ramas de Desarrollo
Para probar cambios sin afectar producción:

```bash
# Crear rama de desarrollo
git checkout -b desarrollo

# Hacer cambios y commit
git add .
git commit -m "🧪 Probando nueva funcionalidad"
git push origin desarrollo
```

Vercel creará automáticamente un preview deployment para la rama `desarrollo`.

## 🛠️ Solución de Problemas Comunes

### Error: "Module not found"
- Verifica que todas las dependencias estén en `requirements-vercel.txt`
- Asegúrate de que `PYTHONPATH=backend` esté en las variables de entorno

### Error: "Database not found"
- La base de datos se crea automáticamente en el primer despliegue
- Si persiste, redespliega el proyecto

### Error: "API Key not configured"
- Verifica que hayas configurado al menos una API key de IA
- Asegúrate de que `AI_PROVIDER` coincida con la API configurada

### Funciones de IA no funcionan
- Verifica que tu API key sea válida
- Revisa los logs en el dashboard de Vercel
- Asegúrate de tener créditos en tu cuenta de IA

## 📊 Monitoreo y Logs

### Ver Logs en Tiempo Real
1. Ve al dashboard de Vercel
2. Selecciona tu proyecto
3. Ve a la pestaña "Functions"
4. Haz clic en cualquier función para ver los logs

### Métricas de Uso
- Vercel proporciona métricas automáticas de:
  - Requests por minuto
  - Tiempo de respuesta
  - Errores
  - Uso de ancho de banda

## 🎉 ¡Listo!

Tu Autopublicador Web ahora está funcionando en Vercel con:

✅ **Generación automática de contenido con IA**
✅ **Dashboard web completo**
✅ **API REST documentada**
✅ **Análisis de keywords**
✅ **Generación de imágenes**
✅ **Landing pages automáticas**
✅ **Escalabilidad automática**
✅ **HTTPS incluido**
✅ **CDN global**

## 🔗 Enlaces Útiles

- **Tu aplicación:** `https://tu-proyecto.vercel.app`
- **Dashboard:** `https://tu-proyecto.vercel.app/dashboard`
- **API Docs:** `https://tu-proyecto.vercel.app/docs`
- **Panel de Vercel:** [vercel.com/dashboard](https://vercel.com/dashboard)

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en Vercel
2. Verifica las variables de entorno
3. Consulta la documentación de la API en `/docs`
4. Revisa que las APIs de IA tengan créditos disponibles

¡Disfruta de tu Autopublicador Web en la nube! 🚀