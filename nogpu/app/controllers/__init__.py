import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

from flask import jsonify
from app.models.FirebaseHandler import FirebaseHandler
from app.services.EmailSender import EmailSender
import threading
import requests


firebase_handler = FirebaseHandler()
emailSender = EmailSender()

# Load environment variables from .env file
load_dotenv()

# Get the BASE_ENDPOINT variable
base_endpoint = os.getenv('BASE_ENDPOINT')


def send_request(json_data, endpoint_path):
    try:
        # Combine the base endpoint with the specific endpoint path
        full_url = base_endpoint + endpoint_path

        # Send the JSON data to the full URL
        response = requests.post(full_url, json=json_data)
        print(response)

        # Raise an error if the request was unsuccessful
        response.raise_for_status()

        print("end point called", response.json())

        # Get the JSON response from the endpoint
        return response.json()

    except requests.exceptions.RequestException as e:
        # Handle any errors that occur during the request
        print("end point called, but error", str(e))
        return {'error': str(e)}


def detect_handler(project_payload):

    # check api_key

    try:
        project_detection = send_request(project_payload, "/v1/detect/all")
        # check return output

        # Success
        # Failed
        # Invalid Api Key
        # Already Exceeded credit limit
    except:
        raise Exception("Couldn't Create The Project")

    if not project_detection:
        raise Exception("Authentication failed")

    return jsonify({'message': 'Project Created successfully'}), 200


def get_thumbnail(center_coords_payload):
    center_coords = center_coords_payload.get("center_coords", (0, 0))
    thumbnail = firebase_handler.get_thumbnail(center_coords)

    return jsonify({'thumbnail': thumbnail})


def create_job(job_payload):
    job_payload = job_payload.get("job_payload")
    # Extract variables from job_payload dictionary
    userid = job_payload.get('userid')
    jobid = job_payload.get('jobid')
    startTime = job_payload.get('startTime')
    isdone = job_payload.get('isdone')
    jobTitle = job_payload.get('jobTitle')
    jobDescription = job_payload.get('jobDescription')
    thumbnail = job_payload.get('thumbnail')
    area = job_payload.get('area')

    # Call the firebase_handler.add_job function with extracted variables
    firebase_handler.add_job(
        userid=userid,
        jobid=jobid,
        startTime=startTime,
        isdone=isdone,
        jobTitle=jobTitle,
        jobDescription=jobDescription,
        thumbnail=thumbnail,
        area=area
    )

    return jsonify({'Success': "true"})


def update_job(job_payload):
    job_payload = job_payload.get("job_payload")

    # Extract common variables
    jobid = job_payload.get('jobid')
    startTime = job_payload.get('startTime')
    endTime = job_payload.get('endTime')
    # Default to False if not provided
    isdone = job_payload.get('isdone', False)

    print(f"Type of startTime: {type(startTime)}, Value: {startTime}")
    print(f"Type of endTime: {type(endTime)}, Value: {endTime}")

    # Extract additional variables for successful update
    thumbnail = job_payload.get('thumbnail')
    area = job_payload.get('area')
    basemap = job_payload.get('basemap')
    userid = job_payload.get('userid')
    jobTitle = job_payload.get('jobTitle')
    jobDescription = job_payload.get('jobDescription')
    # Default to None if not provided
    features = job_payload.get('features', None)
    center = job_payload.get('center', None)  # Default to None if not provided

    # Call function to handle successful job update
    firebase_handler.update_job(
        userid=userid,
        jobid=jobid,
        startTime=startTime,
        endTime=endTime,
        thumbnail=thumbnail,
        area=area,
        basemap=basemap,
        jobTitle=jobTitle,
        jobDescription=jobDescription,
        features=features,
        isdone=isdone,
        center=center
    )

    return jsonify({'Success': "true"})


def send_pending_email(email_payload):
    recipient_name = email_payload.get('recipient_name')
    recipient_email = email_payload.get('recipient_email')
    print(recipient_email)
    project_name = email_payload.get('project_name')
    job_id = email_payload.get('job_id')

    html_content = plaintext_content = f""" 
      A job with id  has been created, we'll notify you once the job is done
        This email confirms that we have received your submission for {project_name} with {job_id}.

        We will now process the project and once it is ready for usage, an email will be sent to notify you.

        Thank you for using Drangue and do contact us for any further enquiries.
    """
    subject = f"[DRANGUE] Project Submission Received: {recipient_email}"
    emailSender.send_email(recipient_name, recipient_email,
                           subject, html_content, plaintext_content)

    return jsonify({'Success': "true"})


def send_confirmation_email(email_payload):

    recipient_name = email_payload.get('recipient_name')
    recipient_email = email_payload.get('recipient_email')
    project_name = email_payload.get('project_name')
    job_id = email_payload.get('job_id')

    html_content = plaintext_content = f""" 
                A job with id {job_id} has been processed successfully.
            Please use this link to access it: https://drangue.ai/display_project?jobid={job_id}
            Or use this link to access all projects: https://drangue.ai/projects
    """
    subject = f"[DRANGUE] Project Submission Received: {recipient_email}"
    emailSender.send_email(recipient_name, recipient_email,
                           subject, html_content, plaintext_content)

    return jsonify({'Success': "true"})


def send_failed_email(email_payload):
    recipient_name = email_payload.get('recipient_name')
    recipient_email = email_payload.get('recipient_email')
    project_name = email_payload.get('project_name')
    job_id = email_payload.get('job_id')
    error = email_payload.get('error')

    html_content = plaintext_content = """ 
           A job with id {job_id} has failed, we're very sorry. Please try again later
            
            Error Message: {error}
    """
    subject = f"[DRANGUE] Project Submission Received: {recipient_email}"
    emailSender.send_email(recipient_name, recipient_email,
                           subject, html_content, plaintext_content)

    return jsonify({'Success': "true"})


def display_jobs_retrieve_handler(data):
    # Extract the user email from the input data

    if 'jobid' in data:
        user_email = data['jobid']

        # Initialize the Firebase handler
        firebase_handler = FirebaseHandler()

        # Get jobs by user email
        job = firebase_handler.get_job(user_email)
        # Return the retrieved jobs as JSON
        return jsonify({'job': job})
    else:
        # If 'email' is missing, return an error response
        return jsonify({'error': 'Invalid JSON data. Expected "email" field.'}), 400


def jobs_retrieve_handler(data):
    # Extract the user email from the input data

    if 'userid' in data:
        user_email = data['userid']

        # Initialize the Firebase handler
        firebase_handler = FirebaseHandler()

        # Get jobs by user email
        jobs = firebase_handler.get_jobs_by_email(user_email)
        # Return the retrieved jobs as JSON
        return jsonify({'jobs': jobs})
    else:
        # If 'email' is missing, return an error response
        return jsonify({'error': 'Invalid JSON data. Expected "email" field.'}), 400


def login_handler(data):

    credentials = data
    # Extract the relevant fields
    # reporter_email = report_data.get('reporterEmail')
    email = credentials.get('email')
    password = credentials.get('password')
    firebase_handler = FirebaseHandler()

    try:
        authentication_success = firebase_handler.authenticate_user(
            email, password)
    except Exception as e:
        print("Login Error: ", e)
        raise Exception("Account already registered")

    if not authentication_success:
        raise Exception("Authentication failed")

    return jsonify({'message': 'User Logged In Successfully', "authenticated": True}), 200


def registeration_handler(data):
   # Extract the relevant fields
    # reporter_email = report_data.get('reporterEmail')
    credentials = data
    email = credentials.get('email')
    password = credentials.get('password')
    first_name = credentials.get('firstName', "test")
    last_name = credentials.get('lastName', "test")
    isgoogle = credentials.get('isGoogle', False)
    display_name = credentials.get('displayName', "test")
    firebase_handler = FirebaseHandler()
    if isgoogle:
        try:
            authentication_success = firebase_handler.add_user(
                display_name, email)
            return jsonify({'message': 'Report received successfully', "authenticated": True}), 200
        except:
            raise Exception("Account already registered")
    else:

        try:
            authentication_success = firebase_handler.register_user(
                first_name, last_name, email, password, password)
            return jsonify({'message': 'Report received successfully', "authenticated": True}), 200
        except Exception as e:
            raise Exception(f"Account already registered")


def get_profile_handler(data):

    user_data = data
    email = user_data.get('userId')
    firebase_handler = FirebaseHandler()

    try:
        user_profile_fetch = firebase_handler.get_profile(email)
    except Exception as e:
        print("Fetching Error while retrieving user record: ", e)
        raise Exception("Fetching Error while retrieving user record:", e)

    if not user_profile_fetch:
        raise Exception("Fetching failed")

    return jsonify(user_profile_fetch), 200


def update_profile_handler(data):
    new_user_data = data

    first_name = new_user_data.get('firstName', None)
    last_name = new_user_data.get('lastName', None)
    email = new_user_data.get('email', None)
    old_password = new_user_data.get('oldPassword', None)
    new_password = new_user_data.get('newPassword', None)

    try:
        user_profile_update = firebase_handler.update_profile(
            first_name, last_name, email, old_password, new_password)
    except Exception as e:
        print("Update Error while updating user record: ", e)
        raise Exception("Fetching Error while updating user record:", e)

    if not user_profile_update:
        raise Exception("Update failed")

    return jsonify(user_profile_update), 200

def email_enquiry_handler(data):
    email_details = data

    first_name = email_details.get('first_name', None)
    last_name = email_details.get('last_name', None)
    email = email_details.get('email', None)
    phone_number = email_details.get('phone_number', None)
    details = email_details.get('details', None)

    recipient_name = "Drangue Offical"
    recipient_email = "dranguoffical@gmail.com"

    html_content = plaintext_content = f""" 
      {first_name} {last_name} with email address: {email} and phone number {phone_number} has sent an enquiry with the following details \n 
      {details}
    """
    subject = f"Enquiry by {first_name} {last_name} with email address: {email}"

    try:
        email_sent = emailSender.send_email(recipient_name, recipient_email,
                               subject, html_content, plaintext_content)
    except Exception as e:
        print("Update Error while Sending Email: ", e)
        raise Exception("Email Error while sending user enquiry email:", e)

    if not email_sent:
        raise Exception("Email sending failed")

    return jsonify("Email Sent successfully"), 200
