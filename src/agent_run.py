from src.utils import get_gemini_model, save_call_record
import time # For simulating delays

# --- Conversation State Management ---
# In a real application with concurrent calls, you would need
# a dictionary or database to store conversation state per call ID.
# For this example, we'll simulate a single conversation.

conversation_history = [] # Stores messages for Gemini context

def initialize_agent():
    """Initializes the Gemini model for a new conversation."""
    global conversation_history
    conversation_history = [] # Reset history for a new call
    model = get_gemini_model()
    if model:
        print("Gemini agent initialized.")
        return model.start_chat(history=conversation_history)
    else:
        print("Failed to initialize Gemini agent.")
        return None

def process_user_audio_text(user_text):
    """
    Processes the user's transcribed text, interacts with Gemini,
    and returns the agent's text response.
    """
    global conversation_history

    if not user_text or user_text.strip() == "":
        print("Received empty user text.")
        return "I didn't quite catch that. Could you please repeat?"

    print(f"User says: {user_text}")

    chat_session = get_gemini_model().start_chat(history=conversation_history)

    try:
        # Send user's text to Gemini
        response = chat_session.send_message(user_text)

        # Add to conversation history
        conversation_history.append({"role": "user", "parts": [user_text]})
        conversation_history.append({"role": "model", "parts": [response.text]})

        print(f"Agent responds: {response.text}")
        return response.text

    except Exception as e:
        print(f"Error interacting with Gemini API: {e}")
        # Simple error response
        return "I'm sorry, I encountered an error. Could you please try again?"

# Note: Real-time voice requires integrating this with STT/TTS
# and the Telephony API's audio stream webhooks.
# This function only handles the text processing part.
# The audio_processor.py (conceptual) would wrap this.

# Example of how state would be managed with a call ID:
# call_states = {} # { 'call_sid': chat_session }
# def get_agent_for_call(call_sid):
#     if call_sid not in call_states:
#         model = get_gemini_model()
#         if model:
#             call_states[call_sid] = model.start_chat(history=[])
#             print(f"Initialized agent for call {call_sid}")
#         else:
#              return None # Handle error
#     return call_states[call_sid]

# def process_audio_for_call(call_sid, user_text):
#    chat_session = get_agent_for_call(call_sid)
#    if chat_session:
#       # ... interact with Gemini using chat_session ...
#       # Update chat_session.history and potentially store it
#       pass