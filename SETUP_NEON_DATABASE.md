# 🗄️ Configuración de Base de Datos Neon para Vercel

## 🎯 ¿Por qué Neon?
- ✅ **Gratuita** hasta 10GB
- ✅ **Serverless** (perfecta para Vercel)
- ✅ **PostgreSQL** completo
- ✅ **Sin configuración compleja**

## 📝 Paso 1: Crear cuenta en Neon

1. Ve a [neon.tech](https://neon.tech)
2. Haz clic en **"Sign Up"**
3. Regístrate con GitHub (recomendado)

## 🗄️ Paso 2: Crear base de datos

1. En el dashboard de Neon, haz clic en **"Create Project"**
2. Configura:
   - **Project name:** `autopublicador-web`
   - **Database name:** `autopublicador`
   - **Region:** Selecciona la más cercana a ti
3. Haz clic en **"Create Project"**

## 🔗 Paso 3: Obtener URL de conexión

1. En tu proyecto de Neon, ve a **"Dashboard"**
2. En la sección **"Connection Details"**, copia la **"Connection string"**
3. Se verá así:
   ```
   postgresql://usuario:password@host.neon.tech:5432/autopublicador?sslmode=require
   ```

## ⚙️ Paso 4: Configurar en Vercel

1. Ve a tu proyecto en [vercel.com](https://vercel.com)
2. Ve a **Settings > Environment Variables**
3. Agrega la variable:
   - **Name:** `DATABASE_URL`
   - **Value:** La URL que copiaste de Neon
   - **Environment:** Production, Preview, Development

## 🔄 Paso 5: Actualizar configuración para PostgreSQL

Tu aplicación ya está preparada para PostgreSQL, pero vamos a asegurar la migración:

### Verificar dependencias
El archivo `requirements-vercel.txt` ya incluye:
```
sqlalchemy==2.0.23
aiosqlite==0.19.0  # Para desarrollo local
```

### Agregar soporte para PostgreSQL
Necesitamos agregar `psycopg2-binary` para PostgreSQL en Vercel.

## 🧪 Paso 6: Probar conexión

Una vez configurado, tu aplicación:
1. Se conectará automáticamente a Neon
2. Creará las tablas necesarias
3. Inicializará el usuario admin

## 🔍 Verificación

Para verificar que todo funciona:
1. Despliega en Vercel
2. Ve a `https://tu-app.vercel.app/health`
3. Deberías ver: `{"status": "healthy", "database": "connected"}`

## 🆘 Solución de problemas

### Error: "could not connect to server"
- Verifica que la URL de Neon esté correcta
- Asegúrate de incluir `?sslmode=require` al final

### Error: "relation does not exist"
- Las tablas se crean automáticamente en el primer despliegue
- Si persiste, verifica los logs de Vercel

### Error: "password authentication failed"
- Regenera la password en Neon
- Actualiza la variable `DATABASE_URL` en Vercel

## 💡 Consejos

1. **Backup:** Neon hace backups automáticos
2. **Monitoreo:** Usa el dashboard de Neon para ver queries
3. **Límites:** Plan gratuito: 10GB, 100 conexiones concurrentes
4. **Escalabilidad:** Fácil upgrade a plan pagado si creces

## 🎉 ¡Listo!

Con Neon configurado, tu aplicación tendrá:
- ✅ Persistencia de datos real
- ✅ Configuración del scheduler persistente
- ✅ Usuarios y contenido que no se pierden
- ✅ Rendimiento optimizado para serverless