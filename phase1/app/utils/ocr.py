import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
import sys
import logging
import base64
import base64
from typing import Dict, Any, Optional

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT, AZURE_DOCUMENT_INTELLIGENCE_KEY

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentIntelligenceExtractor:
    def __init__(self):
        """Initialize the Document Intelligence client."""
        endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        
        if not endpoint or not key:
            raise ValueError("Azure Document Intelligence credentials not found in environment variables")
            
        self.client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    def _extract_bounding_box(self, polygon):
        """
        Extraire la boîte englobante à partir d'un polygone retourné par l'API.
        Gère les deux formats possibles de polygones (liste de points ou liste de coordonnées).
        
        Args:
            polygon: Liste de points ou de coordonnées représentant le polygone
            
        Returns:
            Dict contenant x, y, width et height de la boîte englobante
        """
        try:
            if not polygon:
                return {"x": 0, "y": 0, "width": 100, "height": 20}
                
            # Si polygon est une liste d'objets Point avec attributs x et y
            if hasattr(polygon[0], 'x') and hasattr(polygon[0], 'y'):
                # Format avec des objets Points
                x_coordinates = [p.x for p in polygon]
                y_coordinates = [p.y for p in polygon]
            # Si polygon contient directement des nombres (liste plate [x1, y1, x2, y2, ...])
            elif isinstance(polygon[0], (int, float)):
                if len(polygon) % 2 == 0:
                    x_coordinates = [polygon[i] for i in range(0, len(polygon), 2)]
                    y_coordinates = [polygon[i] for i in range(1, len(polygon), 2)]
                else:
                    # Format inconnu, on utilise des valeurs par défaut
                    return {"x": 0, "y": 0, "width": 100, "height": 20}
            # Si polygon est une liste de listes/tuples de coordonnées [[x1,y1], [x2,y2], ...]
            elif isinstance(polygon[0], (list, tuple)) and len(polygon[0]) == 2:
                x_coordinates = [p[0] for p in polygon]
                y_coordinates = [p[1] for p in polygon]
            else:
                # Format inconnu, on utilise des valeurs par défaut
                logger.warning(f"Format de polygone non reconnu: {type(polygon[0])}")
                return {"x": 0, "y": 0, "width": 100, "height": 20}
                    
            # Calculer les dimensions de la boîte englobante
            min_x = min(x_coordinates)
            min_y = min(y_coordinates)
            max_x = max(x_coordinates)
            max_y = max(y_coordinates)
            
            return {
                "x": min_x,
                "y": min_y,
                "width": max_x - min_x,
                "height": max_y - min_y
            }
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction de la boîte englobante: {str(e)}")
            # En cas d'erreur, retourner une boîte par défaut
            return {"x": 0, "y": 0, "width": 100, "height": 20}

    def extract_text(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text, tables and layout from a document using Azure Document Intelligence.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dict containing extracted text, tables, layout and confidence scores
        """
        try:
            with open(file_path, "rb") as f:
                document_bytes = f.read()
                base64_encoded = base64.b64encode(document_bytes).decode()
                
            poller = self.client.begin_analyze_document("prebuilt-layout", {"base64Source": base64_encoded})
            result = poller.result()

            # Extraire le texte avec les scores de confiance
            text_with_confidence = []
            for page in result.pages:
                for line in page.lines:
                    try:
                        # Vérifier si polygon est une liste de points ou de coordonnées directes
                        bbox = self._extract_bounding_box(line.polygon)
                        text_with_confidence.append({
                            "text": line.content,
                            "confidence": getattr(line, 'confidence', 0.8),
                            "bounding_box": bbox,
                            "page": page.page_number
                        })
                    except Exception as e:
                        logger.warning(f"Erreur lors du traitement d'une ligne: {str(e)}")

            # Extraire les tables
            tables = []
            for table in result.tables:
                table_data = []
                for cell in table.cells:
                    table_data.append({
                        "text": cell.content,
                        "row_index": cell.row_index,
                        "column_index": cell.column_index,
                        "confidence": cell.confidence if hasattr(cell, 'confidence') else None
                    })
                tables.append(table_data)

            # Extraire les informations de mise en page
            layout = []
            for page in result.pages:
                page_layout = {
                    "page_number": page.page_number,
                    "width": page.width,
                    "height": page.height,
                    "unit": "points",
                    "spans": []
                }
                
                # Ajouter les spans avec leurs positions
                for word in page.words:
                    try:
                        bbox = self._extract_bounding_box(word.polygon)
                        page_layout["spans"].append({
                            "text": word.content,
                            "confidence": getattr(word, 'confidence', 0.8),
                            "bounding_box": bbox
                        })
                    except Exception as e:
                        logger.warning(f"Erreur lors du traitement d'un mot: {str(e)}")
                    
                layout.append(page_layout)

            # Calculer la confiance moyenne
            confidences = [span["confidence"] for page in layout for span in page["spans"] if span["confidence"] is not None]
            average_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                "text": text_with_confidence,
                "tables": tables,
                "layout": layout,
                "average_confidence": average_confidence
            }

        except Exception as e:
            logger.error(f"Error extracting text from document: {str(e)}")
            raise 