#!/usr/bin/env python3
import os
import sys
import time
import socket
import subprocess
import threading
import platform
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def get_local_ip():
    """Récupère l'adresse IP locale de la machine"""
    try:
        # Crée un socket qui se connecte à un serveur externe
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Pas besoin d'être réellement connecté
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"Erreur lors de la récupération de l'IP locale: {str(e)}")
        return "localhost"

# Configuration
API_PORT = int(os.getenv("API_PORT", "8000"))
UI_PORT = int(os.getenv("UI_PORT", "8501"))
HOST = get_local_ip()

def start_api():
    """Démarrer l'API FastAPI avec accès externe"""
    api_cmd = [
        sys.executable,
        "-m", "uvicorn", 
        "app.api.main:app", 
        "--host", HOST, 
        "--port", str(API_PORT)
    ]
    
    print(f"Démarrage de l'API sur http://{HOST}:{API_PORT}")
    api_process = subprocess.Popen(api_cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    return api_process

def start_ui():
    """Démarrer l'interface Streamlit avec accès externe"""
    streamlit_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "ui", "streamlit_app.py")
    
    if not os.path.exists(streamlit_app_path):
        print(f"Erreur: Le fichier {streamlit_app_path} n'existe pas")
        return None
    
    # Trouver le chemin vers l'exécutable streamlit
    if platform.system() == "Darwin":  # macOS
        streamlit_path = os.path.expanduser("~/Library/Python/3.9/bin/streamlit")
        if not os.path.exists(streamlit_path):
            streamlit_path = "streamlit"  # Utiliser la commande globale si le chemin spécifique n'existe pas
    else:
        streamlit_path = "streamlit"
    
    # Configurer Streamlit pour accepter les connexions externes
    ui_cmd = [
        streamlit_path, "run", 
        streamlit_app_path,
        "--server.port", str(UI_PORT),
        "--server.address", HOST,
        "--browser.serverAddress", HOST,
        "--server.headless", "true"
    ]
    
    print(f"Démarrage de l'interface sur http://{HOST}:{UI_PORT}")
    ui_process = subprocess.Popen(ui_cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    return ui_process

def main():
    """Fonction principale pour démarrer l'application avec accès externe"""
    print(f"Démarrage de l'application sur le réseau. Votre adresse IP est: {HOST}")
    
    try:
        # Démarrer l'API
        api_process = start_api()
        
        # Attendre que l'API soit prête
        print("Attente du démarrage de l'API...")
        time.sleep(5)
        
        # Démarrer l'interface
        ui_process = start_ui()
        
        if api_process and ui_process:
            print("\nApplication démarrée avec succès!")
            print(f"- API: http://{HOST}:{API_PORT}")
            print(f"- Interface: http://{HOST}:{UI_PORT}")
            print(f"\nPartagez ces liens pour permettre à d'autres ordinateurs de votre réseau d'accéder à l'application.")
            print("\nPour arrêter l'application, utilisez Ctrl+C dans ce terminal.")
            
            # Attendre indéfiniment (jusqu'à interruption par Ctrl+C)
            try:
                api_process.wait()
                ui_process.wait()
            except KeyboardInterrupt:
                print("\nArrêt de l'application...")
                # Arrêter les processus
                api_process.terminate()
                ui_process.terminate()
                print("Application arrêtée.")
        else:
            print("Erreur: Impossible de démarrer l'API ou l'interface.")
            if api_process:
                api_process.terminate()
            if ui_process:
                ui_process.terminate()
                
    except KeyboardInterrupt:
        print("\nArrêt de l'application...")
        sys.exit(0)
    except Exception as e:
        print(f"Erreur lors du démarrage de l'application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 