# Unit Tests for Geography Generation

import pytest
import numpy as np
from src.data_generation.geography import generate_geography
from src.data_generation.constants import GEOGRAPHY_MATRIX

@pytest.fixture
def rng():
    return np.random.default_rng(42)

def test_geography_matrix_mappings(rng):
    """
    Asserts that every sampled geography matches one of the configurations in constants.py.
    """
    valid_combinations = {
        (entry["city"], entry["state"], entry["tier"]) for entry in GEOGRAPHY_MATRIX
    }
    
    for _ in range(500):
        geo = generate_geography(rng)
        assert "state" in geo
        assert "city" in geo
        assert "city_tier" in geo
        
        combo = (geo["city"], geo["state"], geo["city_tier"])
        assert combo in valid_combinations
