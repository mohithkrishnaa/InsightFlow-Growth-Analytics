# Data Validation Module for the InsightFlow Data Generation Pipeline

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from src.data_generation.config import GeneratorConfig
from src.data_generation.constants import GEOGRAPHY_MATRIX

logger = logging.getLogger("InsightFlowGenerator")

def validate_record_integrity(record: Dict[str, Any]) -> bool:
    """
    Validates a single user record's business rules and boundary constraints.
    Returns True if valid, otherwise False.
    """
    try:
        # 1. Bounds check on age
        age = record["age"]
        if not (18 <= age <= 65):
            return False

        # 2. Bounds check on monthly income
        monthly_income = record["monthly_income"]
        if monthly_income < 0:
            return False

        # 3. Bounds check on CIBIL
        cibil = record["cibil_score"]
        if not (cibil == -1 or (300 <= cibil <= 900)):
            return False

        # 4. Education age checks
        edu = record["education_level"]
        if edu in ["Postgraduate", "Doctorate"] and age < 22:
            return False
        if edu == "Doctorate" and age < 21:
            return False

        # 5. Occupation income limits
        occ = record["occupation"]
        if occ == "Student" and monthly_income > 25000:
            return False
        if occ == "Retired" and monthly_income > 80000:
            return False
        if monthly_income == 0 and occ not in ["Student", "Retired"]:
            return False

        # 6. Geography mapping alignment checks
        state = record["state"]
        city = record["city"]
        tier = record["city_tier"]
        
        # Check against GEOGRAPHY_MATRIX
        geo_match = False
        for entry in GEOGRAPHY_MATRIX:
            if entry["city"] == city:
                if entry["state"] == state and entry["tier"] == tier:
                    geo_match = True
                    break
        if not geo_match:
            return False

        return True

    except KeyError as e:
        logger.error(f"Missing column in record during validation: {e}")
        return False
    except Exception as e:
        logger.error(f"Error during record validation: {e}")
        return False

def validate_dataset_distributions(df: pd.DataFrame, config: GeneratorConfig) -> bool:
    """
    Validates aggregate statistical checks, PK uniqueness, null counts, 
    and checks if generated features align with target weights within configured tolerances.
    """
    passed = True
    base_tolerance = config.VALIDATION_TOLERANCE
    n_users = len(df)

    if n_users == 0:
        logger.error("Dataset validation failed: Empty DataFrame.")
        return False

    # Adjust tolerance for small sample sizes (under 5,000 records) due to natural statistical variance
    sample_adj = 0.05 if n_users < 5000 else 0.0

    # Categorize variables by generation pattern
    # Direct variables (should match configuration weights closely)
    direct_tolerance = base_tolerance + sample_adj
    
    # Skewed/Correlated variables (drift from baseline is expected due to correlations)
    skewed_tolerance = max(0.10, base_tolerance * 4) + sample_adj

    # 1. Primary Key Uniqueness
    if df["user_id"].duplicated().any():
        logger.error("Dataset validation failed: Duplicate user_id entries detected.")
        passed = False

    # 2. Completeness / No Nulls
    if df.isnull().any().any():
        logger.error("Dataset validation failed: Null values found in columns.")
        passed = False

    # 3. Distribution Checks:
    # 3a. Gender Distribution (Direct)
    gender_actual = df["gender"].value_counts(normalize=True).to_dict()
    for gender, target in config.GENDER_DISTRIBUTION.items():
        actual = gender_actual.get(gender, 0.0)
        diff = abs(actual - target)
        if diff > direct_tolerance:
            logger.error(f"Gender distribution check failed for '{gender}': Target={target:.4f}, Actual={actual:.4f} (diff={diff:.4f} > tolerance={direct_tolerance})")
            passed = False

    # 3b. Education Distribution (Skewed due to age correlations)
    edu_actual = df["education_level"].value_counts(normalize=True).to_dict()
    for edu, target in config.EDUCATION_DISTRIBUTION.items():
        actual = edu_actual.get(edu, 0.0)
        diff = abs(actual - target)
        if diff > skewed_tolerance:
            logger.error(f"Education distribution check failed for '{edu}': Target={target:.4f}, Actual={actual:.4f} (diff={diff:.4f} > tolerance={skewed_tolerance})")
            passed = False

    # 3c. Occupation Distribution (Skewed)
    occ_actual = df["occupation"].value_counts(normalize=True).to_dict()
    for occ, target in config.OCCUPATION_DISTRIBUTION.items():
        actual = occ_actual.get(occ, 0.0)
        diff = abs(actual - target)
        if diff > skewed_tolerance:
            logger.error(f"Occupation distribution check failed for '{occ}': Target={target:.4f}, Actual={actual:.4f} (diff={diff:.4f} > tolerance={skewed_tolerance})")
            passed = False

    # 3d. Device Distribution (Skewed)
    dev_actual = df["device"].value_counts(normalize=True).to_dict()
    for dev, target in config.DEVICE_DISTRIBUTION.items():
        actual = dev_actual.get(dev, 0.0)
        diff = abs(actual - target)
        if diff > skewed_tolerance:
            logger.error(f"Device distribution check failed for '{dev}': Target={target:.4f}, Actual={actual:.4f} (diff={diff:.4f} > tolerance={skewed_tolerance})")
            passed = False

    # 3e. Acquisition Channel Distribution (Skewed)
    chan_actual = df["acquisition_channel"].value_counts(normalize=True).to_dict()
    for chan, target in config.CHANNEL_DISTRIBUTION.items():
        actual = chan_actual.get(chan, 0.0)
        diff = abs(actual - target)
        if diff > skewed_tolerance:
            logger.error(f"Acquisition channel distribution check failed for '{chan}': Target={target:.4f}, Actual={actual:.4f} (diff={diff:.4f} > tolerance={skewed_tolerance})")
            passed = False

    # 3f. CIBIL Scores Segment Distributions (Skewed)
    cibil_scores = df["cibil_score"].values
    ntc_count = np.sum(cibil_scores == -1)
    poor_count = np.sum((cibil_scores >= 300) & (cibil_scores <= 549))
    fair_count = np.sum((cibil_scores >= 550) & (cibil_scores <= 649))
    good_count = np.sum((cibil_scores >= 650) & (cibil_scores <= 749))
    excellent_count = np.sum((cibil_scores >= 750) & (cibil_scores <= 900))

    actual_cibil_dist = {
        "NTC": ntc_count / n_users,
        "Poor": poor_count / n_users,
        "Fair": fair_count / n_users,
        "Good": good_count / n_users,
        "Excellent": excellent_count / n_users
    }

    for segment, target in config.CIBIL_DISTRIBUTION.items():
        actual = actual_cibil_dist.get(segment, 0.0)
        diff = abs(actual - target)
        if diff > skewed_tolerance:
            logger.error(f"CIBIL segment distribution check failed for '{segment}': Target={target:.4f}, Actual={actual:.4f} (diff={diff:.4f} > tolerance={skewed_tolerance})")
            passed = False

    # 3g. State Distributions (Direct)
    state_weights = {}
    for entry in GEOGRAPHY_MATRIX:
        state_weights[entry["state"]] = state_weights.get(entry["state"], 0.0) + entry["weight"]
    
    state_actual = df["state"].value_counts(normalize=True).to_dict()
    for state, target in state_weights.items():
        actual = state_actual.get(state, 0.0)
        diff = abs(actual - target)
        if diff > direct_tolerance:
            logger.error(f"State distribution check failed for '{state}': Target={target:.4f}, Actual={actual:.4f} (diff={diff:.4f} > tolerance={direct_tolerance})")
            passed = False

    return passed
