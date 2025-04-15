#!/usr/bin/env python
"""
Study Planner - Run Script
--------------------------
This script is the entry point for the Study Planner application.
It sets up the environment and runs the application.
"""
import os
import sys
import subprocess
import webbrowser
from time import sleep

def check_dependencies():
    """Check if required dependencies are installed, and install them if not."""
    try:
        import flask
        import pandas
    except ImportError:
        print("Installing required dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "pandas"])
        print("Dependencies installed successfully.")

def ensure_config_directory():
    """Ensure the config directory exists."""
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        print(f"Created config directory: {config_dir}")
    
    # Create empty config files if they don't exist
    for filename in ['modules.json', 'assignments.json', 'settings.json']:
        filepath = os.path.join(config_dir, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                if filename in ['modules.json', 'assignments.json']:
                    f.write('[]')  # Empty array
                else:
                    f.write('{}')  # Empty object
            print(f"Created empty config file: {filepath}")

def run_application():
    """Run the Flask application."""
    from app import app
    
    # Open the browser after a short delay
    def open_browser():
        sleep(1)  # Wait for the server to start
        webbrowser.open('http://127.0.0.1:5000')
    
    import threading
    threading.Timer(1, open_browser).start()
    
    # Run the Flask application
    app.run(debug=True)

if __name__ == "__main__":
    print("Starting Study Planner...")
    
    # Check dependencies
    check_dependencies()
    
    # Ensure config directory exists
    ensure_config_directory()
    
    # Run the application
    run_application()
