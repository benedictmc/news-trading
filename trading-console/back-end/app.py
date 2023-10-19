from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from endpoints.routes import endpoints
from tinydb import TinyDB
import requests
from flask_login import LoginManager
# from flask_jwt_extended import JWTManager
from security import User


load_dotenv()

app = Flask(__name__)

db = TinyDB('db.json')

app.config['db'] = db

app.register_blueprint(endpoints)

# Apply configurations
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['LOG_FILE_PATH'] = "/home/ben/dev/news-trading/binance_ws/logs/trading_log.log"
app.config["MASTER_USERNAME"] = os.environ.get('MASTER_USERNAME')
app.config["MASTER_PASSWORD"] = os.environ.get('MASTER_PASSWORD')
# Enable CORS for the React frontend


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

CORS(app)

if __name__ == '__main__':
    app.run(debug=True, port=5001)