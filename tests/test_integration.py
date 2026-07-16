# Integration and End-to-End Tests for the InsightFlow Data Generation Engine

import os
import pytest
import pandas as pd
from src.data_generation.config import load_config
from src.data_generation.generate_users import generate_users_pipeline

def test_pipeline_integration_e2e(tmp_path):
    """
    Test E2E pipeline execution with custom temporary directory.
    Verifies files are output correctly and distributions match validation tolerances.
    """
    # 1. Create a temporary config file based on current configurations
    config_file = tmp_path / "settings_test.yaml"
    output_csv = tmp_path / "users_test.csv"
    report_md = tmp_path / "report_test.md"

    # Write a small volume test configuration
    config_content = f"""
NUMBER_OF_USERS: 500
SEED: 10
LOG_LEVEL: "INFO"
OUTPUT_FILE_PATH: "{output_csv.as_posix()}"
REPORT_FILE_PATH: "{report_md.as_posix()}"

GENDER_DISTRIBUTION:
  Male: 0.55
  Female: 0.43
  Other: 0.02

EDUCATION_DISTRIBUTION:
  High School: 0.15
  Undergraduate: 0.50
  Graduate: 0.25
  Postgraduate: 0.08
  Doctorate: 0.02

OCCUPATION_DISTRIBUTION:
  Salaried: 0.60
  Self-Employed: 0.20
  Professional: 0.10
  Retired: 0.05
  Student: 0.05

CIBIL_DISTRIBUTION:
  NTC: 0.12
  Poor: 0.08
  Fair: 0.20
  Good: 0.40
  Excellent: 0.20

DEVICE_DISTRIBUTION:
  Mobile-Android: 0.85
  Mobile-iOS: 0.10
  Desktop-Windows: 0.04
  Desktop-MacOS: 0.01

CHANNEL_DISTRIBUTION:
  Google Ads: 0.30
  Meta Ads: 0.35
  Affiliate: 0.20
  Referral: 0.10
  Organic: 0.05

DATE_RANGE:
  START_DATE: "2025-07-01"
  END_DATE: "2026-06-30"

GROWTH_RATE: 0.06
VALIDATION_TOLERANCE: 0.05  # Higher tolerance for small sample size (500 records)
"""
    config_file.write_text(config_content)

    # 2. Run the pipeline E2E
    assert not os.path.exists(output_csv)
    assert not os.path.exists(report_md)

    generate_users_pipeline(str(config_file))

    # 3. Verify outputs
    assert os.path.exists(output_csv)
    assert os.path.exists(report_md)

    df = pd.read_csv(output_csv)
    assert len(df) == 500

    # Ensure schema matches exactly
    expected_cols = [
        "user_id", "gender", "age", "education_level", 
        "state", "city", "city_tier", "occupation", 
        "monthly_income", "has_credit_history", "cibil_score", "acquisition_channel", 
        "device", "registration_date"
    ]
    assert list(df.columns) == expected_cols

    # Ensure no nulls except in cibil_score
    null_cols = df.columns[df.isnull().any()].tolist()
    for col in null_cols:
        assert col == "cibil_score"
