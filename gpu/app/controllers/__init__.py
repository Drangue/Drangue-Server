import tempfile
import os
from app.classes import ModelsDetection
from flask import request, jsonify, Blueprint

modelsDetection = ModelsDetection()

def save_uploaded_file(file):
    try:
        # Automatically detect the file extension
        file_extension = os.path.splitext(file.filename)[1].lower()  # Get file extension in lowercase

        # Save the uploaded file as a temporary file with the detected extension
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        temp_file.write(file.read())
        temp_file_path = temp_file.name

        return temp_file_path, file_extension
    except Exception as e:
        print(f'Error saving file: {str(e)}')
        return None, None

def process_detect(api_key, file, detection_type):
    temp_file_path, file_extension = None, None
    try:
        # Save the uploaded file and get the file path and extension
        if detection_type == "damage-assessment":
            temp_file_path = []
            files = file
            for i in files:
                i = save_uploaded_file(i)
                temp_file_path.append(i)
                
        if not temp_file_path:
            raise Exception("Failed to save the uploaded file.")

        # Handle TIFF files specifically if necessary
        if file_extension in ('.tif', '.tiff'):
            # Add any specific processing for TIFF files here if needed
            print(f"Processing a TIFF file: {temp_file_path}")

        # Assuming detect_single_feature is the function that processes the data
        result = modelsDetection.detect_single_feature(feature_type=detection_type, file_path=temp_file_path)
        
        print(f'Processing complete: {result}')
        return result

    except Exception as e:
        print(f'Error during processing: {str(e)}')
        return None  # Return an appropriate error response or result

    finally:
        # Ensure the temporary file is deleted after processing
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
