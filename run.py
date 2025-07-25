from app import create_app

import os
print("[DEBUG] CWD:", os.getcwd())

print("[DEBUG] calling create_app()")  # Add this to verify
app = create_app()

if __name__ == '__main__':
    print("[DEBUG] starting Flask server")  # Add this too
    app.run(debug=True)