# run.py (Blueprint Version)
import eventlet
eventlet.monkey_patch() # <-- Still first!

import os
from flask import Flask
from flask_socketio import SocketIO

import config
import utils

# --- Initialize Flask App ---
app = Flask(__name__,
            # Define app-wide template/static folders if they are shared
            template_folder=os.path.join('src', 'templates'),
            static_folder=os.path.join('src', 'static')
           )
app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY

# --- Initialize SocketIO ---
# IMPORTANT: Initialize SocketIO *before* importing routes that uses it for decorators
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# --- Import and Register Blueprint ---
# Import the blueprint *instance* from routes.py
# This import happens AFTER app and socketio exist.
# routes.py will in turn import 'socketio' from this file.
from routes import main_bp
app.register_blueprint(main_bp) # Register the blueprint with the Flask app

# --- Main Execution ---
if __name__ == '__main__':
    print("Ensuring audio directory exists...")
    utils.ensure_audio_dir_exists()
    print(f"Expecting static files in: {os.path.abspath(app.static_folder)}")
    print(f"Expecting templates in: {os.path.abspath(app.template_folder)}")

    print("\nRegistered routes:")
    print(app.url_map) # Now you should see '/' registered under the 'main' blueprint
    print("-" * 20)

    print("Starting Flask-SocketIO server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=True)