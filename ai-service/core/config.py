"""
Configuration module for BoardRoom AI RAG & Question Generation Service.
Reads environment variables with sensible hackathon defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root or current working dir if available
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY") or ""

    # Model Configuration
    # Gemini 2.5 Flash is ideal for rapid structured outputs during hackathons
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gemini-2.5-flash")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "10"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "2"))

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    KNOWLEDGE_BASE_PATH: Path = BASE_DIR / "data" / "knowledge_base" / "seed_knowledge.json"

    # Service Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

settings = Settings()
