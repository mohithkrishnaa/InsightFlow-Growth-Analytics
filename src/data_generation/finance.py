# Finance and Employment Generator Module for the InsightFlow Data Generation Pipeline

import numpy as np
from typing import Dict, Any, Tuple
from src.data_generation.config import GeneratorConfig
from src.data_generation.constants import INCOME_PARAMETERS

def calculate_occupation_weights(age: int, education_level: str, config: GeneratorConfig) -> list:
    """
    Computes occupation probabilities dynamically based on age and education level.
    """
    occ_weights = dict(config.OCCUPATION_DISTRIBUTION)

    # 1. Age-based rules:
    if age < 22:
        occ_weights["Retired"] = 0.0
    if age >= 25:
        # Scale down student probability for older users
        occ_weights["Student"] = occ_weights.get("Student", 0.05) * 0.1

    # 2. Education-based rules:
    if education_level == "High School":
        occ_weights["Professional"] = 0.0
    if education_level in ["Postgraduate", "Doctorate"]:
        occ_weights["Student"] = 0.0
        # Boost Salaried and Professional
        occ_weights["Salaried"] = occ_weights.get("Salaried", 0.60) * 1.2
        occ_weights["Professional"] = occ_weights.get("Professional", 0.10) * 1.5

    # Normalize weights
    total_weight = sum(occ_weights.values())
    if total_weight > 0:
        return [w / total_weight for w in occ_weights.values()]
    else:
        # Fallback
        return list(config.OCCUPATION_DISTRIBUTION.values())

def generate_employment_and_income(
    age: int, 
    education_level: str, 
    config: GeneratorConfig, 
    rng: np.random.Generator
) -> Tuple[str, int]:
    """
    Generates occupation and monthly income based on age, education, and log-normal parameters.
    """
    # 1. Select Occupation
    occupations = list(config.OCCUPATION_DISTRIBUTION.keys())
    occ_weights = calculate_occupation_weights(age, education_level, config)
    occupation = rng.choice(occupations, p=occ_weights)

    # 2. Generate Monthly Income
    params = INCOME_PARAMETERS[occupation]
    
    # Scale income based on education level
    edu_scale = {
        "High School": 0.8,
        "Undergraduate": 1.0,
        "Graduate": 1.2,
        "Postgraduate": 1.5,
        "Doctorate": 1.8
    }
    scale_factor = edu_scale.get(education_level, 1.0)
    adjusted_median = params["median"] * scale_factor

    # Convert median to log-space mean (mu)
    mu = np.log(adjusted_median)
    sigma = params["sigma"]

    # Draw from log-normal distribution
    sampled_income = int(np.exp(rng.normal(mu, sigma)))

    # Clip to boundaries
    min_val = params["min"]
    max_val = params["max"]
    monthly_income = max(min_val, min(max_val, sampled_income))

    # Apply strict validation caps
    if occupation == "Student":
        # Students cap: max 25,000. 15% chance of exactly 0 income
        if rng.random() < 0.15:
            monthly_income = 0
        else:
            monthly_income = min(25000, monthly_income)
    elif occupation == "Retired":
        # Retired cap: max 80,000. 5% chance of exactly 0 income
        if rng.random() < 0.05:
            monthly_income = 0
        else:
            monthly_income = min(80000, monthly_income)
    else:
        # Guarantee non-zero income for employed classes
        if monthly_income <= 0:
            monthly_income = params["min"] if params["min"] > 0 else 15000

    return occupation, monthly_income

def generate_credit_profile(
    age: int,
    occupation: str,
    monthly_income: int,
    config: GeneratorConfig,
    rng: np.random.Generator
) -> int:
    """
    Generates CIBIL score based on demographic characteristics, income, and configured probability weights.
    """
    # 1. Check for New to Credit (NTC) flag
    # If Student or Age < 22: 80% probability of being NTC
    if occupation == "Student" or age < 22:
        if rng.random() < 0.80:
            return -1
    else:
        # Base probability of NTC for others (e.g. 5% chance)
        if rng.random() < 0.05:
            return -1

    # 2. For scored users, shift probabilities based on age, income, and occupation
    # Relative baseline probabilities of scored segments (sums to 0.88 in config, normalize it here)
    cibil_dist = config.CIBIL_DISTRIBUTION
    scored_categories = ["Poor", "Fair", "Good", "Excellent"]
    scored_probs = [
        cibil_dist.get("Poor", 0.08),
        cibil_dist.get("Fair", 0.20),
        cibil_dist.get("Good", 0.40),
        cibil_dist.get("Excellent", 0.20)
    ]
    sum_probs = sum(scored_probs)
    normalized_probs = [p / sum_probs for p in scored_probs]

    # Calculate score factor based on normalized age and income
    # Normalized age in [-1, 1] relative to center of range (18 to 65, center = 41)
    age_norm = (age - 41.5) / 23.5
    
    # Normalized income in [-1, 1] relative to typical median of 45,000, capped at 150k
    income_cap = min(150000, monthly_income)
    income_norm = (income_cap - 45000) / 105000

    # Combine factors: Income (weight 0.5) + Age (weight 0.2) + Occupation (Salaried/Professional boost)
    score_factor = 0.2 * age_norm + 0.5 * income_norm
    if occupation in ["Professional", "Salaried"]:
        score_factor += 0.15
    elif occupation == "Student":
        score_factor -= 0.3

    # Clip score factor to reasonable shift boundaries
    score_factor = max(-0.7, min(0.7, score_factor))

    # Apply probability shifts:
    # If score_factor > 0, shift weight from Poor/Fair to Good/Excellent
    # If score_factor < 0, shift weight from Excellent/Good to Poor/Fair
    if score_factor > 0:
        # Decrease Poor and Fair probabilities
        p_poor = normalized_probs[0] * (1 - 0.6 * score_factor)
        p_fair = normalized_probs[1] * (1 - 0.4 * score_factor)
        diff = (normalized_probs[0] - p_poor) + (normalized_probs[1] - p_fair)
        
        # Distribute difference to Good and Excellent
        p_good = normalized_probs[2] + diff * 0.4
        p_excellent = normalized_probs[3] + diff * 0.6
    else:
        # Negative shift: Decrease Excellent and Good probabilities
        abs_factor = abs(score_factor)
        p_excellent = normalized_probs[3] * (1 - 0.6 * abs_factor)
        p_good = normalized_probs[2] * (1 - 0.4 * abs_factor)
        diff = (normalized_probs[3] - p_excellent) + (normalized_probs[2] - p_good)
        
        # Distribute difference to Poor and Fair
        p_fair = normalized_probs[1] + diff * 0.6
        p_poor = normalized_probs[0] + diff * 0.4

    adjusted_weights = [p_poor, p_fair, p_good, p_excellent]
    # Re-normalize adjusted weights just in case
    adj_sum = sum(adjusted_weights)
    final_probs = [w / adj_sum for w in adjusted_weights]

    selected_category = rng.choice(scored_categories, p=final_probs)

    # 3. Sample score inside selected category boundaries
    if selected_category == "Poor":
        return int(rng.integers(300, 549, endpoint=True))
    elif selected_category == "Fair":
        return int(rng.integers(550, 649, endpoint=True))
    elif selected_category == "Good":
        return int(rng.integers(650, 749, endpoint=True))
    else: # Excellent
        return int(rng.integers(750, 900, endpoint=True))
