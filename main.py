#!/usr/bin/env python3
"""
Punto de entrada principal para Railway deployment.
Este archivo importa la aplicación desde el directorio backend.
"""

import sys
import os

# Agregar el directorio backend al path de Python
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Cambiar el directorio de trabajo al backend
os.chdir(backend_path)

# Importar la aplicación desde backend/main.py
from main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)