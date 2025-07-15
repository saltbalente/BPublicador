#!/usr/bin/env python3
"""
Script de Verificación Pre-Deployment para Railway
Verifica que todo esté configurado correctamente antes de hacer deploy
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import importlib.util
from typing import List, Dict, Tuple

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class RailwayChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backend_path = self.project_root / "backend"
        self.frontend_path = self.project_root / "frontend"
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0

    def print_header(self, title: str):
        print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}{title.center(60)}{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")

    def print_check(self, description: str, status: bool, details: str = ""):
        self.total_checks += 1
        if status:
            self.success_count += 1
            print(f"{Colors.GREEN}✓{Colors.END} {description}")
            if details:
                print(f"  {Colors.GREEN}{details}{Colors.END}")
        else:
            print(f"{Colors.RED}✗{Colors.END} {description}")
            if details:
                print(f"  {Colors.RED}{details}{Colors.END}")
                self.errors.append(f"{description}: {details}")

    def print_warning(self, description: str, details: str = ""):
        print(f"{Colors.YELLOW}⚠{Colors.END} {description}")
        if details:
            print(f"  {Colors.YELLOW}{details}{Colors.END}")
            self.warnings.append(f"{description}: {details}")

    def check_file_exists(self, file_path: Path, description: str) -> bool:
        """Verifica que un archivo existe"""
        exists = file_path.exists()
        self.print_check(
            description,
            exists,
            f"Encontrado en: {file_path}" if exists else f"No encontrado: {file_path}"
        )
        return exists

    def check_railway_config_files(self):
        """Verifica archivos de configuración de Railway"""
        self.print_header("ARCHIVOS DE CONFIGURACIÓN RAILWAY")
        
        # Archivos críticos
        critical_files = [
            (self.project_root / "railway.toml", "railway.toml"),
            (self.project_root / "nixpacks.toml", "nixpacks.toml"),
            (self.project_root / "start.sh", "start.sh"),
            (self.backend_path / "main.py", "main.py (backend)"),
            (self.backend_path / "requirements.txt", "requirements.txt"),
        ]
        
        for file_path, description in critical_files:
            self.check_file_exists(file_path, description)

        # Verificar que start.sh sea ejecutable
        start_sh = self.project_root / "start.sh"
        if start_sh.exists():
            is_executable = os.access(start_sh, os.X_OK)
            self.print_check(
                "start.sh es ejecutable",
                is_executable,
                "Permisos correctos" if is_executable else "Ejecutar: chmod +x start.sh"
            )

    def check_python_dependencies(self):
        """Verifica dependencias de Python"""
        self.print_header("DEPENDENCIAS DE PYTHON")
        
        requirements_file = self.backend_path / "requirements.txt"
        if not requirements_file.exists():
            self.print_check("requirements.txt existe", False, "Archivo no encontrado")
            return

        # Leer requirements.txt
        try:
            with open(requirements_file, 'r') as f:
                requirements = f.read().strip().split('\n')
            
            critical_deps = [
                'fastapi',
                'uvicorn',
                'sqlalchemy',
                'alembic',
                'psycopg2-binary',
                'redis',
                'python-multipart',
                'jinja2'
            ]
            
            for dep in critical_deps:
                found = any(dep.lower() in req.lower() for req in requirements if req.strip())
                self.print_check(
                    f"Dependencia crítica: {dep}",
                    found,
                    "Encontrada" if found else "No encontrada en requirements.txt"
                )
                
        except Exception as e:
            self.print_check("Lectura de requirements.txt", False, str(e))

    def check_main_app_structure(self):
        """Verifica la estructura de la aplicación principal"""
        self.print_header("ESTRUCTURA DE LA APLICACIÓN")
        
        main_py = self.backend_path / "main.py"
        if not main_py.exists():
            self.print_check("main.py existe", False, "Archivo principal no encontrado")
            return

        try:
            # Verificar que main.py se puede importar
            sys.path.insert(0, str(self.backend_path))
            
            # Leer el contenido de main.py
            with open(main_py, 'r') as f:
                content = f.read()
            
            # Verificar elementos críticos
            checks = [
                ('app = FastAPI', 'Instancia de FastAPI'),
                ('@app.get("/ping")', 'Endpoint /ping'),
                ('@app.get("/ready")', 'Endpoint /ready'),
                ('@app.get("/healthz")', 'Endpoint /healthz'),
                ('mount', 'Archivos estáticos montados'),
            ]
            
            for pattern, description in checks:
                found = pattern in content
                self.print_check(
                    description,
                    found,
                    "Configurado" if found else f"No encontrado: {pattern}"
                )
                
        except Exception as e:
            self.print_check("Análisis de main.py", False, str(e))

    def check_database_migrations(self):
        """Verifica configuración de migraciones de base de datos"""
        self.print_header("MIGRACIONES DE BASE DE DATOS")
        
        alembic_ini = self.backend_path / "alembic.ini"
        alembic_dir = self.backend_path / "alembic"
        versions_dir = alembic_dir / "versions"
        
        self.check_file_exists(alembic_ini, "alembic.ini")
        self.check_file_exists(alembic_dir / "env.py", "alembic/env.py")
        
        if versions_dir.exists():
            migration_files = list(versions_dir.glob("*.py"))
            migration_count = len([f for f in migration_files if f.name != "__pycache__"])
            self.print_check(
                "Archivos de migración",
                migration_count > 0,
                f"Encontradas {migration_count} migraciones" if migration_count > 0 else "No hay migraciones"
            )

    def check_environment_variables(self):
        """Verifica variables de entorno críticas"""
        self.print_header("VARIABLES DE ENTORNO")
        
        # Variables críticas para Railway
        critical_vars = {
            'SECRET_KEY': 'Clave secreta para JWT y sesiones',
            'ENVIRONMENT': 'Entorno de ejecución (production)',
            'DEBUG': 'Modo debug (debe ser false en producción)'
        }
        
        # Variables opcionales pero importantes
        optional_vars = {
            'DATABASE_URL': 'URL de base de datos PostgreSQL',
            'REDIS_URL': 'URL de Redis',
            'DEEPSEEK_API_KEY': 'API key para DeepSeek',
            'OPENAI_API_KEY': 'API key para OpenAI',
            'GEMINI_API_KEY': 'API key para Gemini'
        }
        
        # Verificar variables críticas
        for var, description in critical_vars.items():
            value = os.getenv(var)
            has_value = value is not None and value.strip() != ''
            
            if var == 'SECRET_KEY' and has_value:
                # Verificar que no sea el valor por defecto
                is_default = 'changeme' in value.lower() or 'default' in value.lower() or len(value) < 32
                self.print_check(
                    f"{var} configurado",
                    has_value and not is_default,
                    "Configurado correctamente" if (has_value and not is_default) else "Usar clave segura en producción"
                )
            else:
                self.print_check(
                    f"{var} configurado",
                    has_value,
                    f"Valor: {value[:20]}..." if has_value else "No configurado"
                )
        
        # Verificar variables opcionales
        print(f"\n{Colors.YELLOW}Variables opcionales:{Colors.END}")
        for var, description in optional_vars.items():
            value = os.getenv(var)
            has_value = value is not None and value.strip() != ''
            status = "✓" if has_value else "○"
            color = Colors.GREEN if has_value else Colors.YELLOW
            print(f"  {color}{status}{Colors.END} {var}: {description}")

    def check_git_status(self):
        """Verifica el estado de Git"""
        self.print_header("ESTADO DE GIT")
        
        try:
            # Verificar si estamos en un repositorio git
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                uncommitted = result.stdout.strip()
                self.print_check(
                    "Repositorio Git inicializado",
                    True,
                    "Repositorio encontrado"
                )
                
                self.print_check(
                    "Todos los cambios committeados",
                    not uncommitted,
                    "Working tree clean" if not uncommitted else f"Archivos sin commit: {len(uncommitted.split())} archivos"
                )
                
                # Verificar rama actual
                branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                             capture_output=True, text=True, cwd=self.project_root)
                if branch_result.returncode == 0:
                    current_branch = branch_result.stdout.strip()
                    print(f"  {Colors.BLUE}Rama actual: {current_branch}{Colors.END}")
                    
            else:
                self.print_check("Repositorio Git", False, "No es un repositorio Git")
                
        except FileNotFoundError:
            self.print_check("Git instalado", False, "Git no encontrado en el sistema")
        except Exception as e:
            self.print_check("Verificación de Git", False, str(e))

    def check_railway_specific_requirements(self):
        """Verifica requisitos específicos de Railway"""
        self.print_header("REQUISITOS ESPECÍFICOS DE RAILWAY")
        
        # Verificar configuración en railway.toml
        railway_toml = self.project_root / "railway.toml"
        if railway_toml.exists():
            try:
                with open(railway_toml, 'r') as f:
                    content = f.read()
                
                checks = [
                    ('healthcheckPath', 'Health check path configurado'),
                    ('healthcheckTimeout', 'Timeout de health check configurado'),
                    ('startCommand', 'Comando de inicio configurado'),
                    ('restartPolicyType', 'Política de reinicio configurada')
                ]
                
                for pattern, description in checks:
                    found = pattern in content
                    self.print_check(
                        description,
                        found,
                        "Configurado" if found else f"Falta configuración: {pattern}"
                    )
                    
            except Exception as e:
                self.print_check("Análisis de railway.toml", False, str(e))
        
        # Verificar que el puerto sea configurable
        start_sh = self.project_root / "start.sh"
        if start_sh.exists():
            try:
                with open(start_sh, 'r') as f:
                    content = f.read()
                
                port_configurable = '$PORT' in content or '${PORT}' in content
                self.print_check(
                    "Puerto configurable via $PORT",
                    port_configurable,
                    "Configurado" if port_configurable else "start.sh debe usar variable $PORT"
                )
                
                host_binding = '--host 0.0.0.0' in content
                self.print_check(
                    "Binding a todas las interfaces (0.0.0.0)",
                    host_binding,
                    "Configurado" if host_binding else "Debe usar --host 0.0.0.0"
                )
                
            except Exception as e:
                self.print_check("Análisis de start.sh", False, str(e))

    def run_test_import(self):
        """Intenta importar la aplicación para verificar que no hay errores"""
        self.print_header("TEST DE IMPORTACIÓN")
        
        try:
            # Cambiar al directorio backend
            original_cwd = os.getcwd()
            os.chdir(self.backend_path)
            
            # Intentar importar la aplicación
            result = subprocess.run(
                [sys.executable, '-c', 'from main import app; print("✓ Import successful")'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            self.print_check(
                "Importación de la aplicación",
                success,
                "Aplicación se importa correctamente" if success else f"Error: {result.stderr}"
            )
            
            if success:
                # Test adicional de endpoints
                endpoint_test = subprocess.run(
                    [sys.executable, '-c', '''
from main import app
routes = [route.path for route in app.routes if hasattr(route, "path")]
health_endpoints = ["/ping", "/ready", "/healthz"]
for endpoint in health_endpoints:
    if endpoint not in routes:
        print(f"Missing: {endpoint}")
        exit(1)
print("✓ All health endpoints found")
'''],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                endpoints_ok = endpoint_test.returncode == 0
                self.print_check(
                    "Endpoints de health check",
                    endpoints_ok,
                    "Todos los endpoints configurados" if endpoints_ok else f"Error: {endpoint_test.stderr}"
                )
            
        except subprocess.TimeoutExpired:
            self.print_check("Test de importación", False, "Timeout - la aplicación tarda mucho en cargar")
        except Exception as e:
            self.print_check("Test de importación", False, str(e))
        finally:
            os.chdir(original_cwd)

    def generate_summary(self):
        """Genera un resumen final"""
        self.print_header("RESUMEN FINAL")
        
        success_rate = (self.success_count / self.total_checks * 100) if self.total_checks > 0 else 0
        
        print(f"\n{Colors.BOLD}Estadísticas:{Colors.END}")
        print(f"  ✓ Verificaciones exitosas: {Colors.GREEN}{self.success_count}{Colors.END}")
        print(f"  ✗ Verificaciones fallidas: {Colors.RED}{self.total_checks - self.success_count}{Colors.END}")
        print(f"  ⚠ Advertencias: {Colors.YELLOW}{len(self.warnings)}{Colors.END}")
        print(f"  📊 Tasa de éxito: {Colors.GREEN if success_rate >= 90 else Colors.YELLOW if success_rate >= 70 else Colors.RED}{success_rate:.1f}%{Colors.END}")
        
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}Errores críticos que deben resolverse:{Colors.END}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {Colors.RED}{error}{Colors.END}")
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}Advertencias (recomendado resolver):{Colors.END}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {Colors.YELLOW}{warning}{Colors.END}")
        
        # Recomendación final
        if success_rate >= 90 and not self.errors:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ¡LISTO PARA DEPLOYMENT!{Colors.END}")
            print(f"{Colors.GREEN}Tu proyecto está bien configurado para Railway.{Colors.END}")
        elif success_rate >= 70:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  CASI LISTO{Colors.END}")
            print(f"{Colors.YELLOW}Resuelve los errores críticos antes del deployment.{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ NO LISTO PARA DEPLOYMENT{Colors.END}")
            print(f"{Colors.RED}Hay varios problemas que deben resolverse.{Colors.END}")
        
        return success_rate >= 90 and not self.errors

    def run_all_checks(self):
        """Ejecuta todas las verificaciones"""
        print(f"{Colors.BOLD}🚀 VERIFICACIÓN PRE-DEPLOYMENT PARA RAILWAY{Colors.END}")
        print(f"Proyecto: {self.project_root}")
        
        # Ejecutar todas las verificaciones
        self.check_railway_config_files()
        self.check_python_dependencies()
        self.check_main_app_structure()
        self.check_database_migrations()
        self.check_environment_variables()
        self.check_git_status()
        self.check_railway_specific_requirements()
        self.run_test_import()
        
        # Generar resumen
        return self.generate_summary()

def main():
    """Función principal"""
    checker = RailwayChecker()
    ready_for_deployment = checker.run_all_checks()
    
    # Exit code para scripts automatizados
    sys.exit(0 if ready_for_deployment else 1)

if __name__ == "__main__":
    main()