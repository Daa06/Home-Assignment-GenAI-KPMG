import streamlit as st
import requests
import json
import time
import uuid
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Chatbot des Services Médicaux",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Variables pour les APIs
API_BASE_URL = "http://localhost:8000/api/v1"  # À remplacer par l'URL de l'API en production
PROFILE_ENDPOINT = f"{API_BASE_URL}/profile"
QA_ENDPOINT = f"{API_BASE_URL}/qa"

# Initialisation des variables de session
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = {"messages": []}

if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}

if "profile_complete" not in st.session_state:
    st.session_state.profile_complete = False

if "mode" not in st.session_state:
    st.session_state.mode = "profile"  # 'profile' ou 'qa'

if "current_step" not in st.session_state:
    st.session_state.current_step = None

# Fonctions utilitaires
def detect_language(text: str) -> str:
    """Détecte si le texte est principalement en hébreu ou en anglais."""
    # Plages Unicode pour l'hébreu
    hebrew_chars = ['\u0590', '\u05FF']
    
    # Compter les caractères hébreux
    hebrew_count = sum(1 for char in text if hebrew_chars[0] <= char <= hebrew_chars[1])
    
    # Si plus de 30% des caractères sont hébreux, considérer comme de l'hébreu
    if hebrew_count > 0.3 * len(text):
        return 'he'
    return 'en'

def is_rtl(text: str) -> bool:
    """Détecte si le texte doit être affiché de droite à gauche."""
    return detect_language(text) == 'he'

def format_time(timestamp: Optional[str] = None) -> str:
    """Formate un timestamp en heure locale."""
    if timestamp is None:
        now = datetime.now()
    else:
        try:
            now = datetime.fromisoformat(timestamp)
        except:
            now = datetime.now()
    
    return now.strftime("%H:%M")

def call_api(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Appelle l'API avec les données fournies."""
    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": st.session_state.session_id
    }
    
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            data=json.dumps(data),
            timeout=60  # Timeout de 60 secondes
        )
        
        # Vérifier si la requête a réussi
        response.raise_for_status()
        
        return response.json()
    
    except requests.RequestException as e:
        st.error(f"Erreur lors de la communication avec l'API: {str(e)}")
        return {
            "response": "Je suis désolé, une erreur s'est produite lors de la communication avec le serveur. Veuillez réessayer plus tard.",
            "updated_conversation_history": data.get("conversation_history", {"messages": []}),
            "metadata": {"error": str(e)}
        }

def process_profile_message(user_message: str) -> None:
    """Traite un message utilisateur pour la collecte de profil."""
    if not user_message.strip():
        return
    
    # Préparer les données pour l'API
    request_data = {
        "user_message": user_message,
        "conversation_history": st.session_state.conversation_history,
        "partial_profile": st.session_state.user_profile,
        "current_step": st.session_state.current_step
    }
    
    # Appeler l'API
    response = call_api(PROFILE_ENDPOINT, request_data)
    
    # Mettre à jour l'état de la session
    st.session_state.conversation_history = response.get("updated_conversation_history", {"messages": []})
    st.session_state.user_profile = response.get("metadata", {}).get("updated_profile", {})
    st.session_state.current_step = response.get("metadata", {}).get("next_step")
    
    # Vérifier si le profil est complet
    if st.session_state.current_step == "confirmation":
        # Vérifier si tous les champs nécessaires sont présents
        required_fields = [
            "first_name", "last_name", "id_number", "gender", 
            "age", "hmo_name", "hmo_card_number", "insurance_tier"
        ]
        
        if all(field in st.session_state.user_profile for field in required_fields):
            st.session_state.profile_complete = True

def process_qa_message(user_message: str) -> None:
    """Traite une question utilisateur pour la phase Q&A."""
    if not user_message.strip():
        return
    
    # Préparer les données pour l'API
    request_data = {
        "user_message": user_message,
        "conversation_history": st.session_state.conversation_history,
        "user_profile": st.session_state.user_profile
    }
    
    # Appeler l'API
    response = call_api(QA_ENDPOINT, request_data)
    
    # Mettre à jour l'état de la session
    st.session_state.conversation_history = response.get("updated_conversation_history", {"messages": []})

def reset_session() -> None:
    """Réinitialise la session complète."""
    st.session_state.conversation_history = {"messages": []}
    st.session_state.user_profile = {}
    st.session_state.profile_complete = False
    st.session_state.mode = "profile"
    st.session_state.current_step = None

def change_mode(new_mode: str) -> None:
    """Change le mode de l'application."""
    if new_mode in ["profile", "qa"]:
        # Si on passe au mode Q&A, vérifier que le profil est complet
        if new_mode == "qa" and not st.session_state.profile_complete:
            st.warning("Veuillez d'abord compléter votre profil.")
            return
        
        st.session_state.mode = new_mode
        
        # Réinitialiser l'historique de conversation si on change de mode
        if st.session_state.mode == "qa":
            st.session_state.conversation_history = {"messages": []}

# Interface utilisateur

# Sidebar
with st.sidebar:
    st.title("🏥 Chatbot Médical")
    
    # Afficher le profil utilisateur s'il est complet
    if st.session_state.profile_complete:
        st.subheader("Votre profil")
        profile = st.session_state.user_profile
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Nom**: {profile.get('first_name', '')} {profile.get('last_name', '')}")
            st.markdown(f"**Âge**: {profile.get('age', '')}")
            st.markdown(f"**Genre**: {profile.get('gender', '')}")
        
        with col2:
            st.markdown(f"**HMO**: {profile.get('hmo_name', '')}")
            st.markdown(f"**Niveau**: {profile.get('insurance_tier', '')}")
        
        # Masquer partiellement les informations sensibles
        id_number = profile.get('id_number', '')
        hmo_card = profile.get('hmo_card_number', '')
        
        if id_number:
            masked_id = "●●●●●" + id_number[-4:] if len(id_number) >= 4 else id_number
            st.markdown(f"**ID**: {masked_id}")
        
        if hmo_card:
            masked_card = "●●●●●" + hmo_card[-4:] if len(hmo_card) >= 4 else hmo_card
            st.markdown(f"**Carte HMO**: {masked_card}")
    
    # Boutons de navigation
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 Mode Profil", use_container_width=True, 
                     disabled=st.session_state.mode == "profile"):
            change_mode("profile")
    
    with col2:
        if st.button("❓ Mode Q&A", use_container_width=True, 
                     disabled=st.session_state.mode == "qa" or not st.session_state.profile_complete):
            change_mode("qa")
    
    # Bouton de réinitialisation
    st.markdown("---")
    if st.button("🗑️ Réinitialiser", use_container_width=True):
        reset_session()
    
    # Informations supplémentaires
    st.markdown("---")
    with st.expander("ℹ️ À propos"):
        st.markdown("""
        Ce chatbot vous aide à obtenir des informations sur les services médicaux de votre caisse maladie en Israël.
        
        Toutes vos données sont conservées localement sur votre appareil et ne sont jamais stockées sur nos serveurs.
        """)

# Zone principale
st.header("Chatbot des Services Médicaux" if st.session_state.mode == "profile" else "Questions sur les Services Médicaux")

# Conteneur de messages
chat_container = st.container()

# Zone de saisie utilisateur
with st.form(key="message_form", clear_on_submit=True):
    user_input = st.text_area(
        "Votre message:", 
        height=100, 
        placeholder="Tapez votre message ici..."
    )
    
    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        submit_button = st.form_submit_button("Envoyer", use_container_width=True)

# Afficher les messages
with chat_container:
    if st.session_state.conversation_history and st.session_state.conversation_history.get("messages"):
        messages = st.session_state.conversation_history["messages"]
        
        for i, msg in enumerate(messages):
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if not content.strip():
                continue
            
            is_hebrew = is_rtl(content)
            align = "right" if is_hebrew and role == "user" else "left"
            bg_color = "#F0F2F6" if role == "user" else "#E1EBEE"
            
            # Ajout de la direction du texte en fonction de la langue
            dir_attr = "rtl" if is_hebrew else "ltr"
            
            # Formatter le message
            message_html = f"""
            <div style="display: flex; justify-content: {align}; margin-bottom: 10px;">
                <div style="background-color: {bg_color}; padding: 10px; border-radius: 10px; max-width: 80%;">
                    <div style="direction: {dir_attr}; text-align: {'right' if is_hebrew else 'left'};">
                        {content}
                    </div>
                    <div style="font-size: 0.8em; color: gray; text-align: {'right' if is_hebrew else 'left'}; margin-top: 5px;">
                        {format_time(None)}
                    </div>
                </div>
            </div>
            """
            
            st.markdown(message_html, unsafe_allow_html=True)

# Traiter le message utilisateur
if submit_button and user_input:
    if st.session_state.mode == "profile":
        process_profile_message(user_input)
    else:
        process_qa_message(user_input)
    
    # Forcer le rechargement pour afficher la réponse
    st.experimental_rerun()

# CSS personnalisé
st.markdown("""
<style>
    .stTextArea textarea {
        direction: auto;
    }
</style>
""", unsafe_allow_html=True) 