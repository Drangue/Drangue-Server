from functools import wraps
from flask import request, jsonify
from app.models.FirebaseHandler import FirebaseHandler


def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the API key from the request headers
        api_key = request.headers.get('X-API-KEY')

        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401
        
        firebase_handler = FirebaseHandler()
        if not firebase_handler.check_user_api_key(api_key):
            return jsonify({'error': 'Invalid API key'})

        return f(*args, **kwargs)

    return decorated_function