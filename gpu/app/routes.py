from app import app
from app.controllers import detect_handler
from flask import request, jsonify
from flask import redirect, url_for


@app.route('/detect', methods=['POST'])
def detect():
    # Get JSON data from request
    data = request.json
    print(data)

    # Check if 'features' array exists in JSON data
    if 'polygons' in data and isinstance(data['polygons'], list):
        # Process features using controller function
        result = detect_handler(data)
    
        # Return the result as JSON
        return jsonify({'result': result})
    else:
        # If 'features' array is missing or not a list, return an error response
        return jsonify({'error': 'Invalid JSON data. Expected "features" array.'}), 400
    

