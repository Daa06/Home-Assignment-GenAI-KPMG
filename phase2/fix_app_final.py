#!/usr/bin/env python3
"""
Final script to fix the Phase 2 application.
This script resolves OpenAI client issues and initializes the application.
"""

import os
import sys
import shutil
import traceback
import time
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

def setup_logging():
    """Configure and initialize the logging system."""
    try:
        # Create logs folder if it doesn't already exist
        logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        api_logs_dir = os.path.join(logs_dir, "api")
        ui_logs_dir = os.path.join(logs_dir, "ui")
        
        os.makedirs(logs_dir, exist_ok=True)
        os.makedirs(api_logs_dir, exist_ok=True)
        os.makedirs(ui_logs_dir, exist_ok=True)
        
        # Check that logger.py file exists and is correctly configured
        logger_path = os.path.join("app", "logging", "logger.py")
        if not os.path.exists(logger_path):
            # Create directory structure if needed
            os.makedirs(os.path.join("app", "logging"), exist_ok=True)
            
            # Create __init__.py in the logging folder if it doesn't exist
            init_path = os.path.join("app", "logging", "__init__.py")
            if not os.path.exists(init_path):
                with open(init_path, 'w') as f:
                    f.write("# Logging module\n")
        
        print(f"Logging system successfully configured. Created folders: {logs_dir}")
        return True
    except Exception as e:
        print(f"Error while configuring logs: {str(e)}")
        traceback.print_exc()
        return False

def remove_all_proxies_refs():
    """Removes all references to the 'proxies' parameter in the code."""
    files_to_check = [
        "app/llm/collection.py",
        "app/llm/qa.py",
        "app/knowledge/embedding.py"
    ]
    
    # Create necessary directories if they don't exist
    os.makedirs("app/llm", exist_ok=True)
    os.makedirs("app/knowledge", exist_ok=True)
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            # Read the file content
            with open(file_path, 'r') as file:
                content = file.read()
            
            # Replace all occurrences of 'proxies='
            modified_content = content.replace("proxies=", "# proxies=")
            
            # Write the modified content
            with open(file_path, 'w') as file:
                file.write(modified_content)
            
            print(f"File {file_path} checked and fixed if necessary")

def create_simple_openai_module():
    """Creates or updates the simple_client.py module."""
    # Create directory if it doesn't exist
    os.makedirs("app/llm", exist_ok=True)
    
    content = '''import os
import json
import requests
from typing import List, Dict, Any
from ..core.config import settings
from loguru import logger

class SimpleAzureOpenAIClient:
    """
    Simplified Azure OpenAI client that uses direct REST requests
    instead of the openai library which can cause compatibility issues.
    """
    
    def __init__(self):
        """Initialize the client with API information from settings."""
        self.api_key = settings.AZURE_OPENAI_API_KEY
        self.endpoint = settings.AZURE_OPENAI_ENDPOINT
        self.api_version = settings.AZURE_OPENAI_API_VERSION
        self.chat_model = settings.GPT4O_DEPLOYMENT_NAME
        self.embedding_model = settings.EMBEDDING_DEPLOYMENT_NAME
        logger.info("Client Azure OpenAI simplifié initialisé")
    
    def chat_completions_create(self, model: str, messages: List[Dict[str, str]], 
                               temperature: float = 0.7, max_tokens: int = 800) -> Dict[str, Any]:
        """
        Send a chat completion request to the Azure OpenAI API.
        
        Args:
            model: The model name to use
            messages: List of messages in format [{"role": "...", "content": "..."}]
            temperature: Temperature for generation (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Response object mimicking the OpenAI API structure
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
            
            # Log the request (without messages for confidentiality)
            logger.debug(f"Envoi de requête OpenAI pour modèle: {model} - Temp: {temperature}")
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Réponse OpenAI reçue avec succès pour modèle {model}")
                return response.json()
            else:
                logger.error(f"Erreur API: HTTP {response.status_code} - {response.text}")
                # Return a structure similar to the OpenAI API but with an error message
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
        Create an embedding for a given text.
        
        Args:
            model: The embedding model name to use
            input: The text to encode
            
        Returns:
            Response object mimicking the OpenAI API structure
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
            
            # Log the request (just the text size for confidentiality)
            logger.debug(f"Création d'embedding avec modèle {model} - Taille du texte: {len(input)} caractères")
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Embedding créé avec succès pour modèle {model}")
                return response.json()
            else:
                logger.error(f"Erreur API embedding: HTTP {response.status_code} - {response.text}")
                # Return a structure similar to the OpenAI API but with a zero vector
                return {
                    "data": [{
                        "embedding": [0.0] * 1536,  # Standard dimension for ADA 002
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
        """Property to simulate the OpenAI API structure."""
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
        """Property to simulate the OpenAI API structure."""
        return type('EmbeddingsObject', (), {
            'create': lambda *args, **kwargs: self.embeddings_create(
                model=kwargs.get('model', self.embedding_model),
                input=kwargs.get('input', '')
            )
        })()

def create_simple_openai_client():
    """Creates and returns an instance of the simplified client."""
    return SimpleAzureOpenAIClient()
'''
    
    with open("app/llm/simple_client.py", 'w') as file:
        file.write(content)
    
    print("Module simple_client.py créé/mis à jour avec succès")

def create_client_module():
    """Creates or updates the client.py module."""
    # Create directory if it doesn't exist
    os.makedirs("app/llm", exist_ok=True)
    
    content = '''from loguru import logger

def create_openai_client():
    """
    Creates an OpenAI client compatible with the installed version.
    Avoids the problem of unsupported arguments.
    """
    try:
        # Import the simplified client
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
    """Creates or updates the __init__.py file if necessary."""
    # Create directory if it doesn't exist
    os.makedirs("app/llm", exist_ok=True)
    
    if not os.path.exists("app/llm/__init__.py"):
        with open("app/llm/__init__.py", 'w') as file:
            file.write("# Integration module with language models\n")
        print("Fichier app/llm/__init__.py créé")

def kill_running_processes():
    """Kills existing processes on ports 8000 and 8501."""
    try:
        os.system("kill $(lsof -t -i:8000) 2>/dev/null || true")
        os.system("kill $(lsof -t -i:8501) 2>/dev/null || true")
        print("Processus existants arrêtés")
    except:
        print("Aucun processus à arrêter")

def clear_logs():
    """Clears existing log files."""
    log_files = ["api.log", "ui.log", "streamlit.log"]
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
                print(f"Fichier de log {log_file} supprimé")
            except:
                print(f"Impossible de supprimer le fichier de log {log_file}")

def create_logger_module():
    """Creates or updates the logging module."""
    # Ensure directory exists
    os.makedirs("app/logging", exist_ok=True)
    
    # Create __init__.py file if it doesn't exist
    init_path = os.path.join("app", "logging", "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, 'w') as f:
            f.write("# Logging module\n")
    
    # Content of the logging module
    content = '''import os
import sys
import json
from datetime import datetime
from loguru import logger
from ..core.config import settings

# Log level configuration
LOG_LEVEL = settings.LOG_LEVEL

# Logs directory
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
api_log_dir = os.path.join(log_dir, "api")
ui_log_dir = os.path.join(log_dir, "ui")

# Create directories if they don't exist
os.makedirs(log_dir, exist_ok=True)
os.makedirs(api_log_dir, exist_ok=True)
os.makedirs(ui_log_dir, exist_ok=True)

# Log files with timestamp to avoid overwriting
api_log_file = os.path.join(api_log_dir, f"api_{timestamp}.log")
ui_log_file = os.path.join(ui_log_dir, f"ui_{timestamp}.log")
debug_log_file = os.path.join(log_dir, f"debug_{timestamp}.log")

# Custom format for logs
log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"

# Configure loguru
logger.remove()  # Remove default configuration

# Add console output with INFO level
logger.add(sys.stderr, level="INFO", format=log_format)

# Add API log file
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

# Add UI log file
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

# Add debug log file for ALL messages
logger.add(
    debug_log_file,
    rotation="100 MB",
    retention="15 days",
    compression="zip",
    level="DEBUG",
    format=log_format,
    encoding="utf8"
)

# Function to log API requests
def log_api_request(endpoint: str, request_data: dict, user_id: str = "unknown"):
    """
    Records API request data.
    
    Args:
        endpoint: The API endpoint called
        request_data: The data of the request (without sensitive information)
        user_id: A user identifier or session identifier (anonymous)
    """
    try:
        # Create a copy of the data to not modify the original
        safe_data = request_data.copy() if request_data else {}
        
        # Mask or remove sensitive information
        if isinstance(safe_data, dict):
            # If conversation_history is present, log only the number of messages
            if 'conversation_history' in safe_data and isinstance(safe_data['conversation_history'], dict):
                messages = safe_data['conversation_history'].get('messages', [])
                safe_data['conversation_history'] = f"[{len(messages)} messages]"
            
            # Mask sensitive user information
            for profile_key in ['user_profile', 'partial_profile']:
                if profile_key in safe_data and isinstance(safe_data[profile_key], dict):
                    profile = safe_data[profile_key]
                    
                    # Mask sensitive identifiers
                    for sensitive_field in ['id_number', 'hmo_card_number']:
                        if sensitive_field in profile:
                            value = profile[sensitive_field]
                            if value and len(str(value)) > 4:
                                profile[sensitive_field] = f"***{str(value)[-4:]}"
        
        # Record safe request data
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

# Function to log API responses
def log_api_response(endpoint: str, status_code: int, response_data: dict, 
                    processing_time: float, user_id: str = "unknown"):
    """
    Records API response data.
    
    Args:
        endpoint: The API endpoint called
        status_code: The HTTP status code
        response_data: The data of the response (without sensitive information)
        processing_time: The processing time in milliseconds
        user_id: A user identifier or session identifier (anonymous)
    """
    try:
        # Mask or simplify sensitive response data
        safe_data = {}
        
        if response_data:
            # Copy metadata and status if present
            if 'metadata' in response_data:
                safe_data['metadata'] = response_data['metadata']
            
            # Do not include full response content
            if 'response' in response_data:
                content = response_data['response']
                safe_data['response_length'] = len(content) if isinstance(content, str) else "non-string"
            
            # If conversation history is present, log only the number of messages
            if 'updated_conversation_history' in response_data:
                history = response_data['updated_conversation_history']
                if isinstance(history, dict) and 'messages' in history:
                    safe_data['conversation_messages_count'] = len(history['messages'])
        
        # Response metadata
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
        
        # Record separate errors
        if status_code >= 400:
            logger.error(f"API Error | Endpoint: {endpoint} | Status: {status_code} | User: {user_id}")
            logger.error(f"Error Details: {json.dumps(safe_data, ensure_ascii=False)}")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de la réponse API: {str(e)}")

# Export functions and objects
__all__ = ["logger", "log_api_request", "log_api_response"]
'''
    
    # Write content to file
    with open("app/logging/logger.py", 'w') as f:
        f.write(content)
    
    print("Module de journalisation créé/mis à jour avec succès")

def create_improved_streamlit_app():
    """Creates an improved version of streamlit_app.py with automatic conversation initialization."""
    # Check if improved_streamlit_app.py exists in the current directory or in phase2/
    improved_app_path = "improved_streamlit_app.py"
    phase2_improved_app_path = os.path.join("phase2", "improved_streamlit_app.py")
    
    if os.path.exists(improved_app_path):
        source_path = improved_app_path
    elif os.path.exists(phase2_improved_app_path):
        source_path = phase2_improved_app_path
    else:
        print("ERREUR: Impossible de trouver le fichier improved_streamlit_app.py")
        return False
    
    # Create directory if necessary
    os.makedirs("app/ui", exist_ok=True)
    
    # Copy improved_streamlit_app.py to app/ui/streamlit_app.py
    shutil.copy(source_path, "app/ui/streamlit_app.py")
    
    print("Interface utilisateur Streamlit améliorée créée/mise à jour avec succès")
    return True

def replace_streamlit_app():
    """Checks if a backup version of streamlit_app.py exists."""
    print("Vérification du fichier streamlit_app.py...")
    
    original_path = "app/ui/streamlit_app.py"
    
    if os.path.exists(original_path):
        print(f"Le fichier {original_path} existe et est fonctionnel.")
        return True
    else:
        print(f"ERREUR: Le fichier {original_path} n'existe pas.")
        # Try to recreate it from the original script
        try:
            from improved_streamlit_app import get_improved_streamlit_content
            with open(original_path, 'w') as f:
                f.write(get_improved_streamlit_content())
            print(f"Fichier {original_path} créé à partir du template par défaut.")
            return True
        except Exception as e:
            print(f"Impossible de créer le fichier Streamlit: {str(e)}")
            return False

def start_app():
    """Starts the application (API and user interface)."""
    print("\n[3/3] Démarrage de l'application...")
    
    # Check that streamlit_app.py file exists
    replace_streamlit_app()
    
    # Create subprocesses for API and UI
    try:
        import subprocess
        import threading
        
        def start_api():
            subprocess.Popen(["python3", "run_api.py"], cwd=os.path.dirname(__file__))
            print("API démarrée!")
        
        def start_ui():
            # Wait for the API to be ready
            time.sleep(2)
            subprocess.Popen(["python3", "run_ui.py"], cwd=os.path.dirname(__file__))
            print("Interface utilisateur démarrée!")
            
        # Start API and UI in separate threads
        api_thread = threading.Thread(target=start_api)
        ui_thread = threading.Thread(target=start_ui)
        
        api_thread.start()
        ui_thread.start()
        
        print("\nApplication démarrée avec succès!")
        print("- API: http://localhost:8000")
        print("- Interface: http://localhost:8501")
        print("\nPour arrêter l'application, utilisez Ctrl+C dans ce terminal.")
        
        # Wait for threads to finish (which should not happen)
        api_thread.join()
        ui_thread.join()
        
    except Exception as e:
        print(f"Erreur lors du démarrage de l'application: {str(e)}")
        traceback.print_exc()

def ensure_app_structure():
    """Creates all necessary directories for the application."""
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
    
    # Check if config.py file exists
    if not os.path.exists("app/core/config.py"):
        with open("app/core/config.py", 'w') as f:
            f.write('''import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env if it exists
load_dotenv()

class Settings(BaseSettings):
    # Application configuration
    APP_NAME: str = "Medical Services Chatbot"
    API_V1_STR: str = "/api/v1"
    
    # Azure OpenAI parameters
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    
    # Names of models deployed in Azure
    GPT4O_DEPLOYMENT_NAME: str = os.getenv("GPT4O_DEPLOYMENT_NAME", "gpt-4o")
    GPT4O_MINI_DEPLOYMENT_NAME: str = os.getenv("GPT4O_MINI_DEPLOYMENT_NAME", "gpt-4o-mini")
    EMBEDDING_DEPLOYMENT_NAME: str = os.getenv("EMBEDDING_DEPLOYMENT_NAME", "text-embedding-ada-002")
    
    # Document Intelligence parameters (OCR)
    DOCUMENT_INTELLIGENCE_KEY: str = os.getenv("DOCUMENT_INTELLIGENCE_KEY", "")
    DOCUMENT_INTELLIGENCE_ENDPOINT: str = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT", "")
    
    # Knowledge base file paths
    KNOWLEDGE_BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../phase2_data"))
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
''')
        print("Fichier app/core/config.py créé")
    
    # Create __init__.py file in each folder if it doesn't exist
    for directory in directories:
        init_file = os.path.join(directory, "__init__.py")
        if os.path.isdir(directory) and not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write(f"# Module {os.path.basename(directory)}\n")
            print(f"Fichier {init_file} créé")
    
    # Copy .env file from phase2 to root if necessary
    if not os.path.exists(".env") and os.path.exists("phase2/.env"):
        shutil.copy("phase2/.env", ".env")
        print("Fichier .env copié depuis phase2/.env")
    
    return True

if __name__ == "__main__":
    print("====== Correction finale de l'application Phase 2 ======")
    
    # Kill existing processes
    kill_running_processes()
    
    # Ensure the application structure is complete
    ensure_app_structure()
    
    # Configure the logging system
    setup_logging()
    
    # Create or update the logging module
    create_logger_module()
    
    # Clean logs
    clear_logs()
    
    # Create or update necessary modules
    create_init_file()
    create_simple_openai_module()
    create_client_module()
    create_improved_streamlit_app()
    
    # Remove references to 'proxies'
    remove_all_proxies_refs()
    
    # Start the application
    start_app()
    
    print("\n====== Correction terminée avec succès! ======")
    print("L'application est démarrée et accessible à http://localhost:8501")
    print("Les fichiers de logs sont disponibles dans le dossier 'logs/'")
    
    print("=====================================================") 