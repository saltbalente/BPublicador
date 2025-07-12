# Carpeta de Imágenes del Proyecto

Esta carpeta centraliza todas las imágenes del proyecto Autopublicador Web.

## Estructura de Carpetas

### `/uploads`
Imágenes subidas por los usuarios de forma general.

### `/generated`
Imágenes generadas automáticamente por IA para contenido.

### `/manual`
Imágenes subidas manualmente por los usuarios a través del editor de contenido.

### `/featured`
Imágenes destacadas para artículos y contenido principal.

## Configuración del Servidor

Las imágenes se sirven a través del endpoint `/images` configurado en `main.py`:
- URL base: `http://localhost:8001/images/`
- Ejemplo: `http://localhost:8001/images/manual/imagen.jpg`

## Formatos Soportados

- JPG/JPEG
- PNG
- GIF
- WebP

## Límites

- Tamaño máximo por imagen: 10MB
- Formatos permitidos: Imágenes únicamente

## Uso en el Frontend

Para referenciar imágenes en el frontend, usar la ruta relativa:
```html
<img src="/images/manual/nombre-imagen.jpg" alt="Descripción">
```

## Notas

- Las imágenes se organizan automáticamente en subcarpetas según su tipo
- Cada imagen subida recibe un nombre único (UUID) para evitar conflictos
- Se genera automáticamente texto alternativo para accesibilidad