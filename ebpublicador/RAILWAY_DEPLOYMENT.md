# 🚀 Deployment en Railway - EBPublicador

## Pasos para Deploy Automático

### 1. Conectar Repositorio
1. Ve a [Railway.app](https://railway.app)
2. Haz clic en "New Project"
3. Selecciona "Deploy from GitHub repo"
4. Conecta este repositorio: `https://github.com/saltbalente/ebpublicador`

### 2. Configurar Variables de Entorno
En el dashboard de Railway, ve a Variables y agrega:

```bash
# Base de datos (Railway la provee automáticamente)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Claves de API de IA (REQUERIDAS)
OPENAI_API_KEY=tu_clave_openai_aqui
GEMINI_API_KEY=tu_clave_gemini_aqui

# Seguridad (REQUERIDA)
SECRET_KEY=tu_clave_secreta_super_segura_aqui

# Configuración de aplicación
ENVIRONMENT=railway
DEBUG=false
LOG_LEVEL=INFO
PYTHONPATH=.
PYTHONUNBUFFERED=1

# CORS (opcional)
ALLOWED_ORIGINS=https://tu-dominio.railway.app

# Configuración del sitio (opcional)
SITE_TITLE=EBPublicador
SITE_DESCRIPTION=Sistema de gestión de contenido con IA
SITE_URL=https://tu-dominio.railway.app
```

### 3. Agregar Base de Datos PostgreSQL
1. En tu proyecto de Railway, haz clic en "+ New"
2. Selecciona "Database" → "Add PostgreSQL"
3. Railway automáticamente conectará la base de datos

### 4. Deploy Automático
- Railway detectará automáticamente el `railway.toml`
- El build y deploy se ejecutarán automáticamente
- La aplicación estará disponible en tu dominio de Railway

## ✅ Verificación Post-Deploy

1. **Health Check**: Visita `https://tu-dominio.railway.app/health`
2. **API Docs**: Visita `https://tu-dominio.railway.app/docs`
3. **Frontend**: Visita `https://tu-dominio.railway.app`

## 🔧 Configuración Avanzada

### Dominio Personalizado
1. Ve a Settings → Domains en Railway
2. Agrega tu dominio personalizado
3. Configura los DNS según las instrucciones

### Monitoreo
- Railway provee logs automáticos
- Métricas de CPU y memoria disponibles
- Health checks configurados automáticamente

### Escalado
- Railway escala automáticamente según demanda
- Configuración de recursos en `railway.toml`
- Límites: 1GB RAM, 1 vCPU por defecto

## 🚨 Troubleshooting

### Error de Build
```bash
# Verificar logs de build en Railway dashboard
# Común: dependencias faltantes
```

### Error de Database
```bash
# Verificar que PostgreSQL esté conectado
# Verificar DATABASE_URL en variables
```

### Error de API Keys
```bash
# Verificar OPENAI_API_KEY y GEMINI_API_KEY
# Las claves deben ser válidas y tener créditos
```

## 📞 Soporte

- **Logs**: Railway Dashboard → Deployments → View Logs
- **Métricas**: Railway Dashboard → Metrics
- **Variables**: Railway Dashboard → Variables

---

**¡Tu aplicación estará lista en minutos!** 🎉