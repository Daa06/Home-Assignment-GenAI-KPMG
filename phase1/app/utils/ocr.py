from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
import os
import sys
import logging
import base64

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT, AZURE_DOCUMENT_INTELLIGENCE_KEY

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentIntelligenceExtractor:
    def __init__(self):
        """Initialise le client Azure Document Intelligence."""
        self.client = DocumentIntelligenceClient(
            endpoint=AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(AZURE_DOCUMENT_INTELLIGENCE_KEY)
        )

    def extract_text(self, document_path: str) -> dict:
        """
        Extrait le texte et la mise en page d'un document.
        
        Args:
            document_path (str): Chemin vers le document PDF ou image
            
        Returns:
            dict: Contient le texte extrait et la mise en page
        """
        try:
            # Lire le fichier en base64
            with open(document_path, "rb") as document:
                base64_encoded = base64.b64encode(document.read()).decode()

            # Créer la requête
            analyze_request = {
                "base64Source": base64_encoded
            }

            # Appeler l'API
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-layout",
                analyze_request=analyze_request
            )
            result = poller.result()

            # Extraction du texte et de la mise en page
            extracted_data = {
                "text": "",
                "tables": [],
                "layout": []
            }

            # Extraction du texte
            for page in result.pages:
                for line in page.lines:
                    extracted_data["text"] += line.content + "\n"

            # Extraction des tables
            for table in result.tables:
                table_data = []
                for row in range(table.row_count):
                    row_data = []
                    for cell in table.cells:
                        if cell.row_index == row:
                            row_data.append(cell.content)
                    table_data.append(row_data)
                extracted_data["tables"].append(table_data)

            # Extraction de la mise en page
            for page in result.pages:
                page_layout = {
                    "page_number": page.page_number,
                    "width": page.width,
                    "height": page.height,
                    "unit": page.unit,
                    "lines": []
                }
                for line in page.lines:
                    page_layout["lines"].append({
                        "content": line.content,
                        "polygon": line.polygon if hasattr(line, 'polygon') else None,
                        "spans": [{"offset": span.offset, "length": span.length} 
                                 for span in line.spans] if hasattr(line, 'spans') else []
                    })
                extracted_data["layout"].append(page_layout)

            logger.info(f"Extraction réussie pour le document: {document_path}")
            return extracted_data

        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du document {document_path}: {str(e)}")
            raise 