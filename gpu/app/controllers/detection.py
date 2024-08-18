# from app.services.detection import detect_handler
# import asyncio
# from app import app
# from flask import request, jsonify, Blueprint
# detection_bp = Blueprint('detect', __name__)


# @detection_bp.route('/all', methods=['GET', "POST"])
# def detect():
#     data = request.json
#     print(f'Received data: {data}')
    
#     if not data:
#         return jsonify({'error': 'No JSON payload provided.'}), 400
    
#     if 'polygons' in data and isinstance(data['polygons'], list):
#         # Create a new event loop and run the async function
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         loop.run_until_complete(process_detect(data))
#         return jsonify({'message': 'Processing started, results will be available soon.'}), 200
#     else:
#         return jsonify({'error': 'Invalid JSON data. Expected "polygons" array.'}), 400
