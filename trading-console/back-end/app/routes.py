from flask import render_template, jsonify, request
from app import app
# Additional imports such as models, forms, etc.

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint
@app.route('/api/items', methods=['GET'])
def get_items():
    items = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]  # Example data
    return jsonify(items)

@app.route('/api/items', methods=['POST'])
def add_item():
    data = request.json
    # Logic to add item to database (not shown here)
    return jsonify({"message": "Item added!", "data": data}), 201

# Error handler for 404
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404
In more complex applications: