# src/routes.py
from flask import Blueprint, render_template, request, jsonify
# from app import twilio_client # You might need to pass the client or get it globally

routes = Blueprint('routes', __name__)

@routes.route('/other_page')
def other_page():
    return "This is another page."



# The core routes like '/', '/initiate_call', '/twilio_...' are kept in app.py
# because they closely interact with the app instance and Telephony API setup.