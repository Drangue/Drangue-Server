from app import app
from app.controllers import process_request, detect_handler
from flask import request, jsonify

@app.route('/')
def index():
    # Simulating data received from request
    input_data = 10

    # Process request using controller function
    result = process_request(input_data)

    return f"Result: {result}"

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