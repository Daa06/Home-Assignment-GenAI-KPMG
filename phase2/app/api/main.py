import time
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..api.models import ProfileRequest, QARequest, AIResponse
from ..llm.collection import ProfileCollector
from ..llm.qa import QAProcessor
from ..logging.logger import logger, log_api_request, log_api_response
from ..core.config import settings

# Initialiser l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="API pour le chatbot médical basé sur les services des caisses maladie israéliennes",
    version="1.0.0"
)

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit tourne sur le port 8501
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware pour générer des ID de session et mesurer le temps de traitement
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # Générer un ID de session si non présent dans les headers
    session_id = request.headers.get("X-Session-ID", str(uuid.uuid4()))
    
    # Mesurer le temps de traitement
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    # Ajouter les headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Session-ID"] = session_id
    
    return response

# Point de terminaison pour vérifier la santé de l'API
@app.get("/health")
async def health_check():
    """Vérifie que l'API est en cours d'exécution."""
    try:
        return {
            "status": "ok",
            "service": settings.APP_NAME,
            "version": "1.0.0",
            "endpoints": {
                "profile": f"{settings.API_V1_STR}/profile",
                "qa": f"{settings.API_V1_STR}/qa"
            }
        }
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de santé: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Point de terminaison pour la phase de collecte de profil
@app.post(f"{settings.API_V1_STR}/profile", response_model=AIResponse)
async def process_profile_message(request: ProfileRequest, req: Request):
    """Traite un message pour la collecte de profil utilisateur."""
    session_id = req.headers.get("X-Session-ID", "unknown")
    
    try:
        # Enregistrer la requête
        log_api_request(
            endpoint="/profile",
            request_data=request.dict(),
            user_id=session_id
        )
        
        start_time = time.time()
        
        # Initialiser le collecteur de profil
        profile_collector = ProfileCollector()
        
        # Traiter le message
        result = profile_collector.process_message(
            user_message=request.user_message,
            conversation_history=request.conversation_history,
            partial_profile=request.partial_profile,
            current_step=request.current_step
        )
        
        # Vérifier le résultat
        if not result or "response" not in result:
            raise HTTPException(
                status_code=500,
                detail="Réponse invalide du collecteur de profil"
            )
        
        # Préparer la réponse
        response = AIResponse(
            response=result.get("response", ""),
            updated_conversation_history=result.get("updated_history", {"messages": []}),
            metadata={
                "next_step": result.get("next_step", ""),
                "updated_profile": result.get("updated_profile", {})
            }
        )
        
        process_time = (time.time() - start_time) * 1000
        
        # Enregistrer la réponse
        log_api_response(
            endpoint="/profile",
            status_code=200,
            response_data=response.dict(),
            processing_time=process_time,
            user_id=session_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du message de profil: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement du message: {str(e)}"
        )

# Point de terminaison pour la phase de questions-réponses
@app.post(f"{settings.API_V1_STR}/qa", response_model=AIResponse)
async def process_qa_message(request: QARequest, req: Request):
    session_id = req.headers.get("X-Session-ID", "unknown")
    
    # Enregistrer la requête
    log_api_request(
        endpoint="/qa",
        request_data=request.dict(),
        user_id=session_id
    )
    
    start_time = time.time()
    
    try:
        # Initialiser le processeur Q&A
        qa_processor = QAProcessor()
        
        # Traiter la question
        result = qa_processor.process_question(
            user_message=request.user_message,
            conversation_history=request.conversation_history,
            user_profile=request.user_profile
        )
        
        # Préparer la réponse
        response = AIResponse(
            response=result["response"],
            updated_conversation_history=result["updated_conversation_history"],
            metadata=result["metadata"]
        )
        
        process_time = (time.time() - start_time) * 1000
        
        # Enregistrer la réponse
        log_api_response(
            endpoint="/qa",
            status_code=200,
            response_data=response.dict(),
            processing_time=process_time,
            user_id=session_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la question: {str(e)}")
        
        process_time = (time.time() - start_time) * 1000
        
        # Enregistrer l'erreur
        log_api_response(
            endpoint="/qa",
            status_code=500,
            response_data={"error": str(e)},
            processing_time=process_time,
            user_id=session_id
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement de la question: {str(e)}"
        )

# Gestionnaire d'erreurs global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Gestionnaire d'erreurs global pour toutes les exceptions non gérées."""
    logger.error(f"Erreur non gérée: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur interne est survenue. Veuillez réessayer plus tard."}
    )

# Point d'entrée pour démarrer le serveur avec uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 