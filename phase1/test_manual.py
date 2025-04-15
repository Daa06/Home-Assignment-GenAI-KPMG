from app.utils.ocr import DocumentIntelligenceExtractor
import json
import os

def main():
    # Créer l'extracteur
    extractor = DocumentIntelligenceExtractor()
    
    # Chemin vers le document de test
    document_path = "../phase1_data/283_ex1.pdf"
    
    # Vérifier que le fichier existe
    if not os.path.exists(document_path):
        print(f"❌ Erreur: Le fichier {document_path} n'existe pas!")
        return
    
    print(f"🔍 Analyse du document: {document_path}")
    print("⏳ Extraction en cours...")
    
    # Extraire le texte
    result = extractor.extract_text(document_path)
    
    print("\n✅ Extraction réussie!")
    print("\n📝 Texte extrait:")
    print("-" * 50)
    print(result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"])
    print("-" * 50)
    
    print("\n📊 Tables trouvées:", len(result["tables"]))
    if result["tables"]:
        print("\nPremière table:")
        for row in result["tables"][0]:
            print(row)
    
    print("\n📄 Pages analysées:", len(result["layout"]))
    
    # Sauvegarder le résultat complet dans un fichier JSON
    output_file = "extraction_result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Résultat complet sauvegardé dans: {output_file}")

if __name__ == "__main__":
    main() 