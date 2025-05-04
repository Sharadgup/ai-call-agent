from flask import Flask, render_template, request, jsonify, redirect, url_for
from config import Config
from src.routes import routes # Import routes Blueprint
from src.utils import save_call_record
from src.db import close_db, get_db # Import get_db if needed in app.py
import os

# Import Telephony API client (Example: Twilio)
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Start, Stream, Pause, Say

# --- Telephony API Client Setup ---
twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)

# --- Create Flask App ---
app = Flask(__name__, template_folder='src/templates', static_folder='src/static')
app.config.from_object(Config)

# Register blueprints (if you use them for routes)
# app.register_blueprint(routes) # If you put routes in src/routes.py as a Blueprint

# --- Routes (Can be in src/routes.py or here for simplicity) ---

@app.route('/')
def index():
    """Render the main page with the call form."""
    return render_template('index.html')

@app.route('/initiate_call', methods=['POST'])
def initiate_call():
    """Initiates an outbound call using the Telephony API."""
    data = request.json
    target_number = data.get('number')

    if not target_number:
        return jsonify({'status': 'error', 'message': 'Phone number is required'}), 400

    try:
        # Use the Telephony API to create the call
        # The 'url' is the webhook your server exposes to the Telephony API
        # This URL will be requested when the call connects to tell your app what to do
        call = twilio_client.calls.create(
            to=target_number,
            from_=Config.TWILIO_PHONE_NUMBER, # Your purchased Twilio number
            url=f'{Config.PUBLIC_BASE_URL}/twilio_voice_webhook', # Webhook for call instructions
            status_callback=f'{Config.PUBLIC_BASE_URL}/twilio_status_callback', # Webhook for status updates (optional but recommended)
            status_callback_event=['initiated', 'ringing', 'answered', 'completed', 'failed'],
            record=True, # Ask Twilio to record the call
            recording_status_callback=f'{Config.PUBLIC_BASE_URL}/twilio_recording_callback' # Webhook when recording is ready
        )

        # Save initial call record to DB
        call_id = save_call_record({
            'call_sid': call.sid,
            'target_number': target_number,
            'status': 'initiated',
            'twilio_status': call.status
        })

        print(f"Call initiated to {target_number} with SID: {call.sid}")

        return jsonify({
            'status': 'success',
            'message': f'Call initiated to {target_number}',
            'call_sid': call.sid,
            'db_id': str(call_id) if call_id else None # Convert ObjectId to string
        })

    except Exception as e:
        print(f"Error initiating call: {e}")
        return jsonify({'status': 'error', 'message': f'Failed to initiate call: {e}'}), 500

# --- Telephony API Webhook Handlers (Example: Twilio) ---

@app.route('/twilio_voice_webhook', methods=['POST'])
def twilio_voice_webhook():
    """
    This webhook is called by Twilio when the call connects.
    It returns TwiML instructions to Twilio to start the interaction.
    """
    response = VoiceResponse()

    # Initial greeting and setup for the first user input
    response.say("Hello! I am your AI agent. How can I help you today?")

    # Start gathering the first user response
    response.gather(
        input='speech',          # Listen for spoken words
        action='/twilio_gather_callback', # Send the transcribed speech here
        method='POST',
        speechTimeout='auto',    # Twilio automatically detects end of speech
        timeout=5,               # Max time to wait for any input before action (in seconds)
        language='en-US',        # Specify language
        # finishOnKey=''         # Optional: Remove or set to empty string if you don't want *any* key to interrupt speech
                                 # Default is '#'
    )

    # If the user doesn't say anything and the gather times out, redirect to a fallback
    response.redirect('/twilio_gather_fallback', method='POST')

    print("Returned initial TwiML with Gather.")
    print(str(response))
    return str(response), 200, {'Content-Type': 'text/xml'}


@app.route('/twilio_gather_callback', methods=['POST'])
def twilio_gather_callback():
    """
    This webhook is called by Twilio when <Gather> collects input (speech or DTMF).
    Process the user's input and return the AI's response.
    """
    # Get the collected input from Twilio's POST request
    # If input='speech', Twilio sends 'SpeechResult'
    # If input='dtmf', Twilio sends 'Digits'
    user_text = request.form.get('SpeechResult')
    digits = request.form.get('Digits')
    call_sid = request.form.get('CallSid')

    response = VoiceResponse()

    if user_text:
        print(f"Received transcribed speech for Call SID {call_sid}: {user_text}")

        # --- Process the user's text with your AI Agent ---
        # This is where you'd call your agent_run.py logic
        # You need to manage conversation state per call_sid (e.g., in a dict or DB)
        # For simplicity here, let's use a placeholder or a basic call to the agent function
        # from src.agent_run import process_user_audio_text # Assuming global state for demo
        # agent_response_text = process_user_audio_text(user_text)

        # In a real app, you'd need:
        # from src.agent_run import get_agent_for_call, process_audio_text_for_call
        # chat_session = get_agent_for_call(call_sid) # Get or create chat history for this call
        # agent_response_text = process_audio_text_for_call(call_sid, user_text) # Process and update history

        # Placeholder for AI response:
        agent_response_text = f"You said: {user_text}. I understand. What else would you like to know?" # Replace with actual AI call

        if agent_response_text:
            # Say the AI's response
            response.say(agent_response_text)

            # After speaking the response, *prompt the user again* by
            # starting another <Gather> to listen for their next input.
            response.gather(
                input='speech',
                action='/twilio_gather_callback', # Send next response back here
                method='POST',
                speechTimeout='auto',
                timeout=5,
                language='en-US',
                # finishOnKey=''
            )
            # If the next gather times out, redirect to fallback or hangup
            response.redirect('/twilio_gather_fallback', method='POST')

        else:
            # Handle cases where the AI doesn't produce a response
            response.say("I'm sorry, I couldn't generate a response at this time.")
            response.say("Please try again.")
            response.gather(
                input='speech',
                action='/twilio_gather_callback',
                method='POST',
                speechTimeout='auto',
                timeout=5,
                language='en-US',
                # finishOnKey=''
            )
            response.redirect('/twilio_gather_fallback', method='POST')


    elif digits:
        print(f"Received digits for Call SID {call_sid}: {digits}")
        # Handle DTMF input if necessary (e.g., press 1 for sales, 2 for support)
        # In a pure conversational AI, you might ignore DTMF or have a specific use case.
        response.say(f"You pressed {digits}. Let's continue the conversation.")
        # Re-prompt with gather after acknowledging digit
        response.gather(
            input='speech',
            action='/twilio_gather_callback',
            method='POST',
            speechTimeout='auto',
            timeout=5,
            language='en-US',
            # finishOnKey=''
        )
        response.redirect('/twilio_gather_fallback', method='POST')

    else:
        # This case shouldn't happen if speechTimeout or timeout triggers action,
        # but it's good for robustness. It means Gather finished but got no input.
        print(f"Gather completed with no input for Call SID {call_sid}.")
        response.say("I didn't hear anything.")
        # Re-prompt or end the call
        response.say("Are you still there?")
        response.gather(
            input='speech',
            action='/twilio_gather_callback',
            method='POST',
            speechTimeout='auto',
            timeout=5,
            language='en-US',
            # finishOnKey=''
        )
        response.redirect('/twilio_gather_fallback', method='POST')


    print(f"Returned TwiML for Gather callback: {str(response)}")
    return str(response), 200, {'Content-Type': 'text/xml'}


@app.route('/twilio_gather_fallback', methods=['POST'])
def twilio_gather_fallback():
    """
    This webhook is called if the <Gather> times out without any input
    and is configured with a redirect URL.
    """
    call_sid = request.form.get('CallSid')
    print(f"Gather fallback triggered for Call SID {call_sid}.")
    response = VoiceResponse()
    response.say("I apologize, I didn't receive any input.")
    response.say("Thank you for calling. Goodbye.")
    response.hangup()
    print(f"Returned TwiML for fallback: {str(response)}")
    return str(response), 200, {'Content-Type': 'text/xml'}


# ... (rest of your app.py like status_callback, recording_callback, etc.) ...

# --- Error Handling ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404 # You would create a 404.html template

# --- App Cleanup ---
@app.teardown_appcontext
def teardown_db(exception):
    """Closes the database connection when the app context tears down."""
    close_db()

# --- Run the App ---
if __name__ == '__main__':
    # Ensure the recordings directory exists
    os.makedirs(Config.RECORDINGS_FOLDER, exist_ok=True)

    # In development, use debug=True.
    # For production, use a production WSGI server like Gunicorn or uWSGI.
    # You also need to expose your Flask app to the internet for Telephony API webhooks (e.g., using ngrok)
    print(f"Flask app running. Ensure PUBLIC_BASE_URL ({Config.PUBLIC_BASE_URL}) is accessible for webhooks.")
    app.run(debug=True, port=5000)