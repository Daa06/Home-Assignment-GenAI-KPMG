import os
import numpy as np
import json
from typing import List, Dict, Any, Optional, Tuple
import faiss
from openai import AzureOpenAI
from ..core.config import settings
from loguru import logger

class EmbeddingManager:
    """Gestionnaire pour créer et rechercher des embeddings à partir de la base de connaissances"""
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.embedding_model = settings.EMBEDDING_DEPLOYMENT_NAME
        self.index_file = os.path.join(os.path.dirname(__file__), "knowledge_index.json")
        self.embedding_file = os.path.join(os.path.dirname(__file__), "knowledge_embeddings.npy")
        self.index = None
        self.documents = []
        self.embeddings = None
        logger.info("Gestionnaire d'embeddings initialisé")
    
    def create_embedding(self, text: str) -> List[float]:
        """Crée un embedding pour un texte donné"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            embedding = response.data[0].embedding
            return embedding
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'embedding: {str(e)}")
            # Retourner un vecteur de zéros en cas d'erreur (à remplacer par une meilleure stratégie de fallback)
            return [0.0] * 1536  # 1536 est la dimension des embeddings ADA 002
    
    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Découpe un document en fragments pour l'embedding"""
        chunks = []
        
        # Ajouter le titre et l'introduction comme un fragment
        intro_text = document.get('title', '') + "\n"
        for para in document.get('introduction', []):
            intro_text += para + "\n"
        
        if intro_text.strip():
            chunks.append({
                'text': intro_text,
                'metadata': {
                    'service_type': document.get('service_type', ''),
                    'source_file': document.get('source_file', ''),
                    'chunk_type': 'introduction'
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
                        hmo_data = row[i]
                        
                        chunk_text = f"Service: {service_name}\nHMO: {hmo_name}\nDétails: {hmo_data}"
                        
                        chunks.append({
                            'text': chunk_text,
                            'metadata': {
                                'service_type': document.get('service_type', ''),
                                'source_file': document.get('source_file', ''),
                                'chunk_type': 'table',
                                'table_idx': table_idx,
                                'row_idx': row_idx,
                                'service_name': service_name,
                                'hmo_name': hmo_name
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
                    'service_type': document.get('service_type', ''),
                    'source_file': document.get('source_file', ''),
                    'chunk_type': 'contact'
                }
            })
        
        return chunks
    
    def build_index(self, knowledge_items: List[Dict[str, Any]]) -> None:
        """Construit un index de recherche à partir des éléments de la base de connaissances"""
        logger.info("Construction de l'index d'embeddings...")
        all_chunks = []
        
        # Découper tous les documents en fragments
        for item in knowledge_items:
            chunks = self.chunk_document(item)
            all_chunks.extend(chunks)
        
        # Créer des embeddings pour tous les fragments
        embeddings_list = []
        for chunk in all_chunks:
            embedding = self.create_embedding(chunk['text'])
            embeddings_list.append(embedding)
        
        # Convertir en tableau NumPy
        embeddings_array = np.array(embeddings_list).astype('float32')
        
        # Créer l'index FAISS
        dimension = embeddings_array.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings_array)
        
        # Sauvegarder l'index et les données
        self.documents = all_chunks
        self.embeddings = embeddings_array
        self.index = index
        
        # Sauvegarder les documents et les embeddings sur disque
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
        
        np.save(self.embedding_file, self.embeddings)
        
        logger.info(f"Index construit avec {len(all_chunks)} fragments")
    
    def load_index(self) -> bool:
        """Charge l'index depuis le disque s'il existe"""
        if os.path.exists(self.index_file) and os.path.exists(self.embedding_file):
            try:
                # Charger les documents
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                
                # Charger les embeddings
                self.embeddings = np.load(self.embedding_file)
                
                # Reconstruire l'index FAISS
                dimension = self.embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dimension)
                self.index.add(self.embeddings)
                
                logger.info(f"Index chargé avec {len(self.documents)} fragments")
                return True
            
            except Exception as e:
                logger.error(f"Erreur lors du chargement de l'index: {str(e)}")
                return False
        else:
            logger.warning("Aucun index trouvé sur le disque")
            return False
    
    def search(self, query: str, top_k: int = 5, 
               filter_hmo: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recherche les documents les plus pertinents pour une requête"""
        if self.index is None:
            success = self.load_index()
            if not success:
                logger.error("Impossible de charger l'index pour la recherche")
                return []
        
        # Créer l'embedding de la requête
        query_embedding = self.create_embedding(query)
        query_embedding_array = np.array([query_embedding]).astype('float32')
        
        # Effectuer la recherche
        distances, indices = self.index.search(query_embedding_array, top_k * 3)  # Récupérer plus pour filtrer ensuite
        
        # Récupérer les résultats
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                document = self.documents[idx].copy()
                document['score'] = float(1.0 / (1.0 + distance))  # Convertir la distance en score de similarité
                
                # Appliquer le filtre HMO si spécifié
                if filter_hmo is None or document.get('metadata', {}).get('hmo_name') in [filter_hmo, None]:
                    results.append(document)
        
        # Trier par score et limiter au top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

# Exemple d'utilisation
if __name__ == "__main__":
    from processor import KnowledgeProcessor
    
    processor = KnowledgeProcessor()
    knowledge_base = processor.process_all_knowledge_base()
    
    embedding_manager = EmbeddingManager()
    embedding_manager.build_index(knowledge_base)
    
    results = embedding_manager.search("Quels sont les avantages pour les traitements dentaires?", 3, "מכבי")
    for result in results:
        print(f"Score: {result['score']}")
        print(f"Texte: {result['text'][:100]}...")
        print(f"Metadata: {result['metadata']}")
        print("-" * 50) 