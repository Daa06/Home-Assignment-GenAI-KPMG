from typing import Dict, Any, List, Optional
from ..core.config import settings
from ..api.models import Message, ConversationHistory, UserProfile
from ..knowledge.embedding import EmbeddingManager
from ..llm.client import create_openai_client
from loguru import logger

class QAProcessor:
    """
    Classe pour gérer les questions-réponses basées sur la base de connaissances
    et le profil utilisateur.
    """
    
    def __init__(self):
        """Initialise le processeur Q&A avec le client Azure OpenAI."""
        try:
            self.client = create_openai_client()
            self.model = settings.GPT4O_DEPLOYMENT_NAME
            self.embedding_manager = EmbeddingManager()
            logger.info("QAProcessor initialisé")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du client OpenAI: {str(e)}")
            raise
    
    def detect_language(self, text: str) -> str:
        """
        Détecte si le texte est en anglais ou en hébreu.
        Retourne 'en' pour l'anglais, 'he' pour l'hébreu, et 'en' par défaut.
        """
        # Plages Unicode pour l'hébreu
        hebrew_chars = ['\u0590', '\u05FF']
        
        # Compter les caractères hébreux
        hebrew_count = sum(1 for char in text if hebrew_chars[0] <= char <= hebrew_chars[1])
        
        # Si plus de 30% des caractères sont hébreux, considérer comme de l'hébreu
        if hebrew_count > 0.3 * len(text):
            return 'he'
        return 'en'
    
    def format_conversation_history(self, history: ConversationHistory, max_turns: int = 10) -> List[Dict[str, str]]:
        """
        Formate l'historique de conversation pour l'API OpenAI.
        Limite le nombre de tours pour éviter de dépasser les limites de tokens.
        """
        formatted_messages = []
        
        # Prendre les derniers messages jusqu'à max_turns
        recent_messages = history.messages[-2*max_turns:] if history.messages else []
        
        for message in recent_messages:
            formatted_messages.append({
                "role": message.role,
                "content": message.content
            })
        
        return formatted_messages
    
    def create_system_prompt(self, user_profile: UserProfile, language: str = 'en') -> str:
        """
        Crée le prompt système pour les questions-réponses.
        
        Args:
            user_profile: Le profil complet de l'utilisateur
            language: La langue détectée ('en' ou 'he')
        
        Returns:
            Le prompt système formaté
        """
        # Instructions de base
        if language == 'he':
            prompt = """אתה עוזר שירות לקוחות ידידותי ומקצועי המספק מידע על שירותי בריאות בישראל.
תפקידך הוא לענות על שאלות מדויקות המבוססות על המידע הזמין בבסיס הידע שלך ועל פרופיל המשתמש.

"""
        else:
            prompt = """You are a friendly and professional customer service assistant providing information about health services in Israel.
Your role is to answer accurate questions based on the information available in your knowledge base and the user's profile.

"""
        
        # Ajouter les informations sur le profil utilisateur
        if language == 'he':
            prompt += f"""פרופיל המשתמש:
- שם: {user_profile.first_name} {user_profile.last_name}
- גיל: {user_profile.age}
- מגדר: {user_profile.gender}
- קופת חולים: {user_profile.hmo_name}
- רמת ביטוח: {user_profile.insurance_tier}

"""
        else:
            prompt += f"""User Profile:
- Name: {user_profile.first_name} {user_profile.last_name}
- Age: {user_profile.age}
- Gender: {user_profile.gender}
- HMO: {user_profile.hmo_name}
- Insurance Tier: {user_profile.insurance_tier}

"""
        
        # Règles et instructions
        if language == 'he':
            prompt += """הנחיות:
1. השתמש תמיד בשפה בה המשתמש פונה אליך (עברית או אנגלית).
2. ספק מידע ספציפי לקופת החולים ורמת הביטוח של המשתמש.
3. חשוב: השתמש בכל מידע רלוונטי ממסמך ההקשר, גם אם אינו תואם באופן מושלם. חלץ וסכם התאמות חלקיות או מידע קשור אם זמין.
4. ציין שהמידע אינו זמין רק אם אתה בהחלט לא יכול למצוא פרטים רלוונטיים כלשהם בהקשר.
5. היה מנומס, מקצועי ותמציתי.
6. בסס את תשובותיך אך ורק על המידע שסופק לך במסמך ההקשר.
7. אל תעביר ביקורת על קופות חולים או שירותים.
8. אל תציע אבחנות רפואיות או המלצות טיפוליות.

ענה כעת על שאלת המשתמש בהתבסס על המידע שסופק בהקשר.
"""
        else:
            prompt += """Guidelines:
1. Always use the language in which the user addresses you (Hebrew or English).
2. Provide information specific to the user's HMO and insurance tier.
3. IMPORTANT: Use ANY relevant information from the context document, even if it's not a perfect match. Extract and summarize partial matches or related information if available.
4. Only state that information is not available if you absolutely cannot find ANY relevant details in the context.
5. Be polite, professional, and concise.
6. Base your answers only on the information provided to you in the context document.
7. Do not criticize HMOs or services.
8. Do not offer medical diagnoses or treatment recommendations.

Now answer the user's question based on the information provided in the context.
"""
        
        return prompt
    
    def process_question(self, user_message: str, conversation_history: ConversationHistory,
                         user_profile: UserProfile) -> Dict[str, Any]:
        """
        Traite une question utilisateur et génère une réponse basée sur la base de connaissances.
        
        Args:
            user_message: La question de l'utilisateur
            conversation_history: L'historique de la conversation
            user_profile: Le profil complet de l'utilisateur
        
        Returns:
            Un dictionnaire contenant la réponse et l'historique mis à jour
        """
        # Détecter la langue de la question
        language = self.detect_language(user_message)
        
        # Mise à jour de l'historique avec la question utilisateur
        updated_history = ConversationHistory(messages=conversation_history.messages.copy())
        updated_history.messages.append(Message(role="user", content=user_message))
        
        # Formater l'historique de conversation
        formatted_history = self.format_conversation_history(updated_history)
        
        # Créer le prompt système
        system_prompt = self.create_system_prompt(user_profile, language)
        
        try:
            # Rechercher les informations pertinentes dans la base de connaissances
            search_results = self.embedding_manager.search(
                query=user_message,
                top_k=5,
                filter_hmo=user_profile.hmo_name,
                filter_tier=user_profile.insurance_tier
            )
            
            # Pour la journalisation
            logger.info(f"Recherche effectuée avec HMO={user_profile.hmo_name}, Tier={user_profile.insurance_tier}")
            logger.info(f"Nombre de résultats trouvés: {len(search_results)}")
            
            # Préparer le contexte à partir des résultats de recherche
            context = "Informations contextuelles extraites de la base de connaissances:\n\n"
            
            for i, result in enumerate(search_results, 1):
                context += f"--- Document {i} ---\n"
                context += result['text'] + "\n\n"
            
            # Ajouter le contexte comme message système additionnel
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": context},
                *formatted_history
            ]
            
            # Appeler le modèle
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            
            # Accéder à la réponse (gestion des deux formats possibles)
            if hasattr(response, 'choices') and hasattr(response.choices[0], 'message'):
                # Nouvelle structure objet
                assistant_message = response.choices[0].message.content.strip()
            elif isinstance(response, dict) and 'choices' in response:
                # Ancienne structure dict
                assistant_message = response["choices"][0]["message"]["content"].strip()
            else:
                logger.error(f"Format de réponse non reconnu: {type(response)}")
                logger.debug(f"Réponse: {response}")
                raise ValueError("Format de réponse OpenAI non reconnu")
            
            # Mise à jour de l'historique avec la réponse de l'assistant
            updated_history.messages.append(Message(role="assistant", content=assistant_message))
            
            # Préparer les métadonnées
            metadata = {
                "sources": [result.get('metadata', {}).get('service_type', 'unknown') for result in search_results],
                "confidence_scores": [result.get('score', 0) for result in search_results],
                "language": language
            }
            
            return {
                "response": assistant_message,
                "updated_conversation_history": updated_history,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la question: {str(e)}")
            
            # Message d'erreur dans la langue appropriée
            if language == 'he':
                error_message = "אני מתנצל, אירעה שגיאה בעיבוד השאלה שלך. אנא נסה שוב מאוחר יותר או שאל שאלה אחרת."
            else:
                error_message = "I apologize, there was an error processing your question. Please try again later or ask a different question."
            
            # Mise à jour de l'historique avec le message d'erreur
            updated_history.messages.append(Message(role="assistant", content=error_message))
            
            return {
                "response": error_message,
                "updated_conversation_history": updated_history,
                "metadata": {"error": str(e)}
            } 