from datetime import datetime
import uuid
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
    # This function might preprocess the input data
    modelsDetection = ModelsDetection()
    firebase_handler = FirebaseHandler()
    emailSender = EmailSender()

    # Function to process each polygon asynchronously
    def process_polygon(polygon, features_selected):
        print("checkpoint 1")
        job_id = f"job_{uuid.uuid4()}"
        startTime = datetime.now().isoformat()
        firebase_handler.add_job(
            userid="user123",
            jobid=job_id,
            startTime=startTime,  # Example start time
            isdone=False
        )

        # Confirmation Email
        recipient_name = "Mohammed Alshami"
        recipient_email = "mshami2021@gmail.com"
        subject = "Confirmation Email @noreply"
        html_content = plaintext_content = f"""
        A job with id {job_id} has been created, we'll notify you once the job is done
        """
        emailSender.send_email(recipient_name, recipient_email, subject, html_content, plaintext_content)

        print("checkpoint 2")
        try:
            print("checkpoint 3")
            output = modelsDetection.detect_polygons(polygons=polygon, zoom=18, output_file="temp.tiff", area_km2=4, features_selected=features_selected)
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
            firebase_handler.update_job(jobid=job_id,endTime=endTime, isdone="Failed")


        # Success
        print("checkpoint 5")
        endTime = datetime.now().isoformat()
        firebase_handler.update_job(jobid=job_id,endTime=endTime,features=output,isdone=True)

        # Success Email
        html_content = plaintext_content = f"""
        A job with id {job_id} has been processed successfully.
        
        please use this link to access it https://drangue.com/jobs/{job_id}
        
        or this link to access all projects https://drangue.com/jobs
        """
        emailSender.send_email(recipient_name, recipient_email, subject, html_content, plaintext_content)
        print("checkpoint 6")

    # Start a new thread to process the polygon asynchronously
    threading.Thread(target=process_polygon, args=(polygons,features_selected)).start()
    return "Success"
