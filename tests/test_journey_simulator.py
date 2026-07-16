# Unit Tests for Journey Simulation Engine Module

import pytest
import pandas as pd
import numpy as np
import os
from src.data_generation.config import load_config
from src.data_generation.journey_simulator import JourneySimulator

@pytest.fixture
def config():
    return load_config("config/settings.yaml")

@pytest.fixture
def rng():
    return np.random.default_rng(42)

def test_journey_events_schema(config, rng):
    """
    Verifies that journey simulator generates correctly structured event schemas.
    """
    # Set all conversion probabilities to 1.0 for testing schema guarantee
    config.FUNNEL_CONVERSION_RATES = {
        "otp_to_kyc_start": 1.0,
        "kyc_start_to_face_match": 1.0,
        "face_match_to_pan_verify": 1.0,
        "pan_verify_to_kyc_complete": 1.0,
        "kyc_complete_to_loan_apply": 1.0,
        "approved_to_disbursed": 1.0
    }
    simulator = JourneySimulator(config)
    
    # Create a mock user series
    user_row = pd.Series({
        "user_id": "usr_0000001",
        "device": "Mobile-Android",
        "acquisition_channel": "Google Ads",
        "has_credit_history": True,
        "cibil_score": 780,
        "monthly_income": 60000,
        "state": "Karnataka",
        "registration_date": "2025-07-15"
    })
    
    # Run simulation stages
    otp_time = pd.to_datetime("2025-07-15 12:00:00")
    app_events, app_open_time = simulator.simulate_verification_stage("usr_0000001", "Mobile-Android", otp_time, rng)
    mkt_events = simulator.simulate_marketing_stage("usr_0000001", "Mobile-Android", "Karnataka", "Google Ads", app_open_time, rng)
    
    # Check if user applied for loan to run loan stage
    has_applied = any(evt["event_name"] == "Loan Apply" for evt in app_events)
    assert has_applied is True  # with seed 42, it should apply
    
    apply_evt = [evt for evt in app_events if evt["event_name"] == "Loan Apply"][0]
    apply_time = pd.to_datetime(apply_evt["timestamp"])
    loan_events = simulator.simulate_loan_stage("usr_0000001", 780, 60000, apply_time, rng)

    # 1. Marketing Events assertions
    assert len(mkt_events) == 3
    for event in mkt_events:
        assert "event_id" in event
        assert "user_id" in event
        assert "campaign" in event
        assert "channel" in event
        assert "ad_group" in event
        assert "device" in event
        assert "state" in event
        assert "cost" in event
        assert "timestamp" in event
        assert event["user_id"] == "usr_0000001"
        assert event["channel"] == "Google Ads"
        assert event["state"] == "Karnataka"
        assert event["device"] == "Mobile-Android"

    # 2. App Events assertions
    assert len(app_events) >= 3
    for event in app_events:
        assert "event_id" in event
        assert "user_id" in event
        assert "session_id" in event
        assert "platform" in event
        assert "event_name" in event
        assert "timestamp" in event
        assert event["user_id"] == "usr_0000001"
        assert event["platform"] == "Android"

    # 3. Loan Events assertions
    assert len(loan_events) >= 2
    for event in loan_events:
        assert "event_id" in event
        assert "user_id" in event
        assert "loan_amount" in event
        assert "approval_status" in event
        assert "rejection_reason" in event
        assert "interest_rate" in event
        assert "timestamp" in event
        assert event["user_id"] == "usr_0000001"

def test_chronological_and_business_validation(config, rng):
    """
    Verifies that journey simulator validates chronological and state transitions correctly.
    """
    simulator = JourneySimulator(config)
    
    # 1. Valid journey
    valid_journey = [
        {"user_id": "usr_1", "event_type": "Impression", "timestamp": "2025-07-15 10:00:00"},
        {"user_id": "usr_1", "event_type": "Click", "timestamp": "2025-07-15 10:05:00"},
        {"user_id": "usr_1", "event_type": "Install", "timestamp": "2025-07-15 10:10:00"},
        {"user_id": "usr_1", "event_type": "App Open", "timestamp": "2025-07-15 10:12:00"},
        {"user_id": "usr_1", "event_type": "Signup", "timestamp": "2025-07-15 10:15:00"},
        {"user_id": "usr_1", "event_type": "OTP Verification", "timestamp": "2025-07-15 10:16:00"},
        {"user_id": "usr_1", "event_type": "KYC Start", "timestamp": "2025-07-15 10:18:00"},
        {"user_id": "usr_1", "event_type": "KYC Complete", "timestamp": "2025-07-15 10:22:00"},
        {"user_id": "usr_1", "event_type": "Loan Apply", "timestamp": "2025-07-15 10:25:00"},
        {"user_id": "usr_1", "event_type": "Pending", "timestamp": "2025-07-15 10:26:00"},
        {"user_id": "usr_1", "event_type": "Approved", "timestamp": "2025-07-15 10:30:00"},
        {"user_id": "usr_1", "event_type": "Disbursed", "timestamp": "2025-07-15 11:00:00"}
    ]
    assert simulator.validate_journey(valid_journey) is True

    # 2. Chronology error (App Open occurs after Signup)
    invalid_chronology = [
        {"user_id": "usr_1", "event_type": "Signup", "timestamp": "2025-07-15 10:10:00"},
        {"user_id": "usr_1", "event_type": "App Open", "timestamp": "2025-07-15 10:05:00"}
    ]
    assert simulator.validate_journey(invalid_chronology) is False

    # 3. Business order error (Disbursed -> Rejected)
    invalid_business_1 = [
        {"user_id": "usr_1", "event_type": "Approved", "timestamp": "2025-07-15 10:10:00"},
        {"user_id": "usr_1", "event_type": "Disbursed", "timestamp": "2025-07-15 10:15:00"},
        {"user_id": "usr_1", "event_type": "Rejected", "timestamp": "2025-07-15 10:20:00"}
    ]
    assert simulator.validate_journey(invalid_business_1) is False

    # 4. Business order error (Loan Apply -> Signup)
    invalid_business_2 = [
        {"user_id": "usr_1", "event_type": "Loan Apply", "timestamp": "2025-07-15 10:10:00"},
        {"user_id": "usr_1", "event_type": "Signup", "timestamp": "2025-07-15 10:15:00"}
    ]
    assert simulator.validate_journey(invalid_business_2) is False

def test_approval_rates_and_rejections(config, rng):
    """
    Verifies that CIBIL-based approval rates and rejection reasons behave as expected.
    """
    simulator = JourneySimulator(config)

    # 1. Test Approval Probabilities mapping
    assert simulator._get_loan_approval_probability(800) == 0.95  # Excellent
    assert simulator._get_loan_approval_probability(400) == 0.10  # Poor
    assert simulator._get_loan_approval_probability(None) == 0.55   # NTC

    # 2. Test rejection reason when CIBIL is low
    apply_time = pd.to_datetime("2025-07-15 12:00:00")
    rejection_evts = simulator.simulate_loan_stage("usr_test", 400, 30000, apply_time, rng)
    # Filter for Rejected event
    rejected = [evt for evt in rejection_evts if evt["approval_status"] == "Rejected"]
    if rejected:
        assert rejected[0]["rejection_reason"] == "Low CIBIL Score"

def test_journey_simulation_generation(config, tmp_path):
    """
    Tests simulator generation E2E on a dummy user dataset.
    """
    users_csv = tmp_path / "users_dummy.csv"
    dummy_data = pd.DataFrame({
        "user_id": ["usr_0000001", "usr_0000002"],
        "device": ["Mobile-Android", "Mobile-iOS"],
        "acquisition_channel": ["Google Ads", "Organic"],
        "has_credit_history": [True, False],
        "cibil_score": [780, None],
        "monthly_income": [60000, 15000],
        "state": ["Delhi", "Maharashtra"],
        "registration_date": ["2025-07-01", "2025-07-02"]
    })
    # Force Int64 type
    dummy_data["cibil_score"] = dummy_data["cibil_score"].astype("Int64")
    dummy_data.to_csv(users_csv, index=False)
    
    # Set all conversion probabilities to 1.0 for testing generation guarantee
    config.FUNNEL_CONVERSION_RATES = {
        "otp_to_kyc_start": 1.0,
        "kyc_start_to_face_match": 1.0,
        "face_match_to_pan_verify": 1.0,
        "pan_verify_to_kyc_complete": 1.0,
        "kyc_complete_to_loan_apply": 1.0,
        "approved_to_disbursed": 1.0
    }
    simulator = JourneySimulator(config)
    mkt, app, lon = simulator.generate(str(users_csv), str(tmp_path))
    
    # Assert output files exist
    assert os.path.exists(tmp_path / "marketing_events.csv")
    assert os.path.exists(tmp_path / "app_events.csv")
    assert os.path.exists(tmp_path / "loan_events.csv")
    
    # Check shape/lengths
    assert len(mkt) == 6  # 3 events per user * 2 users
    assert len(app) >= 6
    assert len(lon) >= 2  # Pending + Approved/Rejected per user
