from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
import os
import sys
import json
import logging

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_DEPLOYMENT_NAME
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIExtractor:
    def __init__(self):
        """Initialise le client Azure OpenAI."""
        self.client = AzureOpenAI(
            api_key=AZURE_OPENAI_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )

    def _create_extraction_prompt(self, text_content: str) -> str:
        """
        Crée le prompt pour l'extraction des champs.
        
        Args:
            text_content (str): Le texte extrait du document
            
        Returns:
            str: Le prompt formaté
        """
        return f"""Tu es un expert en extraction d'informations à partir de documents en hébreu et en anglais.
Je vais te donner le texte extrait d'un formulaire de l'Institut National d'Assurance (ביטוח לאומי).
Ta tâche est d'extraire les informations pertinentes et de les structurer dans un format JSON spécifique.

Format JSON requis:
{{
  "lastName": "",          // שם משפחה
  "firstName": "",         // שם פרטי
  "idNumber": "",         // מספר זהות
  "gender": "",           // מין
  "dateOfBirth": {{
    "day": "",
    "month": "",
    "year": ""
  }},
  "address": {{
    "street": "",         // רחוב
    "houseNumber": "",    // מספר בית
    "entrance": "",       // כניסה
    "apartment": "",      // דירה
    "city": "",          // עיר
    "postalCode": "",    // מיקוד
    "poBox": ""          // תא דואר
  }},
  "landlinePhone": "",    // טלפון קווי
  "mobilePhone": "",      // טלפון נייד
  "jobType": "",         // סוג העבודה
  "dateOfInjury": {{
    "day": "",
    "month": "",
    "year": ""
  }},
  "timeOfInjury": "",     // שעת הפגיעה
  "accidentLocation": "", // מקום התאונה
  "accidentAddress": "",  // כתובת מקום התאונה
  "accidentDescription": "", // תיאור התאונה
  "injuredBodyPart": "",  // האיבר שנפגע
  "signature": "",        // חתימה
  "formFillingDate": {{
    "day": "",
    "month": "",
    "year": ""
  }},
  "formReceiptDateAtClinic": {{
    "day": "",
    "month": "",
    "year": ""
  }},
  "medicalInstitutionFields": {{
    "healthFundMember": "",    // חבר בקופת חולים
    "natureOfAccident": "",    // מהות התאונה
    "medicalDiagnoses": ""     // אבחנות רפואיות
  }}
}}

Texte du document:
{text_content}

Extrais toutes les informations pertinentes et retourne-les dans le format JSON spécifié.
Pour les champs non trouvés, laisse une chaîne vide.
Assure-toi que les dates sont correctement formatées dans leurs composants jour/mois/année.
"""

    def extract_structured_data(self, text_content: str) -> dict:
        """
        Extrait les données structurées à partir du texte en utilisant Azure OpenAI.
        
        Args:
            text_content (str): Le texte extrait du document
            
        Returns:
            dict: Les données structurées au format JSON demandé
        """
        try:
            # Créer le prompt
            prompt = self._create_extraction_prompt(text_content)
            
            # Appeler Azure OpenAI
            response = self.client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": "Tu es un assistant expert en extraction de données à partir de documents hébreux et anglais."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Réduire la créativité pour plus de précision
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Extraire et valider le JSON
            result = json.loads(response.choices[0].message.content)
            logger.info("Extraction structurée réussie")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction structurée: {str(e)}")
            raise 