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
        
        # Définir ici exactement la structure JSON attendue selon le README
        self.expected_schema = {
            "lastName": "",
            "firstName": "",
            "idNumber": "",
            "gender": "",
            "dateOfBirth": {
                "day": "",
                "month": "",
                "year": ""
            },
            "address": {
                "street": "",
                "houseNumber": "",
                "entrance": "",
                "apartment": "",
                "city": "",
                "postalCode": "",
                "poBox": ""
            },
            "landlinePhone": "",
            "mobilePhone": "",
            "jobType": "",
            "dateOfInjury": {
                "day": "",
                "month": "",
                "year": ""
            },
            "timeOfInjury": "",
            "accidentLocation": "",
            "accidentAddress": "",
            "accidentDescription": "",
            "injuredBodyPart": "",
            "signature": "",
            "formFillingDate": {
                "day": "",
                "month": "",
                "year": ""
            },
            "formReceiptDateAtClinic": {
                "day": "",
                "month": "",
                "year": ""
            },
            "medicalInstitutionFields": {
                "healthFundMember": "",
                "natureOfAccident": "",
                "medicalDiagnoses": ""
            }
        }

    def _create_extraction_prompt(self, text_content: str) -> str:
        """
        Crée le prompt pour l'extraction des champs.
        
        Args:
            text_content (str): Le texte extrait du document
            
        Returns:
            str: Le prompt formaté
        """
        # Créer une représentation JSON du schéma attendu
        schema_json = json.dumps(self.expected_schema, ensure_ascii=False, indent=2)
        
        return f"""Tu es un expert en extraction d'informations à partir de documents en hébreu et en anglais.
Je vais te donner le texte extrait d'un formulaire de l'Institut National d'Assurance (ביטוח לאומי).
Ta tâche est d'extraire les informations pertinentes et de les structurer dans un format JSON précis.

Voici EXACTEMENT le format JSON attendu, respecte STRICTEMENT cette structure sans ajouter de champs supplémentaires :
{schema_json}

Important :
1. Respecte EXACTEMENT cette structure sans AUCUNE modification
2. Ne crée PAS de nouveaux champs qui ne sont pas dans la structure
3. Assure-toi que chaque champ est présent, même s'il est vide
4. Si tu ne trouves pas d'information pour un champ, laisse une chaîne vide ("")
5. Pour les dates, extrais correctement les composants jour/mois/année
6. N'ajoute PAS de scores de confiance ou d'autres métadonnées aux champs

Texte du document:
{text_content}

Ton rôle est d'extraire toutes les informations pertinentes du texte et de les organiser selon le format JSON spécifié ci-dessus.
Assure-toi de renvoyer UNIQUEMENT le JSON sans aucun texte supplémentaire.
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
                    {"role": "system", "content": "Tu es un assistant expert en extraction de données à partir de documents hébreux et anglais. Tu réponds UNIQUEMENT avec un objet JSON valide selon le format demandé, sans texte supplémentaire et sans ajouter de champs supplémentaires."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Réduire au minimum la créativité pour une extraction précise
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Extraire le JSON brut de la réponse
            raw_result = json.loads(response.choices[0].message.content)
            
            # IMPORTANT: Supprimer explicitement toute section 'confidences' qui pourrait apparaître
            if 'confidences' in raw_result:
                logger.warning("Removing 'confidences' section from OpenAI response")
                del raw_result['confidences']
            
            # Au lieu de modifier la réponse, créer un nouveau dictionnaire en utilisant uniquement les champs attendus
            result = {}
            
            # Fonction récursive pour copier uniquement les champs définis dans expected_schema
            def copy_expected_fields(source, schema, target):
                for key, value in schema.items():
                    # Ignorer explicitement toute clé liée aux confidences
                    if key == 'confidences' or key.endswith('_confidence'):
                        continue
                        
                    if isinstance(value, dict):
                        # Si le champ est un dictionnaire imbriqué
                        if key in source and isinstance(source[key], dict):
                            target[key] = {}
                            copy_expected_fields(source[key], schema[key], target[key])
                        else:
                            # Si le champ n'existe pas dans la source ou n'est pas un dictionnaire
                            # créer une structure vide
                            target[key] = {k: "" for k, v in schema[key].items()}
                    else:
                        # Pour les champs simples, copier la valeur si elle existe
                        target[key] = source.get(key, "")
            
            # Copier uniquement les champs attendus
            copy_expected_fields(raw_result, self.expected_schema, result)
            
            # Log du résultat final (pour débogage)
            logger.info(f"Extraction structurée réussie avec {len(result)} champs de premier niveau")
            
            # Vérification finale : s'assurer qu'il n'y a pas de champ 'confidences'
            if 'confidences' in result:
                logger.warning("Removing 'confidences' section from final result")
                del result['confidences']
                
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction structurée: {str(e)}")
            raise 