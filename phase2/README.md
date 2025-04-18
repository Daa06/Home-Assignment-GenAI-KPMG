# Chatbot Phase 2: Medical Services Information System

## Project Description

This project is an advanced medical chatbot system designed to provide information about medical services offered by various Israeli health insurance providers (Maccabi, Meuhedet, and Clalit). The system uses artificial intelligence to understand user questions and provide accurate, personalized information about available services based on the user's specific profile.

## Key Features

- **Intuitive conversational interface**: Simple and user-friendly Streamlit interface
- **Bilingual system**: Support for Hebrew and English
- **Response personalization**: Adaptation of responses based on the user's health insurance provider and coverage level
- **Contextual search**: Vector search to find the most relevant information
- **Stateless architecture**: Robust and scalable design
- **Knowledge base processing**: Efficient indexing and storage of medical information
- **Two-phase dialogue**: User information collection followed by personalized Q&A
- **Data privacy**: All user data stored client-side only

## Technical Architecture

The application is designed using a microservices architecture comprising:

1. **Backend API (FastAPI)**:
   - Processing requests from the user interface
   - Communication with the language model
   - Searching for information in the knowledge base

2. **User Interface (Streamlit)**:
   - Conversational interface
   - Session state management
   - User information collection
   - Response display

3. **Artificial Intelligence Components**:
   - Azure OpenAI (GPT-4o) for understanding and generating responses
   - Embeddings (ADA 002) for vector search
   - Response personalization logic

4. **Knowledge Base**:
   - HTML document indexing
   - Semantic search via FAISS
   - Efficient metadata storage

## Prerequisites

- Python 3.8 or higher
- Bash (to run the installation script)
- Internet access to download dependencies
- API keys for Azure OpenAI

## Configuration

### Environment Variables

Create a `.env` file at the root of the `phase2` directory with the following information:

```
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_VERSION=2023-05-15

# Azure Deployment Names
GPT4O_DEPLOYMENT_NAME=gpt-4o
GPT4O_MINI_DEPLOYMENT_NAME=gpt-4o-mini
EMBEDDING_DEPLOYMENT_NAME=text-embedding-ada-002

# Server Configuration (optional)
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False
UI_HOST=0.0.0.0
UI_PORT=8501

# Log Level
LOG_LEVEL=INFO
```

## Installation and Execution

### Simple Method (Recommended)

Use the `chatbot_phase2.sh` script which automates the entire installation and startup process:

```bash
# Make the script executable
chmod +x chatbot_phase2.sh

# Run the script
./chatbot_phase2.sh
```

The script automatically performs the following actions:
1. Checking Python and pip installation
2. Installing all required dependencies
3. Generating the knowledge index
4. Starting the API and user interface

#### Script Options

- Virtual environment mode: `./chatbot_phase2.sh -v` or `./chatbot_phase2.sh --venv`

### Manual Installation

If you prefer a manual installation:

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Generate the knowledge index:
```bash
python rebuild_index_complete.py
```

3. Start the application:
```bash
python fix_app_final.py
```

## Project Structure

```
phase2/
├── app/                       # Main code directory
│   ├── api/                   # FastAPI API
│   │   ├── __init__.py
│   │   ├── endpoints.py       # API endpoints
│   │   └── main.py            # Main FastAPI application
│   ├── core/                  # Central configuration
│   │   ├── __init__.py
│   │   └── config.py          # Configuration management
│   ├── knowledge/             # Knowledge base management
│   │   ├── __init__.py
│   │   ├── processor.py       # HTML file processing
│   │   ├── embedding.py       # Embedding creation
│   │   └── knowledge_faiss.index # Vector index (generated)
│   ├── llm/                   # Language model integration
│   │   ├── __init__.py
│   │   ├── client.py          # OpenAI client
│   │   ├── simple_client.py   # Simplified OpenAI client
│   │   ├── collection.py      # Prompt collection
│   │   └── qa.py              # Q&A logic
│   ├── logging/               # Log configuration
│   │   ├── __init__.py
│   │   └── logger.py          # Logger configuration
│   ├── ui/                    # User interface
│   │   ├── __init__.py
│   │   └── streamlit_app.py   # Streamlit application
│   └── __init__.py            # Package initialization
├── logs/                      # Log files (generated)
│   ├── api/                   # API logs
│   └── ui/                    # UI logs
├── phase2_data/               # Source data for knowledge base
├── .env                       # Environment variables (to be created)
├── .gitignore                 # Files to ignore for git
├── chatbot_phase2.sh          # Installation and startup script
├── fix_app_final.py           # Application correction script
├── rebuild_index_complete.py  # Index generation script
├── requirements.txt           # Python dependencies
├── run_api.py                 # API startup script
└── run_ui.py                  # UI startup script
```

## Detailed Operation

### 1. Initialization and Configuration

The system begins by loading environment variables and configuring necessary components, including:
- Logger configuration
- Directory structure verification
- API client initialization

### 2. Knowledge Index Generation

The knowledge base is processed by:
1. Reading HTML files in the `phase2_data` directory
2. Extracting relevant content
3. Breaking down into informative fragments
4. Generating vector embeddings for each fragment
5. Creating a FAISS index for efficient searching
6. Storing associated metadata

### 3. User Interface

The Streamlit interface manages:
- User information collection
- Field validation
- Conversation state management
- Sending requests to the API
- Displaying formatted responses

### 4. Question Processing

When a user asks a question:
1. The question is sent to the API
2. The system searches for relevant fragments in the knowledge base
3. Fragments are extracted with their metadata
4. The GPT-4o model receives the context and question
5. A personalized response is generated taking into account the user's profile
6. The response is returned to the user interface

## Response Personalization

The system adapts its responses based on:
- The user's health insurance provider (Maccabi, Meuhedet, Clalit)
- Insurance coverage level (standard, silver, gold, platinum)
- Type of medical service being searched for
- Language used to ask the question

## Development and Extension

### Adding New Data Sources

To add new sources to the knowledge base:
1. Add HTML files to the `phase2_data` directory
2. Run `python rebuild_index_complete.py` to rebuild the index

### Modifying Prompts

System prompts are defined in `app/llm/collection.py` and can be customized as needed.

### Adding Features

The code is modular and allows easy addition of:
- New API endpoints in `app/api/endpoints.py`
- UI features in `app/ui/streamlit_app.py`
- Processing capabilities in `app/knowledge/processor.py`

## Troubleshooting

### Common Issues

1. **Azure OpenAI connection error**:
   - Check API keys and endpoints in `.env`
   - Ensure models are correctly deployed

2. **API won't start**:
   - Check logs in `logs/api/`
   - Make sure no other service is using port 8000

3. **Interface not connecting to API**:
   - Verify that the API is running
   - Check connection parameters in `.env`

4. **Errors during index generation**:
   - Check Azure OpenAI access
   - Verify that data files are in the correct format

### Logs

System logs are stored in:
- API logs: `logs/api/`
- UI logs: `logs/ui/`

## Performance and Optimizations

- FAISS index is optimized for fast searches even with large knowledge bases
- Client-side caching reduces server requests
- Asynchronous communication between API and interface improves responsiveness

## Security

- No personal information is stored on the server
- All communications with Azure use secure connections
- User information is kept only in the browser session

## Future Improvements

Several aspects of the system could be enhanced in the future:

- **User Interface**: More modern and responsive design with accessibility features
- **Multilingual Support**: Extension to other languages common in Israel
- **Integration**: Public API for integration with other healthcare systems
- **Knowledge Base**: Live connectors to health insurance databases and automated updates
- **Analytics**: Administrative dashboard for frequently asked questions and usage patterns
- **Performance**: Optimizations for handling large numbers of simultaneous users

## Authors and License

© 2025 - Project developed for KPMG as part of a technical evaluation. 