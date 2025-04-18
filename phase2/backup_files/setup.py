#!/usr/bin/env python3
"""
Script de configuration pour l'installation du projet phase2.
"""

import subprocess
import os
import sys
import shutil
from pathlib import Path

# Fonction pour exécuter une commande shell
def run_command(command):
    print(f"Exécution de: {command}")
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        print(f"Erreur ({process.returncode}):")
        print(stderr)
        return False
    
    print(stdout)
    return True

# Vérifier la version de Python
required_version = (3, 8)
current_version = sys.version_info

if current_version < required_version:
    print(f"Erreur: Python {required_version[0]}.{required_version[1]} ou supérieur est requis.")
    print(f"Version actuelle: {current_version[0]}.{current_version[1]}")
    sys.exit(1)

# Créer le répertoire des logs
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
print(f"Répertoire des logs créé: {log_dir}")

# Créer le fichier .env s'il n'existe pas
env_file = Path(".env")
if not env_file.exists():
    print("Création du fichier .env avec des valeurs par défaut...")
    with open(env_file, "w") as f:
        f.write("""# Azure OpenAI
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_API_VERSION=2023-05-15

# Model deployments
GPT4O_DEPLOYMENT_NAME=gpt-4o
GPT4O_MINI_DEPLOYMENT_NAME=gpt-4o-mini
EMBEDDING_DEPLOYMENT_NAME=text-embedding-ada-002

# Server configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False
UI_HOST=0.0.0.0
UI_PORT=8501

# Logging
LOG_LEVEL=INFO
""")
    print("Fichier .env créé. Veuillez y ajouter vos clés API Azure.")
else:
    print("Le fichier .env existe déjà.")

# Installer les dépendances
print("Installation des dépendances...")
if not run_command("pip install -r requirements.txt"):
    print("Erreur lors de l'installation des dépendances.")
    sys.exit(1)

print("\nConfiguration terminée avec succès!")
print("\nPour initialiser la base de connaissances, exécutez:")
print("python -m app.knowledge.init_knowledge_base")
print("\nPour démarrer l'API backend, exécutez:")
print("python run_api.py")
print("\nPour démarrer l'interface utilisateur, exécutez:")
print("python run_ui.py")
print("\nL'interface utilisateur sera accessible à l'adresse http://localhost:8501") 