from app import create_app

import os
print("[DEBUG] CWD:", os.getcwd())

print("[DEBUG] calling create_app()")  # Add this to verify
app = create_app()

if __name__ == '__main__':
    # Get port from environment variable or default to 8080
    port = int(os.environ.get('PORT', 8081))
    
    # Listen on all interfaces (0.0.0.0) not just localhost
    app.run(host='0.0.0.0', port=port, debug=True)