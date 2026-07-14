# Unit Tests for Demographics Generation Layer

import pytest
import numpy as np
from src.data_generation.config import load_config
from src.data_generation.demographics import (
    generate_age,
    generate_gender,
    generate_education,
    validate_age,
    validate_gender,
    validate_education
)

@pytest.fixture
def config():
    return load_config("config/settings.yaml")

@pytest.fixture
def rng():
    return np.random.default_rng(42)

def test_generate_age_boundaries(config, rng):
    """Asserts that generated age falls strictly within configured limits."""
    for _ in range(1000):
        age = generate_age(config, rng)
        assert validate_age(age) is True
        assert 18 <= age <= 65

def test_generate_gender_validity(config, rng):
    """Asserts that generated gender belongs to permissible categories."""
    genders_list = list(config.GENDER_DISTRIBUTION.keys())
    for _ in range(500):
        gender = generate_gender(config, rng)
        assert validate_gender(gender, config) is True
        assert gender in genders_list

def test_education_correlation_and_limits(config, rng):
    """
    Verifies age-to-education boundaries:
    - Postgraduate & Doctorate require age >= 22
    - Doctorate requires age >= 21
    """
    for _ in range(1000):
        age = generate_age(config, rng)
        edu = generate_education(age, config, rng)
        
        assert validate_education(edu, age, config) is True
        
        if age < 22:
            assert edu not in ["Postgraduate", "Doctorate"]
        if age < 21:
            assert edu != "Doctorate"

def test_validate_age_out_of_bounds():
    """Asserts age bounds check catches invalid numbers."""
    assert validate_age(17) is False
    assert validate_age(18) is True
    assert validate_age(65) is True
    assert validate_age(66) is False

def test_validate_education_rules(config):
    """Checks that validate_education filters out inconsistent states."""
    # Underage Doctorate
    assert validate_education("Doctorate", 20, config) is False
    assert validate_education("Doctorate", 21, config) is False
    assert validate_education("Doctorate", 22, config) is True
    
    # Underage Postgraduate
    assert validate_education("Postgraduate", 21, config) is False
    assert validate_education("Postgraduate", 22, config) is True
