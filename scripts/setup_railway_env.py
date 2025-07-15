#!/usr/bin/env python3
"""
Script para configurar variables de entorno para Railway
Genera comandos para configurar todas las variables necesarias
"""

import os
import secrets
import string
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def generate_secret_key(length=64):
    """Genera una clave secreta segura"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def print_header(title):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{title.center(60)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")

def print_section(title):
    print(f"\n{Colors.YELLOW}{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.YELLOW}{'-'*len(title)}{Colors.END}")

def main():
    print_header("CONFIGURACIÓN DE VARIABLES DE ENTORNO PARA RAILWAY")
    
    print(f"{Colors.BOLD}Este script te ayudará a configurar todas las variables necesarias.{Colors.END}")
    print(f"Copia y pega los comandos en la terminal de Railway o configúralas en la interfaz web.\n")
    
    # Variables críticas
    print_section("1. VARIABLES CRÍTICAS (OBLIGATORIAS)")
    
    secret_key = generate_secret_key()
    
    critical_vars = {
        'ENVIRONMENT': 'production',
        'SECRET_KEY': secret_key,
        'DEBUG': 'false',
        'LOG_LEVEL': 'info',
        'PORT': '8000'
    }
    
    print(f"{Colors.GREEN}# Configurar variables críticas:{Colors.END}")
    for var, value in critical_vars.items():
        if var == 'SECRET_KEY':
            print(f"railway variables set {var}='{value}'")
            print(f"{Colors.YELLOW}# ⚠️  IMPORTANTE: Guarda esta clave secreta en un lugar seguro{Colors.END}")
        else:
            print(f"railway variables set {var}={value}")
    
    # Variables de contenido
    print_section("2. VARIABLES DE CONFIGURACIÓN DE CONTENIDO")
    
    content_vars = {
        'DEFAULT_CONTENT_PROVIDER': 'deepseek',
        'CONTENT_LANGUAGE': 'es',
        'WRITING_STYLE': 'profesional',
        'ENABLE_IMAGE_GENERATION': 'true',
        'DEFAULT_IMAGE_PROVIDER': 'gemini',
        'MAX_CONTENT_LENGTH': '5000',
        'DEFAULT_CTA_COUNT': '2',
        'DEFAULT_PARAGRAPH_COUNT': '4'
    }
    
    print(f"{Colors.GREEN}# Configurar variables de contenido:{Colors.END}")
    for var, value in content_vars.items():
        print(f"railway variables set {var}={value}")
    
    # Variables de API (opcionales)
    print_section("3. VARIABLES DE API (OPCIONALES PERO RECOMENDADAS)")
    
    api_vars = {
        'DEEPSEEK_API_KEY': 'tu_api_key_de_deepseek_aqui',
        'OPENAI_API_KEY': 'sk-tu_api_key_de_openai_aqui',
        'GEMINI_API_KEY': 'tu_api_key_de_gemini_aqui'
    }
    
    print(f"{Colors.YELLOW}# Configura estas variables con tus API keys reales:{Colors.END}")
    for var, placeholder in api_vars.items():
        print(f"railway variables set {var}={placeholder}")
    
    print(f"\n{Colors.YELLOW}💡 Tip: Reemplaza los placeholders con tus API keys reales{Colors.END}")
    
    # Variables de seguridad
    print_section("4. VARIABLES DE SEGURIDAD ADICIONALES")
    
    security_vars = {
        'CORS_ORIGINS': 'https://tu-dominio.railway.app',
        'ALLOWED_HOSTS': 'tu-dominio.railway.app,localhost',
        'SECURE_COOKIES': 'true',
        'SESSION_TIMEOUT': '3600'
    }
    
    print(f"{Colors.GREEN}# Variables de seguridad (ajusta según tu dominio):{Colors.END}")
    for var, value in security_vars.items():
        print(f"railway variables set {var}={value}")
    
    # Servicios de Railway
    print_section("5. SERVICIOS DE RAILWAY (AUTOMÁTICOS)")
    
    print(f"{Colors.BLUE}Estos servicios se configuran automáticamente al agregarlos:{Colors.END}")
    print(f"\n{Colors.GREEN}# Agregar PostgreSQL:{Colors.END}")
    print("railway add postgresql")
    print(f"# Esto configurará automáticamente: DATABASE_URL")
    
    print(f"\n{Colors.GREEN}# Agregar Redis:{Colors.END}")
    print("railway add redis")
    print(f"# Esto configurará automáticamente: REDIS_URL")
    
    # Comandos de verificación
    print_section("6. VERIFICACIÓN")
    
    print(f"{Colors.GREEN}# Verificar variables configuradas:{Colors.END}")
    print("railway variables")
    
    print(f"\n{Colors.GREEN}# Ver logs durante el deployment:{Colors.END}")
    print("railway logs")
    
    print(f"\n{Colors.GREEN}# Hacer redeploy después de configurar variables:{Colors.END}")
    print("railway redeploy")
    
    # Instrucciones adicionales
    print_section("7. PASOS SIGUIENTES")
    
    steps = [
        "1. Ejecuta los comandos de variables críticas",
        "2. Agrega los servicios PostgreSQL y Redis",
        "3. Configura tus API keys reales",
        "4. Ejecuta el script de verificación: python scripts/railway_pre_deployment_check.py",
        "5. Haz commit y push de cualquier cambio",
        "6. Haz redeploy en Railway",
        "7. Verifica que la aplicación funcione correctamente"
    ]
    
    for step in steps:
        print(f"{Colors.YELLOW}  {step}{Colors.END}")
    
    # Información de contacto y troubleshooting
    print_section("8. TROUBLESHOOTING")
    
    print(f"{Colors.BLUE}Si tienes problemas:{Colors.END}")
    print(f"  • Revisa los logs: railway logs")
    print(f"  • Verifica variables: railway variables")
    print(f"  • Ejecuta verificación: python scripts/railway_pre_deployment_check.py")
    print(f"  • Consulta la guía: railway-deployment-guide.md")
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}¡Listo! Ahora puedes configurar tu proyecto en Railway.{Colors.END}")
    
    # Generar archivo .env.railway para referencia
    env_file = Path("../.env.railway.example")
    try:
        with open(env_file, 'w') as f:
            f.write("# Variables de entorno para Railway\n")
            f.write("# NO subas este archivo con valores reales\n\n")
            
            f.write("# Variables críticas\n")
            for var, value in critical_vars.items():
                if var == 'SECRET_KEY':
                    f.write(f"{var}=GENERAR_CLAVE_SECURA_AQUI\n")
                else:
                    f.write(f"{var}={value}\n")
            
            f.write("\n# Variables de contenido\n")
            for var, value in content_vars.items():
                f.write(f"{var}={value}\n")
            
            f.write("\n# API Keys (configurar con valores reales)\n")
            for var, value in api_vars.items():
                f.write(f"{var}={value}\n")
            
            f.write("\n# Variables de seguridad\n")
            for var, value in security_vars.items():
                f.write(f"{var}={value}\n")
            
            f.write("\n# Variables automáticas (configuradas por Railway)\n")
            f.write("DATABASE_URL=postgresql://...\n")
            f.write("REDIS_URL=redis://...\n")
        
        print(f"\n{Colors.GREEN}📄 Archivo de referencia creado: {env_file}{Colors.END}")
        
    except Exception as e:
        print(f"\n{Colors.YELLOW}⚠️  No se pudo crear archivo de referencia: {e}{Colors.END}")

if __name__ == "__main__":
    main()