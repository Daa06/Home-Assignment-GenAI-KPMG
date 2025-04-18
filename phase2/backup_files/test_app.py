#!/usr/bin/env python3
"""
Script de test pour l'application Medical Services Chatbot.
Ce script simule les interactions utilisateur pour identifier les problèmes.
"""

import requests
import json
import time
import uuid
import sys
import os

# Configuration
API_URL = "http://localhost:8000"
PROFILE_ENDPOINT = f"{API_URL}/api/v1/profile"
QA_ENDPOINT = f"{API_URL}/api/v1/qa"
HEALTH_ENDPOINT = f"{API_URL}/health"

# Données de test
TEST_USER_INFO = {
    "first_name": "Daniel",
    "last_name": "Dahan",
    "id_number": "111111111",
    "gender": "MALE",
    "age": 22,
    "hmo_name": "כללית",
    "hmo_card_number": "111123123",
    "insurance_tier": "כסף"
}

# Créer un identifiant de session
session_id = str(uuid.uuid4())
print(f"ID de session de test: {session_id}")

def check_api_health():
    """Vérifie si l'API est en ligne."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            print(f"✅ API en ligne")
            return True
        else:
            print(f"❌ API hors ligne (status code: {response.status_code})")
            return False
    except requests.RequestException as e:
        print(f"❌ Erreur de connexion à l'API: {str(e)}")
        return False

def call_profile_api(message, history, profile_data, current_step):
    """Appelle l'API de profil avec les données fournies."""
    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": session_id
    }
    
    data = {
        "user_message": message,
        "conversation_history": history,
        "partial_profile": profile_data,
        "current_step": current_step
    }
    
    try:
        print(f"\n📤 Envoi à l'API: Message '{message}', Étape '{current_step}'")
        response = requests.post(
            PROFILE_ENDPOINT,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"📥 Réponse API reçue:")
            print(f"  - Message: \"{response_data.get('response', 'Pas de réponse')[:50]}...\"")
            if 'metadata' in response_data:
                metadata = response_data['metadata']
                print(f"  - Prochaine étape: {metadata.get('next_step', 'Inconnue')}")
                if 'updated_profile' in metadata:
                    print(f"  - Profil mis à jour: {metadata['updated_profile']}")
            return response_data
        else:
            print(f"❌ Erreur API: {response.status_code}")
            print(response.text)
            return None
            
    except requests.RequestException as e:
        print(f"❌ Erreur API: {str(e)}")
        return None

def simulate_profile_collection():
    """Simule la collecte de profil complète."""
    print("\n🔄 Démarrage de la simulation de collecte de profil...\n")
    
    # Initialiser les données
    history = {"messages": []}
    profile = {}
    current_step = "collecting_first_name"
    
    # Définir l'ordre des étapes et les messages correspondants
    steps = [
        ("collecting_first_name", TEST_USER_INFO["first_name"], "collecting_last_name"),
        ("collecting_last_name", TEST_USER_INFO["last_name"], "collecting_id_number"),
        ("collecting_id_number", TEST_USER_INFO["id_number"], "collecting_gender"),
        ("collecting_gender", TEST_USER_INFO["gender"], "collecting_age"),
        ("collecting_age", str(TEST_USER_INFO["age"]), "collecting_hmo_name"),
        ("collecting_hmo_name", TEST_USER_INFO["hmo_name"], "collecting_hmo_card_number"),
        ("collecting_hmo_card_number", TEST_USER_INFO["hmo_card_number"], "collecting_insurance_tier"),
        ("collecting_insurance_tier", TEST_USER_INFO["insurance_tier"], "confirmation"),
        ("confirmation", "YES", "confirmation")
    ]
    
    for i, (step, user_message, expected_next_step) in enumerate(steps):
        print(f"\n📊 Test {i+1}/{len(steps)}: Étape '{step}' → Message '{user_message}'")
        
        # Vérifier que l'étape actuelle correspond à celle attendue
        if step != current_step:
            print(f"❌ Erreur: Étape actuelle '{current_step}' ne correspond pas à l'étape attendue '{step}'")
            return False
        
        # Appeler l'API
        response = call_profile_api(user_message, history, profile, current_step)
        
        if not response:
            print("❌ Échec de l'appel API")
            return False
        
        # Mettre à jour l'historique avec le message utilisateur
        history["messages"].append({"role": "user", "content": user_message})
        
        # Mettre à jour l'historique avec la réponse
        history["messages"].append({"role": "assistant", "content": response["response"]})
        
        # Mettre à jour le profil
        if "metadata" in response and "updated_profile" in response["metadata"]:
            profile = response["metadata"]["updated_profile"]
        
        # Mettre à jour l'étape actuelle
        if "metadata" in response and "next_step" in response["metadata"]:
            current_step = response["metadata"]["next_step"]
            
            # Vérifier que l'étape suivante correspond à celle attendue
            if current_step != expected_next_step:
                print(f"❌ Erreur: Étape suivante '{current_step}' ne correspond pas à l'étape attendue '{expected_next_step}'")
                return False
            
            print(f"✅ Passage à l'étape: {current_step}")
        else:
            print(f"❌ Erreur: Pas d'étape suivante dans la réponse")
            return False
        
        # Pause pour simuler l'interaction utilisateur
        time.sleep(1)
    
    print("\n✅ Simulation de collecte de profil terminée avec succès")
    print(f"Profil final: {profile}")
    return True

def test_qa_mode():
    """Teste le mode Q&A après la collecte de profil."""
    print("\n🔄 Test du mode Q&A...\n")
    
    # Initialiser les données
    history = {"messages": []}
    
    # Appeler l'API avec une question de test
    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": session_id
    }
    
    test_question = "Tell me about my coverage for dental care"
    
    data = {
        "user_message": test_question,
        "conversation_history": history,
        "user_profile": TEST_USER_INFO
    }
    
    try:
        print(f"\n📤 Envoi de question à l'API: '{test_question}'")
        response = requests.post(
            QA_ENDPOINT,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"📥 Réponse API reçue:")
            print(f"  - Réponse: \"{response_data.get('response', 'Pas de réponse')[:100]}...\"")
            return True
        else:
            print(f"❌ Erreur API: {response.status_code}")
            print(response.text)
            return False
            
    except requests.RequestException as e:
        print(f"❌ Erreur API: {str(e)}")
        return False

def main():
    """Fonction principale du script de test."""
    print("🔍 Démarrage des tests de l'application Medical Services Chatbot\n")
    
    # Vérifier que l'API est en ligne
    if not check_api_health():
        print("❌ Impossible de se connecter à l'API. Tests annulés.")
        sys.exit(1)
        
    # Test de collecte de profil
    if simulate_profile_collection():
        print("\n✅ Test de collecte de profil réussi")
    else:
        print("\n❌ Test de collecte de profil échoué")
        sys.exit(1)
        
    # Test du mode Q&A
    if test_qa_mode():
        print("\n✅ Test du mode Q&A réussi")
    else:
        print("\n❌ Test du mode Q&A échoué")
        sys.exit(1)
        
    print("\n🎉 Tous les tests ont réussi!")

if __name__ == "__main__":
    main() 