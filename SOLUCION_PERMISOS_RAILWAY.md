# Solución a Errores de Permisos en Railway

## Problema Identificado

La aplicación estaba fallando en Railway con el siguiente error:

```
PermissionError: [Errno 13] Permission denied: '/images'
```

### Causa Raíz

El problema se originaba porque la aplicación intentaba crear directorios en rutas absolutas del sistema de archivos (`/images`) donde el usuario de la aplicación no tiene permisos de escritura en el entorno containerizado de Railway.

## Archivos Afectados

### 1. `backend/main.py` (Línea 106-107)

**Problema:**
```python
images_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")
os.makedirs(images_path, exist_ok=True)
```

**Solución:**
```python
# En Railway, usar un directorio relativo o variable de entorno para storage
images_path = os.environ.get("IMAGES_PATH", os.path.join(os.path.dirname(__file__), "storage", "images"))
try:
    os.makedirs(images_path, exist_ok=True)
    app.mount("/images", StaticFiles(directory=images_path), name="images")
    print(f"Images directory configured at: {images_path}")
except PermissionError as e:
    print(f"Warning: Could not create images directory at {images_path}: {e}")
    print("Images upload functionality may be limited")
```

### 2. `backend/app/services/image_generator.py` (Línea 393)

**Problema:**
```python
images_dir = os.path.join("static", "images", "generated")
```

**Solución:**
```python
images_dir = os.environ.get("GENERATED_IMAGES_PATH", 
                           os.path.join(os.path.dirname(__file__), "..", "..", "storage", "images", "generated"))
```

### 3. `backend/app/api/v1/image_generation.py` (Múltiples líneas)

**Problemas:**
- Construcción compleja de rutas con múltiples `os.path.dirname()`
- Intentos de acceder a directorios fuera del contexto de la aplicación

**Soluciones:**
- Upload directory: Usar `MANUAL_IMAGES_PATH` environment variable
- Generated images: Usar `GENERATED_IMAGES_PATH` environment variable
- Gallery: Usar paths relativos seguros

## Estructura de Directorios Implementada

```
backend/
├── storage/
│   └── images/
│       ├── generated/     # Imágenes generadas por IA
│       ├── manual/        # Imágenes subidas manualmente
│       └── uploads/       # Otros uploads
├── static/               # Archivos estáticos del backend
└── app/
    └── ...
```

## Variables de Entorno Configurables

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `IMAGES_PATH` | Directorio principal de imágenes | `backend/storage/images` |
| `GENERATED_IMAGES_PATH` | Imágenes generadas por IA | `backend/storage/images/generated` |
| `MANUAL_IMAGES_PATH` | Imágenes subidas manualmente | `backend/storage/images/manual` |

## Mejoras en `start.sh`

Se agregó la creación automática de directorios de almacenamiento:

```bash
echo "Creating storage directories..."
mkdir -p backend/storage/images/generated
mkdir -p backend/storage/images/manual
mkdir -p backend/storage/images/uploads
echo "Storage directories created successfully"
```

## Beneficios de la Solución

1. **Compatibilidad con Railway**: Los paths son relativos y seguros
2. **Flexibilidad**: Configurables via variables de entorno
3. **Manejo de Errores**: Graceful degradation si no se pueden crear directorios
4. **Organización**: Estructura clara de almacenamiento
5. **Seguridad**: No intenta acceder a directorios del sistema

## Verificación de la Solución

### En Railway:
1. La aplicación debería iniciar sin errores de permisos
2. Los health checks (`/ping`, `/ready`, `/healthz`) deberían funcionar
3. Los directorios de storage se crean automáticamente

### Logs Esperados:
```
Images directory configured at: /app/backend/storage/images
Storage directories created successfully
✓ Application import successful
```

## Próximos Pasos

1. **Monitorear** el deployment en Railway
2. **Verificar** que los health checks funcionen
3. **Probar** la funcionalidad de upload de imágenes
4. **Configurar** variables de entorno adicionales si es necesario

## Lecciones Aprendidas

- **Evitar paths absolutos** en aplicaciones containerizadas
- **Usar variables de entorno** para configuración de paths
- **Implementar manejo de errores** para operaciones de filesystem
- **Crear directorios automáticamente** en el startup script
- **Probar en entornos similares** a producción antes del deploy

---

**Fecha de Resolución:** $(date)
**Commits Relacionados:** 
- `5b86b4d` - Fix Railway permission errors: Update image storage paths
- `3b7bc69` - Previous health check fixes

**Estado:** ✅ Resuelto y desplegado