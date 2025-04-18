#!/usr/bin/env python3
import os
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Streamlit configuration
PORT = int(os.getenv("UI_PORT", "8501"))
HOST = os.getenv("UI_HOST", "0.0.0.0")

if __name__ == "__main__":
    # Path to the Streamlit application
    streamlit_app_path = os.path.join(os.path.dirname(__file__), "app", "ui", "streamlit_app.py")
    
    # Check if the file exists
    if not os.path.exists(streamlit_app_path):
        print(f"Error: The file {streamlit_app_path} does not exist")
        sys.exit(1)
    
    print(f"Starting the Streamlit UI on {HOST}:{PORT}")
    
    # Full path to the streamlit executable
    streamlit_path = os.path.expanduser("~/Library/Python/3.9/bin/streamlit")
    
    # Launch Streamlit with parameters
    cmd = [
        streamlit_path, "run", 
        streamlit_app_path,
        "--server.port", str(PORT),
        "--server.address", HOST,
        "--browser.serverAddress", HOST,
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("Stopping the Streamlit application...")
    except Exception as e:
        print(f"Error starting Streamlit: {str(e)}")
        sys.exit(1) 