# routes.py (Blueprint Version)
print("--- routes.py executed (Blueprint Version) ---") # Add this line for debug
import os
import time
from flask import (
    Blueprint, render_template, request, jsonify, url_for, session
)
from flask_socketio import emit # Use emit directly from flask_socketio

# Import necessary components from other modules
import utils
import agent

# --- Create Blueprint ---
# The first argument 'main' is the blueprint's name.
# The second argument __name__ helps locate the blueprint's root path.
main_bp = Blueprint('main', __name__,
                    template_folder='../src/templates', # Path relative to this file (routes.py)
                    static_folder='../src/static'       # Path relative to this file (routes.py)
                    )
# Note: If your static/templates are ONLY used by this blueprint, define them here.
# If they are shared application-wide, it's often better to define them
# on the main Flask app in run.py and remove template_folder/static_folder here.
# Let's assume they are app-wide for now and remove these lines:
# main_bp = Blueprint('main', __name__)


# Track message index per call for unique TTS filenames
call_message_counters = {}

# --- HTTP Route (using the Blueprint) ---
@main_bp.route('/')
def index():
    """Serves the main HTML page."""
    # render_template will now look in the app's template folder first
    return render_template('index.html')


# --- SocketIO Event Handlers ---
# We need the 'socketio' instance to attach handlers.
# We will import it from run.py. Blueprints help manage the import order.
from run import socketio # Import socketio instance here

@socketio.on('connect')
def handle_connect():
    """Handles new client connections."""
    sid = request.sid # SocketIO makes request context available
    print(f"Client connected: {sid}")
    emit('status_update', {'message': 'Connected to server.'}, room=sid) # Emit to the specific client

@socketio.on('disconnect')
def handle_disconnect():
    """Handles client disconnections."""
    sid = request.sid
    print(f"Client disconnected: {sid}")
    # You might want to clean up resources associated with 'sid' if needed
    # e.g., find the call_id associated with this sid and end it.
    # This requires storing the sid <-> call_id mapping somewhere (e.g., a dictionary)

@socketio.on('start_call')
def handle_start_call(data):
    """Handles the request to start a new call simulation."""
    phone_number = data.get('number')
    sid = request.sid
    print(f"Received start_call request from {sid} for number: {phone_number}")

    if not phone_number:
        emit('call_started', {'status': 'error', 'message': 'Phone number is required.'}, room=sid)
        return

    call_id = utils.create_call_record(phone_number)

    if call_id:
        call_message_counters[call_id] = 0
        agent.start_chat_session(call_id)
        # Optional: Store sid -> call_id mapping for cleanup on disconnect
        # active_sessions[sid] = call_id
        print(f"Call simulation started successfully. Call ID: {call_id}")
        emit('call_started', {
            'status': 'success',
            'call_id': call_id,
            'number': phone_number,
        }, room=sid)
    else:
        print("Failed to create call record in database.")
        emit('call_started', {'status': 'error', 'message': 'Failed to initialize call.'}, room=sid)

@socketio.on('audio_input')
def handle_audio_input(data):
    """Handles transcribed audio text from the client."""
    user_text = data.get('text')
    call_id = data.get('call_id')
    sid = request.sid

    print(f"Received audio_input from {sid} for call {call_id}: '{user_text}'")

    if not call_id or not user_text:
        emit('status_update', {'message': 'Error: Missing call ID or text.'}, room=sid)
        return

    # Check if call is still active / counter exists (add safety)
    if call_id not in call_message_counters:
        print(f"Warning: Received audio for inactive/unknown call ID {call_id}")
        emit('status_update', {'message': 'Error: Call session not active.'}, room=sid)
        return

    utils.add_message_to_log(call_id, "User", user_text)
    emit('status_update', {'message': 'Getting response from AI...'}, room=sid)
    ai_response_text = agent.get_gemini_response(call_id, user_text)

    if ai_response_text:
        utils.add_message_to_log(call_id, "Agent", ai_response_text)
        emit('status_update', {'message': 'Generating AI speech...'}, room=sid)

        # Increment message counter
        call_message_counters[call_id] += 1
        message_index = call_message_counters[call_id]

        audio_filename_fragment = utils.text_to_speech(ai_response_text, call_id, message_index)

        if audio_filename_fragment:
            # url_for is context-aware and works fine within request handlers
            audio_url = url_for('static', filename=audio_filename_fragment, _external=False)
            print(f"Sending agent_response to {sid} for call {call_id}. Audio URL: {audio_url}")
            emit('agent_response', {
                'text': ai_response_text,
                'audio_url': audio_url
            }, room=sid)
        else:
            emit('status_update', {'message': 'Error generating AI speech.'}, room=sid)
            # Optionally send text only if TTS fails
            # emit('agent_response', {'text': ai_response_text, 'audio_url': None}, room=sid)
    else:
        emit('status_update', {'message': 'Error getting AI response.'}, room=sid)


@socketio.on('end_call')
def handle_end_call(data):
    """Handles the request to end the call simulation."""
    call_id = data.get('call_id')
    sid = request.sid
    print(f"Received end_call request from {sid} for call {call_id}")

    if not call_id:
        emit('status_update', {'message': 'Error: Missing call ID for ending call.'}, room=sid)
        return

    # Check if call exists before trying to end
    if call_id in call_message_counters:
        agent.end_chat_session(call_id)
        utils.end_call_record(call_id, status="ended_by_user")
        del call_message_counters[call_id]
        # Optional: remove sid -> call_id mapping
        # if sid in active_sessions and active_sessions[sid] == call_id:
        #    del active_sessions[sid]
        emit('call_ended', {'call_id': call_id, 'reason': 'User ended call'}, room=sid)
        print(f"Call simulation {call_id} ended by user {sid}.")
    else:
        print(f"Warning: Attempted to end non-existent or already ended call {call_id}")
        emit('call_ended', {'call_id': call_id, 'reason': 'Call already ended or invalid ID'}, room=sid)
        # Ensure client UI resets even if server state was weird