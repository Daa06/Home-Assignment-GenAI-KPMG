import numpy as np
from typing import List, Dict, Any, Tuple
from loguru import logger

class SimpleIndex:
    """
    Implémentation simple d'un index de recherche basé sur la distance euclidienne.
    Utilisé comme solution de secours si FAISS n'est pas disponible.
    """
    
    def __init__(self, dimension: int):
        """Initialise l'index avec la dimension spécifiée"""
        self.dimension = dimension
        self.embeddings = np.zeros((0, dimension), dtype=np.float32)
    
    def add(self, vectors: np.ndarray) -> None:
        """Ajoute des vecteurs à l'index"""
        if vectors.shape[1] != self.dimension:
            raise ValueError(f"Les vecteurs doivent avoir une dimension de {self.dimension}")
        
        if self.embeddings.shape[0] == 0:
            self.embeddings = vectors
        else:
            self.embeddings = np.vstack((self.embeddings, vectors))
    
    def search(self, query_vectors: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Recherche les k plus proches voisins des vecteurs de requête.
        
        Args:
            query_vectors: Vecteurs de requête (n_queries, dimension)
            k: Nombre de plus proches voisins à retourner
        
        Returns:
            Tuple contenant (distances, indices)
        """
        if query_vectors.shape[1] != self.dimension:
            raise ValueError(f"Les vecteurs de requête doivent avoir une dimension de {self.dimension}")
        
        n_queries = query_vectors.shape[0]
        
        # Calculer les distances euclidiennes
        distances = np.zeros((n_queries, self.embeddings.shape[0]), dtype=np.float32)
        
        for i in range(n_queries):
            for j in range(self.embeddings.shape[0]):
                # Distance euclidienne au carré
                distances[i, j] = np.sum((query_vectors[i] - self.embeddings[j])**2)
        
        # Trier les distances et obtenir les indices
        indices = np.argsort(distances, axis=1)[:, :k]
        sorted_distances = np.take_along_axis(distances, indices, axis=1)
        
        return sorted_distances, indices 