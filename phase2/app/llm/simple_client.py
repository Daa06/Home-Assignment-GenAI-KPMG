import os
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
