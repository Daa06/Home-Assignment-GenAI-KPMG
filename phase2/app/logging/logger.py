import os
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
