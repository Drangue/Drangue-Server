import tempfile
import os
from app.classes.ModelsDetection import ModelsDetection
from flask import request, jsonify, Blueprint
detection_bp = Blueprint('detect', __name__)


modelsDetection = ModelsDetection()


def process_detect(api_key, file, detection_type):
    try:
        # Save the uploaded file as a temporary file
        file_extension = ".tif"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(file.read())
            temp_file_path = temp_file.name

        # Assuming detect_handler is the function that processes the data
        result = modelsDetection.detect_single_feature(feature_type=detection_type, file_path=temp_file_path)
        return result
        print(f'Processing complete: {result}')
        
        # Clean up the temporary file after processing
        os.remove(temp_file_path)
    except Exception as e:
        print(f'Error during processing: {str(e)}')
        # Ensure the temporary file is deleted even if an error occurs
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
