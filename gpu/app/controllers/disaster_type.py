# from app.services.detection import detect_handler
# import asyncio
# from app import app
# from flask import request, jsonify, Blueprint
# detection_bp = Blueprint('detect', __name__)

# @detection_bp.route('/landslide', methods=['GET', "POST"])
# def landslide():
#     if request.method == 'POST':
#         api_key = request.form.get('api_key')
#         polygons = request.form.get('polygons')  # Polygons should be a JSON string, so parse it
#         file = request.files.get('file')

#         if not api_key or not polygons or not file:
#             return jsonify({'error': 'Missing form data. Ensure api_key, polygons, and file are provided.'}), 400

#         try:
#             # Convert polygons from JSON string to a list
#             polygons = json.loads(polygons)
#         except ValueError:
#             return jsonify({'error': 'Invalid polygons data. Ensure it is a valid JSON array.'}), 400

#         if isinstance(polygons, list):
#             # Create a new event loop and run the async function
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)
#             loop.run_until_complete(process_detect({'api_key': api_key, 'polygons': polygons, 'file': file}))
#             return jsonify({'message': 'Processing started, results will be available soon.'}), 200
#         else:
#             return jsonify({'error': 'Invalid polygons data. Expected "polygons" to be a JSON array.'}), 400
#     else:
#         return jsonify({'error': 'Invalid request method. Use POST.'}), 405
