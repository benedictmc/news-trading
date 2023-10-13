from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from endpoints.routes import endpoints
from tinydb import TinyDB
load_dotenv()

app = Flask(__name__)

db = TinyDB('db.json')

app.config['db'] = db

app.register_blueprint(endpoints)

# Apply configurations
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# Enable CORS for the React frontend
CORS(app)

if __name__ == '__main__':
    app.run(debug=True)