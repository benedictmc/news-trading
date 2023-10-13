from flask import render_template, jsonify, Blueprint, request, current_app as app
from tinydb import Query
from datetime import datetime

endpoints = Blueprint('endpoints', __name__)

@endpoints.route('/')
def index():
    return "TODO: Add a home page"


@endpoints.route('/health-ping', methods=['GET', 'POST'])
def recieve_health():
    MetaData = Query()
    db = app.config['db']
    metadata = db.get(MetaData.type == "metadata")
    if request.method == 'POST':
        current_timestamp = datetime.now().isoformat()

        if not metadata:
            db.insert({'last_ping': current_timestamp, 'type': 'metadata'})
        else:
            db.update({'last_ping': current_timestamp}, MetaData.type == "metadata")
        
        return jsonify({"message": "Pinged successfully!", "last_ping": current_timestamp})
    
    if request.method == 'GET':
        if not metadata or "last_ping" not in metadata:
            return jsonify({"message": "Last ping not available"}), 404

        return jsonify({"last_ping": metadata['last_ping']})
