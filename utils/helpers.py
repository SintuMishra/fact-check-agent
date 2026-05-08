import os
import openai
import logging
from typing import Optional, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

import os
import openai
import logging
import streamlit as st
from typing import Optional, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def get_openai_client() -> Optional[openai.OpenAI]:
    """Get OpenAI client with API key from Streamlit secrets or environment."""
    # Try Streamlit secrets first
    try:
        api_key = st.secrets.get('OPENAI_API_KEY')
        if api_key:
            return openai.OpenAI(api_key=api_key)
    except:
        pass

    # Fall back to environment variables
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OpenAI API key not found in Streamlit secrets or environment variables")
        return None

    return openai.OpenAI(api_key=api_key)

def get_serper_api_key() -> Optional[str]:
    """Get Serper API key from Streamlit secrets or environment."""
    # Try Streamlit secrets first
    try:
        api_key = st.secrets.get('SERPER_API_KEY')
        if api_key:
            return api_key
    except:
        pass

    # Fall back to environment variables
    api_key = os.getenv('SERPER_API_KEY')
    if not api_key:
        logger.error("Serper API key not found in Streamlit secrets or environment variables")
        return None

    return api_key

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('fact_check_agent.log')
        ]
    )

def validate_environment() -> Dict[str, bool]:
    """Validate that all required environment variables are set."""
    required_vars = ['OPENAI_API_KEY', 'SERPER_API_KEY']
    validation = {}

    for var in required_vars:
        validation[var] = bool(os.getenv(var))

    all_valid = all(validation.values())
    if not all_valid:
        missing = [k for k, v in validation.items() if not v]
        logger.error(f"Missing required environment variables: {missing}")

    return validation

def format_confidence_score(confidence: float) -> str:
    """Format confidence score as percentage string."""
    if not isinstance(confidence, (int, float)):
        return "N/A"
    if confidence <= 1:
        confidence = confidence * 100
    return f"{int(confidence)}%"

def get_status_color(status: str) -> str:
    """Get color for status badge."""
    status = status.upper()
    colors = {
        'VERIFIED': '#28a745',  # Green
        'INACCURATE': '#ffc107',  # Yellow
        'FALSE': '#dc3545',  # Red
        'ERROR': '#6c757d',  # Gray
        'UNKNOWN': '#6c757d'  # Gray
    }
    return colors.get(status, '#6c757d')

def safe_api_call(func, *args, **kwargs):
    """Wrapper for API calls with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return None