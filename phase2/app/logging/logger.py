import os
import sys
import json
from datetime import datetime
from loguru import logger
from ..core.config import settings

# Configuration du niveau de log
LOG_LEVEL = settings.LOG_LEVEL

# Répertoire des logs
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)

# Fichier de log avec rotation journalière
log_file = os.path.join(log_dir, "app_{time:YYYY-MM-DD}.log")

# Format personnalisé
log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"

# Configurer loguru
logger.remove()  # Supprimer la configuration par défaut
logger.add(sys.stderr, level=LOG_LEVEL, format=log_format)  # Ajouter la sortie console
logger.add(
    log_file,
    rotation="00:00",  # Nouvelle rotation à minuit
    retention="30 days",  # Conserver les logs pendant 30 jours
    compression="zip",  # Compresser les anciens logs
    level=LOG_LEVEL,
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
    # Créer une copie des données pour ne pas modifier l'original
    safe_data = request_data.copy() if request_data else {}
    
    # Supprimer les informations sensibles si elles existent
    if isinstance(safe_data, dict):
        # Masquer les informations sensibles dans user_profile si présent
        if 'user_profile' in safe_data and isinstance(safe_data['user_profile'], dict):
            profile = safe_data['user_profile']
            if 'id_number' in profile:
                profile['id_number'] = f"***{profile.get('id_number', '')[-4:]}"
            if 'hmo_card_number' in profile:
                profile['hmo_card_number'] = f"***{profile.get('hmo_card_number', '')[-4:]}"
        
        # Masquer les informations sensibles dans partial_profile si présent
        if 'partial_profile' in safe_data and isinstance(safe_data['partial_profile'], dict):
            partial = safe_data['partial_profile']
            if 'id_number' in partial:
                partial['id_number'] = f"***{partial.get('id_number', '')[-4:]}"
            if 'hmo_card_number' in partial:
                partial['hmo_card_number'] = f"***{partial.get('hmo_card_number', '')[-4:]}"
    
    try:
        # Enregistrer les données de requête sécurisées
        logger.info(f"API Request | Endpoint: {endpoint} | User: {user_id} | Data: {json.dumps(safe_data, ensure_ascii=False)}")
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
        # Enregistrer uniquement les métadonnées de la réponse, pas le contenu complet
        metadata = {
            "status_code": status_code,
            "processing_time_ms": processing_time,
            "response_size": len(json.dumps(response_data)) if response_data else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"API Response | Endpoint: {endpoint} | User: {user_id} | Status: {status_code} | Time: {processing_time:.2f}ms")
        
        # Enregistrer les erreurs en détail
        if status_code >= 400:
            logger.error(f"API Error | Endpoint: {endpoint} | Status: {status_code} | Details: {response_data}")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de la réponse API: {str(e)}")

# Exporter les fonctions et objets
__all__ = ["logger", "log_api_request", "log_api_response"] 