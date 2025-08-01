# 🚀 Guía Completa: Despliegue en Vercel (100% Funcional)

## 📋 **Checklist Pre-Despliegue**

### ✅ **Lo que YA tienes listo:**
- [x] Configuración de Vercel (`vercel.json`)
- [x] Dependencias optimizadas (`requirements-vercel.txt`)
- [x] Aplicación para Vercel (`main_vercel.py`)
- [x] Script de inicialización (`vercel_init.py`)
- [x] Soporte para PostgreSQL
- [x] Configuración del scheduler persistente

### ⚠️ **Lo que DEBES configurar:**
- [ ] Base de datos PostgreSQL (Neon)
- [ ] Variables de entorno en Vercel
- [ ] API keys de IA
- [ ] Clave secreta de seguridad

---

## 🗄️ **Paso 1: Configurar Base de Datos (CRÍTICO)**

### **Opción A: Neon PostgreSQL (RECOMENDADA)**

1. **Crear cuenta en Neon:**
   - Ve a [neon.tech](https://neon.tech)
   - Regístrate con GitHub
   - Es **GRATUITO** hasta 10GB

2. **Crear proyecto:**
   - Nombre: `autopublicador-web`
   - Database: `autopublicador`
   - Región: Selecciona la más cercana

3. **Obtener URL de conexión:**
   ```
   postgresql://usuario:password@host.neon.tech:5432/autopublicador?sslmode=require
   ```

### **Opción B: Supabase (Alternativa)**

1. Ve a [supabase.com](https://supabase.com)
2. Crea nuevo proyecto
3. Ve a Settings > Database
4. Copia la "Connection string"

---

## ⚙️ **Paso 2: Configurar Variables de Entorno en Vercel**

### **Variables OBLIGATORIAS:**

```bash
# 🔑 SEGURIDAD (CRÍTICO)
SECRET_KEY=tu-clave-super-secreta-de-al-menos-32-caracteres

# 🗄️ BASE DE DATOS (CRÍTICO)
DATABASE_URL=postgresql://usuario:password@host:port/database?sslmode=require

# 🤖 IA - AL MENOS UNA OBLIGATORIA
OPENAI_API_KEY=sk-proj-...
# O
GEMINI_API_KEY=AIza...
# O
DEEPSEEK_API_KEY=sk-...

# 🎨 GENERACIÓN DE IMÁGENES (OPCIONAL)
IMAGE_GENERATION_ENABLED=true
IMAGE_PROVIDER=openai
```

### **Variables OPCIONALES:**

```bash
# 🔧 CONFIGURACIÓN AVANZADA
AI_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini
GEMINI_MODEL=gemini-1.5-flash
MAX_CONTENT_LENGTH=2000
DEFAULT_LANGUAGE=es
RATE_LIMIT_ENABLED=true
REQUESTS_PER_MINUTE=60
```

### **Cómo configurar en Vercel:**

1. Ve a tu proyecto en [vercel.com](https://vercel.com)
2. **Settings > Environment Variables**
3. Agrega cada variable:
   - **Name:** Nombre de la variable
   - **Value:** Valor de la variable
   - **Environment:** Selecciona "Production", "Preview", "Development"

---

## 🚀 **Paso 3: Desplegar en Vercel**

### **Método 1: Desde GitHub (Recomendado)**

1. **Subir código a GitHub:**
   ```bash
   git add .
   git commit -m "🚀 Preparado para Vercel con PostgreSQL"
   git push origin main
   ```

2. **Conectar con Vercel:**
   - Ve a [vercel.com](https://vercel.com)
   - "New Project" > "Import Git Repository"
   - Selecciona tu repositorio
   - **Framework Preset:** Other
   - **Build Command:** (dejar vacío)
   - **Output Directory:** (dejar vacío)
   - **Install Command:** `pip install -r requirements-vercel.txt`

3. **Deploy:**
   - Haz clic en "Deploy"
   - Espera 2-3 minutos

### **Método 2: Vercel CLI**

```bash
# Instalar Vercel CLI
npm i -g vercel

# Desplegar
vercel --prod
```

---

## 🧪 **Paso 4: Verificar Funcionamiento**

### **1. Health Check:**
```
https://tu-app.vercel.app/health
```
**Respuesta esperada:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### **2. Acceder al Dashboard:**
```
https://tu-app.vercel.app/dashboard
```
**Credenciales por defecto:**
- Email: `admin@autopublicador.com`
- Password: `admin123`

### **3. API Documentation:**
```
https://tu-app.vercel.app/docs
```

---

## 🔍 **Paso 5: Verificar Funcionalidades**

### **✅ Checklist de Funcionalidades:**

- [ ] **Login funciona** (admin@autopublicador.com / admin123)
- [ ] **Generación de contenido** (requiere API key de IA)
- [ ] **Scheduler persistente** (configuración se guarda)
- [ ] **Gestión de keywords**
- [ ] **Landing pages**
- [ ] **Análisis de contenido**
- [ ] **Generación de imágenes** (si está habilitada)

---

## 🆘 **Solución de Problemas**

### **Error: "Internal Server Error"**
```bash
# Ver logs en tiempo real
vercel logs --follow

# Ver logs específicos
vercel logs --function=backend/main_vercel.py
```

### **Error: "Database connection failed"**
- ✅ Verifica que `DATABASE_URL` esté configurada
- ✅ Asegúrate de incluir `?sslmode=require` para PostgreSQL
- ✅ Verifica que la base de datos esté activa en Neon/Supabase

### **Error: "No AI provider configured"**
- ✅ Configura al menos una API key: `OPENAI_API_KEY`, `GEMINI_API_KEY`, o `DEEPSEEK_API_KEY`
- ✅ Verifica que la API key sea válida

### **Error: "Function timeout"**
- ✅ Verifica que `maxDuration: 30` esté en `vercel.json`
- ✅ Algunas operaciones de IA pueden tardar más

### **Error: "Module not found"**
- ✅ Verifica que todas las dependencias estén en `requirements-vercel.txt`
- ✅ Redespliega después de cambios en requirements

---

## 📊 **Monitoreo y Mantenimiento**

### **Dashboard de Vercel:**
- **Analytics:** Tráfico y rendimiento
- **Functions:** Logs y métricas
- **Deployments:** Historial de despliegues

### **Dashboard de Neon:**
- **Queries:** Consultas SQL ejecutadas
- **Storage:** Uso de almacenamiento
- **Connections:** Conexiones activas

### **Comandos Útiles:**
```bash
# Ver logs en tiempo real
vercel logs --follow

# Ver información del proyecto
vercel ls

# Ver variables de entorno
vercel env ls

# Redeploy manual
vercel --prod
```

---

## 🎯 **Optimizaciones Adicionales**

### **1. Dominio Personalizado:**
1. Ve a **Settings > Domains** en Vercel
2. Agrega tu dominio
3. Configura DNS según instrucciones

### **2. Monitoreo Avanzado:**
- Configura alertas en Vercel
- Usa Neon dashboard para monitorear DB
- Configura Sentry para error tracking (opcional)

### **3. Backup de Base de Datos:**
- Neon hace backups automáticos
- Configura exports periódicos si necesario

---

## 🎉 **¡Listo para Producción!**

### **URLs Importantes:**
- **Aplicación:** `https://tu-proyecto.vercel.app`
- **Dashboard:** `https://tu-proyecto.vercel.app/dashboard`
- **API Docs:** `https://tu-proyecto.vercel.app/docs`
- **Health Check:** `https://tu-proyecto.vercel.app/health`

### **Credenciales por Defecto:**
- **Email:** admin@autopublicador.com
- **Password:** admin123
- **⚠️ CAMBIAR** después del primer login

### **Funcionalidades Disponibles:**
- ✅ **Generación de contenido con IA**
- ✅ **Scheduler automático persistente**
- ✅ **Gestión de keywords**
- ✅ **Landing pages dinámicas**
- ✅ **Análisis de contenido**
- ✅ **Generación de imágenes**
- ✅ **API REST completa**
- ✅ **Dashboard web intuitivo**

---

## 💡 **Consejos Finales**

1. **Seguridad:** Cambia las credenciales por defecto
2. **Monitoreo:** Revisa logs regularmente
3. **Backup:** Neon hace backups automáticos
4. **Escalabilidad:** Fácil upgrade a planes pagados
5. **Soporte:** Usa GitHub Issues para reportar problemas

**¡Tu Autopublicador Web está listo para conquistar el mundo! 🌍**