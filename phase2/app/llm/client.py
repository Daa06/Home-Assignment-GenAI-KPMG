from loguru import logger

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
