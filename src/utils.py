from config import Config
import google.generativeai as genai
import os
import datetime
from src.db import get_db

# Configure Gemini API
genai.configure(api_key=Config.GEMINI_API_KEY)

# Helper function to get the Gemini model
def get_gemini_model():
    """Returns the Gemini conversational model."""
    # Use a suitable model for conversational AI
    # Consider models optimized for chat or low-latency
    try:
        model = genai.GenerativeModel('gemini-1.5-flash') # Or 'gemini-pro' or other suitable model
        return model
    except Exception as e:
        print(f"Error configuring Gemini model: {e}")
        return None

# Helper function to save call details to MongoDB
def save_call_record(call_data):
    """Saves call details to the MongoDB database."""
    db = get_db()
    calls_collection = db.calls
    call_data['timestamp'] = datetime.datetime.utcnow()
    try:
        result = calls_collection.insert_one(call_data)
        print(f"Call record saved with id: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        print(f"Error saving call record: {e}")
        return None

# Ensure recordings folder exists
if not os.path.exists(Config.RECORDINGS_FOLDER):
    os.makedirs(Config.RECORDINGS_FOLDER)