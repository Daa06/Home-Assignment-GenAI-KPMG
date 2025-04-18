#!/usr/bin/env python3
"""
Script to rebuild the vector index with FAISS and generate a JSON file
that documents the embeddings with all important metadata.
"""

import os
import sys
import time
import json
import numpy as np
from loguru import logger

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Check if FAISS is available
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
    """Creates an embedding for a given text"""
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
    """Rebuilds the knowledge index with FAISS and all important metadata."""
    start_time = time.time()
    
    logger.info("Démarrage de la reconstruction de l'index de connaissances avec FAISS...")
    
    # Create file paths
    base_dir = os.path.dirname(__file__)
    index_dir = os.path.join(base_dir, "app/knowledge")
    index_file = os.path.join(index_dir, "knowledge_index.json")
    embedding_file = os.path.join(index_dir, "knowledge_embeddings.npy")
    faiss_index_file = os.path.join(index_dir, "knowledge_faiss.index")
    embedding_metadata_file = os.path.join(index_dir, "embedding_metadata.json")
    
    # Delete existing index files
    for file_path in [index_file, embedding_file, faiss_index_file, embedding_metadata_file]:
        if os.path.exists(file_path):
            logger.info(f"Suppression du fichier existant: {file_path}")
            os.remove(file_path)
    
    # Initialize OpenAI client
    client = create_openai_client()
    
    # Process documents and extract knowledge
    processor = KnowledgeProcessor()
    knowledge_items = processor.process_all_knowledge_base()
    
    if not knowledge_items:
        logger.error("Aucun élément de connaissance extrait")
        return False
    
    logger.info(f"Extraction réussie de {len(knowledge_items)} éléments de connaissance")
    
    # Split documents into chunks
    all_chunks = []
    service_types = set()
    hmo_names = set()
    insurance_tiers = set()
    
    # Function to split a document into chunks
    def chunk_document(document):
        chunks = []
        service_type = document.get('service_type', '')
        service_types.add(service_type)
        
        # Add title and introduction as a chunk
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
        
        # Add each table row as a separate chunk
        for table_idx, table in enumerate(document.get('tables', [])):
            headers = table.get('headers', [])
            
            for row_idx, row in enumerate(table.get('data', [])):
                if len(row) >= 2:  # At least service name and one HMO column
                    service_name = row[0]
                    
                    # Create a chunk for each HMO column
                    for i in range(1, min(len(row), len(headers))):
                        hmo_name = headers[i]
                        hmo_names.add(hmo_name)  # Add to the set of HMOs
                        hmo_data = row[i]
                        
                        # Try to extract insurance tier from text
                        insurance_tier = None
                        for tier in ["זהב", "כסף", "ארד"]:  # Gold, Silver, Bronze
                            if tier in hmo_data:
                                insurance_tier = tier
                                insurance_tiers.add(tier)  # Add to the set of insurance tiers
                                break
                        
                        chunk_text = f"Service: {service_name}\nHMO: {hmo_name}\nDétails: {hmo_data}"
                        
                        # Enrich text with English keywords to improve search
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
        
        # Add contact information as a chunk
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
    
    # Split all documents into chunks
    for item in knowledge_items:
        chunks = chunk_document(item)
        all_chunks.extend(chunks)
    
    # Shuffle chunks to avoid bias related to order
    import random
    random.shuffle(all_chunks)
    
    logger.info(f"Création de {len(all_chunks)} fragments au total")
    logger.info(f"Types de services trouvés: {service_types}")
    logger.info(f"HMO trouvés: {hmo_names}")
    logger.info(f"Niveaux d'assurance trouvés: {insurance_tiers}")
    
    # Create embeddings for all chunks
    embeddings_list = []
    embedding_metadata = []
    
    for i, chunk in enumerate(all_chunks):
        logger.info(f"Création de l'embedding {i+1}/{len(all_chunks)} pour {chunk['metadata']['service_type']}")
        embedding = create_embedding(client, chunk['text'])
        embeddings_list.append(embedding)
        
        # Add embedding metadata
        embedding_metadata.append({
            'index': i,
            'text_preview': chunk['text'][:100] + '...' if len(chunk['text']) > 100 else chunk['text'],
            'service_type': chunk['metadata']['service_type'],
            'chunk_type': chunk['metadata']['chunk_type'],
            'hmo_name': chunk['metadata']['hmo_name'],
            'insurance_tier': chunk['metadata']['insurance_tier'],
            'embedding_dimension': len(embedding)
        })
    
    # Convert to NumPy array
    embeddings_array = np.array(embeddings_list).astype('float32')
    
    # Check embedding dimension
    dimension = embeddings_array.shape[1]
    logger.info(f"Dimension des embeddings: {dimension}")
    
    # Create FAISS index
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)
    logger.info(f"Index FAISS créé avec succès avec {index.ntotal} vecteurs")
    
    # Save FAISS index
    faiss.write_index(index, faiss_index_file)
    logger.info(f"Index FAISS sauvegardé: {faiss_index_file}")
    
    # Save documents and embeddings to disk
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    logger.info(f"Index des documents sauvegardé: {index_file}")
    
    # Save embeddings in numpy format
    np.save(embedding_file, embeddings_array)
    logger.info(f"Embeddings sauvegardés: {embedding_file}")
    
    # Save embedding metadata
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
    # Configure logger
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add("rebuild_index_complete.log", rotation="10 MB", level="DEBUG")
    
    # Run index reconstruction
    if rebuild_knowledge_index():
        logger.info("Index reconstruit avec succès!")
        sys.exit(0)
    else:
        logger.error("Échec de la reconstruction de l'index")
        sys.exit(1) 