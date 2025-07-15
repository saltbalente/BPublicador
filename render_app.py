# render_app.py
# This file is a shim to make the app runnable by Render from the root directory.

from backend.main_simple import app

# The 'app' object is now exposed at the root level for Gunicorn to find.