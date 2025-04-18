import os
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