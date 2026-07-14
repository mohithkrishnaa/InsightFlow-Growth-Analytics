# Configuration Layer for InsightFlow Synthetic Data Generation Engine
"""
This module defines the configuration models and loader for the InsightFlow platform.
It uses Pydantic for validation and strict type checking of all generation distributions,
ranges, limits, and structures.
"""

import os
import logging
from typing import Dict, List
import yaml
from pydantic import BaseModel, Field, model_validator

# Setup local logger
logger = logging.getLogger("InsightFlowGenerator")

class DateRangeConfig(BaseModel):
    """Configuration model for temporal date boundaries."""
    START_DATE: str = Field(description="Start date of the generation window (format YYYY-MM-DD)")
    END_DATE: str = Field(description="End date of the generation window (format YYYY-MM-DD)")


class IncomeRangeConfig(BaseModel):
    """Configuration model for log-normal income generation variables by occupation."""
    median: int = Field(gt=0, description="Median monthly income in INR")
    sigma: float = Field(gt=0.0, description="Standard deviation in log-space")
    min: int = Field(ge=0, description="Minimum floor income value in INR")
    max: int = Field(gt=0, description="Maximum ceiling income value in INR")

    @model_validator(mode="after")
    def validate_bounds(self) -> "IncomeRangeConfig":
        """Asserts that min bounds are less than max bounds."""
        if self.min >= self.max:
            raise ValueError(f"min income ({self.min}) must be strictly less than max income ({self.max})")
        return self


class AppConfig(BaseModel):
    """
    Core application configuration model mapping all user profiles,
    distribution matrices, and logical mapping boundaries.
    """
    NUMBER_OF_USERS: int = Field(gt=0, description="Target volume size of the synthetic users dataset")
    RANDOM_SEED: int = Field(ge=0, description="Seed to ensure generation reproducibility")
    LOG_LEVEL: str = Field(default="INFO", description="Global logging verbosity")
    OUTPUT_FILE_PATH: str = Field(description="Target CSV file output location")
    REPORT_FILE_PATH: str = Field(description="Target Markdown summary report location")

    REGISTRATION_DATE_RANGE: DateRangeConfig = Field(description="Temporal window boundaries")
    STATE_DISTRIBUTION: Dict[str, float] = Field(description="Geographical region distribution weights")
    CITY_MAPPING: Dict[str, List[str]] = Field(description="State to city array lookup mapping")
    CITY_TIER_MAPPING: Dict[str, str] = Field(description="City to RBI cost-of-living Tier classification")

    OCCUPATION_DISTRIBUTION: Dict[str, float] = Field(description="Occupation segment distribution weights")
    EDUCATION_MAPPING: Dict[str, float] = Field(description="Education level distribution weights")
    GENDER_DISTRIBUTION: Dict[str, float] = Field(description="Gender segment distribution weights")
    AGE_DISTRIBUTION: Dict[str, float] = Field(description="Age band distribution weights")
    INCOME_RANGES: Dict[str, IncomeRangeConfig] = Field(description="Lognormal parameters by occupation class")
    CIBIL_DISTRIBUTION: Dict[str, float] = Field(description="Credit score segment distribution weights")
    DEVICE_DISTRIBUTION: Dict[str, float] = Field(description="Device hardware class distribution weights")
    ACQUISITION_CHANNEL_DISTRIBUTION: Dict[str, float] = Field(description="Marketing channel distribution weights")

    GROWTH_RATE: float = Field(ge=0.0, default=0.06, description="Compounding growth rate factor")
    VALIDATION_TOLERANCE: float = Field(gt=0.0, default=0.02, description="Allowed deviation fraction in QA validation")

    @model_validator(mode="after")
    def validate_probabilities(self) -> "AppConfig":
        """
        Validates that all probability distribution tables sum to exactly 1.0 (with small float margin).
        """
        distributions = [
            ("STATE_DISTRIBUTION", self.STATE_DISTRIBUTION),
            ("OCCUPATION_DISTRIBUTION", self.OCCUPATION_DISTRIBUTION),
            ("EDUCATION_MAPPING", self.EDUCATION_MAPPING),
            ("GENDER_DISTRIBUTION", self.GENDER_DISTRIBUTION),
            ("AGE_DISTRIBUTION", self.AGE_DISTRIBUTION),
            ("CIBIL_DISTRIBUTION", self.CIBIL_DISTRIBUTION),
            ("DEVICE_DISTRIBUTION", self.DEVICE_DISTRIBUTION),
            ("ACQUISITION_CHANNEL_DISTRIBUTION", self.ACQUISITION_CHANNEL_DISTRIBUTION)
        ]

        for name, dist in distributions:
            total = sum(dist.values())
            if not (0.9999 <= total <= 1.0001):
                raise ValueError(
                    f"Probability weights in '{name}' must sum to 1.0. Found: {total:.4f}"
                )
        return self

    @model_validator(mode="after")
    def validate_geography_mappings(self) -> "AppConfig":
        """
        Ensures that every state in STATE_DISTRIBUTION is defined in CITY_MAPPING,
        and every mapped city is classified in CITY_TIER_MAPPING.
        """
        # 1. State-City matching
        for state in self.STATE_DISTRIBUTION.keys():
            if state not in self.CITY_MAPPING:
                raise ValueError(f"State '{state}' has weights defined but is missing in CITY_MAPPING.")

        # 2. City-Tier matching
        for state, cities in self.CITY_MAPPING.items():
            for city in cities:
                if city not in self.CITY_TIER_MAPPING:
                    raise ValueError(f"City '{city}' in state '{state}' is missing in CITY_TIER_MAPPING.")
                
                tier = self.CITY_TIER_MAPPING[city]
                if tier not in ["Tier 1", "Tier 2", "Tier 3"]:
                    raise ValueError(f"City '{city}' has an invalid tier '{tier}'. Must be Tier 1, Tier 2, or Tier 3.")
        return self


def load_config(config_path: str = "config/settings.yaml") -> AppConfig:
    """
    Loads configuration parameters from a YAML file, parses and executes 
    schema and logical structural validations, and returns an AppConfig instance.
    
    Args:
        config_path (str): File path to settings YAML configuration.

    Returns:
        AppConfig: Validated application configuration model.
        
    Raises:
        FileNotFoundError: If the settings file is missing.
        ValidationError: If schema types or probability checksum checks fail.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    logger.info(f"Loading application configuration from {config_path}...")
    with open(config_path, "r", encoding="utf-8") as f:
        try:
            config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML file: {e}")
            raise e

    # Parse and validate using Pydantic AppConfig model
    return AppConfig(**config_data)
