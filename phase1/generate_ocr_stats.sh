#!/bin/bash

# Obtenir le chemin du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
EXTRACTIONS_DIR="$SCRIPT_DIR/extractions"
REPORT_FILE="$SCRIPT_DIR/ocr_reliability_report.html"

# Activer l'environnement virtuel si nécessaire
# source venv/bin/activate

echo "Génération du rapport de statistiques OCR..."
echo "Dossier d'extractions: $EXTRACTIONS_DIR"
echo "Rapport de sortie: $REPORT_FILE"

# Exécuter le script de génération de statistiques
python3 "$SCRIPT_DIR/generate_ocr_stats.py" --extractions "$EXTRACTIONS_DIR" --output "$REPORT_FILE" --open

# Afficher un message
echo "Terminé!" 