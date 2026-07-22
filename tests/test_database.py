"""
Unit Tests for Database Connection Layer.
Verifies loading config, engine creation, caching, and mock connection testing.
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from src.database.connection import create_engine, get_engine, test_connection as db_test_connection

def test_database_engine_creation():
    """Verifies that create_engine builds a valid SQLAlchemy Engine."""
    with patch("src.database.connection.sqlalchemy_create_engine") as mock_create:
        mock_engine = MagicMock(spec=Engine)
        mock_create.return_value = mock_engine
        
        engine = create_engine()
        assert engine == mock_engine
        mock_create.assert_called_once()

def test_database_engine_caching():
    """Verifies that get_engine returns the cached Engine instance."""
    with patch("src.database.connection.sqlalchemy_create_engine") as mock_create:
        mock_engine = MagicMock(spec=Engine)
        mock_create.return_value = mock_engine
        
        # Reset cache for testing
        import src.database.connection as conn_mod
        conn_mod._engine = None
        
        engine1 = get_engine()
        engine2 = get_engine()
        
        assert engine1 == mock_engine
        assert engine2 == mock_engine
        mock_create.assert_called_once()

def test_test_connection_success():
    """Verifies test_connection returns True when database is reachable."""
    with patch("src.database.connection.get_engine") as mock_get:
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_get.return_value = mock_engine
        
        result = db_test_connection()
        assert result is True
        mock_engine.connect.assert_called_once()

def test_test_connection_failure():
    """Verifies test_connection returns False when database is unreachable."""
    with patch("src.database.connection.get_engine") as mock_get:
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = SQLAlchemyError("Connection refused")
        mock_get.return_value = mock_engine
        
        result = db_test_connection()
        assert result is False
