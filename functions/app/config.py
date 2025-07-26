# config.py
import os
from pathlib import Path

class Config:
    # Existing configuration
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT', 'agenticaihackathon2025')
    GOOGLE_CLOUD_LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
    
    # Flask Configuration
    # SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    @staticmethod
    def setup_google_credentials():
        """Setup Google Cloud credentials for the Flask application"""
        # Check if running in Firebase Cloud Functions environment
        if (os.getenv('FUNCTION_NAME') or 
            os.getenv('FUNCTION_TARGET') or 
            os.getenv('FUNCTIONS_EMULATOR') or
            'GAE_APPLICATION' in os.environ):
            print("✅ Running in cloud environment - using default credentials")
            return True
            
        # Only set up credentials file for local development
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            print("✅ Google Cloud credentials already configured")
            return True
        
        # Get the project root directory (where config.py is located)
        project_root = Path(__file__).parent
        credentials_file = "agenticaihackathon2025-416e44094541.json"
        
        # Search for credentials file in common locations
        credential_paths = [
            project_root / credentials_file,                    # Same directory as config.py
            project_root.parent / credentials_file,             # Parent directory
            project_root / "credentials" / credentials_file,    # credentials folder
            project_root / "keys" / credentials_file,           # keys folder
        ]
        
        for path in credential_paths:
            if path.exists():
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(path.absolute())
                print(f"Google Cloud credentials configured: {path.absolute()}")
                return True
        
        print(f"⚠️ Google Cloud credentials file '{credentials_file}' not found")
        print("Consider using 'gcloud auth application-default login' instead")
        return False
    
    @staticmethod
    def validate_config():
        """Validate that all required configuration is present"""
        required_vars = {
            'GOOGLE_API_KEY': Config.GOOGLE_API_KEY,
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        print("All required configuration variables are set")
        return True

# Initialize credentials when the config module is imported
Config.setup_google_credentials()