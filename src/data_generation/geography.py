# Geography Generator Module for the InsightFlow Data Generation Pipeline

import numpy as np
from typing import Dict, Any
from src.data_generation.constants import GEOGRAPHY_MATRIX

def generate_geography(rng: np.random.Generator) -> Dict[str, Any]:
    """
    Selects a state, city, and corresponding RBI city tier based on weighted probabilities.
    Ensures exact geographical integrity and alignment.
    """
    # Extract entries and weights
    weights = [entry["weight"] for entry in GEOGRAPHY_MATRIX]
    
    # Normalize weights just in case of rounding errors in configuration
    total_weight = sum(weights)
    normalized_weights = [w / total_weight for w in weights]

    # Select matrix index
    selected_index = rng.choice(len(GEOGRAPHY_MATRIX), p=normalized_weights)
    selected_geography = GEOGRAPHY_MATRIX[selected_index]

    return {
        "state": selected_geography["state"],
        "city": selected_geography["city"],
        "city_tier": selected_geography["tier"]
    }
