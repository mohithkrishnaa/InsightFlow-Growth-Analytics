# Unit Tests for Data Validation Functions

import pytest
import pandas as pd
from src.data_generation.config import load_config
from src.data_generation.validators import validate_record_integrity, validate_dataset_distributions

@pytest.fixture
def config():
    return load_config("config/settings.yaml")

@pytest.fixture
def valid_record():
    return {
        "user_id": "usr_0000001",
        "gender": "Male",
        "age": 28,
        "education_level": "Undergraduate",
        "state": "Karnataka",
        "city": "Bangalore",
        "city_tier": "Tier 1",
        "occupation": "Salaried",
        "monthly_income": 48000,
        "has_credit_history": True,
        "cibil_score": 745,
        "acquisition_channel": "Google Ads",
        "device": "Mobile-Android",
        "registration_date": "2025-07-02"
    }

def test_validate_record_integrity_pass(valid_record):
    """
    Assert that a valid record passes validation rules.
    """
    assert validate_record_integrity(valid_record) is True

def test_validate_record_integrity_age_boundaries(valid_record):
    """
    Fails validation if age is outside 18-65.
    """
    r_under = valid_record.copy()
    r_under["age"] = 17
    assert validate_record_integrity(r_under) is False

    r_over = valid_record.copy()
    r_over["age"] = 66
    assert validate_record_integrity(r_over) is False

def test_validate_record_integrity_income_boundaries(valid_record):
    """
    Fails validation if monthly income is negative.
    """
    r = valid_record.copy()
    r["monthly_income"] = -100
    assert validate_record_integrity(r) is False

def test_validate_record_integrity_cibil_boundaries(valid_record):
    """
    Fails validation if CIBIL is out of range.
    """
    r_low = valid_record.copy()
    r_low["cibil_score"] = 299
    assert validate_record_integrity(r_low) is False

    r_high = valid_record.copy()
    r_high["cibil_score"] = 901
    assert validate_record_integrity(r_high) is False

def test_validate_record_integrity_student_income_cap(valid_record):
    """
    Fails if a student exceeds INR 25,000 in monthly income.
    """
    r = valid_record.copy()
    r["occupation"] = "Student"
    r["education_level"] = "Undergraduate"
    r["monthly_income"] = 26000
    assert validate_record_integrity(r) is False

def test_validate_record_integrity_retired_income_cap(valid_record):
    """
    Fails if retired exceeds INR 80,000 in monthly income.
    """
    r = valid_record.copy()
    r["occupation"] = "Retired"
    r["monthly_income"] = 81000
    assert validate_record_integrity(r) is False

def test_validate_record_integrity_geographic_mismatch(valid_record):
    """
    Fails validation if state and city tier do not match the city.
    """
    # Mismatch state
    r_state = valid_record.copy()
    r_state["state"] = "Maharashtra"
    assert validate_record_integrity(r_state) is False

    # Mismatch tier
    r_tier = valid_record.copy()
    r_tier["city_tier"] = "Tier 3"
    assert validate_record_integrity(r_tier) is False

def test_validate_dataset_duplicates(config, valid_record):
    """
    Fails dataset validation if duplicate user_id exists.
    """
    r2 = valid_record.copy()
    r2["user_id"] = "usr_0000001"  # duplicate ID
    
    df = pd.DataFrame([valid_record, r2])
    assert validate_dataset_distributions(df, config) is False

def test_validate_record_integrity_ntc(valid_record):
    """
    Asserts NTC users pass with None CIBIL score.
    """
    r_ntc = valid_record.copy()
    r_ntc["has_credit_history"] = False
    r_ntc["cibil_score"] = None
    assert validate_record_integrity(r_ntc) is True

    # Mismatch: has_credit_history=False, but cibil_score is set
    r_mismatch = valid_record.copy()
    r_mismatch["has_credit_history"] = False
    r_mismatch["cibil_score"] = 700
    assert validate_record_integrity(r_mismatch) is False
    
    # Mismatch: has_credit_history=True, but cibil_score is None
    r_mismatch_2 = valid_record.copy()
    r_mismatch_2["has_credit_history"] = True
    r_mismatch_2["cibil_score"] = None
    assert validate_record_integrity(r_mismatch_2) is False
