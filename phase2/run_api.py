#!/usr/bin/env python3
import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server configuration
HOST = os.getenv("API_HOST", "0.0.0.0")
PORT = int(os.getenv("API_PORT", "8000"))
RELOAD = os.getenv("API_RELOAD", "False").lower() in ("true", "1", "t")

if __name__ == "__main__":
    print(f"Démarrage de l'API sur {HOST}:{PORT} (reload: {RELOAD})")
    # Add current directory to PYTHONPATH
    os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
    uvicorn.run("app.api.main:app", host=HOST, port=PORT, reload=RELOAD) 