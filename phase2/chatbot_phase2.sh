#!/bin/bash

# Couleurs pour la sortie
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Fonction pour détecter le chemin absolu du script
get_script_path() {
    # Obtenir le chemin absolu du script
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        SCRIPT_PATH=$(cd "$(dirname "$0")" && pwd)
    else
        # Linux et autres
        SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
    fi
    echo "$SCRIPT_PATH"
}

# Vérifier si Python 3 est installé
check_python() {
    print_message "Checking Python installation..."
    if command -v python3 &>/dev/null; then
        PYTHON_CMD="python3"
        print_success "Python 3 found: $(python3 --version)"
    elif command -v python &>/dev/null && [[ $(python --version 2>&1) == *"Python 3"* ]]; then
        PYTHON_CMD="python"
        print_success "Python 3 found: $(python --version)"
    else
        print_error "Python 3 is not installed or not in PATH. Please install Python 3.8 or higher."
        exit 1
    fi
}

# Vérifier si pip est installé
check_pip() {
    print_message "Checking pip installation..."
    if command -v pip3 &>/dev/null; then
        PIP_CMD="pip3"
        print_success "pip found: $(pip3 --version)"
    elif command -v pip &>/dev/null; then
        PIP_CMD="pip"
        print_success "pip found: $(pip --version)"
    else
        print_error "pip is not installed or not in PATH. Please install pip."
        exit 1
    fi
}

# Installer les dépendances une par une
install_dependencies() {
    print_message "Installing dependencies one by one..."
    APP_DIR="$1"
    REQUIREMENTS_FILE="$APP_DIR/requirements.txt"
    
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        print_error "Requirements file not found: $REQUIREMENTS_FILE"
        exit 1
    fi
    
    # Créer un environnement virtuel si souhaité
    if [ "$USE_VENV" = true ]; then
        print_message "Creating virtual environment..."
        $PYTHON_CMD -m venv "$APP_DIR/venv" || {
            print_error "Failed to create virtual environment."
            exit 1
        }
        
        # Activer l'environnement virtuel
        if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
            source "$APP_DIR/venv/bin/activate"
        elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
            source "$APP_DIR/venv/Scripts/activate"
        else
            print_error "Unsupported OS for virtual environment activation."
            exit 1
        fi
        
        print_success "Virtual environment activated."
        
        # Mettre à jour pip dans l'environnement virtuel
        $PIP_CMD install --upgrade pip
    fi
    
    # Lire le fichier requirements.txt et installer chaque package individuellement
    while IFS= read -r requirement || [[ -n "$requirement" ]]; do
        # Ignorer les lignes vides et les commentaires
        if [[ -z "$requirement" ]] || [[ "$requirement" =~ ^# ]]; then
            continue
        fi
        
        print_message "Installing $requirement..."
        $PIP_CMD install "$requirement" || {
            print_error "Failed to install $requirement."
            print_warning "Continuing with other packages..."
        }
    done < "$REQUIREMENTS_FILE"
    
    print_success "Dependencies installation completed."
}

# Créer l'index de connaissance
create_knowledge_index() {
    print_message "Creating knowledge index..."
    APP_DIR="$1"
    
    # S'assurer que le répertoire des données existe
    mkdir -p "$APP_DIR/phase2_data"
    
    # Exécuter le script de rebuild d'index
    cd "$APP_DIR" && $PYTHON_CMD rebuild_index_complete.py || {
        print_error "Failed to build knowledge index."
        print_warning "The application may not work properly without the knowledge index."
    }
    
    print_success "Knowledge index created."
}

# Lancer l'application
run_application() {
    print_message "Starting the application..."
    APP_DIR="$1"
    
    # Exécuter le script fix_app_final.py
    cd "$APP_DIR" && $PYTHON_CMD fix_app_final.py || {
        print_error "Failed to start the application."
        exit 1
    }
}

# Fonction principale
main() {
    print_message "====== Phase 2 Application Runner ======"
    
    # Gérer les options en ligne de commande
    USE_VENV=false
    
    while [[ "$#" -gt 0 ]]; do
        case $1 in
            -v|--venv) USE_VENV=true ;;
            *) print_error "Unknown parameter: $1"; exit 1 ;;
        esac
        shift
    done
    
    # Obtenir le chemin du script
    SCRIPT_PATH=$(get_script_path)
    print_message "Script located at: $SCRIPT_PATH"
    
    # Vérifier l'environnement Python
    check_python
    check_pip
    
    # Installer les dépendances
    install_dependencies "$SCRIPT_PATH"
    
    # Créer l'index de connaissance
    create_knowledge_index "$SCRIPT_PATH"
    
    # Lancer l'application
    run_application "$SCRIPT_PATH"
}

# Exécuter la fonction principale
main "$@" 