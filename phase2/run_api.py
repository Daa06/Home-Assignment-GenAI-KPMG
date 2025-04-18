#!/usr/bin/env python3
import os
import uvicorn
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du serveur
HOST = os.getenv("API_HOST", "0.0.0.0")
PORT = int(os.getenv("API_PORT", "8000"))
RELOAD = os.getenv("API_RELOAD", "False").lower() in ("true", "1", "t")

if __name__ == "__main__":
    print(f"Démarrage de l'API sur {HOST}:{PORT} (reload: {RELOAD})")
    # Ajouter le répertoire courant au PYTHONPATH
    os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
    uvicorn.run("app.api.main:app", host=HOST, port=PORT, reload=RELOAD) 