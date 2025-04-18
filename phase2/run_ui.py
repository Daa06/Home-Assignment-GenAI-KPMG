#!/usr/bin/env python3
import os
import subprocess
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration de Streamlit
PORT = int(os.getenv("UI_PORT", "8501"))
HOST = os.getenv("UI_HOST", "0.0.0.0")

if __name__ == "__main__":
    # Chemin vers l'application Streamlit
    streamlit_app_path = os.path.join(os.path.dirname(__file__), "app", "ui", "streamlit_app.py")
    
    # Vérifier que le fichier existe
    if not os.path.exists(streamlit_app_path):
        print(f"Erreur: Le fichier {streamlit_app_path} n'existe pas")
        sys.exit(1)
    
    print(f"Démarrage de l'interface utilisateur Streamlit sur {HOST}:{PORT}")
    
    # Chemin complet vers l'exécutable streamlit
    streamlit_path = os.path.expanduser("~/Library/Python/3.9/bin/streamlit")
    
    # Lancer Streamlit avec les paramètres
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
        print("Arrêt de l'application Streamlit...")
    except Exception as e:
        print(f"Erreur lors du démarrage de Streamlit: {str(e)}")
        sys.exit(1) 