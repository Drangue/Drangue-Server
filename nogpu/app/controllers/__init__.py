# from datetime import datetime
# import uuid

from flask import jsonify
from app.models.FirebaseHandler import FirebaseHandler
from app.services.EmailSender import EmailSender
# import threading


firebase_handler = FirebaseHandler()
emailSender = EmailSender()

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
    isdone = job_payload.get('isdone', False)  # Default to False if not provided
    
    print(f"Type of startTime: {type(startTime)}, Value: {startTime}")
    print(f"Type of endTime: {type(endTime)}, Value: {endTime}")
    
    # Extract additional variables for successful update
    thumbnail = job_payload.get('thumbnail')
    area = job_payload.get('area')
    basemap = job_payload.get('basemap')
    userid = job_payload.get('userid')
    jobTitle = job_payload.get('jobTitle')
    jobDescription = job_payload.get('jobDescription')
    features = job_payload.get('features', None)  # Default to None if not provided
    
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
        isdone=isdone
    )

    return jsonify({'Success': "true"})


def send_pending_email(email_payload):
    recipient_name = email_payload.get('recipient_name')
    recipient_email = email_payload.get('recipient_email')
    project_name = email_payload.get('project_name')
    job_id = email_payload.get('job_id')

    
    html_content = plaintext_content = """ 
      A job with id  has been created, we'll notify you once the job is done
        This email confirms that we have received your submission for {project_name} with {job_id}.

        We will now process the project and once it is ready for usage, an email will be sent to notify you.

        Thank you for using Drangue and do contact us for any further enquiries.
    """
    subject =  f"[DRANGUE] Project Submission Received: {recipient_email}",
    emailSender.send_email(recipient_name, recipient_email, subject, html_content, plaintext_content)

    return jsonify({'Success': "true"})

def send_confirmation_email(email_payload):
    
    recipient_name = email_payload.get('recipient_name')
    recipient_email = email_payload.get('recipient_email')
    project_name = email_payload.get('project_name')
    job_id = email_payload.get('job_id')
    
    html_content = plaintext_content = """ 
                A job with id {job_id} has been processed successfully.
            Please use this link to access it: http://localhost:3001/display_project?jobid={job_id}
            Or use this link to access all projects: https://drangue.com/projects
    """
    subject =  f"[DRANGUE] Project Submission Received: {recipient_email}",
    emailSender.send_email(recipient_name, recipient_email, subject, html_content, plaintext_content)

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
    subject =  f"[DRANGUE] Project Submission Received: {recipient_email}",
    emailSender.send_email(recipient_name, recipient_email, subject, html_content, plaintext_content)

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
        authentication_success = firebase_handler.authenticate_user(email, password)
    except:
        raise Exception("Account already registered")
    
    if not authentication_success:
        raise Exception("Authentication failed")
    
    return jsonify({'message': 'Report received successfully', "authenticated": True}), 200
    
def registeration_handler(data):
   # Extract the relevant fields
        # reporter_email = report_data.get('reporterEmail')
    credentials = data
    email = credentials.get('email')
    password = credentials.get('password')
    first_name = credentials.get('firstName', "test")
    last_name = credentials.get('lastName', "test")
    isgoogle= credentials.get('isGoogle', False)
    display_name = credentials.get('displayName', "test")
    firebase_handler = FirebaseHandler()
    if isgoogle:
        try:
            authentication_success = firebase_handler.add_user(display_name, email)
            return jsonify({'message': 'Report received successfully', "authenticated": True}), 200
        except:
            raise Exception("Account already registered")
    else:

        try:
            authentication_success = firebase_handler.register_user(first_name, last_name, email, password, password)
            return jsonify({'message': 'Report received successfully', "authenticated": True}), 200
        except Exception as e:
            raise Exception(f"Account already registered")