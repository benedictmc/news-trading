from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize the Flask app
app = Flask(__name__)

# Apply configurations
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# Enable CORS for the React frontend
CORS(app)

if __name__ == '__main__':
    app.run(debug=True)