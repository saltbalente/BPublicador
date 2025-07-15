# 🚀 Guía Completa de Deployment en Railway

## ✅ Estado Actual del Proyecto

**Tasa de éxito: 91.4%** - ¡Tu proyecto está casi listo!

### ✓ Verificaciones Exitosas (32/35)
- ✅ Configuración de Railway completa
- ✅ Dependencias instaladas correctamente
- ✅ Aplicación se importa sin errores
- ✅ Health checks configurados
- ✅ Todos los archivos committeados
- ✅ Scripts de verificación funcionando

### ⚠️ Pendientes (Solo variables de entorno)
- Variables de entorno (se configuran en Railway)
- API keys (opcionales)

---

## 🎯 Pasos para Deployment

### 1. Preparar Railway CLI
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login en Railway
railway login

# Crear nuevo proyecto
railway new
```

### 2. Configurar Variables Críticas
```bash
# Variables obligatorias
railway variables set ENVIRONMENT=production
railway variables set SECRET_KEY='tu-clave-secreta-muy-segura-aqui'
railway variables set DEBUG=false
railway variables set LOG_LEVEL=info
railway variables set PORT=8000
```

### 3. Configurar Variables de Contenido
```bash
railway variables set DEFAULT_CONTENT_PROVIDER=deepseek
railway variables set CONTENT_LANGUAGE=es
railway variables set WRITING_STYLE=profesional
railway variables set ENABLE_IMAGE_GENERATION=true
railway variables set DEFAULT_IMAGE_PROVIDER=gemini
railway variables set MAX_CONTENT_LENGTH=5000
railway variables set DEFAULT_CTA_COUNT=2
railway variables set DEFAULT_PARAGRAPH_COUNT=4
```

### 4. Agregar Servicios de Base de Datos
```bash
# Agregar PostgreSQL (automáticamente configura DATABASE_URL)
railway add postgresql

# Agregar Redis (automáticamente configura REDIS_URL)
railway add redis
```

### 5. Configurar API Keys (Opcional pero Recomendado)
```bash
# Reemplaza con tus API keys reales
railway variables set DEEPSEEK_API_KEY=tu_api_key_de_deepseek
railway variables set OPENAI_API_KEY=sk-tu_api_key_de_openai
railway variables set GEMINI_API_KEY=tu_api_key_de_gemini
```

### 6. Configurar Variables de Seguridad
```bash
# Ajusta según tu dominio de Railway
railway variables set CORS_ORIGINS=https://tu-dominio.railway.app
railway variables set ALLOWED_HOSTS=tu-dominio.railway.app,localhost
railway variables set SECURE_COOKIES=true
railway variables set SESSION_TIMEOUT=3600
```

### 7. Deploy
```bash
# Hacer push del código
git push origin main

# Deploy en Railway
railway up

# O conectar repositorio GitHub
railway connect
```

---

## 🔍 Verificación Post-Deployment

### Verificar Variables
```bash
railway variables
```

### Ver Logs
```bash
railway logs
```

### Verificar Health Checks
Una vez deployado, verifica estos endpoints:
- `https://tu-dominio.railway.app/ping`
- `https://tu-dominio.railway.app/ready`
- `https://tu-dominio.railway.app/healthz`

### Verificar Aplicación
- `https://tu-dominio.railway.app/` - Frontend
- `https://tu-dominio.railway.app/docs` - API Documentation

---

## 🛠️ Troubleshooting

### Si el deployment falla:

1. **Revisar logs:**
   ```bash
   railway logs
   ```

2. **Verificar variables:**
   ```bash
   railway variables
   ```

3. **Ejecutar verificación local:**
   ```bash
   python scripts/railway_pre_deployment_check.py
   ```

4. **Problemas comunes:**
   - **Error de SECRET_KEY:** Asegúrate de configurar una clave secreta segura
   - **Error de base de datos:** Verifica que PostgreSQL esté agregado
   - **Error de dependencias:** Verifica que `requirements.txt` esté actualizado
   - **Error de health check:** Verifica que los endpoints `/ping`, `/ready`, `/healthz` respondan

### Si necesitas redeploy:
```bash
railway redeploy
```

---

## 📋 Checklist Final

- [ ] Railway CLI instalado y configurado
- [ ] Proyecto creado en Railway
- [ ] Variables críticas configuradas
- [ ] PostgreSQL agregado
- [ ] Redis agregado (opcional)
- [ ] API keys configuradas
- [ ] Código pusheado a repositorio
- [ ] Deployment ejecutado
- [ ] Health checks funcionando
- [ ] Aplicación accesible

---

## 🎉 ¡Listo!

Tu aplicación debería estar funcionando en Railway. Si tienes problemas:

1. Revisa los logs con `railway logs`
2. Ejecuta `python scripts/railway_pre_deployment_check.py` localmente
3. Consulta la documentación de Railway
4. Verifica que todas las variables estén configuradas

**¡Tu autopublicador web está listo para producción!** 🚀