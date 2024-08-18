from app.controllers import process_detect
import asyncio
from app import app
from flask import request, jsonify, Blueprint

detection_type = "tree"

tree_bp = Blueprint(detection_type, __name__)
@tree_bp.route('/tree', methods=['GET', "POST"])
def landslide():
    if request.method == 'POST':
        api_key = request.form.get('api_key')
        file = request.files.get('file')

        if not api_key or not file:
            return jsonify({'error': 'Missing form data. Ensure api_key, and file are provided.'}), 400

        # validate api_key
        api_key_valid = True

        if api_key_valid:
            # Create a new event loop and run the async function
            result = process_detect(api_key, file, detection_type)
            return jsonify({'message': 'Processing was successful.', 'project_details': result}), 200
        else:
            return jsonify({'error': "Invalid data. Couldn't process"}), 400
    else:
        return jsonify({'error': 'Invalid request method. Use POST.'}), 405