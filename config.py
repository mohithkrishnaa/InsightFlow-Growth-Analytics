"""
Configuration Module for the InsightFlow Streamlit Application.
Loads settings from environment variables via python-dotenv.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup configuration-specific logging
logger = logging.getLogger("InsightFlowConfig")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Determine project root and dotenv path using pathlib.Path
BASE_DIR = Path(__file__).resolve().parent
DOTENV_PATH = BASE_DIR / ".env"

# Streamlit App Configurations
APP_TITLE = "InsightFlow - FinTech Analytics Dashboard"
APP_ICON = "📈"
LAYOUT = "wide"

# Database Connection Settings (will be dynamically loaded and updated)
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "insightflow"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

# Connection Pooling Settings
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 10
DB_POOL_TIMEOUT = 30
DB_POOL_RECYCLE = 1800

# Assets & Paths using pathlib.Path
CSS_FILE_PATH = BASE_DIR / "assets" / "styles.css"
LOGO_FILE_PATH = BASE_DIR / "assets" / "logo.png"

def reload_config() -> None:
    """
    Explicitly reloads environment variables from the .env file
    and updates the module's database configuration attributes.
    """
    global DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    global DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT, DB_POOL_RECYCLE

    env_path = DOTENV_PATH
    if env_path.exists():
        logger.info(f"Loading environment variables from: {env_path}")
        load_dotenv(env_path, override=True)
    else:
        logger.warning(f"No .env file found at: {env_path}. Falling back to default settings.")

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_NAME", "insightflow")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 5))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 10))
    DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", 30))
    DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", 1800))

    # Mask password for secure logging
    masked_pw = DB_PASSWORD[:2] + "****" if DB_PASSWORD else "None"
    logger.info("Configuration loaded:")
    logger.info(f"  DB_HOST = {DB_HOST}")
    logger.info(f"  DB_PORT = {DB_PORT}")
    logger.info(f"  DB_NAME = {DB_NAME}")
    logger.info(f"  DB_USER = {DB_USER}")
    logger.info(f"  DB_PASSWORD = {masked_pw}")

# Perform initial load when module is imported
reload_config()
