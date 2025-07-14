#!/bin/bash
set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Función para imprimir con colores
print_colored() {
    echo -e "${2}${1}${NC}"
}

# Función para imprimir headers
print_header() {
    echo ""
    echo -e "${PURPLE}${BOLD}============================================================${NC}"
    echo -e "${PURPLE}${BOLD}🔮 $1${NC}"
    echo -e "${PURPLE}${BOLD}============================================================${NC}"
    echo ""
}

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Función para verificar la versión de un comando
check_version() {
    local cmd="$1"
    local min_version="$2"
    local current_version
    
    if command_exists "$cmd"; then
        current_version=$("$cmd" --version 2>/dev/null | head -n1 | grep -oE '[0-9]+\.[0-9]+' | head -n1)
        print_colored "✅ $cmd encontrado: versión $current_version" "$GREEN"
        return 0
    else
        print_colored "❌ $cmd no encontrado" "$RED"
        return 1
    fi
}

# Función para instalar Homebrew
install_homebrew() {
    if ! command_exists brew; then
        print_colored "📦 Instalando Homebrew..." "$BLUE"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Agregar Homebrew al PATH
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        
        print_colored "✅ Homebrew instalado" "$GREEN"
    else
        print_colored "✅ Homebrew ya está instalado" "$GREEN"
    fi
}

# Función para instalar dependencias del sistema
install_system_dependencies() {
    print_header "Instalando Dependencias del Sistema"
    
    # Instalar Homebrew si no existe
    install_homebrew
    
    # Actualizar Homebrew
    print_colored "🔄 Actualizando Homebrew..." "$BLUE"
    brew update
    
    # Instalar Python 3.11
    if ! check_version python3 "3.9"; then
        print_colored "📦 Instalando Python 3.11..." "$BLUE"
        brew install python@3.11
        
        # Crear symlink si es necesario
        if [[ ! -L "/opt/homebrew/bin/python3" ]]; then
            ln -sf /opt/homebrew/bin/python3.11 /opt/homebrew/bin/python3
        fi
    fi
    
    # Instalar Node.js
    if ! check_version node "18.0"; then
        print_colored "📦 Instalando Node.js 18..." "$BLUE"
        brew install node@18
        
        # Agregar al PATH
        echo 'export PATH="/opt/homebrew/opt/node@18/bin:$PATH"' >> ~/.zprofile
        export PATH="/opt/homebrew/opt/node@18/bin:$PATH"
    fi
    
    # Instalar Git
    if ! command_exists git; then
        print_colored "📦 Instalando Git..." "$BLUE"
        brew install git
    fi
    
    # Instalar PostgreSQL (opcional)
    if ! command_exists psql; then
        print_colored "📦 Instalando PostgreSQL..." "$BLUE"
        brew install postgresql@15
        print_colored "ℹ️  Para iniciar PostgreSQL: brew services start postgresql@15" "$CYAN"
    fi
    
    # Instalar Redis (opcional)
    if ! command_exists redis-server; then
        print_colored "📦 Instalando Redis..." "$BLUE"
        brew install redis
        print_colored "ℹ️  Para iniciar Redis: brew services start redis" "$CYAN"
    fi
    
    print_colored "✅ Dependencias del sistema instaladas" "$GREEN"
}

# Función para configurar el backend
setup_backend() {
    print_header "Configurando Backend (FastAPI)"
    
    cd backend
    
    # Crear entorno virtual
    if [[ ! -d "venv" ]]; then
        print_colored "📦 Creando entorno virtual..." "$BLUE"
        python3 -m venv venv
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Actualizar pip
    print_colored "📦 Actualizando pip..." "$BLUE"
    pip install --upgrade pip
    
    # Instalar dependencias
    print_colored "📦 Instalando dependencias de Python..." "$BLUE"
    pip install -r requirements.txt
    
    # Configurar archivo .env
    if [[ ! -f ".env" ]]; then
        print_colored "⚙️  Creando archivo .env..." "$BLUE"
        cp .env.example .env
        
        # Generar SECRET_KEY segura
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        
        print_colored "⚠️  Recuerda configurar las API keys en backend/.env" "$YELLOW"
    fi
    
    # Configurar base de datos
    print_colored "🗄️  Configurando base de datos..." "$BLUE"
    alembic upgrade head
    
    # Inicializar datos
    python -c "from app.core.init_db import init_db; import asyncio; asyncio.run(init_db())" 2>/dev/null || true
    
    cd ..
    print_colored "✅ Backend configurado" "$GREEN"
}

# Función para configurar el frontend
setup_frontend() {
    print_header "Configurando Frontend"
    
    cd frontend
    
    # Instalar dependencias
    print_colored "📦 Instalando dependencias de Node.js..." "$BLUE"
    npm install
    
    # Configurar archivo .env.local
    if [[ ! -f ".env.local" ]]; then
        print_colored "⚙️  Creando archivo .env.local..." "$BLUE"
        cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_APP_NAME=Autopublicador Web
EOF
    fi
    
    cd ..
    print_colored "✅ Frontend configurado" "$GREEN"
}

# Función para verificar la instalación
verify_installation() {
    print_header "Verificando Instalación"
    
    # Verificar que se puede importar la aplicación
    cd backend
    source venv/bin/activate
    
    if python -c "from main import app; print('✅ Aplicación importada correctamente')" 2>/dev/null; then
        print_colored "✅ Backend: OK" "$GREEN"
    else
        print_colored "❌ Backend: Error al importar la aplicación" "$RED"
        cd ..
        return 1
    fi
    
    cd ..
    
    # Verificar frontend
    if [[ -f "frontend/package.json" ]] && [[ -d "frontend/node_modules" ]]; then
        print_colored "✅ Frontend: OK" "$GREEN"
    else
        print_colored "❌ Frontend: Configuración incompleta" "$RED"
        return 1
    fi
    
    print_colored "✅ Verificación completada" "$GREEN"
    return 0
}

# Función para mostrar instrucciones finales
show_final_instructions() {
    print_header "¡Instalación Completada!"
    
    print_colored "🎉 Tu Autopublicador Web está listo para usar" "$GREEN"
    echo ""
    print_colored "📚 Próximos pasos:" "$BOLD"
    echo ""
    print_colored "1. Configurar API keys:" "$CYAN"
    echo "   - Edita backend/.env"
    echo "   - Agrega tus API keys de DeepSeek, OpenAI, y/o Gemini"
    echo ""
    print_colored "2. Iniciar la aplicación:" "$CYAN"
    echo "   make dev          # Inicia backend y frontend"
    echo "   # O por separado:"
    echo "   make dev-backend  # Solo backend (puerto 8001)"
    echo "   make dev-frontend # Solo frontend (puerto 3000)"
    echo ""
    print_colored "3. Acceder a la aplicación:" "$CYAN"
    echo "   Frontend:  http://localhost:3000"
    echo "   Backend:   http://localhost:8001"
    echo "   API Docs:  http://localhost:8001/docs"
    echo ""
    print_colored "4. Comandos útiles:" "$CYAN"
    echo "   make help         # Ver todos los comandos"
    echo "   make verify       # Verificar instalación"
    echo "   make test         # Ejecutar tests"
    echo "   make clean        # Limpiar instalación"
    echo ""
    print_colored "📖 Documentación completa en INSTALACION_MAC.md" "$BLUE"
    echo ""
}

# Función principal
main() {
    print_header "Instalador Automático para Mac - Autopublicador Web"
    
    # Verificar que estamos en el directorio correcto
    if [[ ! -f "README.md" ]] || [[ ! -d "backend" ]] || [[ ! -d "frontend" ]]; then
        print_colored "❌ Error: Ejecuta este script desde la raíz del proyecto" "$RED"
        exit 1
    fi
    
    # Verificar macOS
    if [[ "$(uname)" != "Darwin" ]]; then
        print_colored "❌ Error: Este script es solo para macOS" "$RED"
        exit 1
    fi
    
    print_colored "🍎 Detectado macOS $(sw_vers -productVersion)" "$GREEN"
    
    # Preguntar al usuario si quiere continuar
    echo ""
    print_colored "Este script instalará automáticamente:" "$YELLOW"
    echo "  • Homebrew (si no está instalado)"
    echo "  • Python 3.11"
    echo "  • Node.js 18"
    echo "  • PostgreSQL y Redis (opcionales)"
    echo "  • Todas las dependencias del proyecto"
    echo ""
    read -p "¿Continuar con la instalación? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_colored "❌ Instalación cancelada" "$YELLOW"
        exit 0
    fi
    
    # Ejecutar instalación
    install_system_dependencies
    setup_backend
    setup_frontend
    
    # Verificar instalación
    if verify_installation; then
        show_final_instructions
    else
        print_colored "❌ La verificación falló. Revisa los errores anteriores." "$RED"
        echo ""
        print_colored "💡 Puedes ejecutar 'make verify' para más detalles" "$CYAN"
        exit 1
    fi
}

# Ejecutar función principal
main "$@"