# Unit Tests for Customer Profile Generation Module

import pytest
import numpy as np
from src.data_generation.config import load_config
from src.data_generation.profile import (
    calculate_occupation_weights,
    generate_occupation_and_income,
    generate_credit_profile,
    generate_device,
    generate_acquisition_channel,
    generate_profile
)

@pytest.fixture
def config():
    return load_config("config/settings.yaml")

@pytest.fixture
def rng():
    return np.random.default_rng(42)

def test_generate_profile_keys(config, rng):
    """
    Asserts generate_profile returns all required dictionary fields.
    """
    profile = generate_profile(30, "Graduate", config, rng)
    assert "occupation" in profile
    assert "monthly_income" in profile
    assert "has_credit_history" in profile
    assert "cibil_score" in profile
    assert "acquisition_channel" in profile
    assert "device" in profile

def test_occupation_age_constraints(config):
    """
    Verifies age-based occupation constraints.
    - Under 22 cannot be Retired.
    """
    occupations = list(config.OCCUPATION_DISTRIBUTION.keys())
    retired_index = occupations.index("Retired")
    
    # Under 22 Retired weight must be 0
    weights_young = calculate_occupation_weights(20, "Graduate", config)
    assert weights_young[retired_index] == 0.0

    # Over 22 Retired weight can be > 0
    weights_old = calculate_occupation_weights(60, "Graduate", config)
    assert weights_old[retired_index] > 0.0

def test_occupation_education_constraints(config):
    """
    Verifies education-based occupation constraints.
    - High School cannot be Professional.
    - Postgraduate/Doctorate cannot be Student.
    """
    occupations = list(config.OCCUPATION_DISTRIBUTION.keys())
    prof_index = occupations.index("Professional")
    student_index = occupations.index("Student")

    # High School Professional weight must be 0
    weights_hs = calculate_occupation_weights(30, "High School", config)
    assert weights_hs[prof_index] == 0.0

    # Postgraduate Student weight must be 0
    weights_pg = calculate_occupation_weights(30, "Postgraduate", config)
    assert weights_pg[student_index] == 0.0

def test_income_rules_student_and_retired(config, rng):
    """
    Verifies income rules for students and retired users.
    - Student capped at 25,000.
    - Retired capped at 80,000.
    """
    for _ in range(500):
        # Student
        occ, income = generate_occupation_and_income(20, "High School", config, rng)
        if occ == "Student":
            assert income <= 25000
            
        # Retired (simulate with older age to allow retired selection)
        occ_ret, income_ret = generate_occupation_and_income(60, "Graduate", config, rng)
        if occ_ret == "Retired":
            assert income_ret <= 80000

def test_income_non_zero_for_employed(config, rng):
    """
    Verifies employed classes have non-zero income.
    """
    for _ in range(200):
        # Force Salaried or Professional by using PG and age 30
        occ, income = generate_occupation_and_income(30, "Postgraduate", config, rng)
        if occ in ["Salaried", "Professional", "Self-Employed"]:
            assert income > 0

def test_credit_profile_ntc_probability(config, rng):
    """
    Checks that Students/Underage are mostly NTC (-1), and others have a small NTC probability.
    """
    # Young / Students -> 80% NTC
    young_ntc_count = sum(1 for _ in range(500) if generate_credit_profile(20, "Student", 0, config, rng)[0] is None)
    assert young_ntc_count > 300 # Should be around 400

    # Mature Salaried -> 5% NTC
    mature_ntc_count = sum(1 for _ in range(500) if generate_credit_profile(40, "Salaried", 50000, config, rng)[0] is None)
    assert mature_ntc_count < 75 # Should be around 25

def test_credit_profile_scored_bounds(config, rng):
    """
    Verifies scored CIBIL scores fall within correct bands.
    """
    for _ in range(500):
        score, has_credit = generate_credit_profile(45, "Salaried", 60000, config, rng)
        if has_credit:
            assert score is not None
            assert 300 <= score <= 900
        else:
            assert score is None

def test_device_skew_by_income(config, rng):
    """
    Verifies device choice aligns with monthly income.
    - High income skew: premium devices
    - Low income skew: android devices
    """
    # High Income (150k+) -> premium devices (macOS/iOS) should have higher probability
    high_devices = [generate_device(200000, config, rng) for _ in range(500)]
    ios_macos_count_high = high_devices.count("Mobile-iOS") + high_devices.count("Desktop-MacOS")

    # Low Income (<40k) -> Android dominant
    low_devices = [generate_device(25000, config, rng) for _ in range(500)]
    android_count_low = low_devices.count("Mobile-Android")

    assert ios_macos_count_high > 100
    assert android_count_low > 400

def test_generate_acquisition_channel(config, rng):
    """
    Asserts acquisition channels are selected from permissible configuration keys.
    """
    channels_list = list(config.CHANNEL_DISTRIBUTION.keys())
    for _ in range(200):
        chan = generate_acquisition_channel(30, 45000, 700, config, rng)
        assert chan in channels_list
