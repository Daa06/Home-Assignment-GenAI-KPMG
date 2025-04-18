from loguru import logger

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
