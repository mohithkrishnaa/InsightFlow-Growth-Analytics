"""
PostgreSQL Connection Manager for the InsightFlow Application.
Manages SQLAlchemy engine creation, connection pooling, and health checks.
"""

import logging
from typing import Optional
from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text
import config

# Setup logging
logger = logging.getLogger("InsightFlowDashboard")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Global engine cache and its signature
_engine: Optional[Engine] = None
_engine_signature: Optional[str] = None

def create_engine() -> Engine:
    """
    Constructs a new SQLAlchemy Engine instance with connection pooling.
    
    Returns:
        Engine: SQLAlchemy Engine instance.
    """
    # Force config to reload to ensure we have latest parameters
    config.reload_config()

    # Build RFC 3986 / PEP 249 compliant URL
    db_url = f"postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    
    # Mask password for secure logging (Requirement 5)
    masked_url = f"postgresql://{config.DB_USER}:****@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    logger.info(f"Initializing PostgreSQL connection pool to {masked_url}")
    
    try:
        engine = sqlalchemy_create_engine(
            db_url,
            pool_size=config.DB_POOL_SIZE,
            max_overflow=config.DB_MAX_OVERFLOW,
            pool_timeout=config.DB_POOL_TIMEOUT,
            pool_recycle=config.DB_POOL_RECYCLE
        )
        return engine
    except Exception as e:
        logger.error(f"Failed to create SQLAlchemy engine: {e}")
        raise e

import streamlit as st

@st.cache_resource
def get_cached_engine(db_url: str, pool_size: int, max_overflow: int, pool_timeout: int, pool_recycle: int) -> Engine:
    """
    Creates and caches the SQLAlchemy Engine instance using Streamlit's cache_resource.
    """
    logger.info("Initializing cached database engine via st.cache_resource.")
    return sqlalchemy_create_engine(
        db_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle
    )

def get_engine() -> Engine:
    """
    Retrieves the global cached SQLAlchemy Engine instance.
    Utilizes st.cache_resource to reuse connection pools across reruns.
    
    Returns:
        Engine: Cached SQLAlchemy Engine instance.
    """
    # Force configuration reload to detect changes in .env
    config.reload_config()
    
    # Build RFC 3986 / PEP 249 compliant URL
    db_url = f"postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    
    return get_cached_engine(
        db_url,
        pool_size=config.DB_POOL_SIZE,
        max_overflow=config.DB_MAX_OVERFLOW,
        pool_timeout=config.DB_POOL_TIMEOUT,
        pool_recycle=config.DB_POOL_RECYCLE
    )

def test_connection() -> bool:
    """
    Tests connection to the PostgreSQL database by running a dummy select query.
    If the connection fails, clears the cached engine.
    
    Returns:
        bool: True if connection is successful, False otherwise.
    """
    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection test succeeded.")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection test failed: {e}")
        # Clear engine cache on failure so we retry/rebuild with fresh credentials/engine next time
        get_cached_engine.clear()
        return False
