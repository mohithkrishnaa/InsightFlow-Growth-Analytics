# Geography Generator Module for the InsightFlow Data Generation Pipeline
"""
This module contains the logic for generating geographic attributes (state, city,
and city tier) for synthetic users. It implements weighted state selection,
weighted city selection within each state, and RBI tier classification lookup.
All relationships are configuration-driven, with comprehensive validations.
"""

import logging
import numpy as np
from typing import Dict, Any, List
from src.data_generation.config import AppConfig, load_config

# Setup local logger
logger = logging.getLogger("InsightFlowGenerator")

# Cache default configuration to prevent repeated file reading
_default_config = None


def _get_default_config() -> AppConfig:
    """
    Loads and caches the default configuration.

    Returns:
        AppConfig: The default application configuration.
    """
    global _default_config
    if _default_config is None:
        try:
            logger.info("Loading default configuration for geography generator.")
            _default_config = load_config()
        except Exception as e:
            logger.exception("Failed to load default configuration in geography generator", extra={"error": str(e)})
            raise e
    return _default_config


def generate_state(config: AppConfig, rng: np.random.Generator) -> str:
    """
    Selects a state based on configured probability weights in STATE_DISTRIBUTION.

    Args:
        config (AppConfig): The application configuration model.
        rng (np.random.Generator): The random number generator.

    Returns:
        str: Selected state name.

    Raises:
        ValueError: If STATE_DISTRIBUTION is empty or weights sum to zero.
    """
    logger.info("Generating state name based on configured weights")

    if not config.STATE_DISTRIBUTION:
        error_msg = "STATE_DISTRIBUTION is empty or missing in config."
        logger.error(error_msg)
        raise ValueError(error_msg)

    states = list(config.STATE_DISTRIBUTION.keys())
    weights = list(config.STATE_DISTRIBUTION.values())

    total_weight = sum(weights)
    if total_weight <= 0:
        error_msg = "Sum of state distribution weights must be greater than zero."
        logger.error(error_msg, extra={"total_weight": total_weight})
        raise ValueError(error_msg)

    # Normalize weights
    normalized_weights = [w / total_weight for w in weights]
    state = rng.choice(states, p=normalized_weights)

    logger.info("State generated successfully", extra={"state": state})
    return str(state)


def generate_city(state: str, config: AppConfig, rng: np.random.Generator) -> str:
    """
    Selects a city belonging to the specified state, based on the weights in config.CITY_WEIGHTS.

    Args:
        state (str): The state name.
        config (AppConfig): The application configuration model.
        rng (np.random.Generator): The random number generator.

    Returns:
        str: Selected city name.

    Raises:
        ValueError: If state is invalid, has no mapped cities, or city weights are invalid.
    """
    logger.info("Generating city", extra={"state": state})

    if state not in config.CITY_MAPPING:
        error_msg = f"State '{state}' is not defined in CITY_MAPPING."
        logger.error(error_msg, extra={"state": state})
        raise ValueError(error_msg)

    cities = config.CITY_MAPPING[state]
    if not cities:
        error_msg = f"No cities mapped to state '{state}' in CITY_MAPPING."
        logger.error(error_msg, extra={"state": state})
        raise ValueError(error_msg)

    # Fetch weights for the cities in this state
    weights = []
    for city in cities:
        if city not in config.CITY_WEIGHTS:
            error_msg = f"City '{city}' is missing weight in CITY_WEIGHTS."
            logger.error(error_msg, extra={"state": state, "city": city})
            raise ValueError(error_msg)
        weights.append(config.CITY_WEIGHTS[city])

    total_weight = sum(weights)
    if total_weight <= 0:
        error_msg = f"Sum of city weights for state '{state}' must be greater than zero."
        logger.error(error_msg, extra={"state": state, "weights": weights})
        raise ValueError(error_msg)

    # Normalize weights
    normalized_weights = [w / total_weight for w in weights]

    city = rng.choice(cities, p=normalized_weights)
    logger.info("City generated successfully", extra={"state": state, "city": city})
    return str(city)


def get_city_tier(city: str, config: AppConfig) -> str:
    """
    Retrieves the RBI city tier classification for a given city from CITY_TIER_MAPPING.

    Args:
        city (str): The city name to look up.
        config (AppConfig): The application configuration model.

    Returns:
        str: City tier (e.g. 'Tier 1', 'Tier 2', 'Tier 3').

    Raises:
        KeyError: If the city is not found in CITY_TIER_MAPPING.
    """
    logger.info("Looking up city tier classification", extra={"city": city})

    if city not in config.CITY_TIER_MAPPING:
        error_msg = f"City '{city}' not found in CITY_TIER_MAPPING."
        logger.error(error_msg, extra={"city": city})
        raise KeyError(error_msg)

    tier = config.CITY_TIER_MAPPING[city]
    logger.info("City tier retrieved successfully", extra={"city": city, "tier": tier})
    return tier


def validate_geography(state: str, city: str, tier: str, config: AppConfig) -> bool:
    """
    Validates that the combination of state, city, and tier is consistent with config.

    Args:
        state (str): The state name.
        city (str): The city name.
        tier (str): The city tier.
        config (AppConfig): The application configuration model.

    Returns:
        bool: True if the combination is valid.

    Raises:
        ValueError: If state, city, or tier is invalid or inconsistent.
    """
    logger.info("Validating geography combination", extra={"state": state, "city": city, "tier": tier})

    # 1. State check
    if state not in config.STATE_DISTRIBUTION:
        error_msg = f"State '{state}' is not valid under current configuration."
        logger.error(error_msg, extra={"state": state})
        raise ValueError(error_msg)

    # 2. City check
    if state not in config.CITY_MAPPING:
        error_msg = f"State '{state}' has no mapping in CITY_MAPPING."
        logger.error(error_msg, extra={"state": state})
        raise ValueError(error_msg)

    if city not in config.CITY_MAPPING[state]:
        error_msg = f"City '{city}' does not belong to state '{state}' in CITY_MAPPING."
        logger.error(error_msg, extra={"state": state, "city": city})
        raise ValueError(error_msg)

    # 3. Tier check
    if city not in config.CITY_TIER_MAPPING:
        error_msg = f"City '{city}' has no tier configured in CITY_TIER_MAPPING."
        logger.error(error_msg, extra={"city": city})
        raise ValueError(error_msg)

    expected_tier = config.CITY_TIER_MAPPING[city]
    if tier != expected_tier:
        error_msg = f"Tier '{tier}' for city '{city}' does not match expected tier '{expected_tier}'."
        logger.error(error_msg, extra={"city": city, "expected_tier": expected_tier, "actual_tier": tier})
        raise ValueError(error_msg)

    logger.info("Geography validation passed successfully", extra={"state": state, "city": city, "tier": tier})
    return True


def generate_geography(rng: np.random.Generator, config: AppConfig = None) -> Dict[str, Any]:
    """
    Selects a state, city, and corresponding RBI city tier based on configured weights.
    Ensures exact geographical integrity and alignment using modular sub-functions.

    Args:
        rng (np.random.Generator): Independent random number generator.
        config (AppConfig, optional): AppConfig instance. If None, default is loaded.

    Returns:
        Dict[str, Any]: Dictionary containing 'state', 'city', and 'city_tier'.
    """
    if config is None:
        config = _get_default_config()

    state = generate_state(config, rng)
    city = generate_city(state, config, rng)
    tier = get_city_tier(city, config)

    # Validate generated output integrity
    validate_geography(state, city, tier, config)

    return {
        "state": state,
        "city": city,
        "city_tier": tier
    }
