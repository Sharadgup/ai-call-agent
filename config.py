# config.py
import os
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MONGODB_URI = os.getenv('MONGODB_URI')
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_change_me') # Provide a default

if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY environment variable")
if not MONGODB_URI:
    raise ValueError("Missing MONGODB_URI environment variable")