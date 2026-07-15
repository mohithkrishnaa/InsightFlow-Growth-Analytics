# Customer Profile Generator Module for the InsightFlow Data Generation Pipeline
"""
This module generates consolidated user profile attributes (occupation, monthly income,
CIBIL score, acquisition channel, and device) based on demographic features and
configured business logic. All relationships and distribution parameters are
configuration-driven.
"""

import logging
import numpy as np
from typing import Dict, Any, Tuple, List
from src.data_generation.config import AppConfig

# Setup local logger
logger = logging.getLogger("InsightFlowGenerator")


def calculate_occupation_weights(
    age: int, 
    education_level: str, 
    config: AppConfig
) -> List[float]:
    """
    Computes occupation probabilities dynamically based on age and education level.

    Args:
        age (int): The generated age of the user.
        education_level (str): The generated education level of the user.
        config (AppConfig): Shared application configuration.

    Returns:
        List[float]: Normalized occupation selection probabilities.
    """
    logger.info("Calculating occupation probability weights", extra={"age": age, "education_level": education_level})
    
    occ_weights = dict(config.OCCUPATION_DISTRIBUTION)

    # 1. Age-based rules:
    # Under 22 cannot be retired
    if age < 22:
        occ_weights["Retired"] = 0.0
    # Scale down student likelihood for older users (25+)
    if age >= 25:
        occ_weights["Student"] = occ_weights.get("Student", 0.05) * 0.1

    # 2. Education-based rules:
    # High School graduates cannot be professionals
    if education_level == "High School":
        occ_weights["Professional"] = 0.0
    # Postgraduates and Doctorates cannot be students; boost salaried and professional
    if education_level in ["Postgraduate", "Doctorate"]:
        occ_weights["Student"] = 0.0
        occ_weights["Salaried"] = occ_weights.get("Salaried", 0.60) * 1.2
        occ_weights["Professional"] = occ_weights.get("Professional", 0.10) * 1.5

    # Normalize weights
    total_weight = sum(occ_weights.values())
    if total_weight > 0:
        normalized = [w / total_weight for w in occ_weights.values()]
        logger.info("Occupation weights calculated successfully", extra={"weights": dict(zip(occ_weights.keys(), normalized))})
        return normalized
    else:
        logger.warning("Empty occupation weights, falling back to base configuration distribution.")
        return list(config.OCCUPATION_DISTRIBUTION.values())


def generate_occupation_and_income(
    age: int, 
    education_level: str, 
    config: AppConfig, 
    rng: np.random.Generator
) -> Tuple[str, int]:
    """
    Generates occupation and monthly income based on age, education, and log-normal parameters.

    Args:
        age (int): The generated age of the user.
        education_level (str): The generated education level.
        config (AppConfig): Shared application configuration.
        rng (np.random.Generator): Independent random number generator.

    Returns:
        Tuple[str, int]: A tuple containing (occupation, monthly_income).

    Raises:
        ValueError: If occupation configuration range is invalid or occupation is empty.
    """
    logger.info("Generating occupation and income profile", extra={"age": age, "education_level": education_level})

    # 1. Select Occupation
    occupations = list(config.OCCUPATION_DISTRIBUTION.keys())
    occ_weights = calculate_occupation_weights(age, education_level, config)
    occupation = rng.choice(occupations, p=occ_weights)

    # 2. Retrieve Lognormal Income Parameters
    if occupation not in config.INCOME_RANGES:
        error_msg = f"Occupation '{occupation}' is missing in INCOME_RANGES config."
        logger.error(error_msg)
        raise ValueError(error_msg)

    params = config.INCOME_RANGES[occupation]
    
    # Extract properties (handling both Pydantic model and dict formats)
    if hasattr(params, "median"):
        median = params.median
        sigma = params.sigma
        min_val = params.min
        max_val = params.max
    else:
        median = params["median"]
        sigma = params["sigma"]
        min_val = params["min"]
        max_val = params["max"]

    # Apply education-based income multiplier
    edu_scale = {
        "High School": 0.8,
        "Undergraduate": 1.0,
        "Graduate": 1.2,
        "Postgraduate": 1.5,
        "Doctorate": 1.8
    }
    scale_factor = edu_scale.get(education_level, 1.0)
    adjusted_median = median * scale_factor

    # Convert median to log-space mean (mu = ln(median))
    mu = np.log(adjusted_median)

    # Draw from log-normal distribution
    sampled_income = int(np.exp(rng.normal(mu, sigma)))

    # Clip to baseline min/max boundary constraints
    monthly_income = max(min_val, min(max_val, sampled_income))

    # Apply occupation-specific income caps/exceptions
    if occupation == "Student":
        # Students capped at 25k, with a 15% probability of exactly 0 income
        if rng.random() < 0.15:
            monthly_income = 0
        else:
            monthly_income = min(25000, monthly_income)
    elif occupation == "Retired":
        # Retired capped at 80k, with a 5% probability of exactly 0 income
        if rng.random() < 0.05:
            monthly_income = 0
        else:
            monthly_income = min(80000, monthly_income)
    else:
        # Guarantee non-zero income for employed occupations
        if monthly_income <= 0:
            monthly_income = min_val if min_val > 0 else 15000

    logger.info("Generated occupation and income", extra={"occupation": occupation, "monthly_income": monthly_income})
    return occupation, monthly_income


def generate_credit_profile(
    age: int, 
    occupation: str, 
    monthly_income: int, 
    config: AppConfig, 
    rng: np.random.Generator
) -> int:
    """
    Generates CIBIL credit score skewed by age, income, and occupation.

    Args:
        age (int): The user's age.
        occupation (str): The user's occupation.
        monthly_income (int): The user's monthly income.
        config (AppConfig): Shared application configuration.
        rng (np.random.Generator): Independent random number generator.

    Returns:
        int: The generated CIBIL score (-1 for New to Credit, or [300, 900]).
    """
    logger.info("Generating CIBIL credit score", extra={"age": age, "occupation": occupation, "monthly_income": monthly_income})

    # 1. New to Credit (NTC) check
    # Students or users under 22 have an 80% probability of being NTC (-1)
    if occupation == "Student" or age < 22:
        if rng.random() < 0.80:
            logger.info("User is flagged as New to Credit (NTC)", extra={"cibil_score": -1})
            return -1
    else:
        # Other profiles have a base 5% probability of being NTC
        if rng.random() < 0.05:
            logger.info("User is flagged as New to Credit (NTC)", extra={"cibil_score": -1})
            return -1

    # 2. Correlation skews for scored users
    cibil_dist = config.CIBIL_DISTRIBUTION
    scored_categories = ["Poor", "Fair", "Good", "Excellent"]
    scored_probs = [
        cibil_dist.get("Poor", 0.08),
        cibil_dist.get("Fair", 0.20),
        cibil_dist.get("Good", 0.40),
        cibil_dist.get("Excellent", 0.20)
    ]
    sum_probs = sum(scored_probs)
    if sum_probs <= 0:
        normalized_probs = [0.25, 0.25, 0.25, 0.25]
    else:
        normalized_probs = [p / sum_probs for p in scored_probs]

    # Calculate score normalization factors relative to reference values
    # Normalized age relative to range center (center = 41.5)
    age_norm = (age - 41.5) / 23.5

    # Normalized income capped at 150k relative to typical median of 45k
    income_cap = min(150000, monthly_income)
    income_norm = (income_cap - 45000) / 105000

    # Combine factors: Income (weight 0.5) + Age (weight 0.2) + Occupation boosts
    score_factor = 0.2 * age_norm + 0.5 * income_norm
    if occupation in ["Professional", "Salaried"]:
        score_factor += 0.15
    elif occupation == "Student":
        score_factor -= 0.30

    # Clip shift factor to [-0.7, 0.7] boundary limits
    score_factor = max(-0.7, min(0.7, score_factor))

    # Apply probability skews based on shift factor
    if score_factor > 0:
        # Positive shift: decrease Poor/Fair and increase Good/Excellent
        p_poor = normalized_probs[0] * (1 - 0.6 * score_factor)
        p_fair = normalized_probs[1] * (1 - 0.4 * score_factor)
        diff = (normalized_probs[0] - p_poor) + (normalized_probs[1] - p_fair)
        p_good = normalized_probs[2] + diff * 0.4
        p_excellent = normalized_probs[3] + diff * 0.6
    else:
        # Negative shift: decrease Excellent/Good and increase Poor/Fair
        abs_factor = abs(score_factor)
        p_excellent = normalized_probs[3] * (1 - 0.6 * abs_factor)
        p_good = normalized_probs[2] * (1 - 0.4 * abs_factor)
        diff = (normalized_probs[3] - p_excellent) + (normalized_probs[2] - p_good)
        p_fair = normalized_probs[1] + diff * 0.6
        p_poor = normalized_probs[0] + diff * 0.4

    adjusted_weights = [p_poor, p_fair, p_good, p_excellent]
    adj_sum = sum(adjusted_weights)
    final_probs = [w / adj_sum for w in adjusted_weights]

    selected_category = rng.choice(scored_categories, p=final_probs)

    # 3. Sample score inside selected category boundaries
    if selected_category == "Poor":
        score = int(rng.integers(300, 549, endpoint=True))
    elif selected_category == "Fair":
        score = int(rng.integers(550, 649, endpoint=True))
    elif selected_category == "Good":
        score = int(rng.integers(650, 749, endpoint=True))
    else:  # Excellent
        score = int(rng.integers(750, 900, endpoint=True))

    logger.info("Generated CIBIL credit score successfully", extra={"cibil_category": selected_category, "cibil_score": score})
    return score


def generate_device(
    monthly_income: int, 
    config: AppConfig, 
    rng: np.random.Generator
) -> str:
    """
    Selects device OS class based on configured device weights and income level correlations.

    Args:
        monthly_income (int): Monthly income of the user.
        config (AppConfig): Shared application configuration.
        rng (np.random.Generator): Independent random number generator.

    Returns:
        str: Selected device hardware/OS category.
    """
    logger.info("Generating device preference based on income", extra={"monthly_income": monthly_income})
    
    devices = list(config.DEVICE_DISTRIBUTION.keys())

    # Income correlation splits
    if monthly_income >= 150000:
        # High Income: skew toward iOS and macOS premium devices
        weights = [0.35, 0.45, 0.05, 0.15]  # Android, iOS, Windows, macOS
    elif monthly_income < 40000:
        # Low Income: skew heavily toward Android
        weights = [0.95, 0.04, 0.01, 0.00]
    else:
        # Standard mid-income profile
        weights = [0.85, 0.10, 0.04, 0.01]

    sum_w = sum(weights)
    final_weights = [w / sum_w for w in weights]
    device = rng.choice(devices, p=final_weights)

    logger.info("Generated device preference successfully", extra={"device": device})
    return str(device)


def generate_acquisition_channel(
    age: int, 
    monthly_income: int, 
    cibil_score: int, 
    config: AppConfig, 
    rng: np.random.Generator
) -> str:
    """
    Selects an acquisition marketing channel, skewed by age, income, and credit score.

    Args:
        age (int): Pre-generated age.
        monthly_income (int): Pre-generated monthly income.
        cibil_score (int): Pre-generated CIBIL score.
        config (AppConfig): Shared application configuration.
        rng (np.random.Generator): Independent random number generator.

    Returns:
        str: Selected acquisition channel name.
    """
    logger.info("Generating acquisition channel", extra={"age": age, "monthly_income": monthly_income, "cibil_score": cibil_score})

    channels = list(config.CHANNEL_DISTRIBUTION.keys())
    channel_weights = dict(config.CHANNEL_DISTRIBUTION)

    # 1. Income skews
    if monthly_income >= 100000:
        channel_weights["Google Ads"] *= 1.3
        channel_weights["Organic"] *= 1.2
        channel_weights["Affiliate"] *= 0.5
    elif monthly_income < 30000:
        channel_weights["Affiliate"] *= 1.3
        channel_weights["Meta Ads"] *= 1.2

    # 2. Age skews
    if age < 30:
        channel_weights["Meta Ads"] *= 1.3
        channel_weights["Organic"] *= 0.7

    # 3. Credit score skews
    if cibil_score != -1:
        if cibil_score < 600:  # Subprime
            channel_weights["Affiliate"] *= 1.5
            channel_weights["Organic"] *= 0.3
            channel_weights["Google Ads"] *= 0.8
        elif cibil_score >= 750:  # Excellent
            channel_weights["Organic"] *= 1.5
            channel_weights["Google Ads"] *= 1.2
            channel_weights["Affiliate"] *= 0.4

    # Normalize weights
    total_weight = sum(channel_weights.values())
    if total_weight > 0:
        final_weights = [w / total_weight for w in channel_weights.values()]
    else:
        final_weights = list(config.CHANNEL_DISTRIBUTION.values())

    channel = rng.choice(channels, p=final_weights)
    logger.info("Generated acquisition channel successfully", extra={"acquisition_channel": channel})
    return str(channel)


def generate_profile(
    age: int, 
    education: str, 
    config: AppConfig, 
    rng: np.random.Generator
) -> Dict[str, Any]:
    """
    Unified orchestration function that generates occupation, monthly income, CIBIL score,
    device, and acquisition channel for a synthetic customer.

    Args:
        age (int): Generated age of the user.
        education (str): Generated education level.
        config (AppConfig): Shared validated application configuration.
        rng (np.random.Generator): Independent random number generator.

    Returns:
        Dict[str, Any]: Dictionary containing customer profile fields.
    """
    logger.info("Executing unified generate_profile orchestrator", extra={"age": age, "education": education})

    # Step 1: Draw Occupation and Monthly Income
    occupation, income = generate_occupation_and_income(age, education, config, rng)

    # Step 2: Draw Credit Score (CIBIL)
    cibil = generate_credit_profile(age, occupation, income, config, rng)

    # Step 3: Draw Device preference
    device = generate_device(income, config, rng)

    # Step 4: Draw Acquisition marketing channel
    channel = generate_acquisition_channel(age, income, cibil, config, rng)

    return {
        "occupation": occupation,
        "monthly_income": income,
        "cibil_score": cibil,
        "acquisition_channel": channel,
        "device": device
    }
