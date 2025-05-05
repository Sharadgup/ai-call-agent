# agent.py
import google.generativeai as genai
import config
import utils # To access DB functions if needed, e.g., conversation history

# Configure the Gemini API client
try:
    genai.configure(api_key=config.GEMINI_API_KEY)
    # Choose the model - 'gemini-pro' is good for chat-like interactions
    model = genai.GenerativeModel('gemini-pro')
    print("Gemini AI model initialized successfully.")
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    # Handle error appropriately - maybe the app can't function without AI
    raise

# In-memory storage for conversation history *per call*
# A more robust solution might store this in the DB or a dedicated cache (Redis)
# Format: { call_id: genai.ChatSession }
active_chats = {}

def start_chat_session(call_id):
    """Starts a new chat session for a given call ID."""
    if call_id in active_chats:
        print(f"Chat session already exists for call {call_id}")
        # Optionally, return the existing session or reset it
        # For now, let's just use the existing one
        return active_chats[call_id]
    else:
        print(f"Starting new chat session for call {call_id}")
        # You can add system instructions or initial context here if needed
        # chat = model.start_chat(history=[{'role':'user', 'parts': [""]}, {'role':'model', 'parts': [""]}]) # Example priming
        chat = model.start_chat(history=[]) # Start fresh
        active_chats[call_id] = chat
        return chat

def end_chat_session(call_id):
    """Removes the chat session from memory when a call ends."""
    if call_id in active_chats:
        print(f"Ending chat session for call {call_id}")
        del active_chats[call_id]
    else:
        print(f"No active chat session found to end for call {call_id}")


def get_gemini_response(call_id, user_text):
    """Gets a response from the Gemini model for a given call session."""
    if call_id not in active_chats:
        print(f"Error: No active chat session found for call {call_id}. Starting a new one.")
        # Attempt to recover by starting a new session, though context is lost
        start_chat_session(call_id)
        # It might be better to return an error message here instead
        # return "Error: Conversation context lost. Please restart."

    chat = active_chats[call_id]

    try:
        print(f"Sending to Gemini (Call {call_id}): {user_text}")
        # Send the user's message to the chat session
        response = chat.send_message(user_text) # Use stream=True for chunking if needed

        # Extract the text response
        ai_response_text = response.text
        print(f"Received from Gemini (Call {call_id}): {ai_response_text}")
        return ai_response_text

    except Exception as e:
        print(f"Error getting response from Gemini API for call {call_id}: {e}")
        # You might want specific error handling based on Gemini API errors
        # For now, return a generic error message
        return "Sorry, I encountered an error trying to process that."