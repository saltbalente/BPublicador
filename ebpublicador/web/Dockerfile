# Dockerfile para Frontend Web Estático
FROM nginx:alpine AS base

# Instalar dependencias necesarias
RUN apk add --no-cache curl

# Etapa de desarrollo
FROM node:18-alpine AS development

# Instalar dependencias
RUN apk add --no-cache libc6-compat curl

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . .

# Crear usuario no-root
RUN addgroup -g 1001 -S webuser && \
    adduser -S webuser -u 1001

# Cambiar permisos
RUN chown -R webuser:webuser /app
USER webuser

# Exponer puerto para desarrollo
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080 || exit 1

# Comando de desarrollo con servidor simple
CMD ["python3", "-m", "http.server", "8080"]

# Etapa de producción
FROM nginx:alpine AS production

# Variables de entorno
ENV NODE_ENV=production

# Copiar configuración personalizada de nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Copiar archivos estáticos
COPY . /usr/share/nginx/html

# Crear usuario no-root
RUN addgroup -g 1001 -S nginx && \
    adduser -S nginx -u 1001 -G nginx

# Configurar permisos
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d

# Crear directorios necesarios
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Cambiar a usuario no-root
USER nginx

# Exponer puerto
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080 || exit 1

# Comando de producción
CMD ["nginx", "-g", "daemon off;"]