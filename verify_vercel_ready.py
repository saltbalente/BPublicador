#!/usr/bin/env python3
"""
Script de verificación pre-despliegue para Vercel
Verifica que todos los archivos y configuraciones estén listos
"""

import os
import json
from pathlib import Path

def check_file_exists(file_path, description):
    """Verifica si un archivo existe"""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NO ENCONTRADO")
        return False

def check_vercel_config():
    """Verifica la configuración de Vercel"""
    print("🔍 Verificando configuración de Vercel...")
    
    vercel_file = "vercel.json"
    if not check_file_exists(vercel_file, "Configuración de Vercel"):
        return False
    
    try:
        with open(vercel_file, 'r') as f:
            config = json.load(f)
        
        # Verificar estructura básica
        required_keys = ["builds", "routes", "functions"]
        for key in required_keys:
            if key in config:
                print(f"✅ vercel.json contiene '{key}'")
            else:
                print(f"❌ vercel.json falta '{key}'")
                return False
        
        # Verificar build configuration
        builds = config.get("builds", [])
        if any(build.get("src") == "backend/main_vercel.py" for build in builds):
            print("✅ Build configurado para main_vercel.py")
        else:
            print("❌ Build no configurado para main_vercel.py")
            return False
        
        return True
        
    except json.JSONDecodeError:
        print("❌ vercel.json tiene formato JSON inválido")
        return False

def check_requirements():
    """Verifica los requirements para Vercel"""
    print("\n📦 Verificando dependencias...")
    
    req_file = "requirements-vercel.txt"
    if not check_file_exists(req_file, "Requirements para Vercel"):
        return False
    
    try:
        with open(req_file, 'r') as f:
            content = f.read()
        
        # Verificar dependencias críticas
        critical_deps = [
            "fastapi",
            "sqlalchemy",
            "psycopg2-binary",  # Para PostgreSQL
            "aiosqlite",        # Para SQLite
            "pydantic",
            "python-jose",
            "passlib"
        ]
        
        missing_deps = []
        for dep in critical_deps:
            if dep in content:
                print(f"✅ Dependencia encontrada: {dep}")
            else:
                print(f"❌ Dependencia faltante: {dep}")
                missing_deps.append(dep)
        
        return len(missing_deps) == 0
        
    except Exception as e:
        print(f"❌ Error leyendo requirements: {e}")
        return False

def check_vercel_files():
    """Verifica archivos específicos de Vercel"""
    print("\n📁 Verificando archivos de Vercel...")
    
    files_to_check = [
        ("backend/main_vercel.py", "Aplicación principal para Vercel"),
        ("backend/vercel_init.py", "Script de inicialización"),
        ("backend/config_production.py", "Configuración de producción"),
        ("backend/migrate_to_postgresql.py", "Script de migración PostgreSQL")
    ]
    
    all_exist = True
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    return all_exist

def check_models():
    """Verifica que todos los modelos estén presentes"""
    print("\n🗄️ Verificando modelos de base de datos...")
    
    models_dir = Path("backend/app/models")
    if not models_dir.exists():
        print("❌ Directorio de modelos no encontrado")
        return False
    
    required_models = [
        "user.py",
        "content.py", 
        "keyword.py",
        "landing_page.py",
        "scheduler_config.py",
        "__init__.py"
    ]
    
    all_exist = True
    for model in required_models:
        model_path = models_dir / model
        if model_path.exists():
            print(f"✅ Modelo encontrado: {model}")
        else:
            print(f"❌ Modelo faltante: {model}")
            all_exist = False
    
    return all_exist

def check_environment_template():
    """Verifica que exista template de variables de entorno"""
    print("\n🔧 Verificando configuración de entorno...")
    
    env_files = [
        (".env.example", "Template de variables de entorno"),
        (".env.production", "Variables de producción"),
        ("backend/.env.example", "Template backend")
    ]
    
    found_template = False
    for file_path, description in env_files:
        if check_file_exists(file_path, description):
            found_template = True
    
    if not found_template:
        print("⚠️ No se encontró ningún template de variables de entorno")
    
    return True  # No es crítico

def check_documentation():
    """Verifica que exista documentación de despliegue"""
    print("\n📚 Verificando documentación...")
    
    docs = [
        ("DEPLOY_VERCEL_COMPLETO.md", "Guía completa de despliegue"),
        ("SETUP_NEON_DATABASE.md", "Guía de configuración de base de datos"),
        ("README.md", "Documentación principal")
    ]
    
    all_exist = True
    for doc_path, description in docs:
        if not check_file_exists(doc_path, description):
            all_exist = False
    
    return all_exist

def print_summary(checks_passed, total_checks):
    """Imprime resumen final"""
    print("\n" + "="*60)
    print("📋 RESUMEN DE VERIFICACIÓN")
    print("="*60)
    
    if checks_passed == total_checks:
        print("🎉 ¡TODO LISTO PARA VERCEL!")
        print("\n✅ Verificaciones pasadas:")
        print("   - Configuración de Vercel")
        print("   - Dependencias optimizadas")
        print("   - Archivos de aplicación")
        print("   - Modelos de base de datos")
        print("   - Documentación completa")
        
        print("\n🚀 PRÓXIMOS PASOS:")
        print("   1. Configurar base de datos PostgreSQL (Neon)")
        print("   2. Configurar variables de entorno en Vercel")
        print("   3. Desplegar en Vercel")
        print("   4. Verificar funcionamiento")
        
        print("\n📖 GUÍAS DISPONIBLES:")
        print("   - DEPLOY_VERCEL_COMPLETO.md (guía paso a paso)")
        print("   - SETUP_NEON_DATABASE.md (configuración de DB)")
        
    else:
        print(f"⚠️ FALTAN {total_checks - checks_passed} VERIFICACIONES")
        print("\n❌ Corrige los errores antes de desplegar")
        print("💡 Revisa los archivos marcados como faltantes")

def main():
    """Función principal"""
    print("🔍 VERIFICACIÓN PRE-DESPLIEGUE PARA VERCEL")
    print("="*60)
    
    checks = [
        ("Configuración de Vercel", check_vercel_config),
        ("Requirements", check_requirements),
        ("Archivos de Vercel", check_vercel_files),
        ("Modelos de DB", check_models),
        ("Variables de entorno", check_environment_template),
        ("Documentación", check_documentation)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
            print()  # Línea en blanco entre secciones
        except Exception as e:
            print(f"❌ Error en verificación '{name}': {e}")
    
    print_summary(passed, total)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)