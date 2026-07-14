# Constants and Static Parameters for the InsightFlow Data Generation Engine

# Geographic State-City-Tier Matrix with normalized absolute weights (summing to 1.0)
GEOGRAPHY_MATRIX = [
    # North Region (21.0%)
    {"state": "Delhi", "city": "New Delhi", "tier": "Tier 1", "weight": 0.06},
    {"state": "Uttar Pradesh", "city": "Noida", "tier": "Tier 2", "weight": 0.04},
    {"state": "Uttar Pradesh", "city": "Lucknow", "tier": "Tier 2", "weight": 0.03},
    {"state": "Uttar Pradesh", "city": "Kanpur", "tier": "Tier 2", "weight": 0.02},
    {"state": "Uttar Pradesh", "city": "Varanasi", "tier": "Tier 3", "weight": 0.02},
    {"state": "Punjab", "city": "Ludhiana", "tier": "Tier 2", "weight": 0.02},
    {"state": "Punjab", "city": "Amritsar", "tier": "Tier 2", "weight": 0.02},

    # South Region (33.0%)
    {"state": "Karnataka", "city": "Bangalore", "tier": "Tier 1", "weight": 0.10},
    {"state": "Karnataka", "city": "Mysore", "tier": "Tier 2", "weight": 0.02},
    {"state": "Karnataka", "city": "Hubli", "tier": "Tier 3", "weight": 0.01},
    {"state": "Tamil Nadu", "city": "Chennai", "tier": "Tier 1", "weight": 0.06},
    {"state": "Tamil Nadu", "city": "Coimbatore", "tier": "Tier 2", "weight": 0.03},
    {"state": "Tamil Nadu", "city": "Madurai", "tier": "Tier 3", "weight": 0.01},
    {"state": "Telangana", "city": "Hyderabad", "tier": "Tier 1", "weight": 0.06},
    {"state": "Telangana", "city": "Warangal", "tier": "Tier 3", "weight": 0.01},
    {"state": "Kerala", "city": "Kochi", "tier": "Tier 2", "weight": 0.02},
    {"state": "Kerala", "city": "Thiruvananthapuram", "tier": "Tier 2", "weight": 0.01},

    # West Region (27.0%)
    {"state": "Maharashtra", "city": "Mumbai", "tier": "Tier 1", "weight": 0.10},
    {"state": "Maharashtra", "city": "Pune", "tier": "Tier 1", "weight": 0.05},
    {"state": "Maharashtra", "city": "Nagpur", "tier": "Tier 2", "weight": 0.02},
    {"state": "Maharashtra", "city": "Nashik", "tier": "Tier 3", "weight": 0.02},
    {"state": "Gujarat", "city": "Ahmedabad", "tier": "Tier 1", "weight": 0.04},
    {"state": "Gujarat", "city": "Surat", "tier": "Tier 2", "weight": 0.02},
    {"state": "Gujarat", "city": "Rajkot", "tier": "Tier 3", "weight": 0.02},

    # East Region (9.0%)
    {"state": "West Bengal", "city": "Kolkata", "tier": "Tier 1", "weight": 0.05},
    {"state": "West Bengal", "city": "Siliguri", "tier": "Tier 3", "weight": 0.01},
    {"state": "Odisha", "city": "Bhubaneswar", "tier": "Tier 2", "weight": 0.02},
    {"state": "Odisha", "city": "Cuttack", "tier": "Tier 3", "weight": 0.01},

    # Central Region (7.0%)
    {"state": "Madhya Pradesh", "city": "Indore", "tier": "Tier 2", "weight": 0.03},
    {"state": "Madhya Pradesh", "city": "Bhopal", "tier": "Tier 2", "weight": 0.03},
    {"state": "Madhya Pradesh", "city": "Gwalior", "tier": "Tier 3", "weight": 0.01},

    # North-East Region (3.0%)
    {"state": "Assam", "city": "Guwahati", "tier": "Tier 2", "weight": 0.02},
    {"state": "Assam", "city": "Silchar", "tier": "Tier 3", "weight": 0.01}
]

# Occupation-based income parameters: median, sigma, min, max
# Sampled via lognormal distribution: exp(N(mu, sigma^2)) where mu = ln(median)
INCOME_PARAMETERS = {
    "Salaried": {
        "median": 42000,
        "sigma": 0.40,
        "min": 18000,
        "max": 250000
    },
    "Self-Employed": {
        "median": 45000,
        "sigma": 0.55,
        "min": 15000,
        "max": 400000
    },
    "Professional": {
        "median": 80000,
        "sigma": 0.45,
        "min": 35000,
        "max": 500000
    },
    "Retired": {
        "median": 25000,
        "sigma": 0.35,
        "min": 12000,
        "max": 80000
    },
    "Student": {
        "median": 3000,
        "sigma": 0.60,
        "min": 0,
        "max": 15000
    }
}
