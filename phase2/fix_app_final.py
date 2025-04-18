#!/usr/bin/env python3
"""
Script final pour corriger l'application Phase 2.
Ce script résout le problème des clients OpenAI et initialise l'application.
"""

import os
import sys
import shutil
import traceback
import time
from datetime import datetime
from dotenv import load_dotenv

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Charger les variables d'environnement
load_dotenv()

def setup_logging():
    """Configure et initialise le système de logs."""
    try:
        # Créer le dossier logs s'il n'existe pas déjà
        logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        api_logs_dir = os.path.join(logs_dir, "api")
        ui_logs_dir = os.path.join(logs_dir, "ui")
        
        os.makedirs(logs_dir, exist_ok=True)
        os.makedirs(api_logs_dir, exist_ok=True)
        os.makedirs(ui_logs_dir, exist_ok=True)
        
        # Vérifier que le fichier logger.py existe et est correctement configuré
        logger_path = os.path.join("app", "logging", "logger.py")
        if not os.path.exists(logger_path):
            # Créer l'arborescence si nécessaire
            os.makedirs(os.path.join("app", "logging"), exist_ok=True)
            
            # Création de __init__.py dans le dossier logging s'il n'existe pas
            init_path = os.path.join("app", "logging", "__init__.py")
            if not os.path.exists(init_path):
                with open(init_path, 'w') as f:
                    f.write("# Module de journalisation\n")
        
        print(f"Système de logs configuré avec succès. Dossiers créés: {logs_dir}")
        return True
    except Exception as e:
        print(f"Erreur lors de la configuration des logs: {str(e)}")
        traceback.print_exc()
        return False

def remove_all_proxies_refs():
    """Supprime toutes les références au paramètre 'proxies' dans le code."""
    files_to_check = [
        "app/llm/collection.py",
        "app/llm/qa.py",
        "app/knowledge/embedding.py"
    ]
    
    # Créer les répertoires nécessaires s'ils n'existent pas
    os.makedirs("app/llm", exist_ok=True)
    os.makedirs("app/knowledge", exist_ok=True)
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            # Lire le contenu du fichier
            with open(file_path, 'r') as file:
                content = file.read()
            
            # Remplacer toutes les occurrences de 'proxies='
            modified_content = content.replace("proxies=", "# proxies=")
            
            # Écrire le contenu modifié
            with open(file_path, 'w') as file:
                file.write(modified_content)
            
            print(f"Fichier {file_path} vérifié et corrigé si nécessaire")

def create_simple_openai_module():
    """Crée ou met à jour le module simple_client.py."""
    # Créer le répertoire s'il n'existe pas
    os.makedirs("app/llm", exist_ok=True)
    
    content = '''import os
import json
import requests
from typing import List, Dict, Any
from ..core.config import settings
from loguru import logger

class SimpleAzureOpenAIClient:
    """
    Client Azure OpenAI simplifié qui utilise des requêtes REST directes
    plutôt que la bibliothèque openai qui peut causer des problèmes de compatibilité.
    """
    
    def __init__(self):
        """Initialise le client avec les informations d'API depuis les paramètres."""
        self.api_key = settings.AZURE_OPENAI_API_KEY
        self.endpoint = settings.AZURE_OPENAI_ENDPOINT
        self.api_version = settings.AZURE_OPENAI_API_VERSION
        self.chat_model = settings.GPT4O_DEPLOYMENT_NAME
        self.embedding_model = settings.EMBEDDING_DEPLOYMENT_NAME
        logger.info("Client Azure OpenAI simplifié initialisé")
    
    def chat_completions_create(self, model: str, messages: List[Dict[str, str]], 
                               temperature: float = 0.7, max_tokens: int = 800) -> Dict[str, Any]:
        """
        Envoie une requête de complétion chat à l'API Azure OpenAI.
        
        Args:
            model: Le nom du modèle à utiliser
            messages: Liste de messages au format [{"role": "...", "content": "..."}]
            temperature: Température pour la génération (0.0 à 1.0)
            max_tokens: Nombre maximum de tokens à générer
            
        Returns:
            Objet de réponse simulant la structure de l'API OpenAI
        """
        try:
            url = f"{self.endpoint}/openai/deployments/{model}/chat/completions?api-version={self.api_version}"
            
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
            
            data = {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Log la requête (sans les messages pour confidentialité)
            logger.debug(f"Envoi de requête OpenAI pour modèle: {model} - Temp: {temperature}")
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Réponse OpenAI reçue avec succès pour modèle {model}")
                return response.json()
            else:
                logger.error(f"Erreur API: HTTP {response.status_code} - {response.text}")
                # Retourner une structure similaire à l'API OpenAI mais avec un message d'erreur
                return {
                    "choices": [{
                        "message": {
                            "content": "Je suis désolé, une erreur s'est produite lors du traitement de votre message.",
                            "role": "assistant"
                        },
                        "finish_reason": "error"
                    }]
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération de complétion: {str(e)}")
            return {
                "choices": [{
                    "message": {
                        "content": "Je suis désolé, une erreur s'est produite lors du traitement de votre message.",
                        "role": "assistant"
                    },
                    "finish_reason": "error"
                }]
            }
    
    def embeddings_create(self, model: str, input: str) -> Dict[str, Any]:
        """
        Crée un embedding pour un texte donné.
        
        Args:
            model: Le nom du modèle d'embedding à utiliser
            input: Le texte à encoder
            
        Returns:
            Objet de réponse simulant la structure de l'API OpenAI
        """
        try:
            url = f"{self.endpoint}/openai/deployments/{model}/embeddings?api-version={self.api_version}"
            
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
            
            data = {
                "input": input
            }
            
            # Log la requête (juste la taille du texte pour confidentialité)
            logger.debug(f"Création d'embedding avec modèle {model} - Taille du texte: {len(input)} caractères")
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Embedding créé avec succès pour modèle {model}")
                return response.json()
            else:
                logger.error(f"Erreur API embedding: HTTP {response.status_code} - {response.text}")
                # Retourner une structure similaire à l'API OpenAI mais avec un vecteur de zéros
                return {
                    "data": [{
                        "embedding": [0.0] * 1536,  # Dimension standard pour ADA 002
                        "index": 0
                    }],
                    "model": model,
                    "usage": {"prompt_tokens": 0, "total_tokens": 0}
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'embedding: {str(e)}")
            return {
                "data": [{
                    "embedding": [0.0] * 1536,
                    "index": 0
                }],
                "model": model,
                "usage": {"prompt_tokens": 0, "total_tokens": 0}
            }
    
    @property
    def chat(self):
        """Propriété pour simuler la structure d'API OpenAI."""
        return type('ChatObject', (), {
            'completions': type('CompletionsObject', (), {
                'create': lambda *args, **kwargs: self.chat_completions_create(
                    model=kwargs.get('model', self.chat_model), 
                    messages=kwargs.get('messages', []),
                    temperature=kwargs.get('temperature', 0.7),
                    max_tokens=kwargs.get('max_tokens', 800)
                )
            })()
        })()
    
    @property
    def embeddings(self):
        """Propriété pour simuler la structure d'API OpenAI."""
        return type('EmbeddingsObject', (), {
            'create': lambda *args, **kwargs: self.embeddings_create(
                model=kwargs.get('model', self.embedding_model),
                input=kwargs.get('input', '')
            )
        })()

def create_simple_openai_client():
    """Crée et retourne une instance du client simplifié."""
    return SimpleAzureOpenAIClient()
'''
    
    with open("app/llm/simple_client.py", 'w') as file:
        file.write(content)
    
    print("Module simple_client.py créé/mis à jour avec succès")

def create_client_module():
    """Crée ou met à jour le module client.py."""
    # Créer le répertoire s'il n'existe pas
    os.makedirs("app/llm", exist_ok=True)
    
    content = '''from loguru import logger

def create_openai_client():
    """
    Crée un client OpenAI compatible avec la version installée.
    Évite le problème des arguments non supportés.
    """
    try:
        # Importer le client simplifié
        from .simple_client import create_simple_openai_client
        logger.info("Utilisation du client OpenAI simplifié")
        return create_simple_openai_client()
    except Exception as e:
        logger.error(f"Impossible d'initialiser le client OpenAI simplifié: {str(e)}")
        raise
'''
    
    with open("app/llm/client.py", 'w') as file:
        file.write(content)
    
    print("Module client.py créé/mis à jour avec succès")

def create_init_file():
    """Crée ou met à jour le fichier __init__.py si nécessaire."""
    # Créer le répertoire s'il n'existe pas
    os.makedirs("app/llm", exist_ok=True)
    
    if not os.path.exists("app/llm/__init__.py"):
        with open("app/llm/__init__.py", 'w') as file:
            file.write("# Module d'intégration avec les modèles de langage\n")
        print("Fichier app/llm/__init__.py créé")

def kill_running_processes():
    """Tue les processus existants sur les ports 8000 et 8501."""
    try:
        os.system("kill $(lsof -t -i:8000) 2>/dev/null || true")
        os.system("kill $(lsof -t -i:8501) 2>/dev/null || true")
        print("Processus existants arrêtés")
    except:
        print("Aucun processus à arrêter")

def clear_logs():
    """Efface les fichiers de logs existants."""
    log_files = ["api.log", "ui.log", "streamlit.log"]
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
                print(f"Fichier de log {log_file} supprimé")
            except:
                print(f"Impossible de supprimer le fichier de log {log_file}")

def create_logger_module():
    """Crée ou met à jour le module de journalisation."""
    # S'assurer que le répertoire existe
    os.makedirs("app/logging", exist_ok=True)
    
    # Créer le fichier __init__.py s'il n'existe pas
    init_path = os.path.join("app", "logging", "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, 'w') as f:
            f.write("# Module de journalisation\n")
    
    # Contenu du module de journalisation
    content = '''import os
import sys
import json
from datetime import datetime
from loguru import logger
from ..core.config import settings

# Configuration du niveau de log
LOG_LEVEL = settings.LOG_LEVEL

# Répertoire des logs
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
api_log_dir = os.path.join(log_dir, "api")
ui_log_dir = os.path.join(log_dir, "ui")

# Créer les répertoires s'ils n'existent pas
os.makedirs(log_dir, exist_ok=True)
os.makedirs(api_log_dir, exist_ok=True)
os.makedirs(ui_log_dir, exist_ok=True)

# Fichiers de log avec timestamp pour éviter les écrasements
api_log_file = os.path.join(api_log_dir, f"api_{timestamp}.log")
ui_log_file = os.path.join(ui_log_dir, f"ui_{timestamp}.log")
debug_log_file = os.path.join(log_dir, f"debug_{timestamp}.log")

# Format personnalisé pour les logs
log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"

# Configurer loguru
logger.remove()  # Supprimer la configuration par défaut

# Ajouter la sortie console avec niveau INFO
logger.add(sys.stderr, level="INFO", format=log_format)

# Ajouter le fichier de log API
logger.add(
    api_log_file,
    rotation="100 MB",
    retention="30 days",
    compression="zip",
    level=LOG_LEVEL,
    format=log_format,
    filter=lambda record: "api" in record["name"].lower(),
    encoding="utf8"
)

# Ajouter le fichier de log UI
logger.add(
    ui_log_file,
    rotation="100 MB",
    retention="30 days",
    compression="zip",
    level=LOG_LEVEL,
    format=log_format,
    filter=lambda record: "ui" in record["name"].lower() or "streamlit" in record["name"].lower(),
    encoding="utf8"
)

# Ajouter le fichier de log debug pour TOUS les messages
logger.add(
    debug_log_file,
    rotation="100 MB",
    retention="15 days",
    compression="zip",
    level="DEBUG",
    format=log_format,
    encoding="utf8"
)

# Fonction pour logger les requêtes API
def log_api_request(endpoint: str, request_data: dict, user_id: str = "unknown"):
    """
    Enregistre les données d'une requête API.
    
    Args:
        endpoint: Le point de terminaison API appelé
        request_data: Les données de la requête (sans informations sensibles)
        user_id: Un identifiant d'utilisateur ou de session (anonyme)
    """
    try:
        # Créer une copie des données pour ne pas modifier l'original
        safe_data = request_data.copy() if request_data else {}
        
        # Masquer ou retirer les informations sensibles
        if isinstance(safe_data, dict):
            # Si des conversation_history est présent, ne logger que le nombre de messages
            if 'conversation_history' in safe_data and isinstance(safe_data['conversation_history'], dict):
                messages = safe_data['conversation_history'].get('messages', [])
                safe_data['conversation_history'] = f"[{len(messages)} messages]"
            
            # Masquer les informations utilisateur sensibles
            for profile_key in ['user_profile', 'partial_profile']:
                if profile_key in safe_data and isinstance(safe_data[profile_key], dict):
                    profile = safe_data[profile_key]
                    
                    # Masquer les identifiants sensibles
                    for sensitive_field in ['id_number', 'hmo_card_number']:
                        if sensitive_field in profile:
                            value = profile[sensitive_field]
                            if value and len(str(value)) > 4:
                                profile[sensitive_field] = f"***{str(value)[-4:]}"
        
        # Enregistrer les données de requête sécurisées
        log_entry = {
            "type": "api_request",
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "user_id": user_id,
            "data": safe_data
        }
        
        logger.info(f"API Request | Endpoint: {endpoint} | User: {user_id}")
        logger.debug(f"API Request Details: {json.dumps(log_entry, ensure_ascii=False)}")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de la requête API: {str(e)}")

# Fonction pour logger les réponses API
def log_api_response(endpoint: str, status_code: int, response_data: dict, 
                    processing_time: float, user_id: str = "unknown"):
    """
    Enregistre les données d'une réponse API.
    
    Args:
        endpoint: Le point de terminaison API appelé
        status_code: Le code de statut HTTP
        response_data: Les données de la réponse (sans informations sensibles)
        processing_time: Le temps de traitement en millisecondes
        user_id: Un identifiant d'utilisateur ou de session (anonyme)
    """
    try:
        # Masquer ou simplifier les données de réponse sensibles
        safe_data = {}
        
        if response_data:
            # Copier les métadonnées et statuts si présents
            if 'metadata' in response_data:
                safe_data['metadata'] = response_data['metadata']
            
            # Ne pas inclure le contenu complet des réponses
            if 'response' in response_data:
                content = response_data['response']
                safe_data['response_length'] = len(content) if isinstance(content, str) else "non-string"
            
            # Si un historique de conversation est présent, ne logger que le nombre de messages
            if 'updated_conversation_history' in response_data:
                history = response_data['updated_conversation_history']
                if isinstance(history, dict) and 'messages' in history:
                    safe_data['conversation_messages_count'] = len(history['messages'])
        
        # Métadonnées de la réponse
        log_entry = {
            "type": "api_response",
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "user_id": user_id,
            "status_code": status_code,
            "processing_time_ms": processing_time,
            "data": safe_data
        }
        
        logger.info(f"API Response | Endpoint: {endpoint} | User: {user_id} | Status: {status_code} | Time: {processing_time:.2f}ms")
        logger.debug(f"API Response Details: {json.dumps(log_entry, ensure_ascii=False)}")
        
        # Enregistrer séparément les erreurs
        if status_code >= 400:
            logger.error(f"API Error | Endpoint: {endpoint} | Status: {status_code} | User: {user_id}")
            logger.error(f"Error Details: {json.dumps(safe_data, ensure_ascii=False)}")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de la réponse API: {str(e)}")

# Exporter les fonctions et objets
__all__ = ["logger", "log_api_request", "log_api_response"]
'''
    
    # Écrire le contenu dans le fichier
    with open("app/logging/logger.py", 'w') as f:
        f.write(content)
    
    print("Module de journalisation créé/mis à jour avec succès")

def create_improved_streamlit_app():
    """Crée une version améliorée de streamlit_app.py avec initialisation automatique de la conversation."""
    # Vérifié si improved_streamlit_app.py existe dans le répertoire courant ou dans phase2/
    improved_app_path = "improved_streamlit_app.py"
    phase2_improved_app_path = os.path.join("phase2", "improved_streamlit_app.py")
    
    if os.path.exists(improved_app_path):
        source_path = improved_app_path
    elif os.path.exists(phase2_improved_app_path):
        source_path = phase2_improved_app_path
    else:
        print("ERREUR: Impossible de trouver le fichier improved_streamlit_app.py")
        return False
    
    # Créer le répertoire si nécessaire
    os.makedirs("app/ui", exist_ok=True)
    
    # Copier le fichier improved_streamlit_app.py vers app/ui/streamlit_app.py
    shutil.copy(source_path, "app/ui/streamlit_app.py")
    
    print("Interface utilisateur Streamlit améliorée créée/mise à jour avec succès")
    return True

def replace_streamlit_app():
    """Remplace le fichier streamlit_app.py par la version corrigée."""
    print("Remplacement du fichier streamlit_app.py par la version corrigée...")
    
    # Vérifier si le nouveau fichier existe
    fixed_path = "app/ui/streamlit_app_fixed.py"
    original_path = "app/ui/streamlit_app.py"
    
    if os.path.exists(fixed_path):
        # Créer une sauvegarde de l'ancien fichier
        backup_path = f"app/ui/streamlit_app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        if os.path.exists(original_path):
            shutil.copy2(original_path, backup_path)
            print(f"Backup créé: {backup_path}")
        
        # Remplacer le fichier original par la version corrigée
        shutil.copy2(fixed_path, original_path)
        print("Fichier streamlit_app.py remplacé avec succès!")
        return True
    else:
        print(f"ERREUR: Le fichier corrigé {fixed_path} n'existe pas.")
        return False

def start_app():
    """Démarre l'application (API et interface utilisateur)."""
    print("\n[3/3] Démarrage de l'application...")
    
    # Remplacer le fichier streamlit_app.py par la version corrigée
    replace_streamlit_app()
    
    # Créer des sous-processus pour l'API et l'UI
    try:
        import subprocess
        import threading
        
        def start_api():
            subprocess.Popen(["python3", "run_api.py"], cwd=os.path.dirname(__file__))
            print("API démarrée!")
        
        def start_ui():
            # Attendre que l'API soit prête
            time.sleep(2)
            subprocess.Popen(["python3", "run_ui.py"], cwd=os.path.dirname(__file__))
            print("Interface utilisateur démarrée!")
            
        # Démarrer l'API et l'UI dans des threads séparés
        api_thread = threading.Thread(target=start_api)
        ui_thread = threading.Thread(target=start_ui)
        
        api_thread.start()
        ui_thread.start()
        
        print("\nApplication démarrée avec succès!")
        print("- API: http://localhost:8000")
        print("- Interface: http://localhost:8501")
        print("\nPour arrêter l'application, utilisez Ctrl+C dans ce terminal.")
        
        # Attendre que les threads se terminent (ce qui ne devrait pas arriver)
        api_thread.join()
        ui_thread.join()
        
    except Exception as e:
        print(f"Erreur lors du démarrage de l'application: {str(e)}")
        traceback.print_exc()

def ensure_app_structure():
    """Crée tous les répertoires nécessaires pour l'application."""
    directories = [
        "app",
        "app/llm",
        "app/api",
        "app/knowledge",
        "app/ui",
        "app/core",
        "app/logging",
        "logs",
        "logs/api",
        "logs/ui"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Répertoire {directory} vérifié/créé")
    
    # Vérifier si le fichier config.py existe
    if not os.path.exists("app/core/config.py"):
        with open("app/core/config.py", 'w') as f:
            f.write('''import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Charger les variables d'environnement depuis .env s'il existe
load_dotenv()

class Settings(BaseSettings):
    # Configuration de l'application
    APP_NAME: str = "Medical Services Chatbot"
    API_V1_STR: str = "/api/v1"
    
    # Paramètres Azure OpenAI
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    
    # Nom des modèles déployés dans Azure
    GPT4O_DEPLOYMENT_NAME: str = os.getenv("GPT4O_DEPLOYMENT_NAME", "gpt-4o")
    GPT4O_MINI_DEPLOYMENT_NAME: str = os.getenv("GPT4O_MINI_DEPLOYMENT_NAME", "gpt-4o-mini")
    EMBEDDING_DEPLOYMENT_NAME: str = os.getenv("EMBEDDING_DEPLOYMENT_NAME", "text-embedding-ada-002")
    
    # Paramètres Document Intelligence (OCR)
    DOCUMENT_INTELLIGENCE_KEY: str = os.getenv("DOCUMENT_INTELLIGENCE_KEY", "")
    DOCUMENT_INTELLIGENCE_ENDPOINT: str = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT", "")
    
    # Chemins des fichiers de la base de connaissances
    KNOWLEDGE_BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../phase2_data"))
    
    # Configuration du logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
''')
        print("Fichier app/core/config.py créé")
    
    # Créer le fichier __init__.py dans chaque dossier s'il n'existe pas
    for directory in directories:
        init_file = os.path.join(directory, "__init__.py")
        if os.path.isdir(directory) and not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write(f"# Module {os.path.basename(directory)}\n")
            print(f"Fichier {init_file} créé")
    
    # Copier le fichier .env de phase2 vers la racine si nécessaire
    if not os.path.exists(".env") and os.path.exists("phase2/.env"):
        shutil.copy("phase2/.env", ".env")
        print("Fichier .env copié depuis phase2/.env")
    
    return True

if __name__ == "__main__":
    print("====== Correction finale de l'application Phase 2 ======")
    
    # Tuer les processus existants
    kill_running_processes()
    
    # S'assurer que la structure de l'application est complète
    ensure_app_structure()
    
    # Configurer le système de logs
    setup_logging()
    
    # Créer ou mettre à jour le module de journalisation
    create_logger_module()
    
    # Nettoyer les logs
    clear_logs()
    
    # Créer ou mettre à jour les modules nécessaires
    create_init_file()
    create_simple_openai_module()
    create_client_module()
    create_improved_streamlit_app()
    
    # Supprimer les références à 'proxies'
    remove_all_proxies_refs()
    
    # Démarrer l'application
    start_app()
    
    print("\n====== Correction terminée avec succès! ======")
    print("L'application est démarrée et accessible à http://localhost:8501")
    print("Les fichiers de logs sont disponibles dans le dossier 'logs/'")
    
    print("=====================================================") 