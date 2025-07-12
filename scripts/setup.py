#!/usr/bin/env python3
"""
Script de configuración y utilidades para Autopublicador Web
Facilita la instalación, configuración y mantenimiento de la plataforma
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import argparse
from typing import Optional

# Colores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(message: str, color: str = Colors.OKGREEN):
    """Imprimir mensaje con color"""
    print(f"{color}{message}{Colors.ENDC}")

def print_header(message: str):
    """Imprimir header con formato"""
    print("\n" + "="*60)
    print_colored(f"🔮 {message}", Colors.HEADER + Colors.BOLD)
    print("="*60)

def run_command(command: str, cwd: Optional[str] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Ejecutar comando del sistema"""
    print_colored(f"▶️  Ejecutando: {command}", Colors.OKBLUE)
    try:
        result = subprocess.run(
            command.split(),
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Error ejecutando comando: {e}", Colors.FAIL)
        if e.stderr:
            print_colored(f"Error: {e.stderr}", Colors.FAIL)
        raise

def check_requirements():
    """Verificar que estén instalados los requisitos del sistema"""
    print_header("Verificando Requisitos del Sistema")
    
    requirements = {
        "python3": "Python 3.9+",
        "node": "Node.js 18+",
        "npm": "NPM",
        "git": "Git"
    }
    
    missing = []
    
    for cmd, desc in requirements.items():
        try:
            result = subprocess.run([cmd, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print_colored(f"✅ {desc}: {version}", Colors.OKGREEN)
            else:
                missing.append(desc)
        except FileNotFoundError:
            missing.append(desc)
            print_colored(f"❌ {desc}: No encontrado", Colors.FAIL)
    
    if missing:
        print_colored(f"\n⚠️  Faltan requisitos: {', '.join(missing)}", Colors.WARNING)
        return False
    
    print_colored("\n✅ Todos los requisitos están instalados", Colors.OKGREEN)
    return True

def setup_backend():
    """Configurar el backend"""
    print_header("Configurando Backend (FastAPI)")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print_colored("❌ Directorio backend no encontrado", Colors.FAIL)
        return False
    
    # Crear entorno virtual
    venv_path = backend_dir / "venv"
    if not venv_path.exists():
        print_colored("📦 Creando entorno virtual...", Colors.OKBLUE)
        run_command("python3 -m venv venv", cwd=str(backend_dir))
    
    # Activar entorno virtual y instalar dependencias
    pip_path = venv_path / "bin" / "pip" if os.name != 'nt' else venv_path / "Scripts" / "pip.exe"
    
    if pip_path.exists():
        print_colored("📦 Instalando dependencias de Python...", Colors.OKBLUE)
        run_command(f"{pip_path} install --upgrade pip", cwd=str(backend_dir))
        run_command(f"{pip_path} install -r requirements.txt", cwd=str(backend_dir))
    
    # Configurar archivo .env
    env_file = backend_dir / ".env"
    env_example = backend_dir / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print_colored("⚙️  Creando archivo .env...", Colors.OKBLUE)
        shutil.copy(env_example, env_file)
        print_colored("⚠️  Recuerda configurar las API keys en .env", Colors.WARNING)
    
    print_colored("✅ Backend configurado correctamente", Colors.OKGREEN)
    return True

def setup_frontend():
    """Configurar el frontend"""
    print_header("Configurando Frontend (React/Next.js)")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print_colored("⚠️  Directorio frontend no encontrado, creando estructura básica...", Colors.WARNING)
        frontend_dir.mkdir()
        
        # Crear package.json básico
        package_json = {
            "name": "autopublicador-frontend",
            "version": "1.0.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint"
            },
            "dependencies": {
                "next": "14.0.3",
                "react": "18.2.0",
                "react-dom": "18.2.0",
                "@tanstack/react-query": "5.8.4",
                "axios": "1.6.2",
                "tailwindcss": "3.3.6",
                "@headlessui/react": "1.7.17",
                "react-hook-form": "7.48.2",
                "recharts": "2.8.0"
            },
            "devDependencies": {
                "@types/node": "20.9.0",
                "@types/react": "18.2.37",
                "@types/react-dom": "18.2.15",
                "eslint": "8.53.0",
                "eslint-config-next": "14.0.3",
                "typescript": "5.2.2"
            }
        }
        
        import json
        with open(frontend_dir / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
    
    # Instalar dependencias
    print_colored("📦 Instalando dependencias de Node.js...", Colors.OKBLUE)
    run_command("npm install", cwd=str(frontend_dir))
    
    # Configurar archivo .env.local
    env_file = frontend_dir / ".env.local"
    if not env_file.exists():
        print_colored("⚙️  Creando archivo .env.local...", Colors.OKBLUE)
        with open(env_file, "w") as f:
            f.write("NEXT_PUBLIC_API_URL=http://localhost:8000\n")
            f.write("NEXT_PUBLIC_APP_NAME=Autopublicador Web\n")
    
    print_colored("✅ Frontend configurado correctamente", Colors.OKGREEN)
    return True

def init_database():
    """Inicializar la base de datos"""
    print_header("Inicializando Base de Datos")
    
    backend_dir = Path("backend")
    python_path = backend_dir / "venv" / "bin" / "python" if os.name != 'nt' else backend_dir / "venv" / "Scripts" / "python.exe"
    
    if not python_path.exists():
        print_colored("❌ Entorno virtual no encontrado. Ejecuta 'setup backend' primero", Colors.FAIL)
        return False
    
    try:
        # Ejecutar migraciones
        print_colored("🗄️  Ejecutando migraciones...", Colors.OKBLUE)
        run_command(f"{python_path} -m alembic upgrade head", cwd=str(backend_dir))
        
        # Inicializar datos
        print_colored("📊 Creando datos iniciales...", Colors.OKBLUE)
        run_command(f"{python_path} -c \"from app.core.init_db import init_db; import asyncio; asyncio.run(init_db())\"", cwd=str(backend_dir))
        
        print_colored("✅ Base de datos inicializada correctamente", Colors.OKGREEN)
        return True
        
    except subprocess.CalledProcessError:
        print_colored("❌ Error inicializando la base de datos", Colors.FAIL)
        return False

def start_backend():
    """Iniciar el servidor backend"""
    print_header("Iniciando Servidor Backend")
    
    backend_dir = Path("backend")
    python_path = backend_dir / "venv" / "bin" / "python" if os.name != 'nt' else backend_dir / "venv" / "Scripts" / "python.exe"
    
    if not python_path.exists():
        print_colored("❌ Entorno virtual no encontrado. Ejecuta 'setup backend' primero", Colors.FAIL)
        return False
    
    print_colored("🚀 Iniciando FastAPI en http://localhost:8000", Colors.OKGREEN)
    print_colored("📚 Documentación disponible en http://localhost:8000/docs", Colors.OKBLUE)
    print_colored("\n⏹️  Presiona Ctrl+C para detener el servidor\n", Colors.WARNING)
    
    try:
        subprocess.run([
            str(python_path), "-m", "uvicorn", "main:app", 
            "--reload", "--host", "0.0.0.0", "--port", "8000"
        ], cwd=str(backend_dir))
    except KeyboardInterrupt:
        print_colored("\n🛑 Servidor detenido", Colors.WARNING)

def start_frontend():
    """Iniciar el servidor frontend"""
    print_header("Iniciando Servidor Frontend")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print_colored("❌ Directorio frontend no encontrado", Colors.FAIL)
        return False
    
    print_colored("🚀 Iniciando React/Next.js en http://localhost:3000", Colors.OKGREEN)
    print_colored("\n⏹️  Presiona Ctrl+C para detener el servidor\n", Colors.WARNING)
    
    try:
        subprocess.run(["npm", "run", "dev"], cwd=str(frontend_dir))
    except KeyboardInterrupt:
        print_colored("\n🛑 Servidor detenido", Colors.WARNING)

def show_status():
    """Mostrar estado del proyecto"""
    print_header("Estado del Proyecto")
    
    # Verificar estructura de directorios
    dirs_to_check = [
        ("backend", "Backend (FastAPI)"),
        ("frontend", "Frontend (React)"),
        ("backend/venv", "Entorno virtual Python"),
        ("backend/.env", "Configuración Backend"),
        ("frontend/.env.local", "Configuración Frontend")
    ]
    
    for dir_path, description in dirs_to_check:
        path = Path(dir_path)
        if path.exists():
            print_colored(f"✅ {description}: Configurado", Colors.OKGREEN)
        else:
            print_colored(f"❌ {description}: No encontrado", Colors.FAIL)
    
    # Verificar servicios
    print("\n🔗 URLs del proyecto:")
    print_colored("   🖥️  Frontend: http://localhost:3000", Colors.OKBLUE)
    print_colored("   🔌 Backend API: http://localhost:8000", Colors.OKBLUE)
    print_colored("   📚 Documentación: http://localhost:8000/docs", Colors.OKBLUE)

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="🔮 Autopublicador Web - Script de Configuración",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python setup.py check          # Verificar requisitos
  python setup.py setup          # Configuración completa
  python setup.py setup backend  # Solo backend
  python setup.py init-db        # Inicializar base de datos
  python setup.py start backend  # Iniciar servidor backend
  python setup.py status         # Ver estado del proyecto
        """
    )
    
    parser.add_argument(
        "command",
        choices=["check", "setup", "init-db", "start", "status"],
        help="Comando a ejecutar"
    )
    
    parser.add_argument(
        "target",
        nargs="?",
        choices=["backend", "frontend"],
        help="Objetivo específico (para setup y start)"
    )
    
    args = parser.parse_args()
    
    print_colored("🔮 Autopublicador Web - Setup Tool", Colors.HEADER + Colors.BOLD)
    print_colored("Plataforma de Generación de Contenido con IA\n", Colors.OKBLUE)
    
    try:
        if args.command == "check":
            check_requirements()
            
        elif args.command == "setup":
            if not check_requirements():
                sys.exit(1)
                
            if args.target == "backend":
                setup_backend()
            elif args.target == "frontend":
                setup_frontend()
            else:
                # Setup completo
                setup_backend()
                setup_frontend()
                print_header("Configuración Completada")
                print_colored("✅ Proyecto configurado correctamente", Colors.OKGREEN)
                print_colored("\n📋 Próximos pasos:", Colors.OKBLUE)
                print_colored("   1. Configurar API keys en backend/.env", Colors.OKBLUE)
                print_colored("   2. Ejecutar: python setup.py init-db", Colors.OKBLUE)
                print_colored("   3. Ejecutar: python setup.py start backend", Colors.OKBLUE)
                print_colored("   4. En otra terminal: python setup.py start frontend", Colors.OKBLUE)
                
        elif args.command == "init-db":
            init_database()
            
        elif args.command == "start":
            if args.target == "backend":
                start_backend()
            elif args.target == "frontend":
                start_frontend()
            else:
                print_colored("⚠️  Especifica 'backend' o 'frontend'", Colors.WARNING)
                print_colored("Ejemplo: python setup.py start backend", Colors.OKBLUE)
                
        elif args.command == "status":
            show_status()
            
    except KeyboardInterrupt:
        print_colored("\n\n🛑 Operación cancelada por el usuario", Colors.WARNING)
    except Exception as e:
        print_colored(f"\n❌ Error inesperado: {e}", Colors.FAIL)
        sys.exit(1)

if __name__ == "__main__":
    main()