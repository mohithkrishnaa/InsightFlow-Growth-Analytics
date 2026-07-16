# Unit Tests for Experiment Analytics Dataset Generator Module

import pytest
import pandas as pd
import numpy as np
import os
from src.data_generation.config import load_config
from src.data_generation.experiments_generator import ExperimentGenerator

@pytest.fixture
def config():
    return load_config("config/settings.yaml")

@pytest.fixture
def rng():
    return np.random.default_rng(42)

def test_income_segments(config):
    """
    Verifies that income segment classifications are assigned correctly.
    """
    generator = ExperimentGenerator(config)
    assert generator._get_income_segment(15000) == "Low"
    assert generator._get_income_segment(20000) == "Low"
    assert generator._get_income_segment(50000) == "Medium"
    assert generator._get_income_segment(70000) == "Medium"
    assert generator._get_income_segment(80000) == "High"
    assert generator._get_income_segment(150000) == "High"

def test_experiment_generation_schema(config, tmp_path):
    """
    Tests experiment exposures generator schema columns, user segmentations, and status boundaries.
    """
    # 1. Create dummy input CSV files
    users_csv = tmp_path / "users_dummy.csv"
    app_csv = tmp_path / "app_dummy.csv"
    loan_csv = tmp_path / "loan_dummy.csv"

    pd.DataFrame({
        "user_id": ["usr_1", "usr_2"],
        "device": ["Mobile-Android", "Mobile-iOS"],
        "city_tier": ["Tier 1", "Tier 2"],
        "monthly_income": [60000, 20000],
        "registration_date": ["2025-07-01", "2025-07-02"]
    }).to_csv(users_csv, index=False)

    pd.DataFrame({
        "event_id": ["app_1", "app_2", "app_3", "app_4"],
        "user_id": ["usr_1", "usr_1", "usr_2", "usr_2"],
        "session_id": ["ses_1", "ses_1", "ses_2", "ses_2"],
        "platform": ["Android", "Android", "iOS", "iOS"],
        "event_name": ["App Open", "Signup", "App Open", "Signup"],
        "timestamp": [
            "2025-07-01 12:00:00", "2025-07-01 12:05:00",
            "2025-07-02 14:00:00", "2025-07-02 14:05:00"
        ]
    }).to_csv(app_csv, index=False)

    pd.DataFrame({
        "event_id": ["lon_1"],
        "user_id": ["usr_1"],
        "loan_amount": [50000],
        "approval_status": ["Approved"],
        "rejection_reason": [""],
        "interest_rate": [12.5],
        "timestamp": ["2025-07-01 12:10:00"]
    }).to_csv(loan_csv, index=False)

    generator = ExperimentGenerator(config)
    # Generate exposures with small target size
    df = generator.generate(str(users_csv), str(app_csv), str(loan_csv), str(tmp_path), target_exposures_per_exp=2)
    
    # Assert CSV exists
    assert os.path.exists(tmp_path / "experiments.csv")
    assert os.path.exists(tmp_path / "experiment_generation_report.md")

    # Assert column definitions
    assert "experiment_id" in df.columns
    assert "user_id" in df.columns
    assert "experiment_name" in df.columns
    assert "experiment_type" in df.columns
    assert "hypothesis" in df.columns
    assert "success_metric" in df.columns
    assert "variant" in df.columns
    assert "exposure_timestamp" in df.columns
    assert "converted" in df.columns
    assert "conversion_event" in df.columns
    assert "conversion_timestamp" in df.columns
    assert "revenue_generated" in df.columns
    assert "device" in df.columns
    assert "city_tier" in df.columns
    assert "income_segment" in df.columns
    assert "experiment_status" in df.columns
    assert "statistical_significance" in df.columns

    # Assert static field initializations
    assert all(df["statistical_significance"] == "Pending")
    assert all(df["experiment_status"].isin(["Completed", "Running", "Paused"]))

    # Assert segment allocations
    row_usr1 = df[df["user_id"] == "usr_1"].iloc[0]
    assert row_usr1["income_segment"] == "Medium"
    assert row_usr1["device"] == "Mobile-Android"
    assert row_usr1["city_tier"] == "Tier 1"

    row_usr2 = df[df["user_id"] == "usr_2"].iloc[0]
    assert row_usr2["income_segment"] == "Low"
    assert row_usr2["device"] == "Mobile-iOS"
    assert row_usr2["city_tier"] == "Tier 2"

def test_chronological_order_and_revenue_rule(config, tmp_path):
    """
    Verifies that exposures occur after eligibility and conversions occur after exposure.
    Also asserts revenue is only generated for converted users.
    """
    users_csv = tmp_path / "users_dummy.csv"
    app_csv = tmp_path / "app_dummy.csv"
    loan_csv = tmp_path / "loan_dummy.csv"

    pd.DataFrame({
        "user_id": ["usr_1"],
        "device": ["Mobile-Android"],
        "city_tier": ["Tier 1"],
        "monthly_income": [60000],
        "registration_date": ["2025-07-01"]
    }).to_csv(users_csv, index=False)

    pd.DataFrame({
        "event_id": ["app_1", "app_2"],
        "user_id": ["usr_1", "usr_1"],
        "session_id": ["ses_1", "ses_1"],
        "platform": ["Android", "Android"],
        "event_name": ["App Open", "Signup"],
        "timestamp": ["2025-07-01 12:00:00", "2025-07-01 12:02:00"]
    }).to_csv(app_csv, index=False)

    pd.DataFrame(columns=["event_id", "user_id", "loan_amount", "approval_status", "rejection_reason", "interest_rate", "timestamp"]).to_csv(loan_csv, index=False)

    generator = ExperimentGenerator(config)
    df = generator.generate(str(users_csv), str(app_csv), str(loan_csv), str(tmp_path), target_exposures_per_exp=5)

    for _, row in df.iterrows():
        # Check exposure time relative to eligibility (App Open occurs at 12:00:00)
        eligibility_ts = pd.to_datetime("2025-07-01 12:00:00")
        exposure_ts = pd.to_datetime(row["exposure_timestamp"])
        assert exposure_ts > eligibility_ts
        
        # Check conversion rules
        if row["converted"] == "Yes":
            assert row["conversion_timestamp"] != ""
            conv_ts = pd.to_datetime(row["conversion_timestamp"])
            assert conv_ts >= exposure_ts
            assert row["revenue_generated"] > 0
        else:
            assert row["conversion_timestamp"] == ""
            assert row["revenue_generated"] == 0.0
