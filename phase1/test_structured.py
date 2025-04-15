from app.utils.ocr import DocumentIntelligenceExtractor
from app.utils.openai_extractor import OpenAIExtractor
import json

def main():
    # Créer les extracteurs
    doc_extractor = DocumentIntelligenceExtractor()
    openai_extractor = OpenAIExtractor()
    
    # Chemin vers le document de test
    document_path = "../phase1_data/283_ex1.pdf"
    
    print(f"🔍 Analyse du document: {document_path}")
    
    # Étape 1: Extraction OCR
    print("\n⏳ Étape 1: Extraction OCR...")
    ocr_result = doc_extractor.extract_text(document_path)
    print("✅ Extraction OCR réussie")
    
    # Étape 2: Extraction structurée avec OpenAI
    print("\n⏳ Étape 2: Extraction structurée...")
    structured_result = openai_extractor.extract_structured_data(ocr_result["text"])
    print("✅ Extraction structurée réussie")
    
    # Sauvegarder le résultat
    output_file = "structured_result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(structured_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Résultat sauvegardé dans: {output_file}")
    
    # Afficher un aperçu du résultat
    print("\n📋 Aperçu des données extraites:")
    print("-" * 50)
    preview = {
        "Nom": structured_result["lastName"],
        "Prénom": structured_result["firstName"],
        "ID": structured_result["idNumber"],
        "Adresse": {
            "Rue": structured_result["address"]["street"],
            "Ville": structured_result["address"]["city"]
        }
    }
    print(json.dumps(preview, ensure_ascii=False, indent=2))
    print("-" * 50)

if __name__ == "__main__":
    main() 