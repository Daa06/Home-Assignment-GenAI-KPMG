import streamlit as st
import requests
import json
import time
import uuid
import os
from typing import Dict, Any, List, Optional
import re
from datetime import datetime
import logging
import inspect

# Configurer le logging
os.makedirs("logs/ui", exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler("logs/ui/streamlit_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("Démarrage de l'application Streamlit")

# Configuration de la page
st.set_page_config(
    page_title="Medical Services Chatbot",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Variables pour les APIs
API_BASE_URL = "http://localhost:8000"
PROFILE_ENDPOINT = f"{API_BASE_URL}/api/v1/profile"
QA_ENDPOINT = f"{API_BASE_URL}/api/v1/qa"

def check_api_connection() -> bool:
    """Checks if the API is accessible."""
    logger.debug("Vérification de la connexion à l'API")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        logger.info(f"Statut de la connexion API: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Erreur de connexion à l'API: {str(e)}")
        return False

# Vérifier la connexion à l'API
if not check_api_connection():
    st.error("The API is not accessible. Please verify that the server is running.")
    logger.error("API inaccessible. Application arrêtée.")
    st.stop()

logger.debug("Initialisation des variables de session")

# Fonction pour logger l'état de la session
def log_session_state():
    """Log l'état actuel de la session"""
    logger.debug(f"SESSION_ID: {st.session_state.get('session_id', 'non défini')}")
    logger.debug(f"MODE: {st.session_state.get('mode', 'non défini')}")
    logger.debug(f"ÉTAPE COURANTE: {st.session_state.get('current_step', 'non définie')}")
    logger.debug(f"PROFILE COMPLET: {st.session_state.get('profile_complete', False)}")
    logger.debug(f"DERNIER MESSAGE: {st.session_state.get('last_message_content', 'aucun')}")
    logger.debug(f"DERNIER HORODATAGE: {st.session_state.get('last_message_time', 0)}")
    
    # Log le nombre de messages dans l'historique
    messages = st.session_state.get('conversation_history', {}).get('messages', [])
    logger.debug(f"NOMBRE DE MESSAGES: {len(messages)}")
    
    if len(messages) > 0:
        logger.debug("DERNIER MESSAGE DE L'HISTORIQUE:")
        logger.debug(f"  Role: {messages[-1].get('role', 'inconnu')}")
        logger.debug(f"  Contenu: {messages[-1].get('content', 'vide')[:50]}...")

# Initialisation des variables de session
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    logger.info(f"Nouvelle session créée avec ID: {st.session_state.session_id}")

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = {"messages": []}
    logger.debug("Historique de conversation initialisé")

if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}
    logger.debug("Profil utilisateur initialisé")

if "profile_complete" not in st.session_state:
    st.session_state.profile_complete = False
    logger.debug("État du profil initialisé à incomplet")

if "mode" not in st.session_state:
    st.session_state.mode = "profile"  # 'profile' ou 'qa'
    logger.debug("Mode initial défini sur 'profile'")

if "current_step" not in st.session_state:
    st.session_state.current_step = "collecting_first_name"
    logger.debug("Étape initiale définie sur 'collecting_first_name'")

if "initialized" not in st.session_state:
    st.session_state.initialized = False
    # Ajouter un message d'accueil initial sans appeler l'API
    st.session_state.conversation_history["messages"] = [{
        "role": "assistant", 
        "content": "Hello! Let's start by getting to know you a bit better. Could you please tell me your first name?"
    }]
    st.session_state.initialized = True
    logger.info("Message d'accueil initial ajouté à l'historique")

# Add a variable to avoid duplicate submissions
if "last_message_time" not in st.session_state:
    st.session_state.last_message_time = 0
    logger.debug("Variable last_message_time initialisée")

if "last_message_content" not in st.session_state:
    st.session_state.last_message_content = ""
    logger.debug("Variable last_message_content initialisée")

# Add a variable to track if a message has been submitted in this session
if "message_submitted" not in st.session_state:
    st.session_state.message_submitted = False
    logger.debug("Variable message_submitted initialisée")

# Add a counter to generate unique form keys
if "form_key_counter" not in st.session_state:
    st.session_state.form_key_counter = 0
    logger.debug("Variable form_key_counter initialisée")

# Log the initial state of the session
log_session_state()

def detect_language(text: str) -> str:
    """Detects if text is primarily in Hebrew or English."""
    # Unicode ranges for Hebrew
    hebrew_chars = ['\u0590', '\u05FF']
    
    # Count Hebrew characters
    hebrew_count = sum(1 for char in text if hebrew_chars[0] <= char <= hebrew_chars[1])
    
    # If more than 30% of characters are Hebrew, consider it Hebrew
    if hebrew_count > 0.3 * len(text):
        return 'he'
    return 'en'

def is_rtl(text: str) -> bool:
    """Detects if text should be displayed right-to-left."""
    return detect_language(text) == 'he'

def format_time(timestamp: Optional[str] = None) -> str:
    """Formats a timestamp to local time."""
    if timestamp is None:
        now = datetime.now()
    else:
        try:
            now = datetime.fromisoformat(timestamp)
        except:
            now = datetime.now()
    
    return now.strftime("%H:%M")

def call_api(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Calls the API with the provided data."""
    caller_frame = inspect.currentframe().f_back
    caller_function = caller_frame.f_code.co_name if caller_frame else "unknown"
    
    logger.debug(f"Appel API depuis {caller_function} vers {endpoint}")
    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": st.session_state.session_id
    }
    
    try:
        logger.debug(f"Données envoyées à l'API: {json.dumps(data)[:100]}...")
        
        response = requests.post(
            endpoint,
            headers=headers,
            data=json.dumps(data),
            timeout=60
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        logger.debug(f"Réponse API reçue: {response.status_code}")
        return response.json()
    
    except requests.RequestException as e:
        logger.error(f"Erreur de communication avec l'API: {str(e)}")
        st.error(f"Error communicating with the API: {str(e)}")
        return {
            "response": "I'm sorry, there was an error communicating with the server. Please try again later.",
            "updated_conversation_history": data.get("conversation_history", {"messages": []}),
            "metadata": {"error": str(e)}
        }

def process_profile_message(user_message: str) -> None:
    """Processes a message for profile collection."""
    try:
        # Save the current state for comparison
        previous_step = st.session_state.current_step
        
        # CORRECTION: Keep the current history to avoid duplicates
        current_messages = [msg.copy() for msg in st.session_state.conversation_history["messages"]]
        
        # Add the user message to the local history before calling the API
        st.session_state.conversation_history["messages"].append({
            "role": "user",
            "content": user_message
        })
        
        # Prepare data for the API
        data = {
            "user_message": user_message,
            "conversation_history": {"messages": current_messages},  # Send history WITHOUT the new message
            "partial_profile": st.session_state.user_profile,
            "current_step": st.session_state.current_step
        }
        
        # Call the API
        response = call_api(PROFILE_ENDPOINT, data)
        
        # Check if the response is valid
        if not response or "response" not in response:
            st.error("Invalid API response")
            return
        
        # Add only the assistant's response to the history
        st.session_state.conversation_history["messages"].append({
            "role": "assistant",
            "content": response["response"]
        })
        
        # Update the profile if available
        if "metadata" in response and "updated_profile" in response["metadata"]:
            st.session_state.user_profile = response["metadata"]["updated_profile"]
            logger.info(f"Profil mis à jour: {st.session_state.user_profile}")
        
        # Update the current step if available
        if "metadata" in response and "next_step" in response["metadata"]:
            new_step = response["metadata"]["next_step"]
            
            # Log the step change
            if new_step != previous_step:
                logger.info(f"Changement d'étape: {previous_step} -> {new_step}")
            
            st.session_state.current_step = new_step
            
            # Check if the profile is complete
            if st.session_state.current_step == "confirmation":
                st.session_state.profile_complete = True
                logger.info("Profil utilisateur complet!")
                
                # If the profile is complete and we receive a confirmation, offer to switch to QA mode
                if user_message.upper() in ["YES", "Y", "OUI"] and st.session_state.profile_complete:
                    # Notify the user that we are changing mode
                    logger.info("Profil confirmé, passage automatique en mode Q&A")
                    
                    # Add a message to the history to inform about the mode change
                    st.session_state.conversation_history["messages"].append({
                        "role": "assistant",
                        "content": "Your profile is now complete! I'm switching to Q&A mode to help answer your questions about medical services."
                    })
                    
                    # Change the mode after adding the message (will affect the next cycle)
                    st.session_state.mode = "qa"
        
        # Reset the submission flag
        st.session_state.message_submitted = False
        
        # Log the session state after processing
        logger.debug("État de la session après traitement du message:")
        log_session_state()
        
        # Always force a rerun after processing to update the interface
        st.experimental_rerun()
        
    except Exception as e:
        st.error(f"Error processing message: {str(e)}")
        logger.error(f"Error in process_profile_message: {str(e)}")

def process_qa_message(user_message: str) -> None:
    """Processes a question and generates an answer."""
    try:
        # CORRECTION: Keep the current history to avoid duplicates
        current_messages = [msg.copy() for msg in st.session_state.conversation_history["messages"]]
        
        # Add the user message to the local history before calling the API
        st.session_state.conversation_history["messages"].append({
            "role": "user",
            "content": user_message
        })
        
        # Prepare data for the API
        data = {
            "user_message": user_message,
            "conversation_history": {"messages": current_messages},  # Send history WITHOUT the new message
            "user_profile": st.session_state.user_profile
        }
        
        # Call the API
        response = call_api(QA_ENDPOINT, data)
        
        # Check if the response is valid
        if not response or "response" not in response:
            st.error("Invalid API response")
            return
        
        # Add only the assistant's response to the history
        st.session_state.conversation_history["messages"].append({
            "role": "assistant",
            "content": response["response"]
        })
        
        # Reset the submission flag
        st.session_state.message_submitted = False
        
        # Forcer un rerun Streamlit pour rafraîchir l'interface
        st.experimental_rerun()
            
    except Exception as e:
        st.error(f"Error processing message: {str(e)}")
        logger.error(f"Error in process_qa_message: {str(e)}")

def reset_session() -> None:
    """Completely resets the session."""
    logger.info("Réinitialisation de la session")
    # Conserver uniquement l'ID de session
    session_id = st.session_state.session_id
    
    # Effacer toutes les variables de session
    for key in list(st.session_state.keys()):
        if key != "session_id":
            del st.session_state[key]
    
    # Réinitialiser les variables de base
    st.session_state.conversation_history = {"messages": []}
    st.session_state.user_profile = {}
    st.session_state.profile_complete = False
    st.session_state.mode = "profile"
    st.session_state.current_step = "collecting_first_name"
    st.session_state.initialized = False
    st.session_state.message_submitted = False
    # Réinitialiser le compteur de clé de formulaire
    st.session_state.form_key_counter = 0
    st.session_state.last_message_time = 0
    st.session_state.last_message_content = ""
    
    # Ajouter un message d'accueil initial
    st.session_state.conversation_history["messages"] = [{
        "role": "assistant", 
        "content": "Hello! Let's start by getting to know you a bit better. Could you please tell me your first name?"
    }]
    st.session_state.initialized = True
    logger.info("Session réinitialisée avec succès")
    log_session_state()

def change_mode(new_mode: str) -> None:
    """Changes the application mode."""
    logger.info(f"Changement de mode: {st.session_state.mode} -> {new_mode}")
    if new_mode == "qa" and not st.session_state.profile_complete:
        logger.warning("Tentative de passage en mode Q&A avec un profil incomplet")
        st.warning("Please complete your profile before using Q&A mode.")
        return
    
    old_mode = st.session_state.mode
    st.session_state.mode = new_mode
    
    if new_mode == "profile" and old_mode == "qa":
        # Réinitialiser l'historique pour le mode profil
        st.session_state.conversation_history = {"messages": []}
        st.session_state.initialized = False
        # Ajouter un message d'accueil initial
        st.session_state.conversation_history["messages"] = [{
            "role": "assistant", 
            "content": "Hello! Let's start by getting to know you a bit better. Could you please tell me your first name?"
        }]
        st.session_state.initialized = True
        logger.debug("Historique réinitialisé pour le mode profil")
    elif new_mode == "qa" and old_mode == "profile":
        # Conserver l'historique existant et ajouter uniquement le message de transition
        st.session_state.conversation_history["messages"].append({
            "role": "assistant", 
            "content": "I'm ready to answer your questions about medical services based on your profile information. What would you like to know?"
        })
        logger.debug("Message de transition ajouté pour le mode Q&A")
    
    # Reset the submission flag
    st.session_state.message_submitted = False
    # Réinitialiser le compteur de clé de formulaire
    st.session_state.form_key_counter = 0
    st.session_state.last_message_time = 0
    st.session_state.last_message_content = ""
    logger.debug("Variables de contrôle des messages dupliqués réinitialisées")
    log_session_state()

# Functions for message display
def st_message(message, is_user=False, key=None):
    """Display a chat message with appropriate styling."""
    message_container = st.container()
    
    with message_container:
        if is_user:
            st.markdown(f'<div class="user-message">You: {message}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-message">Assistant: {message}</div>', unsafe_allow_html=True)

# Interface utilisateur
st.title("Medical Services Chatbot")

# Barre latérale pour le changement de mode
with st.sidebar:
    st.header("Options")
    
    # Afficher le profil utilisateur s'il est complet
    if st.session_state.profile_complete:
        st.subheader("User Profile")
        st.write(f"**Name:** {st.session_state.user_profile.get('first_name', '')} {st.session_state.user_profile.get('last_name', '')}")
        st.write(f"**ID:** {st.session_state.user_profile.get('id_number', '')}")
        st.write(f"**Age:** {st.session_state.user_profile.get('age', '')}")
        st.write(f"**HMO:** {st.session_state.user_profile.get('hmo_name', '')}")
        st.write(f"**Insurance:** {st.session_state.user_profile.get('insurance_tier', '')}")
        
        # Bouton pour changer de mode
        if st.session_state.mode == "profile":
            if st.button("Switch to Q&A Mode"):
                change_mode("qa")
        else:
            if st.button("Return to Profile Mode"):
                change_mode("profile")
    
    # Bouton de réinitialisation
    if st.button("Reset Conversation"):
        reset_session()

# Conteneur principal pour l'affichage de la conversation
chat_container = st.container()

# Afficher l'historique de conversation
with chat_container:
    # Afficher les messages de l'historique
    messages = st.session_state.conversation_history.get("messages", [])
    for i, message in enumerate(messages):
        if message["role"] == "user":
            st_message(message["content"], is_user=True, key=f"user_{i}")
        else:
            st_message(message["content"], is_user=False, key=f"assistant_{i}")

# Conteneur pour le champ de saisie
input_container = st.container()

# Champ de saisie pour l'utilisateur
with input_container:
    # Utiliser un formulaire avec une clé dynamique pour forcer le rechargement du formulaire
    form_key = f"message_form_{st.session_state.form_key_counter}"
    with st.form(key=form_key):
        user_input = st.text_input("Your message:", key=f"user_input_{st.session_state.form_key_counter}")
        submit_button = st.form_submit_button("Send")
        
        # Traiter l'entrée de l'utilisateur uniquement lorsque le formulaire est soumis
        if submit_button and user_input and not st.session_state.message_submitted:
            logger.debug(f"Formulaire soumis avec le message: '{user_input}'")
            current_time = time.time()
            
            # Log les informations de contrôle des doublons
            logger.debug(f"Temps écoulé depuis le dernier message: {current_time - st.session_state.last_message_time:.2f}s")
            logger.debug(f"Message précédent: '{st.session_state.last_message_content}'")
            logger.debug(f"Message actuel: '{user_input}'")
            logger.debug(f"Messages identiques: {user_input == st.session_state.last_message_content}")
            
            # Marquer le message comme soumis pour éviter les doubles soumissions
            st.session_state.message_submitted = True
            
            # Mettre à jour les variables de contrôle
            st.session_state.last_message_time = current_time
            st.session_state.last_message_content = user_input
            
            # Incrémenter le compteur de clé de formulaire pour le prochain cycle
            st.session_state.form_key_counter += 1
            logger.debug(f"Compteur de formulaire incrémenté: {st.session_state.form_key_counter}")
            
            # Traiter le message
            if st.session_state.mode == "profile":
                process_profile_message(user_input)
            else:
                process_qa_message(user_input)
            
            # Logger l'état de la session après traitement
            logger.debug("État de la session après traitement du message:")
            log_session_state()

            # Réinitialiser le flag de soumission mais ne pas changer le compteur ici
            st.session_state.message_submitted = False
            
            # Forcer un rerun Streamlit pour rafraîchir l'interface
            st.experimental_rerun()

# CSS personnalisé
st.markdown("""
<style>
.user-message {
    background-color: #e6f7ff;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
    text-align: right;
}
.assistant-message {
    background-color: #f0f0f0;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.stTextArea textarea {
    direction: auto;
}
</style>
""", unsafe_allow_html=True) 