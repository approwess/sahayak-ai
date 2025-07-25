import os
import sys
from pathlib import Path

# Add the parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from firebase_functions import https_fn
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your app modules (after path is set)
try:
    from app.routes.lesson import lesson_bp
    from app.routes.combined_assessment_routes import combined_assessment_bp
    print("✅ Successfully imported app modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(lesson_bp)
app.register_blueprint(combined_assessment_bp)

@app.route('/')
def home():
    return {'message': 'Multigrade Assessment API is running', 'status': 'healthy'}

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'service': 'multigrade-assessment-api'}, 200

@https_fn.on_request(max_instances=10)
def api(req: https_fn.Request) -> https_fn.Response:
    """Firebase Function entry point"""
    with app.request_context(req.environ):
        return app.full_dispatch_request()

# Add this section to run Flask directly when testing
if __name__ == '__main__':
    print("🚀 Starting Flask development server...")
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)