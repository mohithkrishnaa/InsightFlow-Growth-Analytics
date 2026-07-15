# Main Orchestration Entrypoint for the InsightFlow Data Generation Pipeline

import time
import argparse
import sys
import logging
import pandas as pd
import numpy as np
from datetime import date
from typing import Tuple, List

from src.data_generation.config import load_config
from src.data_generation.logging_config import setup_logging
from src.data_generation.demographics import generate_demographics
from src.data_generation.geography import generate_geography
from src.data_generation.profile import generate_profile
from src.data_generation.validators import validate_record_integrity, validate_dataset_distributions
from src.data_generation.exporter import export_dataset

logger = logging.getLogger("InsightFlowGenerator")

def precompute_date_probabilities(
    start_date_str: str, 
    end_date_str: str, 
    growth_rate: float
) -> Tuple[np.ndarray, List[float]]:
    """
    Generates all daily dates in range and calculates their probability weights.
    Weights scale with compounding MoM growth rate and have a 30% drop-off on weekends.
    """
    start_date = pd.to_datetime(start_date_str).date()
    end_date = pd.to_datetime(end_date_str).date()
    
    # Generate all days in the range
    all_dates = pd.date_range(start_date, end_date).date
    
    weights = []
    for day in all_dates:
        # Calculate months elapsed from start_date
        months_elapsed = (day.year - start_date.year) * 12 + (day.month - start_date.month)
        
        # Calculate growth weight factor: (1 + growth_rate) ^ months_elapsed
        growth_factor = (1.0 + growth_rate) ** months_elapsed
        
        # Check day of week seasonality (Monday=0, Sunday=6)
        day_of_week = day.weekday()
        if day_of_week >= 5:  # Saturday or Sunday
            seasonality_factor = 0.70  # 30% drop-off
        else:
            seasonality_factor = 1.00
            
        weights.append(growth_factor * seasonality_factor)
        
    # Normalize weights
    total_w = sum(weights)
    probs = [w / total_w for w in weights]
    
    return all_dates, probs

def generate_users_pipeline(config_path: str) -> None:
    """
    Orchestrates the loading of configurations, generation, validation, and export steps.
    """
    start_time = time.time()
    
    # 1. Load configuration
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"CRITICAL: Failed to load configuration from {config_path}: {e}", file=sys.stderr)
        sys.exit(1)
        
    # 2. Setup Logging
    setup_logging(config.LOG_LEVEL)
    logger.info(f"Loaded configuration from {config_path}")
    logger.info(f"Configured to generate {config.NUMBER_OF_USERS:,} users with seed {config.SEED}")

    # 3. Initialize Random state
    rng = np.random.default_state = np.random.default_rng(config.SEED)
    
    # 4. Precompute Date probabilities
    logger.info("Precomputing registration date weights and seasonal trends...")
    all_dates, date_probs = precompute_date_probabilities(
        config.DATE_RANGE.START_DATE,
        config.DATE_RANGE.END_DATE,
        config.GROWTH_RATE
    )
    
    # Sample all dates in a single batch for speed
    sampled_dates = rng.choice(all_dates, size=config.NUMBER_OF_USERS, p=date_probs)
    
    dataset_records = []
    
    # 5. Generation loop
    logger.info("Beginning generation loop...")
    for i in range(config.NUMBER_OF_USERS):
        user_id = f"usr_{i+1:07d}"
        reg_date = sampled_dates[i]
        
        # Single record generation with recovery retry logic
        valid = False
        retries = 0
        max_retries = 50
        record = {}
        
        while not valid and retries < max_retries:
            # Draw demographics
            demo = generate_demographics(config, rng)
            
            # Draw geography
            geo = generate_geography(rng, config)
            
            # Draw customer profile
            prof = generate_profile(demo["age"], demo["education_level"], config, rng)
            
            # Construct dictionary
            record = {
                "user_id": user_id,
                "gender": demo["gender"],
                "age": demo["age"],
                "education_level": demo["education_level"],
                "state": geo["state"],
                "city": geo["city"],
                "city_tier": geo["city_tier"],
                "occupation": prof["occupation"],
                "monthly_income": prof["monthly_income"],
                "cibil_score": prof["cibil_score"],
                "acquisition_channel": prof["acquisition_channel"],
                "device": prof["device"],
                "registration_date": str(reg_date)
            }
            
            valid = validate_record_integrity(record)
            if not valid:
                retries += 1
                
        if not valid:
            logger.error(f"Failed to generate a valid record for user_id {user_id} after {max_retries} retries.")
            raise RuntimeError(f"Generation failure at record index {i+1}")
            
        dataset_records.append(record)
        
        # Log progress every 10%
        if (i + 1) % (config.NUMBER_OF_USERS // 10) == 0:
            logger.info(f"Generated {i+1:,} / {config.NUMBER_OF_USERS:,} records...")

    # 6. Convert to Pandas DataFrame
    logger.info("Converting generated records to DataFrame...")
    df = pd.DataFrame(dataset_records)
    
    # Convert types for correct schema representation
    df["age"] = df["age"].astype(int)
    df["monthly_income"] = df["monthly_income"].astype(int)
    df["cibil_score"] = df["cibil_score"].astype(int)
    
    # 7. Dataset-level validation
    logger.info("Executing dataset-level validation and statistical checks...")
    validation_passed = validate_dataset_distributions(df, config)
    
    if not validation_passed:
        logger.error("Dataset-level validation failed to meet tolerance bounds. Halting export.")
        raise ValueError("Generated dataset does not match configuration criteria within tolerance.")

    # 8. Export dataset and summary report
    logger.info("Exporting dataset to CSV and generating QA summary report...")
    execution_time = time.time() - start_time
    export_dataset(df, config, execution_time)
    
    logger.info(f"InsightFlow synthetic data generation completed successfully in {execution_time:.2f} seconds.")

def main():
    parser = argparse.ArgumentParser(description="InsightFlow Users Synthetic Data Generation Engine")
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/settings.yaml", 
        help="Path to configuration settings YAML file"
    )
    args = parser.parse_args()
    
    try:
        generate_users_pipeline(args.config)
    except Exception as e:
        logger.exception(f"Pipeline execution halted due to error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
