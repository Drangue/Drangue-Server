from app import app
from app.controllers import jobs_retrieve_handler, display_jobs_retrieve_handler, registeration_handler, login_handler, get_thumbnail, create_job, update_job, send_pending_email, send_confirmation_email,  send_failed_email, detect_handler, get_profile_handler, update_profile_handler, email_enquiry_handler
from flask import request, jsonify
from flask import redirect, url_for


@app.route('/')
def index():
    # Redirect users to drangue.ai
    return redirect("https://drangue.ai")


@app.route('/detect', methods=['POST'])
def detect():
    # Get JSON data from request
    data = request.json

    project = detect_handler(data)
    return project


@app.route('/user-jobs', methods=['POST'])
def get_job():
    # Get JSON data from request
    data = request.json

    jobs = jobs_retrieve_handler(data)
    return jobs


@app.route('/get-thumbnail', methods=['POST'])
def get_thumbnail_handler():
    # Get JSON data from request
    data = request.json

    job = get_thumbnail(data)

    return job


@app.route('/create-job', methods=['POST'])
def create_job_handler():
    # Get JSON data from request
    data = request.json

    job = create_job(data)

    return job


@app.route('/update-job', methods=['POST', "GET"])
def update_job_handler():
    # Get JSON data from request
    data = request.json
    job = update_job(data)

    return job


@app.route('/send-pending-email', methods=['POST'])
def send_pending_email_handler():
    # Get JSON data from request
    data = request.json

    print("user email details: ", data)

    data = data["email_payload"]

    job = send_pending_email(data)

    return job


@app.route('/send-confirmation-email', methods=['POST'])
def send_confirmation_email_handler():
    # Get JSON data from request
    data = request.json

    data = data["email_payload"]
    job = send_confirmation_email(data)

    return job


@app.route('/send-failed-email', methods=['POST'])
def send_failed_email_handler():
    # Get JSON data from request
    data = request.json

    data = data["email_payload"]
    job = send_failed_email(data)

    return job


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
        output = login_handler(credentials)
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


@app.route('/get-profile', methods=['POST'])
def get_profile():
    # Get JSON data from request
    data = request.json

    profile = get_profile_handler(data)
    return profile


@app.route('/update-profile', methods=['POST'])
def update_profile():
    # Get JSON data from request
    data = request.json

    updated_profile = update_profile_handler(data)
    return updated_profile


@app.route('/send-enquiry', methods=['POST'])
def email_enquiry():
    # Get JSON data from request
    data = request.json

    send_enquiry_email = email_enquiry_handler(data)
    return send_enquiry_email
