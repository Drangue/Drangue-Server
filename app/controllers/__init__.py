from datetime import datetime
import uuid

from flask import jsonify
from app.services import perform_operation
from app.services.ModelsDetection import ModelsDetection
from app.models.FirebaseHandler import FirebaseHandler
from app.services.EmailSender import EmailSender
import threading

def process_request(data):
    # Import perform_operation here to avoid circular import

    # This function might preprocess the input data
    processed_data = preprocess_input(data)
    result = perform_operation(processed_data)
    return result

def preprocess_input(data):
    # This function might preprocess the input data
    return data

def detect_handler(data):
    
    project_name = data["project_name"]
    project_description = data["project_description"]
    features_selected = data["features_selected"]
    polygons = data["polygons"]
    area = data["area"]
    basemap = data["basemap"]
    recipient_email = data["userid"]
    
    # This function might preprocess the input data
    modelsDetection = ModelsDetection()
    firebase_handler = FirebaseHandler()
    emailSender = EmailSender()

    # Function to process each polygon asynchronously
    def process_polygon(job_id, polygon, features_selected):
        

        print(features_selected)
        print("checkpoint 1")
        
        startTime = datetime.now().isoformat()
        
        center_coords = modelsDetection.centroid(polygon)
        thumbnail = firebase_handler.get_thumbnail(center_coords)
        
        firebase_handler.add_job(
            userid=recipient_email,
            jobid=job_id,
            startTime=startTime,  # Example start time
            isdone=False,
            jobTitle=project_name,
            jobDescription=project_description,
            thumbnail=thumbnail,
            area=area
        )

        # Confirmation Email
        recipient_name = "Mohammed Alshami"
        
        subject = f"[DRANGUE] Project Submission Received: {recipient_email}"
        
        html_content = plaintext_content = f"""
        A job with id  has been created, we'll notify you once the job is done
        This email confirms that we have received your submission for {project_name} with {job_id}.

        We will now process the project and once it is ready for usage, an email will be sent to notify you.

        Thank you for using Drangue and do contact us for any further enquiries.

        Sincerely,
        Drangue Team
        """
        emailSender.send_email(recipient_name, recipient_email, subject, html_content, plaintext_content)

        print("checkpoint 2")
        try:
            print("checkpoint 3")
            output = modelsDetection.detect_polygons(polygons=polygon, zoom=18, output_file="temp.tiff", area_km2=4, features_selected=features_selected)
            
            # Success
            print("checkpoint 5")
            endTime = datetime.now().isoformat()
            firebase_handler.update_job(thumbnail=thumbnail,area=area, basemap=basemap, userid=recipient_email, jobTitle=project_name,jobDescription=project_description,jobid=job_id,startTime=startTime, endTime=endTime,features=output, isdone=True)

            # Success Email
            html_content = plaintext_content = f"""
            A job with id {job_id} has been processed successfully.
            
            please use this link to access it http://localhost:3001/display_project?jobid={job_id}
            
            
            or this link to access all projects https://drangue.com/projects
            """
            emailSender.send_email(recipient_name, recipient_email, subject, html_content, plaintext_content)
            print("checkpoint 6")
        except Exception as e:
            print("checkpoint 4")
            print(e)
            # Fail Email
            html_content = plaintext_content = f"""
            A job with id {job_id} has failed, we're very sorry. Please try again later
            
            Error Message: {e}
            """
            emailSender.send_email(recipient_name, recipient_email, subject, html_content, plaintext_content)

            # Fail
            endTime = datetime.now().isoformat()
            firebase_handler.update_job(jobid=job_id,startTime=startTime, endTime=endTime, isdone="Failed")


    # Start a new thread to process the polygon asynchronously
    job_id = f"job_{uuid.uuid4()}"
    
    threading.Thread(target=process_polygon, args=(job_id, polygons,features_selected)).start()
    return {"Status": "Success", "job_id": job_id}



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
        

def generate_api_key_handler(data):
    email = data['email']

    if not email:
        return jsonify({'error': 'Invalid JSON data. Expected "email" field.'}), 400
    
    firebase_handler = FirebaseHandler()

    try:
        api_key = firebase_handler.generate_user_api_key(email=email)
        return jsonify({'api_key': api_key})
    except Exception as e:
        return jsonify({'error': str(e)}), 400



def delete_api_key_handler(data):
    email = data['email']
    api_key = data['api_key']

    if not email or not api_key:
        return jsonify({'error': 'Invalid JSON data. Expected "email" and "api_key" fields.'}), 400

    
    firebase_handler = FirebaseHandler()

    try:
        firebase_handler.delete_user_api_key(email=email, api_key=api_key)
        return jsonify({'message': 'API key deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    