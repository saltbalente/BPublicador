import sys
from pathlib import Path

# Add the backend directory to the Python path
# This allows gunicorn to find the 'main_simple' module
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Import the FastAPI app instance from the backend's main_simple module
from main_simple import app

# The 'app' variable is now exposed for gunicorn to discover and run.
# When Render runs `gunicorn app:app`, it will find this object.