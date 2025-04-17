from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import re

class UserProfile(BaseModel):
    """Modèle pour les informations de profil utilisateur"""
    first_name: str = Field(..., description="Prénom de l'utilisateur")
    last_name: str = Field(..., description="Nom de famille de l'utilisateur")
    id_number: str = Field(..., description="Numéro d'identification à 9 chiffres")
    gender: str = Field(..., description="Genre de l'utilisateur")
    age: int = Field(..., description="Âge de l'utilisateur entre 0 et 120")
    hmo_name: str = Field(..., description="Nom de la caisse maladie (מכבי, מאוחדת, כללית)")
    hmo_card_number: str = Field(..., description="Numéro de carte de la caisse maladie à 9 chiffres")
    insurance_tier: str = Field(..., description="Niveau d'assurance (זהב, כסף, ארד)")

    @validator('id_number')
    def validate_id_number(cls, v):
        if not re.match(r'^\d{9}$', v):
            raise ValueError('Le numéro d\'identification doit contenir exactement 9 chiffres')
        return v
    
    @validator('age')
    def validate_age(cls, v):
        if not 0 <= v <= 120:
            raise ValueError('L\'âge doit être compris entre 0 et 120')
        return v
    
    @validator('hmo_name')
    def validate_hmo_name(cls, v):
        valid_hmos = ['מכבי', 'מאוחדת', 'כללית']
        if v not in valid_hmos:
            raise ValueError(f'La caisse maladie doit être l\'une des suivantes: {", ".join(valid_hmos)}')
        return v
    
    @validator('hmo_card_number')
    def validate_hmo_card(cls, v):
        if not re.match(r'^\d{9}$', v):
            raise ValueError('Le numéro de carte HMO doit contenir exactement 9 chiffres')
        return v
    
    @validator('insurance_tier')
    def validate_insurance_tier(cls, v):
        valid_tiers = ['זהב', 'כסף', 'ארד']
        if v not in valid_tiers:
            raise ValueError(f'Le niveau d\'assurance doit être l\'un des suivants: {", ".join(valid_tiers)}')
        return v

class Message(BaseModel):
    """Modèle pour un message dans la conversation"""
    role: str = Field(..., description="Rôle du message (user ou assistant)")
    content: str = Field(..., description="Contenu du message")

class ConversationHistory(BaseModel):
    """Modèle pour l'historique de la conversation"""
    messages: List[Message] = Field(default_factory=list, description="Liste des messages dans la conversation")

class ProfileRequest(BaseModel):
    """Modèle pour la requête de collecte de profil"""
    current_step: Optional[str] = Field(None, description="Étape actuelle de la collecte")
    partial_profile: Dict[str, Any] = Field(default_factory=dict, description="Profil partiel collecté jusqu'à présent")
    conversation_history: ConversationHistory = Field(default_factory=ConversationHistory, description="Historique de la conversation")
    user_message: str = Field(..., description="Message de l'utilisateur")

class QARequest(BaseModel):
    """Modèle pour la requête de Q&A"""
    user_profile: UserProfile = Field(..., description="Profil complet de l'utilisateur")
    conversation_history: ConversationHistory = Field(default_factory=ConversationHistory, description="Historique de la conversation")
    user_message: str = Field(..., description="Question de l'utilisateur")

class AIResponse(BaseModel):
    """Modèle pour la réponse du système"""
    response: str = Field(..., description="Réponse du système")
    updated_conversation_history: ConversationHistory = Field(..., description="Historique de conversation mis à jour")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées additionnelles") 