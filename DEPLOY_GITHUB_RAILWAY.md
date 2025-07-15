# 🚀 Deploy desde GitHub en Railway - Guía Paso a Paso

## ✅ Estado Actual
- ✅ Código subido a GitHub: `https://github.com/saltbalente/BPublicador.git`
- ✅ Proyecto verificado al 91.4% para Railway
- ✅ Todos los archivos de configuración listos

---

## 🎯 Pasos para Deploy desde GitHub

### 1. Acceder a Railway
1. Ve a [railway.app](https://railway.app)
2. Haz clic en **"Login"** o **"Start a New Project"**
3. Conecta tu cuenta de GitHub si no lo has hecho

### 2. Crear Nuevo Proyecto desde GitHub
1. En el dashboard de Railway, haz clic en **"New Project"**
2. Selecciona **"Deploy from GitHub repo"**
3. Busca y selecciona tu repositorio: **`saltbalente/BPublicador`**
4. Haz clic en **"Deploy Now"**

### 3. Configurar Variables de Entorno

Una vez que el proyecto esté creado, ve a la pestaña **"Variables"** y agrega:

#### Variables Críticas (OBLIGATORIAS)
```
ENVIRONMENT=production
SECRET_KEY=tu-clave-secreta-muy-segura-de-64-caracteres-minimo
DEBUG=false
LOG_LEVEL=info
PORT=8000
```

#### Variables de Contenido
```
DEFAULT_CONTENT_PROVIDER=deepseek
CONTENT_LANGUAGE=es
WRITING_STYLE=profesional
ENABLE_IMAGE_GENERATION=true
DEFAULT_IMAGE_PROVIDER=gemini
MAX_CONTENT_LENGTH=5000
DEFAULT_CTA_COUNT=2
DEFAULT_PARAGRAPH_COUNT=4
```

#### Variables de Seguridad
```
CORS_ORIGINS=https://tu-dominio.railway.app
ALLOWED_HOSTS=tu-dominio.railway.app,localhost
SECURE_COOKIES=true
SESSION_TIMEOUT=3600
```

### 4. Agregar Servicios de Base de Datos

#### PostgreSQL
1. En tu proyecto de Railway, haz clic en **"+ New"**
2. Selecciona **"Database"** → **"Add PostgreSQL"**
3. Esto configurará automáticamente la variable `DATABASE_URL`

#### Redis (Opcional)
1. Haz clic en **"+ New"** nuevamente
2. Selecciona **"Database"** → **"Add Redis"**
3. Esto configurará automáticamente la variable `REDIS_URL`

### 5. Configurar API Keys (Opcional pero Recomendado)

En la pestaña **"Variables"**, agrega tus API keys:

```
DEEPSEEK_API_KEY=tu_api_key_de_deepseek
OPENAI_API_KEY=sk-tu_api_key_de_openai
GEMINI_API_KEY=tu_api_key_de_gemini
```

### 6. Verificar Configuración de Build

Railway debería detectar automáticamente la configuración desde:
- `railway.toml` - Configuración principal
- `nixpacks.toml` - Configuración de build
- `start.sh` - Script de inicio

Si no, verifica que estos archivos estén en la raíz del repositorio.

### 7. Deploy y Monitoreo

1. **Deploy Automático**: Railway hará deploy automáticamente después de configurar las variables
2. **Ver Logs**: Ve a la pestaña **"Deployments"** para ver el progreso
3. **Verificar Build**: Asegúrate de que el build sea exitoso

---

## 🔍 Verificación Post-Deploy

### Health Checks
Una vez deployado, verifica estos endpoints:
- `https://tu-dominio.railway.app/ping` ✅
- `https://tu-dominio.railway.app/ready` ✅
- `https://tu-dominio.railway.app/healthz` ✅

### Aplicación
- **Frontend**: `https://tu-dominio.railway.app/`
- **API Docs**: `https://tu-dominio.railway.app/docs`
- **Admin**: `https://tu-dominio.railway.app/admin`

---

## 🛠️ Troubleshooting

### Si el Deploy Falla

1. **Revisar Logs de Build**:
   - Ve a **"Deployments"** → Selecciona el deploy fallido
   - Revisa los logs de build para errores específicos

2. **Problemas Comunes**:
   - **Error de SECRET_KEY**: Asegúrate de configurar una clave de al menos 32 caracteres
   - **Error de DATABASE_URL**: Verifica que PostgreSQL esté agregado y conectado
   - **Error de dependencias**: Verifica que `requirements.txt` esté actualizado
   - **Error de puerto**: Railway usa la variable `PORT` automáticamente

3. **Verificar Variables**:
   - Ve a **"Variables"** y confirma que todas las críticas estén configuradas
   - Verifica que no haya espacios extra o caracteres especiales

### Si la Aplicación no Responde

1. **Verificar Health Checks**:
   ```bash
   curl https://tu-dominio.railway.app/ping
   curl https://tu-dominio.railway.app/ready
   ```

2. **Revisar Logs de Runtime**:
   - Ve a **"Logs"** en tiempo real
   - Busca errores de conexión a base de datos o API keys

### Redeploy
Si necesitas hacer redeploy:
1. Ve a **"Deployments"**
2. Haz clic en **"Redeploy"** en el último deployment

---

## 🔄 Deploy Automático

### Configurar Auto-Deploy
Railway está configurado para hacer deploy automático cuando:
- Haces push a la rama `main` en GitHub
- Se detectan cambios en el repositorio

### Desactivar Auto-Deploy (Opcional)
1. Ve a **"Settings"** → **"Service"**
2. En **"Source Repo"**, puedes cambiar la configuración

---

## 📋 Checklist de Deploy

- [ ] ✅ Código subido a GitHub
- [ ] ✅ Proyecto creado en Railway desde GitHub
- [ ] ⚠️ Variables críticas configuradas
- [ ] ⚠️ PostgreSQL agregado
- [ ] ⚠️ Redis agregado (opcional)
- [ ] ⚠️ API keys configuradas
- [ ] ⚠️ Deploy exitoso
- [ ] ⚠️ Health checks funcionando
- [ ] ⚠️ Aplicación accesible

---

## 🎉 ¡Listo!

Tu autopublicador web estará disponible en:
**`https://tu-dominio.railway.app`**

### Próximos Pasos
1. Configura tu dominio personalizado (opcional)
2. Configura SSL/TLS (automático en Railway)
3. Configura monitoreo y alertas
4. ¡Empieza a crear contenido!

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en Railway
2. Ejecuta `python scripts/railway_pre_deployment_check.py` localmente
3. Consulta la documentación de Railway
4. Verifica que todas las variables estén configuradas correctamente

**¡Tu proyecto está listo para producción!** 🚀