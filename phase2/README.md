# Phase 2: Chatbot Medical Services Q&A

## Description
Cette application est un chatbot basé sur l'intelligence artificielle qui fournit des informations sur les services médicaux des caisses maladie israéliennes (Maccabi, Meuhedet et Clalit). Le système est capable de comprendre l'hébreu et l'anglais et adapte ses réponses en fonction du profil spécifique de l'utilisateur.

## Architecture
L'application suit une architecture microservice stateless :
- **Backend**: Une API REST développée avec FastAPI
- **Frontend**: Une interface utilisateur développée avec Streamlit
- **AI**: Utilisation d'Azure OpenAI (GPT-4o et ADA 002 pour les embeddings)
- **Base de connaissances**: Fichiers HTML traités et indexés pour une recherche vectorielle

## Prérequis
- Python 3.8 ou supérieur
- Pip (gestionnaire de paquets Python)
- Accès aux services Azure OpenAI

## Installation

1. Cloner le dépôt (si ce n'est pas déjà fait)
2. Naviguer vers le répertoire du projet:
```bash
cd phase2
```

3. Installer les dépendances:
```bash
pip install -r requirements.txt
```

4. Créer un fichier `.env` à la racine du répertoire `phase2` avec vos informations d'authentification Azure:
```
# Azure OpenAI
AZURE_OPENAI_API_KEY=votre_clé_api
AZURE_OPENAI_ENDPOINT=votre_endpoint
AZURE_OPENAI_API_VERSION=2023-05-15

# Noms des déploiements Azure
GPT4O_DEPLOYMENT_NAME=gpt-4o
GPT4O_MINI_DEPLOYMENT_NAME=gpt-4o-mini
EMBEDDING_DEPLOYMENT_NAME=text-embedding-ada-002

# Configuration serveur (optionnel)
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False
UI_HOST=0.0.0.0
UI_PORT=8501

# Niveau de log
LOG_LEVEL=INFO
```

## Démarrage de l'application

1. Lancer l'API backend:
```bash
python run_api.py
```

2. Dans un nouveau terminal, lancer l'interface utilisateur Streamlit:
```bash
python run_ui.py
```

3. Accéder à l'interface utilisateur dans votre navigateur à l'adresse:
```
http://localhost:8501
```

## Utilisation

L'application comporte deux phases principales:

### Phase 1: Collecte d'informations utilisateur
- L'application vous guidera à travers un dialogue conversationnel pour collecter vos informations personnelles
- Vous devrez fournir: nom, prénom, numéro d'ID, genre, âge, caisse maladie, numéro de carte et niveau d'assurance
- Une fois toutes les informations collectées, un résumé vous sera présenté pour confirmation

### Phase 2: Questions-Réponses
- Après avoir complété votre profil, vous pouvez passer au mode Q&A
- Posez des questions sur les services médicaux de votre caisse maladie
- Le système fournira des réponses personnalisées basées sur votre profil

## Confidentialité des données

- Toutes les données utilisateur sont conservées exclusivement côté client (dans votre navigateur)
- Aucune information personnelle n'est stockée sur le serveur
- Vous pouvez réinitialiser toutes vos données à tout moment via le bouton "Réinitialiser"

## Fonctionnalités clés

- Support multilingue (hébreu et anglais)
- Réponses personnalisées basées sur la caisse maladie et le niveau d'assurance
- Interface adaptative qui s'ajuste automatiquement à la direction du texte
- Architecture sans état pour une haute disponibilité et scalabilité
- Recherche sémantique dans la base de connaissances

## Structure du code

```
phase2/
├── app/
│   ├── api/            # Endpoints FastAPI
│   ├── core/           # Configuration
│   ├── knowledge/      # Gestion de la base de connaissances
│   ├── llm/            # Interaction avec Azure OpenAI
│   ├── logging/        # Configuration des logs
│   └── ui/             # Interface Streamlit
├── logs/               # Fichiers de logs (créés automatiquement)
├── .env                # Variables d'environnement (à créer)
├── README.md           # Ce fichier
├── requirements.txt    # Dépendances
├── run_api.py          # Script pour démarrer l'API
└── run_ui.py           # Script pour démarrer l'UI
```

## Dépannage

1. **Problème de connexion à l'API:**
   - Vérifiez que l'API est bien en cours d'exécution (`python run_api.py`)
   - Vérifiez que les ports ne sont pas bloqués par un pare-feu

2. **Erreurs liées à Azure OpenAI:**
   - Vérifiez vos clés API et endpoints dans le fichier `.env`
   - Assurez-vous que les modèles spécifiés sont bien déployés dans votre ressource Azure

3. **Problèmes avec l'interface utilisateur:**
   - Effacez le cache du navigateur
   - Essayez de réinitialiser la session via le bouton "Réinitialiser" 