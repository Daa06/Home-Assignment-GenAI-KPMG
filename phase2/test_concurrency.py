#!/usr/bin/env python3
import asyncio
import json
import time
import uuid
from typing import Dict, List
import aiohttp
from loguru import logger

# Configuration
API_BASE_URL = "http://localhost:8000"
NUM_USERS = 5
NUM_REQUESTS_PER_USER = 3

# Profils utilisateurs fictifs
USER_PROFILES = [
    {
        "first_name": "Daniel",
        "last_name": "Dahan",
        "id_number": "123456789",
        "gender": "MALE",
        "age": 30,
        "hmo_name": "מכבי",
        "hmo_card_number": "987654321",
        "insurance_tier": "זהב"
    },
    {
        "first_name": "Sarah",
        "last_name": "Cohen",
        "id_number": "234567890",
        "gender": "FEMALE",
        "age": 25,
        "hmo_name": "כללית",
        "hmo_card_number": "876543210",
        "insurance_tier": "כסף"
    },
    {
        "first_name": "David",
        "last_name": "Levy",
        "id_number": "345678901", 
        "gender": "MALE",
        "age": 40,
        "hmo_name": "מאוחדת",
        "hmo_card_number": "765432109",
        "insurance_tier": "ארד"
    },
    {
        "first_name": "Rachel",
        "last_name": "Avraham",
        "id_number": "456789012",
        "gender": "FEMALE",
        "age": 35,
        "hmo_name": "לאומית",
        "hmo_card_number": "654321098",
        "insurance_tier": "זהב"
    },
    {
        "first_name": "Moshe",
        "last_name": "Ben",
        "id_number": "567890123",
        "gender": "MALE",
        "age": 28,
        "hmo_name": "מכבי",
        "hmo_card_number": "543210987",
        "insurance_tier": "כסף"
    }
]

# Questions à poser
QUESTIONS = [
    "Quels services sont couverts par mon assurance?",
    "Combien de consultations médicales puis-je avoir par an?",
    "Est-ce que les traitements dentaires sont couverts?",
    "Comment puis-je obtenir un remboursement pour un traitement?",
    "Quels sont mes avantages avec mon niveau d'assurance?"
]

async def send_requests_for_user(session: aiohttp.ClientSession, user_id: str, profile: Dict, questions: List[str]) -> List[Dict]:
    """Envoie plusieurs requêtes pour un utilisateur donné"""
    results = []
    conversation_history = []
    
    for i in range(NUM_REQUESTS_PER_USER):
        question = questions[i % len(questions)]
        payload = {
            "user_profile": profile,
            "conversation_history": json.dumps(conversation_history),
            "user_message": question
        }
        
        start_time = time.time()
        try:
            async with session.post(f"{API_BASE_URL}/qa", json=payload) as response:
                response_data = await response.json()
                status = response.status
                duration = time.time() - start_time
                
                result = {
                    "user_id": user_id,
                    "request_number": i + 1,
                    "status": status,
                    "duration": duration,
                    "response": response_data
                }
                
                # Mettre à jour l'historique de conversation
                if "answer" in response_data:
                    conversation_history.append({"role": "user", "content": question})
                    conversation_history.append({"role": "assistant", "content": response_data["answer"]})
                
                results.append(result)
                logger.info(f"Utilisateur {user_id} - Requête {i+1} - Statut: {status} - Durée: {duration:.2f}s")
                
                # Pause courte entre les requêtes du même utilisateur
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Erreur pour l'utilisateur {user_id} à la requête {i+1}: {str(e)}")
            results.append({
                "user_id": user_id,
                "request_number": i + 1,
                "status": "error",
                "error": str(e)
            })
    
    return results

async def run_concurrency_test():
    """Exécute le test de concurrence avec plusieurs utilisateurs simultanés"""
    logger.info(f"Démarrage du test de concurrence avec {NUM_USERS} utilisateurs simultanés")
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        # Créer les tâches pour chaque utilisateur
        for i in range(NUM_USERS):
            user_id = str(uuid.uuid4())
            profile = USER_PROFILES[i % len(USER_PROFILES)]
            tasks.append(send_requests_for_user(session, user_id, profile, QUESTIONS))
        
        # Exécuter toutes les tâches en parallèle
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_duration = time.time() - start_time
        
        # Analyser les résultats
        all_requests = [req for user_results in results for req in user_results]
        successful_requests = [req for req in all_requests if isinstance(req.get("status"), int) and 200 <= req.get("status") < 300]
        
        logger.info(f"Test de concurrence terminé en {total_duration:.2f} secondes")
        logger.info(f"Total des requêtes: {len(all_requests)}")
        logger.info(f"Requêtes réussies: {len(successful_requests)}")
        logger.info(f"Taux de réussite: {len(successful_requests)/len(all_requests)*100:.2f}%")
        
        # Calculer les temps de réponse moyens
        durations = [req.get("duration", 0) for req in successful_requests]
        if durations:
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            logger.info(f"Temps de réponse moyen: {avg_duration:.2f}s")
            logger.info(f"Temps de réponse min: {min_duration:.2f}s")
            logger.info(f"Temps de réponse max: {max_duration:.2f}s")

if __name__ == "__main__":
    logger.info("Démarrage du test de concurrence...")
    asyncio.run(run_concurrency_test())
    logger.info("Test de concurrence terminé.") 