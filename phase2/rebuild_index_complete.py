#!/usr/bin/env python3
"""
Script pour reconstruire l'index vectoriel avec FAISS et générer un fichier
JSON qui documente les embeddings avec toutes les métadonnées importantes.
"""

import os
import sys
import time
import json
import numpy as np
from loguru import logger

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Vérifier si FAISS est disponible
try:
    import faiss
    FAISS_AVAILABLE = True
    logger.info("FAISS est disponible et sera utilisé pour construire l'index")
except ImportError:
    FAISS_AVAILABLE = False
    logger.error("FAISS n'est pas disponible. Veuillez l'installer : pip install faiss-cpu ou faiss-gpu")
    sys.exit(1)

from app.knowledge.processor import KnowledgeProcessor
from app.llm.client import create_openai_client
from app.core.config import settings

def create_embedding(client, text, model=settings.EMBEDDING_DEPLOYMENT_NAME):
    """Crée un embedding pour un texte donné"""
    try:
        response = client.embeddings.create(
            model=model,
            input=text
        )
        if hasattr(response, 'data') and hasattr(response.data[0], 'embedding'):
            return response.data[0].embedding
        else:
            logger.warning(f"Structure de réponse d'embedding inconnue pour '{text[:30]}...'")
            return np.zeros(1536).tolist()  # Fallback
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'embedding: {str(e)}")
        return np.zeros(1536).tolist()  # Fallback en cas d'erreur

def rebuild_knowledge_index():
    """Reconstruit l'index de connaissances avec FAISS et toutes les métadonnées importantes."""
    start_time = time.time()
    
    logger.info("Démarrage de la reconstruction de l'index de connaissances avec FAISS...")
    
    # Créer les chemins des fichiers
    base_dir = os.path.dirname(__file__)
    index_dir = os.path.join(base_dir, "app/knowledge")
    index_file = os.path.join(index_dir, "knowledge_index.json")
    embedding_file = os.path.join(index_dir, "knowledge_embeddings.npy")
    faiss_index_file = os.path.join(index_dir, "knowledge_faiss.index")
    embedding_metadata_file = os.path.join(index_dir, "embedding_metadata.json")
    
    # Supprimer les fichiers d'index existants
    for file_path in [index_file, embedding_file, faiss_index_file, embedding_metadata_file]:
        if os.path.exists(file_path):
            logger.info(f"Suppression du fichier existant: {file_path}")
            os.remove(file_path)
    
    # Initialiser le client OpenAI
    client = create_openai_client()
    
    # Traiter les documents et extraire les connaissances
    processor = KnowledgeProcessor()
    knowledge_items = processor.process_all_knowledge_base()
    
    if not knowledge_items:
        logger.error("Aucun élément de connaissance extrait")
        return False
    
    logger.info(f"Extraction réussie de {len(knowledge_items)} éléments de connaissance")
    
    # Découper les documents en chunks
    all_chunks = []
    service_types = set()
    hmo_names = set()
    insurance_tiers = set()
    
    # Fonction pour découper un document en fragments
    def chunk_document(document):
        chunks = []
        service_type = document.get('service_type', '')
        service_types.add(service_type)
        
        # Ajouter le titre et l'introduction comme un fragment
        intro_text = document.get('title', '') + "\n"
        for para in document.get('introduction', []):
            intro_text += para + "\n"
        
        if intro_text.strip():
            chunks.append({
                'text': intro_text,
                'metadata': {
                    'service_type': service_type,
                    'source_file': document.get('source_file', ''),
                    'chunk_type': 'introduction',
                    'hmo_name': None,
                    'insurance_tier': None
                }
            })
        
        # Ajouter chaque ligne de table comme un fragment séparé
        for table_idx, table in enumerate(document.get('tables', [])):
            headers = table.get('headers', [])
            
            for row_idx, row in enumerate(table.get('data', [])):
                if len(row) >= 2:  # Au moins le nom du service et une colonne HMO
                    service_name = row[0]
                    
                    # Créer un fragment pour chaque colonne HMO
                    for i in range(1, min(len(row), len(headers))):
                        hmo_name = headers[i]
                        hmo_names.add(hmo_name)  # Ajouter à l'ensemble des HMO
                        hmo_data = row[i]
                        
                        # Essayer d'extraire le niveau d'assurance à partir du texte
                        insurance_tier = None
                        for tier in ["זהב", "כסף", "ארד"]:  # Gold, Silver, Bronze
                            if tier in hmo_data:
                                insurance_tier = tier
                                insurance_tiers.add(tier)  # Ajouter à l'ensemble des niveaux d'assurance
                                break
                        
                        chunk_text = f"Service: {service_name}\nHMO: {hmo_name}\nDétails: {hmo_data}"
                        
                        # Enrichir le texte avec des mots-clés en anglais pour améliorer la recherche
                        if service_type == "pragrency_services":
                            chunk_text += "\nKeywords: pregnancy, prenatal, birth, maternity, pregnant"
                        elif service_type == "dentel_services":
                            chunk_text += "\nKeywords: dental, teeth, tooth, dentist, oral"
                        elif service_type == "optometry_services":
                            chunk_text += "\nKeywords: vision, eye, glasses, contact lenses, optometry"
                        elif service_type == "communication_clinic_services":
                            chunk_text += "\nKeywords: speech, hearing, communication, language, therapy"
                        elif service_type == "alternative_services":
                            chunk_text += "\nKeywords: alternative medicine, acupuncture, homeopathy, massage, natural"
                        elif service_type == "workshops_services":
                            chunk_text += "\nKeywords: workshop, class, group, training, education"
                        
                        chunks.append({
                            'text': chunk_text,
                            'metadata': {
                                'service_type': service_type,
                                'source_file': document.get('source_file', ''),
                                'chunk_type': 'table',
                                'table_idx': table_idx,
                                'row_idx': row_idx,
                                'service_name': service_name,
                                'hmo_name': hmo_name,
                                'insurance_tier': insurance_tier
                            }
                        })
        
        # Ajouter les informations de contact comme un fragment
        contact_info = document.get('contact_info', {})
        if contact_info:
            contact_text = "Informations de contact:\n"
            for phone_list in contact_info.get('phones', []):
                contact_text += phone_list + "\n"
            
            chunks.append({
                'text': contact_text,
                'metadata': {
                    'service_type': service_type,
                    'source_file': document.get('source_file', ''),
                    'chunk_type': 'contact',
                    'hmo_name': None,
                    'insurance_tier': None
                }
            })
        
        return chunks
    
    # Découper tous les documents en fragments
    for item in knowledge_items:
        chunks = chunk_document(item)
        all_chunks.extend(chunks)
    
    # Mélanger les chunks pour éviter tout biais lié à l'ordre
    import random
    random.shuffle(all_chunks)
    
    logger.info(f"Création de {len(all_chunks)} fragments au total")
    logger.info(f"Types de services trouvés: {service_types}")
    logger.info(f"HMO trouvés: {hmo_names}")
    logger.info(f"Niveaux d'assurance trouvés: {insurance_tiers}")
    
    # Créer des embeddings pour tous les fragments
    embeddings_list = []
    embedding_metadata = []
    
    for i, chunk in enumerate(all_chunks):
        logger.info(f"Création de l'embedding {i+1}/{len(all_chunks)} pour {chunk['metadata']['service_type']}")
        embedding = create_embedding(client, chunk['text'])
        embeddings_list.append(embedding)
        
        # Ajouter les métadonnées de l'embedding
        embedding_metadata.append({
            'index': i,
            'text_preview': chunk['text'][:100] + '...' if len(chunk['text']) > 100 else chunk['text'],
            'service_type': chunk['metadata']['service_type'],
            'chunk_type': chunk['metadata']['chunk_type'],
            'hmo_name': chunk['metadata']['hmo_name'],
            'insurance_tier': chunk['metadata']['insurance_tier'],
            'embedding_dimension': len(embedding)
        })
    
    # Convertir en tableau NumPy
    embeddings_array = np.array(embeddings_list).astype('float32')
    
    # Vérifier la dimension des embeddings
    dimension = embeddings_array.shape[1]
    logger.info(f"Dimension des embeddings: {dimension}")
    
    # Créer l'index FAISS
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)
    logger.info(f"Index FAISS créé avec succès avec {index.ntotal} vecteurs")
    
    # Sauvegarder l'index FAISS
    faiss.write_index(index, faiss_index_file)
    logger.info(f"Index FAISS sauvegardé: {faiss_index_file}")
    
    # Sauvegarder les documents et les embeddings sur disque
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    logger.info(f"Index des documents sauvegardé: {index_file}")
    
    # Sauvegarder les embeddings au format numpy
    np.save(embedding_file, embeddings_array)
    logger.info(f"Embeddings sauvegardés: {embedding_file}")
    
    # Sauvegarder les métadonnées des embeddings
    with open(embedding_metadata_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_embeddings': len(embedding_metadata),
            'dimension': dimension,
            'service_types': list(service_types),
            'hmo_names': list(hmo_names),
            'insurance_tiers': list(insurance_tiers),
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'embeddings': embedding_metadata
        }, f, ensure_ascii=False, indent=2)
    logger.info(f"Métadonnées des embeddings sauvegardées: {embedding_metadata_file}")
    
    end_time = time.time()
    logger.info(f"Reconstruction de l'index terminée en {end_time - start_time:.2f} secondes")
    
    return True

if __name__ == "__main__":
    # Configurer le logger
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add("rebuild_index_complete.log", rotation="10 MB", level="DEBUG")
    
    # Exécuter la reconstruction de l'index
    if rebuild_knowledge_index():
        logger.info("Index reconstruit avec succès!")
        sys.exit(0)
    else:
        logger.error("Échec de la reconstruction de l'index")
        sys.exit(1) 