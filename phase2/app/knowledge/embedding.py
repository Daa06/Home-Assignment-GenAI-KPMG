import os
import numpy as np
import json
from typing import List, Dict, Any, Optional, Tuple
from ..core.config import settings
from ..llm.client import create_openai_client
from loguru import logger

# Import conditionnel de FAISS
try:
    import faiss
    FAISS_AVAILABLE = True
    logger.info("FAISS est disponible")
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS n'est pas disponible, utilisation de l'index simple")
    from .simple_index import SimpleIndex

class EmbeddingManager:
    """Gestionnaire pour créer et rechercher des embeddings à partir de la base de connaissances"""
    
    def __init__(self):
        try:
            self.client = create_openai_client()
            self.embedding_model = settings.EMBEDDING_DEPLOYMENT_NAME
            self.index_file = os.path.join(os.path.dirname(__file__), "knowledge_index.json")
            self.embedding_file = os.path.join(os.path.dirname(__file__), "knowledge_embeddings.npy")
            self.faiss_index_file = os.path.join(os.path.dirname(__file__), "knowledge_faiss.index")
            self.metadata_file = os.path.join(os.path.dirname(__file__), "embedding_metadata.json")
            self.index = None
            self.documents = []
            self.embeddings = None
            self.embedding_metadata = None
            logger.info("Gestionnaire d'embeddings initialisé")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du client OpenAI: {str(e)}")
            raise
    
    def create_embedding(self, text: str) -> List[float]:
        """Crée un embedding pour un texte donné"""
        try:
            # Essayer la nouvelle API
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            # Nouvelle structure de réponse
            if hasattr(response, 'data') and hasattr(response.data[0], 'embedding'):
                embedding = response.data[0].embedding
                return embedding
            # Ancienne structure de réponse possible
            elif hasattr(response, 'embeddings'):
                return response.embeddings[0]
            # Fallback si la structure est différente
            else:
                logger.warning(f"Structure de réponse d'embedding inconnue pour '{text[:30]}...'")
                return [0.0] * 1536  # Dimension standard pour ADA 002
        except (AttributeError, TypeError) as e:
            # Essayer l'ancienne API
            logger.warning(f"Tentative avec l'ancienne API d'embedding: {str(e)}")
            try:
                response = self.client.embeddings.create(
                    engine=self.embedding_model,
                    input=text
                )
                if hasattr(response, 'data') and hasattr(response.data[0], 'embedding'):
                    return response.data[0].embedding
                elif hasattr(response, 'embeddings'):
                    return response.embeddings[0]
                else:
                    logger.warning("Structure de réponse d'embedding inconnue (ancienne API)")
                    return [0.0] * 1536
            except Exception as e2:
                logger.error(f"Erreur lors de la création de l'embedding (ancienne API): {str(e2)}")
                return [0.0] * 1536  # 1536 est la dimension des embeddings ADA 002
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'embedding: {str(e)}")
            # Retourner un vecteur de zéros en cas d'erreur
            return [0.0] * 1536
    
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
                        hmo_data = row[i]
                        
                        # Essayer d'extraire le niveau d'assurance à partir du texte
                        insurance_tier = None
                        for tier in ["זהב", "כסף", "ארד"]:  # Gold, Silver, Bronze
                            if tier in hmo_data:
                                insurance_tier = tier
                                break
                        
                        chunk_text = f"Service: {service_name}\nHMO: {hmo_name}\nDétails: {hmo_data}"
                        
                        # Ajouter des mots-clés en anglais pour améliorer la recherche
                        if document.get('service_type') == "pragrency_services":
                            chunk_text += "\nKeywords: pregnancy, prenatal, birth, maternity, pregnant"
                        elif document.get('service_type') == "dentel_services":
                            chunk_text += "\nKeywords: dental, teeth, tooth, dentist, oral"
                        elif document.get('service_type') == "optometry_services":
                            chunk_text += "\nKeywords: vision, eye, glasses, contact lenses, optometry"
                        elif document.get('service_type') == "communication_clinic_services":
                            chunk_text += "\nKeywords: speech, hearing, communication, language, therapy"
                        elif document.get('service_type') == "alternative_services":
                            chunk_text += "\nKeywords: alternative medicine, acupuncture, homeopathy, massage, natural"
                        elif document.get('service_type') == "workshops_services":
                            chunk_text += "\nKeywords: workshop, class, group, training, education"
                        
                        chunks.append({
                            'text': chunk_text,
                            'metadata': {
                                'service_type': document.get('service_type', ''),
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
                    'service_type': document.get('service_type', ''),
                    'source_file': document.get('source_file', ''),
                    'chunk_type': 'contact',
                    'hmo_name': None,
                    'insurance_tier': None
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
        
        # Créer l'index de recherche
        dimension = embeddings_array.shape[1]
        try:
            if FAISS_AVAILABLE:
                index = faiss.IndexFlatL2(dimension)
                index.add(embeddings_array)
                logger.info("Index FAISS créé avec succès")
            else:
                index = SimpleIndex(dimension)
                index.add(embeddings_array)
                logger.info("Index simple créé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'index: {str(e)}")
            logger.info("Utilisation de l'index simple comme solution de secours")
            index = SimpleIndex(dimension)
            index.add(embeddings_array)
        
        # Sauvegarder l'index et les données
        self.documents = all_chunks
        self.embeddings = embeddings_array
        self.index = index
        
        # Sauvegarder les documents et les embeddings sur disque
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
        
        np.save(self.embedding_file, self.embeddings)
        
        # Sauvegarder l'index FAISS
        if FAISS_AVAILABLE:
            faiss.write_index(self.index, self.faiss_index_file)
        
        # Créer les métadonnées des embeddings
        embedding_metadata = {
            'total_embeddings': len(self.documents),
            'dimension': dimension,
            'service_types': list(set(doc.get('metadata', {}).get('service_type', '') for doc in self.documents)),
            'hmo_names': list(set(doc.get('metadata', {}).get('hmo_name', '') for doc in self.documents if doc.get('metadata', {}).get('hmo_name'))),
            'insurance_tiers': list(set(doc.get('metadata', {}).get('insurance_tier', '') for doc in self.documents if doc.get('metadata', {}).get('insurance_tier'))),
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'embeddings': [
                {
                    'index': i,
                    'text_preview': doc['text'][:100] + '...' if len(doc['text']) > 100 else doc['text'],
                    'service_type': doc.get('metadata', {}).get('service_type', ''),
                    'chunk_type': doc.get('metadata', {}).get('chunk_type', ''),
                    'hmo_name': doc.get('metadata', {}).get('hmo_name'),
                    'insurance_tier': doc.get('metadata', {}).get('insurance_tier'),
                    'embedding_dimension': dimension
                }
                for i, doc in enumerate(self.documents)
            ]
        }
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(embedding_metadata, f, ensure_ascii=False, indent=2)
        
        self.embedding_metadata = embedding_metadata
        
        logger.info(f"Index construit avec {len(all_chunks)} fragments")
    
    def load_index(self) -> bool:
        """Charge l'index depuis le disque s'il existe"""
        if os.path.exists(self.index_file) and os.path.exists(self.faiss_index_file):
            try:
                # Charger les documents
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                
                # Charger les embeddings
                self.embeddings = np.load(self.embedding_file)
                
                # Charger les métadonnées
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.embedding_metadata = json.load(f)
                    logger.info(f"Métadonnées d'embedding chargées: {self.embedding_metadata.get('total_embeddings')} embeddings, "
                               f"dimension {self.embedding_metadata.get('dimension')}")
                
                # Charger l'index FAISS
                if FAISS_AVAILABLE:
                    self.index = faiss.read_index(self.faiss_index_file)
                    logger.info(f"Index FAISS chargé avec succès: {self.index.ntotal} vecteurs")
                else:
                    dimension = self.embeddings.shape[1]
                    self.index = SimpleIndex(dimension)
                    self.index.add(self.embeddings)
                    logger.info("Index simple chargé avec succès")
                
                logger.info(f"Index chargé avec {len(self.documents)} fragments")
                return True
            
            except Exception as e:
                logger.error(f"Erreur lors du chargement de l'index: {str(e)}")
                return False
        else:
            logger.warning("Aucun index trouvé sur le disque")
            return False
    
    def search(self, query: str, top_k: int = 5, 
               filter_hmo: Optional[str] = None,
               filter_tier: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Recherche les documents les plus pertinents pour une requête
        en utilisant deux types de recherche:
        1. Documents spécifiques (HMO + tier)
        2. Documents généraux (NULL values)
        """
        if self.index is None:
            success = self.load_index()
            if not success:
                logger.error("Impossible de charger l'index pour la recherche")
                return []
        
        # Créer l'embedding de la requête
        query_embedding = self.create_embedding(query)
        query_embedding_array = np.array([query_embedding]).astype('float32')
        
        # Effectuer la recherche vectorielle
        try:
            # Récupérer tous les indices de notre index
            all_indices = np.arange(len(self.documents))
            
            # Logger les valeurs uniques de HMO et tier pour diagnostic
            hmo_values = set()
            tier_values = set()
            for idx in all_indices:
                if idx < len(self.documents):
                    metadata = self.documents[idx].get('metadata', {})
                    if metadata.get('hmo_name'):
                        hmo_values.add(metadata.get('hmo_name'))
                    if metadata.get('insurance_tier'):
                        tier_values.add(metadata.get('insurance_tier'))
            
            logger.info(f"Valeurs uniques de HMO dans l'index: {hmo_values}")
            logger.info(f"Valeurs uniques de tier dans l'index: {tier_values}")
            logger.info(f"Recherche pour HMO={filter_hmo!r}, tier={filter_tier!r}")
            
            # Filtrer les indices pour Recherche A: (HMO≈filter_hmo ET tier≈filter_tier)
            specific_indices = []
            for idx in all_indices:
                if idx < len(self.documents):
                    metadata = self.documents[idx].get('metadata', {})
                    hmo_name = metadata.get('hmo_name')
                    insurance_tier = metadata.get('insurance_tier')
                    
                    # Utiliser 'in' pour une comparaison plus souple
                    hmo_match = False
                    tier_match = False
                    
                    if hmo_name and filter_hmo:
                        # Enlever les espaces et comparer
                        hmo_match = filter_hmo.strip() in hmo_name.strip() or hmo_name.strip() in filter_hmo.strip()
                    
                    if insurance_tier and filter_tier:
                        # Enlever les espaces et comparer
                        tier_match = filter_tier.strip() in insurance_tier.strip() or insurance_tier.strip() in filter_tier.strip()
                    
                    if hmo_match and tier_match:
                        specific_indices.append(idx)
                        
                        # Log quelques exemples pour diagnostic
                        if len(specific_indices) <= 5:
                            logger.info(f"Document spécifique trouvé - HMO: {hmo_name!r}, Tier: {insurance_tier!r}")
            
            # Filtrer les indices pour Recherche B: (HMO IS NULL ET tier IS NULL)
            general_indices = []
            for idx in all_indices:
                if idx < len(self.documents):
                    metadata = self.documents[idx].get('metadata', {})
                    if (metadata.get('hmo_name') is None and 
                        metadata.get('insurance_tier') is None):
                        general_indices.append(idx)
            
            # Si aucun document spécifique trouvé, essayer avec une recherche plus large
            if len(specific_indices) == 0:
                logger.warning(f"Aucun document spécifique trouvé avec le filtre exact. Tentative avec filtre élargi.")
                
                # Recherche élargie: correspond à HMO OU à tier (pas les deux)
                for idx in all_indices:
                    if idx < len(self.documents):
                        metadata = self.documents[idx].get('metadata', {})
                        hmo_name = metadata.get('hmo_name')
                        insurance_tier = metadata.get('insurance_tier')
                        
                        hmo_match = False
                        tier_match = False
                        
                        if hmo_name and filter_hmo:
                            hmo_match = filter_hmo.strip() in hmo_name.strip() or hmo_name.strip() in filter_hmo.strip()
                        
                        if insurance_tier and filter_tier:
                            tier_match = filter_tier.strip() in insurance_tier.strip() or insurance_tier.strip() in filter_tier.strip()
                        
                        # Il suffit que l'un des deux corresponde
                        if hmo_match or tier_match:
                            specific_indices.append(idx)
                            
                            # Log quelques exemples
                            if len(specific_indices) <= 5:
                                logger.info(f"Document trouvé avec filtre élargi - HMO: {hmo_name!r}, Tier: {insurance_tier!r}")
            
            # Convertir les listes d'indices en tableaux NumPy
            specific_indices_array = np.array(specific_indices).astype('int64')
            general_indices_array = np.array(general_indices).astype('int64')
            
            logger.info(f"Recherche A: {len(specific_indices)} documents spécifiques trouvés pour HMO={filter_hmo}, tier={filter_tier}")
            logger.info(f"Recherche B: {len(general_indices)} documents généraux trouvés")
            
            # Définir le nombre max de résultats à retourner pour chaque recherche
            specific_top_k = min(30, len(specific_indices))
            general_top_k = min(10, len(general_indices))
            
            # Effectuer les deux recherches
            results_A = []
            results_B = []
            
            # Recherche A: documents spécifiques (HMO + tier)
            if len(specific_indices) > 0:
                # Créer un sous-index pour les documents spécifiques
                if FAISS_AVAILABLE:
                    # Extraire les embeddings des documents spécifiques
                    specific_embeddings = self.embeddings[specific_indices]
                    
                    # Créer un index temporaire
                    specific_index = faiss.IndexFlatL2(specific_embeddings.shape[1])
                    specific_index.add(specific_embeddings)
                    
                    # Effectuer la recherche
                    specific_distances, specific_idx = specific_index.search(query_embedding_array, specific_top_k)
                    
                    # Convertir les indices relatifs en indices absolus
                    absolute_indices = [specific_indices[idx] for idx in specific_idx[0]]
                    
                    # Récupérer les résultats
                    for i, idx in enumerate(absolute_indices):
                        if idx < len(self.documents):
                            document = self.documents[idx].copy()
                            document['score'] = float(1.0 / (1.0 + specific_distances[0][i]))
                            results_A.append(document)
            
            # Recherche B: documents généraux (NULL values)
            if len(general_indices) > 0:
                # Créer un sous-index pour les documents généraux
                if FAISS_AVAILABLE:
                    # Extraire les embeddings des documents généraux
                    general_embeddings = self.embeddings[general_indices]
                    
                    # Créer un index temporaire
                    general_index = faiss.IndexFlatL2(general_embeddings.shape[1])
                    general_index.add(general_embeddings)
                    
                    # Effectuer la recherche
                    general_distances, general_idx = general_index.search(query_embedding_array, general_top_k)
                    
                    # Convertir les indices relatifs en indices absolus
                    absolute_indices = [general_indices[idx] for idx in general_idx[0]]
                    
                    # Récupérer les résultats
                    for i, idx in enumerate(absolute_indices):
                        if idx < len(self.documents):
                            document = self.documents[idx].copy()
                            document['score'] = float(1.0 / (1.0 + general_distances[0][i]))
                            results_B.append(document)
            
            # Fusionner les résultats
            merged_results = results_A + results_B
            
            # Trier par score décroissant
            merged_results.sort(key=lambda x: x['score'], reverse=True)
            
            # Limiter au nombre demandé
            final_results = merged_results[:top_k]
            
            # Analyser les types de services inclus
            service_types_included = {doc.get('metadata', {}).get('service_type', 'unknown') for doc in final_results}
            logger.info(f"Recherche terminée. Types de services inclus: {service_types_included}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {str(e)}")
            logger.exception("Détails de l'erreur:")
            return []

# Exemple d'utilisation
if __name__ == "__main__":
    import time
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