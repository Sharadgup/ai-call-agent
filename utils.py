# utils.py
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from gtts import gTTS
import uuid
import datetime
import config

# --- Configuration ---
# Define AUDIO_DIR relative to the project root where utils.py resides
AUDIO_DIR = os.path.join('src', 'static', 'audio')

def ensure_audio_dir_exists():
    """Ensures the audio directory exists."""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    print(f"Audio directory ensured at: {os.path.abspath(AUDIO_DIR)}")

# --- Database Setup ---
# (Database connection logic remains the same as before)
try:
    client = MongoClient(config.MONGODB_URI)
    db = client.ai_call_agent # Use a specific database name
    calls_collection = db.calls
    # Test connection
    client.admin.command('ping')
    print("MongoDB connection successful.")
except ConnectionFailure as e:
    print(f"MongoDB connection failed: {e}")
    raise
except Exception as e:
    print(f"An error occurred during MongoDB setup: {e}")
    raise

# --- Database Functions ---
# (create_call_record, add_message_to_log, end_call_record remain the same)
def create_call_record(phone_number):
    """Creates a new call record in MongoDB."""
    call_id = str(uuid.uuid4())
    start_time = datetime.datetime.utcnow()
    call_data = {
        "_id": call_id,
        "phone_number": phone_number,
        "start_time": start_time,
        "end_time": None,
        "status": "initiated", # e.g., initiated, active, ended, error
        "conversation_log": [],
        "last_updated": start_time
    }
    try:
        result = calls_collection.insert_one(call_data)
        print(f"Created call record with ID: {result.inserted_id}")
        return call_id
    except OperationFailure as e:
        print(f"Error creating call record in MongoDB: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error saving to MongoDB: {e}")
        return None


def add_message_to_log(call_id, speaker, text):
    """Adds a message to the conversation log for a specific call."""
    timestamp = datetime.datetime.utcnow()
    message = {
        "speaker": speaker, # "user" or "agent"
        "text": text,
        "timestamp": timestamp
    }
    try:
        result = calls_collection.update_one(
            {"_id": call_id},
            {
                "$push": {"conversation_log": message},
                "$set": {"last_updated": timestamp}
            }
        )
        if result.matched_count == 0:
            print(f"Warning: Call ID {call_id} not found for adding message.")
            return False
        print(f"Added message to log for call {call_id}. Speaker: {speaker}")
        return True
    except OperationFailure as e:
        print(f"Error updating call log in MongoDB for call {call_id}: {e}")
        return False
    except Exception as e:
         print(f"Unexpected error updating log for {call_id}: {e}")
         return False


def end_call_record(call_id, status="ended"):
    """Updates the call record to mark it as ended."""
    end_time = datetime.datetime.utcnow()
    try:
        result = calls_collection.update_one(
            {"_id": call_id},
            {
                "$set": {
                    "status": status,
                    "end_time": end_time,
                    "last_updated": end_time
                }
            }
        )
        if result.matched_count == 0:
             print(f"Warning: Call ID {call_id} not found for ending call.")
             return False
        print(f"Marked call {call_id} as {status}.")
        # Add a final system message to the log?
        add_message_to_log(call_id, "System", f"Call ended with status: {status}")
        return True
    except OperationFailure as e:
        print(f"Error ending call record in MongoDB for call {call_id}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error ending call {call_id}: {e}")
        return False

# --- Text-to-Speech Function ---
def text_to_speech(text, call_id, message_index):
    """Converts text to speech using gTTS and saves it to the correct audio dir."""
    ensure_audio_dir_exists() # Make sure directory exists before saving
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        filename = f"response_{call_id}_{message_index}.mp3"
        # Save the file to the correct path within src/static/audio
        filepath = os.path.join(AUDIO_DIR, filename)
        tts.save(filepath)
        print(f"Saved TTS audio to: {filepath}")
        # Return the web-accessible path fragment (relative to static folder)
        # This is what url_for('static', filename=...) will use
        return f"audio/{filename}"
    except Exception as e:
        print(f"Error during Text-to-Speech conversion or saving: {e}")
        return None

# --- Optional: Clean up old audio files ---
# (cleanup_old_audio_files remains the same, but operates on the correct AUDIO_DIR)
def cleanup_old_audio_files(max_age_days=1):
    """Removes audio files older than a specified number of days."""
    ensure_audio_dir_exists()
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=max_age_days)
    try:
        for filename in os.listdir(AUDIO_DIR):
            filepath = os.path.join(AUDIO_DIR, filename)
            if os.path.isfile(filepath):
                file_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_mod_time < cutoff:
                    os.remove(filepath)
                    print(f"Removed old audio file: {filename}")
    except Exception as e:
        print(f"Error during audio cleanup: {e}")