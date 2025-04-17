import json
from typing import Dict, Any, List, Optional
from openai import AzureOpenAI
from ..core.config import settings
from ..api.models import Message, ConversationHistory
from loguru import logger

class ProfileCollector:
    """
    Classe pour gérer la collecte d'informations de profil utilisateur
    via des interactions avec le modèle LLM.
    """
    
    def __init__(self):
        """Initialise le collecteur de profil avec le client Azure OpenAI."""
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.model = settings.GPT4O_DEPLOYMENT_NAME
        logger.info("ProfileCollector initialisé")
    
    def create_system_prompt(self, current_step: Optional[str] = None, 
                              partial_profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Crée le prompt système pour guider la collecte d'informations.
        
        Args:
            current_step: L'étape actuelle de la collecte (si connue)
            partial_profile: Le profil partiel collecté jusqu'à présent
        
        Returns:
            Le prompt système formaté
        """
        # Informations sur les champs à collecter et leurs validations
        fields_info = {
            "first_name": "Prénom de l'utilisateur",
            "last_name": "Nom de famille de l'utilisateur",
            "id_number": "Numéro d'identification à 9 chiffres",
            "gender": "Genre de l'utilisateur",
            "age": "Âge de l'utilisateur entre 0 et 120",
            "hmo_name": "Nom de la caisse maladie (מכבי, מאוחדת, כללית)",
            "hmo_card_number": "Numéro de carte de la caisse maladie à 9 chiffres",
            "insurance_tier": "Niveau d'assurance (זהב, כסף, ארד)"
        }
        
        # Règles de validation
        validation_rules = {
            "id_number": "Doit contenir exactement 9 chiffres",
            "age": "Doit être un nombre entier entre 0 et 120",
            "hmo_name": "Doit être l'une des valeurs suivantes: מכבי, מאוחדת, כללית",
            "hmo_card_number": "Doit contenir exactement 9 chiffres",
            "insurance_tier": "Doit être l'une des valeurs suivantes: זהב, כסף, ארד"
        }
        
        # Construire le prompt de base
        prompt = """Tu es un assistant qui aide à collecter des informations médicales personnelles pour un service de chatbot médical israélien. 
Ta tâche est de collecter les informations suivantes de manière conversationnelle et naturelle:

"""
        
        # Ajouter les informations sur les champs
        for field, description in fields_info.items():
            validation = validation_rules.get(field, "")
            validation_text = f" ({validation})" if validation else ""
            prompt += f"- {field}: {description}{validation_text}\n"
        
        prompt += """
Règles importantes:
1. Communique dans la même langue que l'utilisateur (hébreu ou anglais).
2. Collecte une information à la fois dans un ordre logique.
3. Si une réponse est invalide, explique gentiment pourquoi et redemande.
4. Sois poli, patient et professionnel.
5. Respecte la vie privée de l'utilisateur et explique que ses informations resteront sur son appareil.
6. Ne demande jamais d'informations médicales sensibles ou de diagnostics.
7. Une fois toutes les informations collectées, présente un résumé et demande confirmation.

"""
        
        # Ajouter les informations sur le profil partiel si disponible
        if partial_profile and len(partial_profile) > 0:
            prompt += "Informations déjà collectées:\n"
            for field, value in partial_profile.items():
                prompt += f"- {field}: {value}\n"
            
            # Déterminer la prochaine information à collecter
            collected_fields = set(partial_profile.keys())
            all_fields = set(fields_info.keys())
            missing_fields = all_fields - collected_fields
            
            if missing_fields:
                next_field = next(iter(missing_fields))  # Prendre le premier champ manquant
                prompt += f"\nProchaine information à collecter: {next_field} - {fields_info[next_field]}\n"
            else:
                prompt += "\nToutes les informations ont été collectées. Présente un résumé et demande confirmation.\n"
        else:
            prompt += "\nAucune information n'a encore été collectée. Commence par demander le prénom de l'utilisateur.\n"
        
        # Ajouter des instructions spécifiques à l'étape actuelle si disponible
        if current_step:
            prompt += f"\nÉtape actuelle: {current_step}\n"
        
        return prompt
    
    def format_conversation_history(self, history: ConversationHistory) -> List[Dict[str, str]]:
        """Formate l'historique de conversation pour l'API OpenAI."""
        formatted_messages = []
        for message in history.messages:
            formatted_messages.append({
                "role": message.role,
                "content": message.content
            })
        return formatted_messages
    
    def extract_profile_information(self, conversation_history: ConversationHistory, 
                                    partial_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrait les informations de profil à partir de l'historique de conversation.
        Utilise le LLM pour analyser les réponses et mettre à jour le profil partiel.
        """
        if not conversation_history.messages:
            return partial_profile.copy()
        
        # Créer un prompt spécifique pour l'extraction d'informations
        extract_prompt = """Extrait toutes les informations de profil valides de la conversation précédente. 
Retourne uniquement un objet JSON avec les informations extraites, sans aucun texte additionnel.
N'invente pas d'informations, utilise uniquement celles fournies dans la conversation.

Les champs possibles sont:
- first_name: Prénom
- last_name: Nom de famille
- id_number: Numéro d'ID à 9 chiffres
- gender: Genre
- age: Âge (nombre entier entre 0 et 120)
- hmo_name: Nom de la caisse maladie (מכבי, מאוחדת, כללית)
- hmo_card_number: Numéro de carte à 9 chiffres
- insurance_tier: Niveau d'assurance (זהב, כסף, ארד)

Profil partiel actuel: """ + json.dumps(partial_profile, ensure_ascii=False)
        
        # Formater l'historique de conversation
        formatted_history = self.format_conversation_history(conversation_history)
        
        try:
            # Appeler le modèle avec l'invite d'extraction
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": extract_prompt},
                    *formatted_history
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            extracted_text = response.choices[0].message.content.strip()
            
            # Tenter de parser le JSON extrait
            try:
                # Supprimer les marqueurs de code JSON si présents
                if extracted_text.startswith("```json"):
                    extracted_text = extracted_text.replace("```json", "", 1)
                if extracted_text.endswith("```"):
                    extracted_text = extracted_text[:-3]
                
                extracted_text = extracted_text.strip()
                extracted_info = json.loads(extracted_text)
                
                # Mettre à jour le profil partiel avec les nouvelles informations
                updated_profile = partial_profile.copy()
                updated_profile.update(extracted_info)
                
                return updated_profile
                
            except json.JSONDecodeError as e:
                logger.error(f"Erreur lors du parsing du JSON extrait: {str(e)}")
                logger.debug(f"Texte extrait: {extracted_text}")
                return partial_profile.copy()
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du profil: {str(e)}")
            return partial_profile.copy()
    
    def determine_next_step(self, partial_profile: Dict[str, Any]) -> str:
        """Détermine la prochaine étape de collecte en fonction du profil partiel."""
        all_fields = [
            "first_name", "last_name", "id_number", "gender", 
            "age", "hmo_name", "hmo_card_number", "insurance_tier"
        ]
        
        # Vérifier les champs manquants
        for field in all_fields:
            if field not in partial_profile:
                return f"collecting_{field}"
        
        # Si tous les champs sont présents, passer à la confirmation
        return "confirmation"
    
    def process_message(self, user_message: str, conversation_history: ConversationHistory,
                        partial_profile: Dict[str, Any], current_step: Optional[str] = None) -> Dict[str, Any]:
        """
        Traite un message utilisateur pour la collecte de profil.
        
        Args:
            user_message: Le message de l'utilisateur
            conversation_history: L'historique de la conversation
            partial_profile: Le profil partiel collecté jusqu'à présent
            current_step: L'étape actuelle de la collecte
        
        Returns:
            Un dictionnaire contenant la réponse, l'historique mis à jour et le profil mis à jour
        """
        # Mise à jour de l'historique avec le message utilisateur
        updated_history = ConversationHistory(messages=conversation_history.messages.copy())
        updated_history.messages.append(Message(role="user", content=user_message))
        
        # Déterminer l'étape actuelle si non fournie
        if not current_step:
            current_step = self.determine_next_step(partial_profile)
        
        # Créer le prompt système
        system_prompt = self.create_system_prompt(current_step, partial_profile)
        
        # Formater l'historique de conversation
        formatted_history = self.format_conversation_history(updated_history)
        
        try:
            # Appeler le modèle
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *formatted_history
                ],
                temperature=0.5,
                max_tokens=800
            )
            
            assistant_message = response.choices[0].message.content.strip()
            
            # Mise à jour de l'historique avec la réponse de l'assistant
            updated_history.messages.append(Message(role="assistant", content=assistant_message))
            
            # Extraire et mettre à jour le profil
            updated_profile = self.extract_profile_information(updated_history, partial_profile)
            
            # Déterminer la prochaine étape
            next_step = self.determine_next_step(updated_profile)
            
            return {
                "response": assistant_message,
                "updated_conversation_history": updated_history,
                "updated_profile": updated_profile,
                "next_step": next_step
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {str(e)}")
            error_message = "Je suis désolé, une erreur s'est produite lors du traitement de votre message. Pourriez-vous réessayer?"
            
            # Mise à jour de l'historique avec le message d'erreur
            updated_history.messages.append(Message(role="assistant", content=error_message))
            
            return {
                "response": error_message,
                "updated_conversation_history": updated_history,
                "updated_profile": partial_profile,
                "next_step": current_step
            } 