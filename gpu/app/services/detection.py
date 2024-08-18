# from datetime import datetime
# import uuid
# from flask import jsonify
# from app.classes import ModelsDetection
# import threading
# import requests
# from dotenv import load_dotenv
# import os

# # Load environment variables from .env file
# load_dotenv()

# # Get the BASE_ENDPOINT variable
# base_endpoint = os.getenv('BASE_ENDPOINT')

# def send_request(json_data, endpoint_path):
#     try:
#         # Combine the base endpoint with the specific endpoint path
#         full_url = base_endpoint + endpoint_path
        
#         # Send the JSON data to the full URL
#         response = requests.post(full_url, json=json_data)
        
#         # Raise an error if the request was unsuccessful
#         response.raise_for_status()
        
#         print("end point called", response.json())

#         # Get the JSON response from the endpoint
#         return response.json()
    
#     except requests.exceptions.RequestException as e:
#         # Handle any errors that occur during the request
#         print("end point called, but error", str(e))
#         return {'error': str(e)}
    
# def detect_handler(data):
    
#     project_name = data["project_name"]
#     project_description = data["project_description"]
#     features_selected = data["features_selected"]
#     polygons = data["polygons"]
#     area = data["area"]
#     basemap = data["basemap"]
#     recipient_email = data["userid"]
    
#     recipient_name = "Mohammed Alshami"
#     # This function might preprocess the input data
#     modelsDetection = ModelsDetection()
#     # Function to process each polygon asynchronously
#     def process_polygon(job_id, polygon, features_selected):
        
        

#         print(features_selected)
#         print("checkpoint 1")
        
#         startTime = datetime.now().isoformat()
        
#         center_coords = modelsDetection.centroid(polygon)
        
        
#         # generating thumbnail
#         print("passed by here")
#         thumbnail = send_request({"center_coords": center_coords}, "/get-thumbnail")
#         thumbnail = thumbnail.get("thumbnail")
        
#         # creating a job
#         job_payload = {
#             "userid": recipient_email,
#             "jobid": job_id,
#             "startTime": startTime,  # Example start time
#             "isdone": False,
#             "jobTitle": project_name,
#             "jobDescription": project_description,
#             "thumbnail": thumbnail,
#             "area": area
#         }
#         create_job = send_request({"job_payload": job_payload}, "/create-job")

#         # Send a pending email
#         email_payload = {
#                 "recipient_name": recipient_name,
#                 "recipient_email": recipient_email,
#                 "project_name": project_name,
#                 "job_id": job_id
#             }
#         send_request({"email_payload": email_payload}, "/send-pending-email")

#         try:
#             output = modelsDetection.detect_polygons(polygons=polygon, zoom=18, output_file="temp.tiff", area_km2=4, features_selected=features_selected)
            
#             # Success
#             endTime = datetime.now().isoformat()
        
#             # update job
#             job_payload = {
#                 "thumbnail": thumbnail,
#                 "area": area,
#                 "basemap": basemap,
#                 "userid": recipient_email,
#                 "jobTitle": project_name,
#                 "jobDescription": project_description,
#                 "jobid": job_id,
#                 "startTime": startTime,
#                 "endTime": endTime,
#                 "features": output,
#                 "isdone": True
#             }
#             print("Success", startTime, endTime)

#             update_job = send_request({"job_payload": job_payload}, "/update-job")

#             # Send a success email
#             email_payload = {
#                 "recipient_name": recipient_name,
#                 "recipient_email": recipient_email,
#                 "project_name": project_name,
#                 "job_id": job_id
#             }
#             send_request({"email_payload": email_payload}, "/send-confirmation-email")
#         except Exception as e:
#             print("checkpoint 4")
#             print(e
#                   )
#             # send failed email
   
            
#             email_payload = {
#                 "recipient_name": recipient_name,
#                 "recipient_email": recipient_email,
#                 "project_name": project_name,
#                 "job_id": job_id,
#                 "error": str(e),
#             }
#             fail_email = send_request({"email_payload": email_payload}, "/send-failed-email")


#             # Fail
#             endTime = datetime.now().isoformat()
            
#             # update job
#             job_payload = {
#                 "thumbnail": thumbnail,
#                 "area": area,
#                 "basemap": basemap,
#                 "userid": recipient_email,
#                 "jobTitle": project_name,
#                 "jobDescription": project_description,
#                 "jobid": job_id,
#                 "startTime": startTime,
#                 "endTime": endTime,
#                 "features": output,
#                 "isdone": "Failed"
#             }
#             print("failed", startTime, endTime)

#             update_job = send_request({"job_payload": job_payload}, "/update-job")

#     # Start a new thread to process the polygon asynchronously
#     job_id = f"job_{uuid.uuid4()}"
    
#     threading.Thread(target=process_polygon, args=(job_id, polygons,features_selected)).start()
#     return {"Status": "Success", "job_id": job_id}