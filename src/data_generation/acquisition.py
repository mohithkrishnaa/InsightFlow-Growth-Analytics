# Acquisition Channel and Device Generator Module for the InsightFlow Data Generation Pipeline

import numpy as np
from typing import Dict, Any
from src.data_generation.config import GeneratorConfig

def generate_device(
    monthly_income: int, 
    config: GeneratorConfig, 
    rng: np.random.Generator
) -> str:
    """
    Selects device OS class based on configured device weights and income level correlations.
    """
    devices = list(config.DEVICE_DISTRIBUTION.keys())
    
    # Apply income-based skews:
    if monthly_income >= 150000:
        # High Income: skew toward iOS and macOS
        weights = [0.35, 0.45, 0.05, 0.15]  # Android, iOS, Windows, macOS
    elif monthly_income < 40000:
        # Low Income: skew heavily toward Android
        weights = [0.95, 0.04, 0.01, 0.00]
    else:
        # Standard mid-income profile
        weights = [0.85, 0.10, 0.04, 0.01]

    # Re-normalize to make sure weights sum to 1.0 (some devices might not map directly to enums in config)
    sum_w = sum(weights)
    final_weights = [w / sum_w for w in weights]

    return str(rng.choice(devices, p=final_weights))

def generate_acquisition_channel(
    age: int,
    monthly_income: int,
    cibil_score: int,
    config: GeneratorConfig,
    rng: np.random.Generator
) -> str:
    """
    Selects an acquisition marketing channel, skewed by age, income, and credit scores.
    """
    channels = list(config.CHANNEL_DISTRIBUTION.keys())
    channel_weights = dict(config.CHANNEL_DISTRIBUTION)

    # Apply skews based on user demographic and risk characteristics:
    # 1. Income skews
    if monthly_income >= 100000:
        channel_weights["Google Ads"] *= 1.3
        channel_weights["Organic"] *= 1.2
        channel_weights["Affiliate"] *= 0.5
    elif monthly_income < 30000:
        channel_weights["Affiliate"] *= 1.3
        channel_weights["Meta Ads"] *= 1.2

    # 2. Age skews
    if age < 30:
        channel_weights["Meta Ads"] *= 1.3
        channel_weights["Organic"] *= 0.7

    # 3. Credit score skews
    if cibil_score != -1:
        if cibil_score < 600:  # Subprime
            channel_weights["Affiliate"] *= 1.5
            channel_weights["Organic"] *= 0.3
            channel_weights["Google Ads"] *= 0.8
        elif cibil_score >= 750:  # Excellent
            channel_weights["Organic"] *= 1.5
            channel_weights["Google Ads"] *= 1.2
            channel_weights["Affiliate"] *= 0.4

    # Re-normalize weights
    total_weight = sum(channel_weights.values())
    if total_weight > 0:
        final_weights = [w / total_weight for w in channel_weights.values()]
    else:
        final_weights = list(config.CHANNEL_DISTRIBUTION.values())

    return str(rng.choice(channels, p=final_weights))
