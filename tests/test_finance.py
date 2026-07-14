# Unit Tests for Finance and Employment Generation

import pytest
import numpy as np
from src.data_generation.config import load_config
from src.data_generation.finance import generate_employment_and_income, generate_credit_profile

@pytest.fixture
def config():
    return load_config("config/settings.yaml")

@pytest.fixture
def rng():
    return np.random.default_rng(42)

def test_employment_and_income_constraints(config, rng):
    """
    Assert that occupation and income values comply with dynamic caps.
    """
    for _ in range(500):
        # Test with random age and education
        age = int(rng.integers(18, 65, endpoint=True))
        edu = rng.choice(list(config.EDUCATION_DISTRIBUTION.keys()))
        
        occ, income = generate_employment_and_income(age, edu, config, rng)
        
        assert occ in config.OCCUPATION_DISTRIBUTION.keys()
        assert income >= 0
        
        if occ == "Student":
            assert income <= 25000
        elif occ == "Retired":
            assert income <= 80000
        else:
            # Employed occupations (Salaried, Self-Employed, Professional) must have positive income
            assert income > 0

def test_credit_profile_boundaries(config, rng):
    """
    Assert that CIBIL score outputs are in range or NTC (-1).
    """
    for _ in range(500):
        age = int(rng.integers(18, 65, endpoint=True))
        occ = rng.choice(list(config.OCCUPATION_DISTRIBUTION.keys()))
        income = int(rng.integers(0, 300000))
        
        cibil = generate_credit_profile(age, occ, income, config, rng)
        assert cibil == -1 or (300 <= cibil <= 900)

def test_ntc_probability_skew(config, rng):
    """
    Verify that students and younger users (<22) have high probability of NTC (-1)
    """
    # Sample a batch of students / young users
    young_ntc_count = 0
    total_young = 1000
    for _ in range(total_young):
        age = int(rng.integers(18, 21, endpoint=True))
        occ = "Student"
        income = 2000
        cibil = generate_credit_profile(age, occ, income, config, rng)
        if cibil == -1:
            young_ntc_count += 1
            
    # Empirical check: ~80% should be NTC
    ntc_ratio = young_ntc_count / total_young
    assert 0.70 <= ntc_ratio <= 0.90
