import os
from app.utils.ocr import DocumentIntelligenceExtractor
from app.utils.openai_extractor import OpenAIExtractor
import json

def save_structured_result(result, output_file):
    """Sauvegarde le résultat structuré dans un fichier JSON."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nRésultat sauvegardé dans: {output_file}")

def test_extraction():
    # Initialiser les extracteurs
    doc_extractor = DocumentIntelligenceExtractor()
    openai_extractor = OpenAIExtractor()
    
    # Chemin vers le fichier de test
    test_file = "../phase1_data/283_ex1.pdf"
    
    print(f"Test d'extraction sur le fichier: {test_file}")
    print("-" * 50)
    
    # Étape 1: Extraction OCR
    print("1. Extraction OCR en cours...")
    ocr_result = doc_extractor.extract_text(test_file)
    print("✅ OCR terminé")
    print(f"Longueur du texte extrait: {len(ocr_result['text'])} caractères")
    print("-" * 50)
    
    # Étape 2: Extraction structurée
    print("2. Extraction structurée avec Azure OpenAI en cours...")
    structured_result = openai_extractor.extract_structured_data(ocr_result["text"])
    print("✅ Extraction structurée terminée")
    print("-" * 50)
    
    # Afficher le résultat
    print("Résultat de l'extraction:")
    print(json.dumps(structured_result, ensure_ascii=False, indent=2))
    
    # Sauvegarder le résultat structuré
    output_file = "structured_result.json"
    save_structured_result(structured_result, output_file)

if __name__ == "__main__":
    test_extraction() 