# 🚀 Guía de Deployment en Railway - Autopublicador Web

## ⚠️ Problemas Comunes y Soluciones

### 1. Health Check Failures
**Problema**: Railway reporta "service unavailable" en health checks

**Soluciones implementadas**:
- ✅ Timeout aumentado a 600 segundos (10 minutos)
- ✅ Múltiples endpoints de health: `/ping`, `/ready`, `/healthz`
- ✅ Endpoints ultra-simples sin dependencias externas
- ✅ Script de inicio con verificaciones exhaustivas
- ✅ Reintentos aumentados a 15

### 2. Startup Time Issues
**Problema**: La aplicación tarda mucho en iniciar

**Soluciones**:
- ✅ Verificación de dependencias antes del inicio
- ✅ Logs detallados para debugging
- ✅ Configuración optimizada de uvicorn
- ✅ Variables de entorno con valores por defecto

### 3. IPv6 vs IPv4 Issues
**Problema**: Railway usa IPv4 para health checks pero la app escucha en IPv6

**Solución**: Configurado para escuchar en `0.0.0.0` (IPv4 + IPv6)

## 🔧 Configuración Actual

### Railway.toml
```toml
[build]
builder = "nixpacks"
watchPatterns = ["**/*.py", "requirements.txt", "alembic/**/*"]

[deploy]
startCommand = "/app/start.sh"
healthcheckPath = "/ping"
healthcheckTimeout = 600  # 10 minutos
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 15

[experimental]
incremental = false  # Evita problemas de cache
```

### Endpoints de Health Check
- `/ping` - Ultra simple, respuesta inmediata
- `/ready` - Incluye timestamp, verifica que la app está lista
- `/healthz` - Compatible con estándares Kubernetes/Railway

### Script de Inicio Robusto
- Verificación de Python y dependencias
- Test de importación de la aplicación
- Verificación de endpoints de health
- Migraciones de base de datos (si aplica)
- Configuración optimizada de uvicorn

## 📋 Checklist Pre-Deployment

### Variables de Entorno Mínimas
```bash
ENVIRONMENT=production
SECRET_KEY=tu-clave-secreta-muy-segura
DEBUG=false
LOG_LEVEL=info
```

### Variables de Base de Datos (Auto-configuradas por Railway)
```bash
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

### Variables de API (Opcionales)
```bash
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

## 🚨 Pasos Críticos para Railway

### 1. Configurar Variables de Entorno
1. Ve a tu proyecto en Railway
2. Click en "Variables"
3. Agrega las variables mínimas listadas arriba
4. **IMPORTANTE**: Configura `SECRET_KEY` con un valor seguro

### 2. Agregar Servicios de Base de Datos
1. En Railway Marketplace, agrega:
   - **PostgreSQL** (configurará `DATABASE_URL`)
   - **Redis** (configurará `REDIS_URL`)
2. Espera a que se configuren completamente

### 3. Deploy y Monitoreo
1. Haz push de los cambios a GitHub
2. Railway detectará automáticamente los cambios
3. Monitorea los logs durante el deployment
4. Verifica que el health check pase

## 🔍 Debugging en Railway

### Logs a Revistar
```bash
# En los logs de Railway, busca:
"=== Railway FastAPI Startup Script ==="
"✓ Application imported successfully"
"✓ All health endpoints configured"
"Starting FastAPI application..."
```

### Comandos de Verificación
```bash
# Una vez deployado, verifica:
curl https://tu-app.railway.app/ping
curl https://tu-app.railway.app/ready
curl https://tu-app.railway.app/healthz
```

## ⏱️ Tiempos Esperados

- **Build time**: 3-5 minutos
- **Startup time**: 2-3 minutos
- **Health check**: Hasta 10 minutos (configurado)
- **Total deployment**: 15-20 minutos máximo

## 🆘 Si Aún Falla

### Verificaciones Adicionales
1. **Logs de Railway**: Revisa los logs completos
2. **Variables de entorno**: Verifica que estén configuradas
3. **Servicios**: Asegúrate de que PostgreSQL y Redis estén activos
4. **Timeout**: Si falla por timeout, considera aumentar a 900s

### Fallback Options
1. Deshabilitar health check temporalmente
2. Usar un endpoint aún más simple
3. Configurar un health check externo

## 📞 Soporte

Si el deployment sigue fallando después de seguir esta guía:
1. Revisa los logs completos de Railway
2. Verifica que todas las variables estén configuradas
3. Considera contactar el soporte de Railway con los logs específicos

---

**Última actualización**: Configuración optimizada para Railway con timeouts extendidos y múltiples endpoints de health check.