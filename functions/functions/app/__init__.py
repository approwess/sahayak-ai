from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from .extensions import init_extensions
from .routes import register_blueprints
import os

def create_app():
    print("[DEBUG] create_app() called")
    load_dotenv()
    app = Flask(__name__)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[WARNING] GOOGLE_API_KEY is missing or not loaded from .env")
    else:
        print("[INFO] GOOGLE_API_KEY loaded successfully")

    CORS(app)
    init_extensions(app)
    register_blueprints(app)  # This should handle all blueprint registration
    
    return app