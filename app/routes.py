from app import app
from app.controllers import process_request, detect_handler, jobs_retrieve_handler,display_jobs_retrieve_handler, registeration_handler, login_handler
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
    
    
@app.route('/user-jobs', methods=['POST'])
def get_job():
    # Get JSON data from request
    data = request.json

    jobs = jobs_retrieve_handler(data)
    print(jobs)
    return jobs

@app.route('/job-display', methods=['POST'])
def get_jobs():
    # Get JSON data from request
    data = request.json

    job = display_jobs_retrieve_handler(data)
    
    return job


@app.route('/login', methods=['POST', 'GET'],)
def login():
    try:
        # Get the JSON data from the request
        credentials = request.json
        print("credentials data: ", credentials)
        output  = login_handler(credentials)
        return output

    except Exception as e:
        return jsonify({'error': str(e), "authenticated": False}), 400
    
    
@app.route('/register', methods=['POST', 'GET'],)
def register():
    try:
        # Get the JSON data from the request
        credentials = request.json
        print("credentials data: ", credentials)
        output = registeration_handler(credentials)
        return output
        
     
    except Exception as e:
        return jsonify({'error': str(e), "authenticated": True}), 400



