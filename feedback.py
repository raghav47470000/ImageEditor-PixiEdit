from flask import Blueprint, request, jsonify
import json
import os

feedback_bp = Blueprint('feedback', __name__)
FEEDBACK_FILE = 'feedback_store.json'

# Ensure feedback file exists
if not os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump([], f)

@feedback_bp.route('/api/feedback', methods=['POST'])
def receive_feedback():
    data = request.get_json()
    username = data.get('username')
    comment = data.get('comment')

    if not username or not comment:
        return jsonify({'error': 'Missing username or comment'}), 400

    feedback_entry = {
        'username': username,
        'comment': comment
    }

    with open(FEEDBACK_FILE, 'r+') as f:
        feedback_list = json.load(f)
        feedback_list.append(feedback_entry)
        f.seek(0)
        json.dump(feedback_list, f, indent=2)

    return jsonify({'message': 'Feedback received successfully'}), 200
