# Unit Tests for Geography Generation Module

import pytest
import numpy as np
from src.data_generation.config import load_config, AppConfig
from src.data_generation.geography import (
    generate_state,
    generate_city,
    get_city_tier,
    validate_geography,
    generate_geography
)
from src.data_generation.constants import GEOGRAPHY_MATRIX

@pytest.fixture
def config():
    return load_config("config/settings.yaml")

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

def test_generate_state(config, rng):
    """
    Tests state generation follows probability weights.
    """
    generated_states = [generate_state(config, rng) for _ in range(1000)]
    for state in generated_states:
        assert state in config.STATE_DISTRIBUTION
    
    # Delhi weight is ~6%, Karnataka is ~13%, Maharashtra is ~19%
    # Check frequency order holds roughly
    delhi_count = generated_states.count("Delhi")
    karnataka_count = generated_states.count("Karnataka")
    maharashtra_count = generated_states.count("Maharashtra")
    
    assert maharashtra_count > delhi_count
    assert karnataka_count > delhi_count

def test_generate_city_weighted(config, rng):
    """
    Tests city generation belongs to state and follows config weights.
    """
    # For Punjab, Amritsar (0.02) and Ludhiana (0.02) have equal weights
    punjab_cities = [generate_city("Punjab", config, rng) for _ in range(500)]
    for city in punjab_cities:
        assert city in ["Ludhiana", "Amritsar"]
    
    ludhiana_count = punjab_cities.count("Ludhiana")
    amritsar_count = punjab_cities.count("Amritsar")
    
    # Difference should be within statistical range (e.g. 50/50 split)
    assert abs(ludhiana_count - amritsar_count) < 100

    # For Karnataka, Bangalore has 0.10 weight, Mysore 0.02, Hubli 0.01
    karnataka_cities = [generate_city("Karnataka", config, rng) for _ in range(1000)]
    for city in karnataka_cities:
        assert city in ["Bangalore", "Mysore", "Hubli"]
        
    bangalore_count = karnataka_cities.count("Bangalore")
    mysore_count = karnataka_cities.count("Mysore")
    hubli_count = karnataka_cities.count("Hubli")
    
    assert bangalore_count > mysore_count
    assert mysore_count > hubli_count

def test_generate_city_invalid_state(config, rng):
    """
    Ensures generate_city raises ValueError for invalid states.
    """
    with pytest.raises(ValueError, match="is not defined in CITY_MAPPING"):
        generate_city("InvalidState", config, rng)

def test_get_city_tier(config):
    """
    Tests get_city_tier retrieves classification correctly.
    """
    assert get_city_tier("Bangalore", config) == "Tier 1"
    assert get_city_tier("Noida", config) == "Tier 2"
    assert get_city_tier("Varanasi", config) == "Tier 3"

    with pytest.raises(KeyError, match="not found in CITY_TIER_MAPPING"):
        get_city_tier("InvalidCity", config)

def test_validate_geography(config):
    """
    Verifies validate_geography correctness.
    """
    assert validate_geography("Karnataka", "Bangalore", "Tier 1", config) is True
    
    # Inconsistent tier
    with pytest.raises(ValueError, match="does not match expected tier"):
        validate_geography("Karnataka", "Bangalore", "Tier 2", config)

    # City does not belong to state
    with pytest.raises(ValueError, match="does not belong to state"):
        validate_geography("Delhi", "Bangalore", "Tier 1", config)

    # State not in distribution
    with pytest.raises(ValueError, match="is not valid under current configuration"):
        validate_geography("InvalidState", "Bangalore", "Tier 1", config)

def test_config_missing_mappings():
    """
    Tests validation constraints for invalid configurations.
    """
    # Missing state in mapping
    with pytest.raises(ValueError, match="missing in CITY_MAPPING"):
        AppConfig(
            NUMBER_OF_USERS=100, RANDOM_SEED=42, LOG_LEVEL="INFO",
            OUTPUT_FILE_PATH="test.csv", REPORT_FILE_PATH="test.md",
            REGISTRATION_DATE_RANGE={"START_DATE": "2025-07-01", "END_DATE": "2026-06-30"},
            STATE_DISTRIBUTION={"Delhi": 1.0},
            CITY_MAPPING={}, # Delhi missing
            CITY_TIER_MAPPING={"New Delhi": "Tier 1"},
            CITY_WEIGHTS={"New Delhi": 1.0},
            OCCUPATION_DISTRIBUTION={"Salaried": 1.0},
            EDUCATION_MAPPING={"High School": 1.0},
            GENDER_DISTRIBUTION={"Male": 1.0},
            AGE_DISTRIBUTION={"18-24": 1.0},
            INCOME_RANGES={"Salaried": {"median": 10000, "sigma": 0.5, "min": 5000, "max": 20000}},
            CIBIL_DISTRIBUTION={"Good": 1.0},
            DEVICE_DISTRIBUTION={"Mobile-Android": 1.0},
            ACQUISITION_CHANNEL_DISTRIBUTION={"Organic": 1.0}
        )

    # Missing city weight
    with pytest.raises(ValueError, match="missing a weight in CITY_WEIGHTS"):
        AppConfig(
            NUMBER_OF_USERS=100, RANDOM_SEED=42, LOG_LEVEL="INFO",
            OUTPUT_FILE_PATH="test.csv", REPORT_FILE_PATH="test.md",
            REGISTRATION_DATE_RANGE={"START_DATE": "2025-07-01", "END_DATE": "2026-06-30"},
            STATE_DISTRIBUTION={"Delhi": 1.0},
            CITY_MAPPING={"Delhi": ["New Delhi"]},
            CITY_TIER_MAPPING={"New Delhi": "Tier 1"},
            CITY_WEIGHTS={}, # Missing weight for New Delhi
            OCCUPATION_DISTRIBUTION={"Salaried": 1.0},
            EDUCATION_MAPPING={"High School": 1.0},
            GENDER_DISTRIBUTION={"Male": 1.0},
            AGE_DISTRIBUTION={"18-24": 1.0},
            INCOME_RANGES={"Salaried": {"median": 10000, "sigma": 0.5, "min": 5000, "max": 20000}},
            CIBIL_DISTRIBUTION={"Good": 1.0},
            DEVICE_DISTRIBUTION={"Mobile-Android": 1.0},
            ACQUISITION_CHANNEL_DISTRIBUTION={"Organic": 1.0}
        )
