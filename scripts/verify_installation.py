#!/usr/bin/env python3
"""
Script de verificación de instalación para Autopublicador Web
Verifica que todos los componentes estén correctamente instalados y configurados
"""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path
import json
from typing import Dict, List, Tuple

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_status(message: str, status: str, details: str = ""):
    """Imprimir estado con formato"""
    if status == "OK":
        color = Colors.GREEN
        symbol = "✅"
    elif status == "WARNING":
        color = Colors.YELLOW
        symbol = "⚠️"
    elif status == "ERROR":
        color = Colors.RED
        symbol = "❌"
    else:
        color = Colors.BLUE
        symbol = "ℹ️"
    
    print(f"{symbol} {color}{message}{Colors.END}")
    if details:
        print(f"   {Colors.CYAN}{details}{Colors.END}")

def print_header(title: str):
    """Imprimir header de sección"""
    print(f"\n{Colors.BOLD}{Colors.PURPLE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.PURPLE}🔮 {title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.PURPLE}{'='*60}{Colors.END}\n")

def run_command(command: str, cwd: str = None, timeout: int = 30) -> Tuple[bool, str, str]:
    """Ejecutar comando y retornar resultado"""
    try:
        result = subprocess.run(
            command.split(),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def check_system_requirements() -> Dict[str, bool]:
    """Verificar requisitos del sistema"""
    print_header("Verificando Requisitos del Sistema")
    
    requirements = {
        "python3": "python3 --version",
        "node": "node --version",
        "npm": "npm --version",
        "git": "git --version"
    }
    
    results = {}
    
    for name, command in requirements.items():
        success, stdout, stderr = run_command(command)
        if success:
            version = stdout.strip().split('\n')[0]
            print_status(f"{name.capitalize()}", "OK", version)
            results[name] = True
        else:
            print_status(f"{name.capitalize()}", "ERROR", "No encontrado")
            results[name] = False
    
    return results

def check_project_structure() -> bool:
    """Verificar estructura del proyecto"""
    print_header("Verificando Estructura del Proyecto")
    
    required_files = [
        "README.md",
        "Makefile",
        "backend/main.py",
        "backend/requirements.txt",
        "backend/alembic.ini",
        "frontend/package.json",
        "frontend/app.js",
        "frontend/index.html"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print_status(f"Archivo: {file_path}", "OK")
        else:
            print_status(f"Archivo: {file_path}", "ERROR", "No encontrado")
            missing_files.append(file_path)
    
    if missing_files:
        print_status("Estructura del proyecto", "ERROR", f"Faltan {len(missing_files)} archivos")
        return False
    else:
        print_status("Estructura del proyecto", "OK", "Todos los archivos presentes")
        return True

def check_backend_setup() -> bool:
    """Verificar configuración del backend"""
    print_header("Verificando Configuración del Backend")
    
    backend_dir = Path("backend")
    
    # Verificar entorno virtual
    venv_path = backend_dir / "venv"
    if venv_path.exists():
        print_status("Entorno virtual", "OK", str(venv_path))
    else:
        print_status("Entorno virtual", "ERROR", "No encontrado")
        return False
    
    # Verificar archivo .env
    env_file = backend_dir / ".env"
    if env_file.exists():
        print_status("Archivo .env", "OK")
        
        # Verificar variables críticas
        with open(env_file, 'r') as f:
            env_content = f.read()
            
        critical_vars = ["SECRET_KEY", "DATABASE_URL"]
        for var in critical_vars:
            if var in env_content and not env_content.count(f"{var}=") == env_content.count(f"{var}=tu_"):
                print_status(f"Variable {var}", "OK")
            else:
                print_status(f"Variable {var}", "WARNING", "No configurada o usando valor por defecto")
    else:
        print_status("Archivo .env", "ERROR", "No encontrado")
        return False
    
    # Verificar dependencias de Python
    python_path = venv_path / "bin" / "python" if os.name != 'nt' else venv_path / "Scripts" / "python.exe"
    
    if python_path.exists():
        success, stdout, stderr = run_command(f"{python_path} -c \"import fastapi, uvicorn, sqlalchemy; print('Dependencies OK')\"")
        if success:
            print_status("Dependencias de Python", "OK")
        else:
            print_status("Dependencias de Python", "ERROR", stderr)
            return False
    
    return True

def check_frontend_setup() -> bool:
    """Verificar configuración del frontend"""
    print_header("Verificando Configuración del Frontend")
    
    frontend_dir = Path("frontend")
    
    # Verificar node_modules
    node_modules = frontend_dir / "node_modules"
    if node_modules.exists():
        print_status("Node modules", "OK")
    else:
        print_status("Node modules", "ERROR", "Ejecuta 'npm install' en el directorio frontend")
        return False
    
    # Verificar package.json
    package_json = frontend_dir / "package.json"
    if package_json.exists():
        print_status("Package.json", "OK")
        
        # Verificar scripts
        with open(package_json, 'r') as f:
            package_data = json.load(f)
            
        if "scripts" in package_data and "dev" in package_data["scripts"]:
            print_status("Script de desarrollo", "OK")
        else:
            print_status("Script de desarrollo", "WARNING", "Script 'dev' no encontrado")
    
    # Verificar archivo de configuración
    env_file = frontend_dir / ".env.local"
    if env_file.exists():
        print_status("Archivo .env.local", "OK")
    else:
        print_status("Archivo .env.local", "WARNING", "Archivo de configuración no encontrado")
    
    return True

def check_database() -> bool:
    """Verificar base de datos"""
    print_header("Verificando Base de Datos")
    
    backend_dir = Path("backend")
    python_path = backend_dir / "venv" / "bin" / "python" if os.name != 'nt' else backend_dir / "venv" / "Scripts" / "python.exe"
    
    if not python_path.exists():
        print_status("Base de datos", "ERROR", "Entorno virtual no encontrado")
        return False
    
    # Verificar que se puede importar la aplicación
    success, stdout, stderr = run_command(
        f"{python_path} -c \"from main import app; print('App import OK')\"",
        cwd=str(backend_dir)
    )
    
    if success:
        print_status("Importación de la aplicación", "OK")
    else:
        print_status("Importación de la aplicación", "ERROR", stderr)
        return False
    
    # Verificar migraciones
    success, stdout, stderr = run_command(
        f"{python_path} -m alembic current",
        cwd=str(backend_dir)
    )
    
    if success:
        print_status("Migraciones de base de datos", "OK", stdout.strip())
    else:
        print_status("Migraciones de base de datos", "WARNING", "Ejecuta 'alembic upgrade head'")
    
    return True

def check_services_running() -> Dict[str, bool]:
    """Verificar si los servicios están corriendo"""
    print_header("Verificando Servicios en Ejecución")
    
    services = {
        "Backend (8001)": "http://localhost:8001/ping",
        "Frontend (3000)": "http://localhost:3000"
    }
    
    results = {}
    
    for service_name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print_status(service_name, "OK", f"Respuesta: {response.status_code}")
                results[service_name] = True
            else:
                print_status(service_name, "WARNING", f"Respuesta: {response.status_code}")
                results[service_name] = False
        except requests.exceptions.ConnectionError:
            print_status(service_name, "ERROR", "Servicio no disponible")
            results[service_name] = False
        except requests.exceptions.Timeout:
            print_status(service_name, "ERROR", "Timeout")
            results[service_name] = False
        except Exception as e:
            print_status(service_name, "ERROR", str(e))
            results[service_name] = False
    
    return results

def check_api_endpoints() -> bool:
    """Verificar endpoints críticos de la API"""
    print_header("Verificando Endpoints de la API")
    
    base_url = "http://localhost:8001"
    endpoints = [
        "/ping",
        "/ready",
        "/docs",
        "/api/v1/auth/",
        "/api/v1/content/",
        "/api/v1/keywords/"
    ]
    
    all_ok = True
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 422]:  # 401/422 son OK para endpoints protegidos
                print_status(f"Endpoint {endpoint}", "OK", f"Status: {response.status_code}")
            else:
                print_status(f"Endpoint {endpoint}", "WARNING", f"Status: {response.status_code}")
                all_ok = False
        except Exception as e:
            print_status(f"Endpoint {endpoint}", "ERROR", str(e))
            all_ok = False
    
    return all_ok

def generate_report(results: Dict) -> None:
    """Generar reporte final"""
    print_header("Reporte Final de Verificación")
    
    total_checks = sum(len(v) if isinstance(v, dict) else 1 for v in results.values())
    passed_checks = sum(
        sum(v.values()) if isinstance(v, dict) else (1 if v else 0) 
        for v in results.values()
    )
    
    print(f"📊 {Colors.BOLD}Resumen:{Colors.END}")
    print(f"   Total de verificaciones: {total_checks}")
    print(f"   Verificaciones exitosas: {Colors.GREEN}{passed_checks}{Colors.END}")
    print(f"   Verificaciones fallidas: {Colors.RED}{total_checks - passed_checks}{Colors.END}")
    print(f"   Porcentaje de éxito: {Colors.BOLD}{(passed_checks/total_checks)*100:.1f}%{Colors.END}")
    
    if passed_checks == total_checks:
        print(f"\n🎉 {Colors.GREEN}{Colors.BOLD}¡Instalación completamente exitosa!{Colors.END}")
        print(f"   Tu Autopublicador Web está listo para usar.")
    elif passed_checks >= total_checks * 0.8:
        print(f"\n✅ {Colors.YELLOW}{Colors.BOLD}Instalación mayormente exitosa{Colors.END}")
        print(f"   Hay algunas advertencias menores, pero la aplicación debería funcionar.")
    else:
        print(f"\n⚠️ {Colors.RED}{Colors.BOLD}Instalación incompleta{Colors.END}")
        print(f"   Hay problemas que necesitan ser resueltos antes de usar la aplicación.")
    
    print(f"\n📚 {Colors.BLUE}Próximos pasos:{Colors.END}")
    print(f"   1. Si los servicios no están corriendo: make dev")
    print(f"   2. Configurar API keys en backend/.env")
    print(f"   3. Acceder a http://localhost:3000 (frontend)")
    print(f"   4. Acceder a http://localhost:8001/docs (API docs)")

def main():
    """Función principal"""
    print(f"{Colors.BOLD}{Colors.PURPLE}🔮 Verificador de Instalación - Autopublicador Web{Colors.END}\n")
    
    # Cambiar al directorio del proyecto si es necesario
    if not Path("backend").exists() and not Path("frontend").exists():
        print_status("Directorio del proyecto", "ERROR", "Ejecuta este script desde la raíz del proyecto")
        sys.exit(1)
    
    results = {}
    
    # Ejecutar todas las verificaciones
    results["system"] = check_system_requirements()
    results["structure"] = check_project_structure()
    results["backend"] = check_backend_setup()
    results["frontend"] = check_frontend_setup()
    results["database"] = check_database()
    results["services"] = check_services_running()
    
    # Solo verificar API si el backend está corriendo
    if results["services"].get("Backend (8001)", False):
        results["api"] = check_api_endpoints()
    
    # Generar reporte final
    generate_report(results)

if __name__ == "__main__":
    main()