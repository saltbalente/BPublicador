# 🚀 Despliegue Rápido - Autopublicador Web

## ⚡ Pasos Rápidos (5 minutos)

### 1. 📤 Subir a GitHub
```bash
# Si no tienes repositorio remoto configurado:
git remote add origin https://github.com/TU_USUARIO/autopublicador-web.git

# Subir código
git push -u origin main
```

### 2. 🌐 Desplegar en Vercel

1. **Ve a [vercel.com](https://vercel.com)** y haz login
2. **Clic en "New Project"**
3. **Importa tu repositorio de GitHub**
4. **Configura estas variables de entorno OBLIGATORIAS:**

```env
SECRET_KEY=tu_clave_secreta_muy_segura_aqui
OPENAI_API_KEY=sk-tu_api_key_de_openai
AI_PROVIDER=openai
ENVIRONMENT=production
DEBUG=false
```

5. **Clic en "Deploy"** ✨

### 3. ✅ Verificar Funcionamiento

- Accede a tu URL de Vercel
- Ve a `/dashboard`
- Login: `admin@autopublicador.com` / `admin123`
- **¡Cambia la contraseña inmediatamente!**

## 🔑 Variables de Entorno Esenciales

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `SECRET_KEY` | `tu_clave_secreta` | **OBLIGATORIO** - Clave para JWT |
| `OPENAI_API_KEY` | `sk-...` | **OBLIGATORIO** - API de OpenAI |
| `AI_PROVIDER` | `openai` | Proveedor de IA a usar |
| `ENVIRONMENT` | `production` | Entorno de ejecución |
| `DEBUG` | `false` | Modo debug |

## 🎯 APIs de IA Soportadas

### OpenAI (Recomendado)
```env
OPENAI_API_KEY=sk-tu_api_key
AI_PROVIDER=openai
OPENAI_MODEL=gpt-3.5-turbo
```

### DeepSeek (Alternativa económica)
```env
DEEPSEEK_API_KEY=sk-tu_api_key
AI_PROVIDER=deepseek
DEEPSEEK_MODEL=deepseek-chat
```

### Google Gemini
```env
GEMINI_API_KEY=tu_api_key
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-pro
```

## 🔧 Configuración Opcional

```env
# Contenido
MAX_CONTENT_LENGTH=2000
DEFAULT_LANGUAGE=es
DEFAULT_STYLE=profesional

# Imágenes
IMAGE_GENERATION_ENABLED=true
IMAGE_PROVIDER=openai
DALLE_MODEL=dall-e-3
IMAGE_SIZE=1024x1024

# Seguridad
ACCESS_TOKEN_EXPIRE_MINUTES=30
RATE_LIMIT_ENABLED=true
REQUESTS_PER_MINUTE=60
```

## 🚨 Problemas Comunes

### ❌ Error: "No API key configured"
**Solución:** Configura al menos una API key de IA en las variables de entorno de Vercel.

### ❌ Error: "Invalid SECRET_KEY"
**Solución:** Genera una nueva SECRET_KEY segura:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### ❌ Error: "Database not found"
**Solución:** El script de inicialización se ejecuta automáticamente. Si persiste, verifica los logs de Vercel.

### ❌ Error: "Function timeout"
**Solución:** Verifica que `maxDuration` esté configurado en 30 segundos en `vercel.json`.

## 📊 Monitoreo

### Ver logs en tiempo real:
```bash
vercel logs --follow
```

### Health checks disponibles:
- `/health` - Estado general
- `/ping` - Conectividad básica
- `/ready` - Dependencias

## 🎉 ¡Listo!

Tu Autopublicador Web está ahora:
- ✅ Desplegado en Vercel
- ✅ Conectado a GitHub para actualizaciones automáticas
- ✅ Configurado con IA para generación de contenido
- ✅ Listo para autopublicar contenido

### 🔗 URLs importantes:
- **Dashboard:** `https://tu-app.vercel.app/dashboard`
- **API Docs:** `https://tu-app.vercel.app/docs`
- **Health Check:** `https://tu-app.vercel.app/health`

### 👤 Credenciales por defecto:
- **Email:** `admin@autopublicador.com`
- **Password:** `admin123`

⚠️ **¡Cambia estas credenciales inmediatamente después del primer login!**

---

🎯 **¿Necesitas ayuda?** Consulta `DEPLOY_VERCEL.md` para la guía completa.