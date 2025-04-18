import json
from typing import Dict, Any, List, Optional
from ..core.config import settings
from ..api.models import Message, ConversationHistory
from ..llm.client import create_openai_client
from loguru import logger

class ProfileCollector:
    """
    Classe pour gérer la collecte d'informations de profil utilisateur
    via des interactions avec le modèle LLM.
    """
    
    def __init__(self):
        """Initialise le collecteur de profil avec le client Azure OpenAI."""
        try:
            self.client = create_openai_client()
            self.model = settings.GPT4O_DEPLOYMENT_NAME
            logger.info("ProfileCollector initialisé")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du client OpenAI: {str(e)}")
            raise
    
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
            "first_name": "User's first name",
            "last_name": "User's last name",
            "id_number": "9-digit identification number",
            "gender": "User's gender",
            "age": "User's age between 0 and 120",
            "hmo_name": "Health insurance provider name (מכבי, מאוחדת, כללית)",
            "hmo_card_number": "9-digit health insurance card number",
            "insurance_tier": "Insurance tier (זהב, כסף, ארד)"
        }
        
        # Règles de validation
        validation_rules = {
            "id_number": "Must contain exactly 9 digits",
            "age": "Must be an integer between 0 and 120",
            "hmo_name": "Must be one of the following values: מכבי, מאוחדת, כללית",
            "hmo_card_number": "Must contain exactly 9 digits",
            "insurance_tier": "Must be one of the following values: זהב, כסף, ארד"
        }
        
        # Construire le prompt de base
        prompt = """You are an assistant helping to collect personal medical information for an Israeli medical chatbot service.
Your task is to collect the following information in a conversational and natural way:

"""
        
        # Ajouter les informations sur les champs
        for field, description in fields_info.items():
            validation = validation_rules.get(field, "")
            validation_text = f" ({validation})" if validation else ""
            prompt += f"- {field}: {description}{validation_text}\n"
        
        prompt += """
Important rules:
1. Communicate in the same language as the user (Hebrew or English).
2. Collect one piece of information at a time in a logical order.
3. If a response is invalid, gently explain why and ask again.
4. Be polite, patient, and professional.
5. Respect the user's privacy and explain that their information will remain on their device.
6. Never ask for sensitive medical information or diagnoses.
7. Once all information is collected, present a summary and ask for confirmation.

"""
        
        # Ajouter les informations sur le profil partiel si disponible
        if partial_profile and len(partial_profile) > 0:
            prompt += "Information already collected:\n"
            for field, value in partial_profile.items():
                prompt += f"- {field}: {value}\n"
            
            # Déterminer la prochaine information à collecter
            collected_fields = set(partial_profile.keys())
            all_fields = set(fields_info.keys())
            missing_fields = all_fields - collected_fields
            
            if missing_fields:
                next_field = next(iter(missing_fields))  # Prendre le premier champ manquant
                prompt += f"\nNext information to collect: {next_field} - {fields_info[next_field]}\n"
            else:
                prompt += "\nAll information has been collected. Present a summary and ask for confirmation.\n"
        else:
            prompt += "\nNo information has been collected yet. Start by asking for the user's first name.\n"
        
        # Ajouter des instructions spécifiques à l'étape actuelle si disponible
        if current_step:
            prompt += f"\nCurrent step: {current_step}\n"
        
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
                                   partial_profile: Dict[str, Any], current_step: Optional[str] = None) -> Dict[str, Any]:
        """
        Extrait les informations de profil à partir de l'historique de conversation.
        Utilise le LLM pour analyser les réponses et mettre à jour le profil partiel.
        """
        if not conversation_history.messages:
            return partial_profile.copy()
            
        # Obtenir le dernier message utilisateur
        last_user_message = ""
        for msg in reversed(conversation_history.messages):
            if msg.role == "user":
                last_user_message = msg.content.strip()
                break
        
        # Traiter directement les champs simples basés sur l'étape actuelle
        updated_profile = partial_profile.copy()
        field_name = current_step.replace("collecting_", "") if current_step else None
        
        if field_name and last_user_message:
            import re
            # Traitement spécifique selon le type de champ
            if field_name == "id_number" and re.match(r'^\d{9}$', last_user_message):
                updated_profile["id_number"] = last_user_message
                logger.info(f"ID number directement extrait: {last_user_message}")
                return updated_profile
                
            elif field_name == "hmo_card_number" and re.match(r'^\d{9}$', last_user_message):
                updated_profile["hmo_card_number"] = last_user_message
                logger.info(f"HMO card number directement extrait: {last_user_message}")
                return updated_profile
                
            elif field_name == "age" and re.match(r'^\d{1,3}$', last_user_message):
                try:
                    age = int(last_user_message)
                    if 0 <= age <= 120:
                        updated_profile["age"] = age
                        logger.info(f"Âge directement extrait: {age}")
                        return updated_profile
                except ValueError:
                    pass
                    
            elif field_name == "gender" and last_user_message.lower() in ["male", "female", "other", "m", "f", "o"]:
                gender = last_user_message.upper() if last_user_message.lower() in ["m", "f", "o"] else last_user_message.upper()
                updated_profile["gender"] = gender
                logger.info(f"Genre directement extrait: {gender}")
                return updated_profile
                
            elif field_name == "hmo_name" and last_user_message in ["מכבי", "מאוחדת", "כללית"]:
                updated_profile["hmo_name"] = last_user_message
                logger.info(f"HMO name directement extrait: {last_user_message}")
                return updated_profile
                
            elif field_name == "insurance_tier" and last_user_message in ["זהב", "כסף", "ארד"]:
                updated_profile["insurance_tier"] = last_user_message
                logger.info(f"Insurance tier directement extrait: {last_user_message}")
                return updated_profile
                
            elif field_name in ["first_name", "last_name"]:
                # Pour les noms, on accepte la plupart des entrées textuelles simples
                if len(last_user_message) > 0 and len(last_user_message) < 50:
                    updated_profile[field_name] = last_user_message
                    logger.info(f"{field_name} directement extrait: {last_user_message}")
                    return updated_profile
        
        # Créer un prompt spécifique pour l'extraction d'informations
        extract_prompt = """Extract all valid profile information from the previous conversation.
Return only a JSON object with the extracted information, without any additional text.
Do not invent information, use only what was provided in the conversation.

Your response MUST be only a valid JSON object, no other text.

Example of a valid response format:
```json
{
  "field1": "value1",
  "field2": "value2"
}
```

Possible fields are:
- first_name: First name
- last_name: Last name
- id_number: 9-digit ID number (if the user provides a valid 9-digit number, include it)
- gender: Gender
- age: Age (integer between 0 and 120)
- hmo_name: Health insurance provider name (מכבי, מאוחדת, כללית)
- hmo_card_number: 9-digit card number
- insurance_tier: Insurance tier (זהב, כסף, ארד)

Current partial profile: """ + json.dumps(partial_profile, ensure_ascii=False)
        
        # Ajouter une vérification spécifique pour l'ID number si nécessaire
        if current_step == "collecting_id_number" or "id_number" not in partial_profile:
            import re
            if re.match(r'^\d{9}$', last_user_message):
                # Si le message utilisateur est exactement 9 chiffres, c'est probablement un ID
                # On va explicitement le mentionner dans le prompt
                extract_prompt += f"\n\nNote: The user message '{last_user_message}' appears to be a valid 9-digit ID number."
        
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
            
            # Accéder à la réponse (gestion des deux formats possibles)
            if hasattr(response, 'choices') and hasattr(response.choices[0], 'message'):
                # Nouvelle structure objet
                extracted_text = response.choices[0].message.content.strip()
            elif isinstance(response, dict) and 'choices' in response:
                # Ancienne structure dict
                extracted_text = response["choices"][0]["message"]["content"].strip()
            else:
                logger.error("Format de réponse non reconnu")
                logger.debug(f"Type de réponse: {type(response)}")
                return partial_profile.copy()
            
            # Tenter de parser le JSON extrait
            try:
                # Supprimer les marqueurs de code JSON si présents
                if extracted_text.startswith("```json"):
                    extracted_text = extracted_text.replace("```json", "", 1)
                elif extracted_text.startswith("```"):
                    extracted_text = extracted_text.replace("```", "", 1)
                
                if extracted_text.endswith("```"):
                    extracted_text = extracted_text[:-3]
                
                # Nettoyer le texte
                extracted_text = extracted_text.strip()
                
                # Si le texte est vide, retourner le profil partiel existant
                if not extracted_text:
                    logger.warning("Texte extrait vide, aucune mise à jour du profil")
                    return partial_profile.copy()
                
                # Vérification manuelle pour l'ID number
                import re
                if current_step == "collecting_id_number" or "id_number" not in partial_profile:
                    if re.match(r'^\d{9}$', last_user_message):
                        # Forcer l'ajout de l'ID number si le message utilisateur correspond au format
                        logger.info(f"ID number manuellement extrait du message: {last_user_message}")
                        extracted_info = {"id_number": last_user_message}
                        updated_profile = partial_profile.copy()
                        updated_profile.update(extracted_info)
                        return updated_profile
                
                # Essayer de charger le JSON
                try:
                    extracted_info = json.loads(extracted_text)
                except json.JSONDecodeError:
                    # Si la première tentative échoue, essayer de trouver et extraire juste la partie JSON
                    import re
                    json_pattern = r'\{.*\}'
                    match = re.search(json_pattern, extracted_text, re.DOTALL)
                    if match:
                        try:
                            extracted_info = json.loads(match.group(0))
                        except json.JSONDecodeError:
                            # Si ça échoue encore, logguer l'erreur et retourner le profil existant
                            logger.error("Impossible de parser le JSON même après nettoyage")
                            logger.debug(f"Texte extrait après nettoyage: {match.group(0)}")
                            return partial_profile.copy()
                    else:
                        logger.error("Aucun objet JSON trouvé dans la réponse")
                        logger.debug(f"Texte extrait: {extracted_text}")
                        return partial_profile.copy()
                
                # Mettre à jour le profil partiel avec les nouvelles informations
                updated_profile = partial_profile.copy()
                updated_profile.update(extracted_info)
                
                logger.info(f"Profil mis à jour avec succès, champs extraits: {list(extracted_info.keys())}")
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
        # Définir l'ordre strict de collecte des champs
        collection_order = [
            "first_name", "last_name", "id_number", "gender", 
            "age", "hmo_name", "hmo_card_number", "insurance_tier"
        ]
        
        # Suivre l'ordre prédéfini pour déterminer le prochain champ à collecter
        for field in collection_order:
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
            
            # Accéder à la réponse (gestion des deux formats possibles)
            if hasattr(response, 'choices') and hasattr(response.choices[0], 'message'):
                # Nouvelle structure objet
                assistant_message = response.choices[0].message.content.strip()
            elif isinstance(response, dict) and 'choices' in response:
                # Ancienne structure dict
                assistant_message = response["choices"][0]["message"]["content"].strip()
            else:
                logger.error("Format de réponse non reconnu")
                raise ValueError("Format de réponse OpenAI non reconnu")
            
            # Mise à jour de l'historique avec la réponse de l'assistant
            updated_history.messages.append(Message(role="assistant", content=assistant_message))
            
            # Extraire et mettre à jour le profil
            updated_profile = self.extract_profile_information(updated_history, partial_profile, current_step)
            
            # Déterminer la prochaine étape
            next_step = self.determine_next_step(updated_profile)
            
            return {
                "response": assistant_message,
                "updated_history": updated_history,
                "updated_profile": updated_profile,
                "next_step": next_step
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {str(e)}")
            error_message = "Je suis désolé, une erreur s'est produite lors du traitement de votre message."
            
            # Mise à jour de l'historique avec le message d'erreur
            updated_history.messages.append(Message(role="assistant", content=error_message))
            
            return {
                "response": error_message,
                "updated_history": updated_history,
                "updated_profile": partial_profile,
                "next_step": current_step
            } 