import os
import sys
import json
from datetime import datetime
from loguru import logger
from ..core.config import settings

# Log level configuration
LOG_LEVEL = settings.LOG_LEVEL

# Logs directory
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
api_log_dir = os.path.join(log_dir, "api")
ui_log_dir = os.path.join(log_dir, "ui")

# Create directories if they don't exist
os.makedirs(log_dir, exist_ok=True)
os.makedirs(api_log_dir, exist_ok=True)
os.makedirs(ui_log_dir, exist_ok=True)

# Log files with timestamp to avoid overwriting
api_log_file = os.path.join(api_log_dir, f"api_{timestamp}.log")
ui_log_file = os.path.join(ui_log_dir, f"ui_{timestamp}.log")
debug_log_file = os.path.join(log_dir, f"debug_{timestamp}.log")

# Custom format for logs
log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"

# Configure loguru
logger.remove()  # Remove default configuration

# Add console output with INFO level
logger.add(sys.stderr, level="INFO", format=log_format)

# Add API log file
logger.add(
    api_log_file,
    rotation="100 MB",
    retention="30 days",
    compression="zip",
    level=LOG_LEVEL,
    format=log_format,
    filter=lambda record: "api" in record["name"].lower(),
    encoding="utf8"
)

# Add UI log file
logger.add(
    ui_log_file,
    rotation="100 MB",
    retention="30 days",
    compression="zip",
    level=LOG_LEVEL,
    format=log_format,
    filter=lambda record: "ui" in record["name"].lower() or "streamlit" in record["name"].lower(),
    encoding="utf8"
)

# Add debug log file for ALL messages
logger.add(
    debug_log_file,
    rotation="100 MB",
    retention="15 days",
    compression="zip",
    level="DEBUG",
    format=log_format,
    encoding="utf8"
)

# Function to log API requests
def log_api_request(endpoint: str, request_data: dict, user_id: str = "unknown"):
    """
    Records API request data.
    
    Args:
        endpoint: The API endpoint called
        request_data: The data of the request (without sensitive information)
        user_id: A user identifier or session identifier (anonymous)
    """
    try:
        # Create a copy of the data to not modify the original
        safe_data = request_data.copy() if request_data else {}
        
        # Mask or remove sensitive information
        if isinstance(safe_data, dict):
            # If conversation_history is present, log only the number of messages
            if 'conversation_history' in safe_data and isinstance(safe_data['conversation_history'], dict):
                messages = safe_data['conversation_history'].get('messages', [])
                safe_data['conversation_history'] = f"[{len(messages)} messages]"
            
            # Mask sensitive user information
            for profile_key in ['user_profile', 'partial_profile']:
                if profile_key in safe_data and isinstance(safe_data[profile_key], dict):
                    profile = safe_data[profile_key]
                    
                    # Mask sensitive identifiers
                    for sensitive_field in ['id_number', 'hmo_card_number']:
                        if sensitive_field in profile:
                            value = profile[sensitive_field]
                            if value and len(str(value)) > 4:
                                profile[sensitive_field] = f"***{str(value)[-4:]}"
        
        # Record safe request data
        log_entry = {
            "type": "api_request",
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "user_id": user_id,
            "data": safe_data
        }
        
        logger.info(f"API Request | Endpoint: {endpoint} | User: {user_id}")
        logger.debug(f"API Request Details: {json.dumps(log_entry, ensure_ascii=False)}")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de la requête API: {str(e)}")

# Function to log API responses
def log_api_response(endpoint: str, status_code: int, response_data: dict, 
                    processing_time: float, user_id: str = "unknown"):
    """
    Records API response data.
    
    Args:
        endpoint: The API endpoint called
        status_code: The HTTP status code
        response_data: The data of the response (without sensitive information)
        processing_time: The processing time in milliseconds
        user_id: A user identifier or session identifier (anonymous)
    """
    try:
        # Mask or simplify sensitive response data
        safe_data = {}
        
        if response_data:
            # Copy metadata and status if present
            if 'metadata' in response_data:
                safe_data['metadata'] = response_data['metadata']
            
            # Do not include full response content
            if 'response' in response_data:
                content = response_data['response']
                safe_data['response_length'] = len(content) if isinstance(content, str) else "non-string"
            
            # If conversation history is present, log only the number of messages
            if 'updated_conversation_history' in response_data:
                history = response_data['updated_conversation_history']
                if isinstance(history, dict) and 'messages' in history:
                    safe_data['conversation_messages_count'] = len(history['messages'])
        
        # Response metadata
        log_entry = {
            "type": "api_response",
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "user_id": user_id,
            "status_code": status_code,
            "processing_time_ms": processing_time,
            "data": safe_data
        }
        
        logger.info(f"API Response | Endpoint: {endpoint} | User: {user_id} | Status: {status_code} | Time: {processing_time:.2f}ms")
        logger.debug(f"API Response Details: {json.dumps(log_entry, ensure_ascii=False)}")
        
        # Record separate errors
        if status_code >= 400:
            logger.error(f"API Error | Endpoint: {endpoint} | Status: {status_code} | User: {user_id}")
            logger.error(f"Error Details: {json.dumps(safe_data, ensure_ascii=False)}")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de la réponse API: {str(e)}")

# Export functions and objects
__all__ = ["logger", "log_api_request", "log_api_response"]
