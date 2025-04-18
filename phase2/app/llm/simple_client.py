import os
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
