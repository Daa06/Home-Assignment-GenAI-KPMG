#!/bin/bash

# Script pour réinitialiser les statistiques OCR et le rapport HTML

# Obtenir le chemin du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
EXTRACTIONS_DIR="$SCRIPT_DIR/extractions"
REPORT_FILE="$SCRIPT_DIR/ocr_reliability_report.html"

echo "Réinitialisation des statistiques OCR..."

# 1. Sauvegarder les extractions existantes (optionnel)
BACKUP_DIR="$SCRIPT_DIR/extractions_backup/backup_$(date +%Y%m%d_%H%M%S)"
if [ -d "$EXTRACTIONS_DIR" ] && [ "$(ls -A $EXTRACTIONS_DIR)" ]; then
    echo "Sauvegarde des extractions existantes dans $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    cp "$EXTRACTIONS_DIR"/*.json "$BACKUP_DIR/" 2>/dev/null
fi

# 2. Supprimer les fichiers d'extraction
echo "Suppression des fichiers d'extraction..."
rm -f "$EXTRACTIONS_DIR"/*.json

# 3. Supprimer le rapport HTML s'il existe
if [ -f "$REPORT_FILE" ]; then
    echo "Suppression du rapport HTML..."
    rm -f "$REPORT_FILE"
fi

echo "✅ Réinitialisation terminée avec succès !"
echo "Vous pouvez maintenant relancer l'application et télécharger de nouveaux documents." 