#!/bin/bash

# 🚀 Script de Preparación para GitHub y Vercel
# Este script prepara el proyecto para ser subido a GitHub y desplegado en Vercel

echo "🚀 Preparando Autopublicador Web para GitHub y Vercel..."
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes de éxito
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Función para mostrar mensajes de advertencia
warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Función para mostrar mensajes de error
error() {
    echo -e "${RED}❌ $1${NC}"
}

# Función para mostrar mensajes informativos
info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "vercel.json" ]; then
    error "No se encontró vercel.json. Asegúrate de estar en el directorio raíz del proyecto."
    exit 1
fi

success "Directorio del proyecto verificado"

# 1. Limpiar archivos temporales y de desarrollo
echo ""
info "Paso 1: Limpiando archivos temporales..."

# Eliminar archivos de base de datos de desarrollo
if [ -f "backend/autopublicador.db" ]; then
    rm backend/autopublicador.db
    success "Base de datos de desarrollo eliminada"
fi

if [ -f "backend/app.db" ]; then
    rm backend/app.db
    success "Base de datos temporal eliminada"
fi

# Eliminar logs
if [ -d "logs" ]; then
    rm -rf logs
    success "Directorio de logs eliminado"
fi

# Eliminar archivos temporales
find . -name "*.tmp" -delete
find . -name "*.temp" -delete
find . -name "*.log" -delete
find . -name ".DS_Store" -delete

success "Archivos temporales limpiados"

# 2. Verificar archivos esenciales para Vercel
echo ""
info "Paso 2: Verificando archivos esenciales para Vercel..."

required_files=(
    "vercel.json"
    "requirements-vercel.txt"
    "backend/main_vercel.py"
    "backend/vercel_init.py"
    ".env.production"
    "DEPLOY_VERCEL.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        success "$file existe"
    else
        error "$file no encontrado"
        exit 1
    fi
done

# 3. Verificar estructura de directorios
echo ""
info "Paso 3: Verificando estructura de directorios..."

required_dirs=(
    "backend"
    "frontend"
    "backend/app"
    "backend/app/api"
    "backend/app/models"
    "backend/app/services"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        success "Directorio $dir existe"
    else
        warning "Directorio $dir no encontrado"
    fi
done

# 4. Crear directorios necesarios para Vercel
echo ""
info "Paso 4: Creando directorios necesarios..."

mkdir -p backend/storage/images
mkdir -p backend/app/templates
mkdir -p backend/static
mkdir -p images/generated
mkdir -p images/uploads
mkdir -p images/manual

# Crear archivos .gitkeep para mantener directorios vacíos
touch backend/storage/images/.gitkeep
touch images/generated/.gitkeep
touch images/uploads/.gitkeep
touch images/manual/.gitkeep

success "Directorios creados"

# 5. Generar SECRET_KEY segura para producción
echo ""
info "Paso 5: Generando SECRET_KEY segura..."

# Generar una clave secreta aleatoria
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Actualizar .env.production con la nueva clave
if [ -f ".env.production" ]; then
    sed -i.bak "s/SECRET_KEY=your-super-secret-key-here-change-in-vercel/SECRET_KEY=$SECRET_KEY/" .env.production
    rm .env.production.bak
    success "SECRET_KEY actualizada en .env.production"
else
    warning ".env.production no encontrado"
fi

# 6. Verificar que git está inicializado
echo ""
info "Paso 6: Verificando configuración de Git..."

if [ ! -d ".git" ]; then
    warning "Git no está inicializado. Inicializando..."
    git init
    success "Git inicializado"
else
    success "Git ya está inicializado"
fi

# Verificar si hay un remote configurado
if ! git remote | grep -q origin; then
    warning "No hay remote 'origin' configurado"
    echo ""
    echo "Para configurar el remote, ejecuta:"
    echo "git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git"
else
    success "Remote 'origin' configurado"
fi

# 7. Preparar commit
echo ""
info "Paso 7: Preparando archivos para commit..."

# Agregar todos los archivos al staging
git add .

# Verificar si hay cambios para commitear
if git diff --staged --quiet; then
    info "No hay cambios nuevos para commitear"
else
    success "Archivos preparados para commit"
    
    # Mostrar resumen de archivos
    echo ""
    info "Archivos que serán incluidos en el commit:"
    git diff --staged --name-only | head -20
    
    if [ $(git diff --staged --name-only | wc -l) -gt 20 ]; then
        echo "... y $(( $(git diff --staged --name-only | wc -l) - 20 )) archivos más"
    fi
fi

# 8. Mostrar resumen final
echo ""
echo "=================================================="
echo "🎉 ¡Preparación completada!"
echo "=================================================="
echo ""
info "Próximos pasos:"
echo ""
echo "1. 📝 Revisar y configurar variables de entorno:"
echo "   - Edita .env.production con tus API keys"
echo "   - La SECRET_KEY ya fue generada automáticamente"
echo ""
echo "2. 📤 Subir a GitHub:"
echo "   git commit -m '🚀 Preparado para despliegue en Vercel'"
echo "   git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git"
echo "   git push -u origin main"
echo ""
echo "3. 🌐 Desplegar en Vercel:"
echo "   - Ve a vercel.com"
echo "   - Conecta tu repositorio de GitHub"
echo "   - Configura las variables de entorno"
echo "   - ¡Despliega!"
echo ""
echo "4. 📖 Consultar la guía completa:"
echo "   cat DEPLOY_VERCEL.md"
echo ""
success "¡Tu Autopublicador Web está listo para la nube! 🚀"

# Mostrar información importante
echo ""
warning "IMPORTANTE:"
echo "- Configura al menos una API key de IA (OpenAI, DeepSeek, o Gemini)"
echo "- Cambia las credenciales por defecto después del primer login"
echo "- Revisa las variables de entorno en .env.production"
echo ""
info "Credenciales por defecto:"
echo "Email: admin@autopublicador.com"
echo "Password: admin123"