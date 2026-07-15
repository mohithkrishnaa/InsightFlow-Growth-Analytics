# Demographics Generator Module for the InsightFlow Data Generation Pipeline
"""
This module contains the logic for generating demographic attributes (age, gender,
and education level) for synthetic users. It implements age-based education correlations,
weighted probability selections from AppConfig, and schema validations.
"""

import logging
import numpy as np
from typing import Dict, Any
from src.data_generation.config import AppConfig

# Setup local logger
logger = logging.getLogger("InsightFlowGenerator")


def validate_age(age: int) -> bool:
    """
    Validates that age falls within the eligible lending boundaries.

    Args:
        age (int): Generated age of the user.

    Returns:
        bool: True if age is valid, otherwise False.
    """
    return 18 <= age <= 65


def validate_gender(gender: str, config: AppConfig) -> bool:
    """
    Validates that gender is one of the permitted configured categories.

    Args:
        gender (str): Generated gender value.
        config (AppConfig): The application configuration model.

    Returns:
        bool: True if gender is valid, otherwise False.
    """
    return gender in config.GENDER_DISTRIBUTION


def validate_education(education_level: str, age: int, config: AppConfig) -> bool:
    """
    Validates that the education level is valid and consistent with the user's age.

    Args:
        education_level (str): Generated education level.
        age (int): Generated age of the user.
        config (AppConfig): The application configuration model.

    Returns:
        bool: True if education is valid and consistent, otherwise False.
    """
    if education_level not in config.EDUCATION_MAPPING:
        return False

    # Age-based rules:
    # - Postgraduate and Doctorate degrees require at least 22 years of age.
    # - Doctorate degrees require at least 21 years of age.
    if education_level in ["Postgraduate", "Doctorate"] and age < 22:
        return False
    if education_level == "Doctorate" and age < 21:
        return False

    return True


def generate_age(config: AppConfig, rng: np.random.Generator) -> int:
    """
    Generates a user's age following realistic Indian lending demographics.
    Uses configured age bands and weights, drawing uniformly within the selected band.

    Args:
        config (AppConfig): Shared application configuration.
        rng (np.random.Generator): Independent random number generator.

    Returns:
        int: Validated user age in years.
    """
    age_bands = list(config.AGE_DISTRIBUTION.keys())
    age_weights = list(config.AGE_DISTRIBUTION.values())

    # Draw an age band based on configured weights
    selected_band = rng.choice(age_bands, p=age_weights)

    try:
        # Split age band (e.g. "18-24" -> 18, 24)
        low_str, high_str = selected_band.split("-")
        low, high = int(low_str), int(high_str)
    except ValueError as e:
        logger.error(f"Invalid age band format in config: '{selected_band}'")
        raise e

    # Sample uniformly within the chosen age band
    age = int(rng.integers(low, high, endpoint=True))

    if not validate_age(age):
        error_msg = f"Generated age {age} lies outside eligible range [18, 65]."
        logger.error(error_msg)
        raise ValueError(error_msg)

    return age


def generate_gender(config: AppConfig, rng: np.random.Generator) -> str:
    """
    Generates a user's gender based on weighted configured probabilities.

    Args:
        config (AppConfig): Shared application configuration.
        rng (np.random.Generator): Independent random number generator.

    Returns:
        str: Validated user gender.
    """
    genders = list(config.GENDER_DISTRIBUTION.keys())
    gender_weights = list(config.GENDER_DISTRIBUTION.values())

    gender = str(rng.choice(genders, p=gender_weights))

    if not validate_gender(gender, config):
        error_msg = f"Generated gender '{gender}' is not valid under configuration rules."
        logger.error(error_msg)
        raise ValueError(error_msg)

    return gender


def generate_education(age: int, config: AppConfig, rng: np.random.Generator) -> str:
    """
    Generates an education level correlated with the user's age.
    Applies age-based exclusions and shifts baseline weights dynamically.

    Args:
        age (int): Pre-generated age of the user to correlate against.
        config (AppConfig): Shared application configuration.
        rng (np.random.Generator): Independent random number generator.

    Returns:
        str: Validated education level.
    """
    # Create a copy of the mapping weights
    edu_weights = dict(config.EDUCATION_MAPPING)

    # 1. Apply absolute boundaries based on age:
    # Cannot have a Doctorate or Postgraduate degree if under 22
    if age < 22:
        edu_weights["Postgraduate"] = 0.0
        edu_weights["Doctorate"] = 0.0
    # Cannot have a Doctorate degree if under 21
    elif age < 21:
        edu_weights["Doctorate"] = 0.0

    # 2. Apply age-based correlation skews:
    # Younger users (under 25) are skewed toward High School and Undergraduate levels
    if age < 25:
        edu_weights["High School"] = edu_weights.get("High School", 0.15) * 1.8
        edu_weights["Undergraduate"] = edu_weights.get("Undergraduate", 0.50) * 1.3
        # Reduce higher degree likelihood
        for key in ["Graduate", "Postgraduate", "Doctorate"]:
            if key in edu_weights:
                edu_weights[key] *= 0.5
    # Older users (35+) are skewed toward Graduate and Post-Graduate degrees
    elif age >= 35:
        edu_weights["High School"] = edu_weights.get("High School", 0.15) * 0.4
        for key in ["Graduate", "Postgraduate", "Doctorate"]:
            if key in edu_weights:
                edu_weights[key] *= 1.3

    # Normalize weights to sum to 1.0
    total_weight = sum(edu_weights.values())
    if total_weight <= 0:
        # Fallback to High School in case of empty distributions
        edu_choices = ["High School"]
        normalized_probs = [1.0]
    else:
        edu_choices = list(edu_weights.keys())
        normalized_probs = [w / total_weight for w in edu_weights.values()]

    education_level = str(rng.choice(edu_choices, p=normalized_probs))

    if not validate_education(education_level, age, config):
        error_msg = f"Generated education '{education_level}' is inconsistent with age {age}."
        logger.error(error_msg)
        raise ValueError(error_msg)

    return education_level


def generate_demographics(config: AppConfig, rng: np.random.Generator) -> Dict[str, Any]:
    """
    Orchestrates the generation of age, gender, and education level for a synthetic user.

    Args:
        config (AppConfig): Shared application configuration.
        rng (np.random.Generator): Independent random number generator.

    Returns:
        Dict[str, Any]: Generated demographics with keys 'age', 'gender', and 'education_level'.
    """
    logger.info("Generating user demographics")
    age = generate_age(config, rng)
    gender = generate_gender(config, rng)
    education_level = generate_education(age, config, rng)
    return {
        "age": age,
        "gender": gender,
        "education_level": education_level
    }
