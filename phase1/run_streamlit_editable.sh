#!/bin/bash

# Vérifier si Python est installé
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo "Python n'est pas installé. Veuillez installer Python 3."
    exit 1
fi

# Vérifier si Streamlit est installé
if ! $PYTHON_CMD -c "import streamlit" &>/dev/null; then
    echo "Streamlit n'est pas installé. Installation en cours..."
    $PYTHON_CMD -m pip install streamlit
fi

# Vérifier si pandas est installé
if ! $PYTHON_CMD -c "import pandas" &>/dev/null; then
    echo "Pandas n'est pas installé. Installation en cours..."
    $PYTHON_CMD -m pip install pandas
fi

# Déterminer le chemin absolu du répertoire app
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/app"

# Lancer l'application Streamlit avec l'interface éditable sans spécifier de port
cd "$APP_DIR" && streamlit run streamlit_app_editable.py 