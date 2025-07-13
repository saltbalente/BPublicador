# Variables de Entorno Requeridas para Railway

Para que la aplicación funcione correctamente en Railway, necesitas configurar las siguientes variables de entorno:

## Variables Esenciales (Mínimas para que funcione)

```
ENVIRONMENT=production
SECRET_KEY=tu-clave-secreta-muy-segura-cambiar-en-produccion
DEBUG=false
```

## Variables de Base de Datos (Railway las proporciona automáticamente)

```
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

## Variables de API (Opcionales pero recomendadas)

```
DEEPSEEK_API_KEY=tu_api_key_de_deepseek
OPENAI_API_KEY=tu_api_key_de_openai
GEMINI_API_KEY=tu_api_key_de_gemini
```

## Configuración de Contenido

```
DEFAULT_CONTENT_PROVIDER=deepseek
CONTENT_LANGUAGE=es
WRITING_STYLE=profesional
ENABLE_IMAGE_GENERATION=true
DEFAULT_IMAGE_PROVIDER=gemini
```

## Pasos para configurar en Railway:

1. Ve a tu proyecto en Railway
2. Haz clic en "Variables"
3. Agrega las variables una por una
4. Redeploy la aplicación

## Servicios adicionales necesarios:

1. **PostgreSQL**: Agregar desde Railway Marketplace
2. **Redis**: Agregar desde Railway Marketplace

Estos servicios configurarán automáticamente las variables `DATABASE_URL` y `REDIS_URL`.