#!/usr/bin/env python3
"""
Script pour initialiser la base de connaissances et construire l'index vectoriel.
Ce script doit être exécuté avant de démarrer l'application pour préparer la base de connaissances.
"""

import os
import sys
import time
from loguru import logger

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.knowledge.processor import KnowledgeProcessor
from app.knowledge.embedding import EmbeddingManager
from app.core.config import settings

def init_knowledge_base():
    """Initialise la base de connaissances et construit l'index vectoriel."""
    start_time = time.time()
    
    logger.info("Démarrage de l'initialisation de la base de connaissances...")
    
    # Vérifier que le répertoire de la base de connaissances existe
    if not os.path.exists(settings.KNOWLEDGE_BASE_DIR):
        logger.error(f"Le répertoire de la base de connaissances n'existe pas: {settings.KNOWLEDGE_BASE_DIR}")
        return False
    
    # Vérifier qu'il y a des fichiers HTML dans le répertoire
    html_files = [f for f in os.listdir(settings.KNOWLEDGE_BASE_DIR) if f.endswith('.html')]
    if not html_files:
        logger.error(f"Aucun fichier HTML trouvé dans le répertoire: {settings.KNOWLEDGE_BASE_DIR}")
        return False
    
    logger.info(f"Trouvé {len(html_files)} fichiers HTML dans le répertoire de la base de connaissances")
    
    try:
        # Traiter les fichiers HTML
        processor = KnowledgeProcessor()
        knowledge_items = processor.process_all_knowledge_base()
        
        if not knowledge_items:
            logger.error("Aucun élément de connaissance extrait des fichiers HTML")
            return False
        
        logger.info(f"Extraction réussie de {len(knowledge_items)} éléments de connaissance")
        
        # Construire l'index vectoriel
        embedding_manager = EmbeddingManager()
        embedding_manager.build_index(knowledge_items)
        
        logger.info("Construction de l'index vectoriel terminée")
        
        # Tester la recherche
        test_query = "Quels sont les avantages pour les traitements dentaires?"
        test_results = embedding_manager.search(test_query, top_k=2)
        
        if test_results:
            logger.info("Test de recherche réussi")
        else:
            logger.warning("Test de recherche n'a retourné aucun résultat")
        
        end_time = time.time()
        logger.info(f"Initialisation de la base de connaissances terminée en {end_time - start_time:.2f} secondes")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de connaissances: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_knowledge_base()
    if success:
        print("Base de connaissances initialisée avec succès!")
        sys.exit(0)
    else:
        print("Échec de l'initialisation de la base de connaissances.")
        sys.exit(1) 