import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://shardgupta65:Typer%401345@cluster0.sp87qsr.mongodb.net")
    MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "ai_agent_calls")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    # --- Telephony API (Example using Twilio) ---
    # You'll need account_sid and auth_token to initiate calls
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER") # Your Twilio number
    # Ensure your Flask app is accessible via public URL for webhooks (e.g., using ngrok)
    # This is the base URL Twilio will send requests to (e.g., https://YOUR_NGROK_URL)
    PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL")

    RECORDINGS_FOLDER = "recordings" # Folder to save call recordings locally (optional, Twilio stores them)