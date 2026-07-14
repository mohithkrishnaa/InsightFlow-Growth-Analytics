# Design Review & Architecture Specification: InsightFlow Synthetic Data Generation Engine

This document outlines the final design, architecture, and validation strategy for the `users` dataset synthetic data generation engine of the InsightFlow analytics platform.

---

## PART 1 — Final Design Decisions

### 1. Geographic Scope
To represent a nationwide fintech user base in India, the geographic scope is expanded to 13 states across 6 major regions, containing 30 cities with strict RBI Tier classifications. 

The probability weights below represent the overall absolute distribution weight of the user base (summing to exactly 100%):

*   **North Region (21.0% overall)**
    *   **Delhi**: New Delhi (`Tier 1` - 6.0%)
    - **Uttar Pradesh**: Lucknow (`Tier 2` - 3.0%), Kanpur (`Tier 2` - 2.0%), Varanasi (`Tier 3` - 2.0%), Noida (`Tier 2` - 4.0%)
    - **Punjab**: Ludhiana (`Tier 2` - 2.0%), Amritsar (`Tier 2` - 2.0%)
*   **South Region (33.0% overall)**
    - **Karnataka**: Bangalore (`Tier 1` - 10.0%), Mysore (`Tier 2` - 2.0%), Hubli (`Tier 3` - 1.0%)
    - **Kerala**: Kochi (`Tier 2` - 2.0%), Thiruvananthapuram (`Tier 2` - 1.0%)
    - **Tamil Nadu**: Chennai (`Tier 1` - 6.0%), Coimbatore (`Tier 2` - 3.0%), Madurai (`Tier 3` - 1.0%)
    - **Telangana**: Hyderabad (`Tier 1` - 6.0%), Warangal (`Tier 3` - 1.0%)
*   **West Region (27.0% overall)**
    - **Maharashtra**: Mumbai (`Tier 1` - 10.0%), Pune (`Tier 1` - 5.0%), Nagpur (`Tier 2` - 2.0%), Nashik (`Tier 3` - 2.0%)
    - **Gujarat**: Ahmedabad (`Tier 1` - 4.0%), Surat (`Tier 2` - 2.0%), Rajkot (`Tier 3` - 2.0%)
*   **East Region (9.0% overall)**
    - **West Bengal**: Kolkata (`Tier 1` - 5.0%), Siliguri (`Tier 3` - 1.0%)
    - **Odisha**: Bhubaneswar (`Tier 2` - 2.0%), Cuttack (`Tier 3` - 1.0%)
*   **Central Region (7.0% overall)**
    - **Madhya Pradesh**: Indore (`Tier 2` - 3.0%), Bhopal (`Tier 2` - 3.0%), Gwalior (`Tier 3` - 1.0%)
*   **North-East Region (3.0% overall)**
    - **Assam**: Guwahati (`Tier 2` - 2.0%), Silchar (`Tier 3` - 1.0%)

### 2. CIBIL Distribution & Correlations
The baseline CIBIL score distribution is adjusted to follow the credit profile segments below:
- **New to Credit (NTC)**: 12.0% (CIBIL score = `-1`)
- **Poor** (300–549): 8.0%
- **Fair** (550–649): 20.0%
- **Good** (650–749): 40.0%
- **Excellent** (750–900): 20.0%

#### Correlative Drivers:
1.  **Income & Occupation Influence**: 
    - *Professionals* and *Salaried* individuals with higher monthly incomes are assigned a higher probability of Good/Excellent scores.
    - *Self-Employed* profiles follow a higher variance distribution (stretching from Poor to Excellent).
2.  **Age Influence**: 
    - Age exerts a mild positive shift. Users older than 35 have an increased probability of shifting up one tier (e.g., from Fair to Good), representing longer credit histories.
3.  **NTC Constraints**: 
    - Users under 22 years of age or classified as *Student* have an 80% probability of being NTC (`-1`).

### 3. Additional Attributes
- **Included Column**: `education_level` (VARCHAR)
  - *Categories*: `High School`, `Undergraduate`, `Graduate`, `Postgraduate`, `Doctorate`.
  - *Business Justification*: Influences occupation selection (e.g., a Doctorate or Postgraduate is highly unlikely to have a blank profile or work in manual trades, skews towards `Professional` or `Salaried`), establishes monthly income ranges, and serves as an auxiliary feature in credit scorecard underwriting.
- **Excluded Columns**: `marital_status`, `app_version`, `device_os_version`, and `network_type` are excluded, as they belong to transactional tracking logs or application lifecycle events.

---

## PART 2 — Design the Data Generation Engine

The generation engine in `generate_users.py` will be structured in a modular, functional pattern adhering to clean coding standards.

### 1. Configuration Layer
*   **Function Name**: `load_config`
    - **Purpose**: Load, parse, and validate JSON/YAML configuration settings containing distributions and volumes.
    - **Inputs**: `config_path: str`
    - **Outputs**: `config: dict`
    - **Dependencies**: `pyyaml` (or standard `json`), `pydantic`
    - **Validation**: Schema verification to ensure all required weights and ranges are defined and sum to 1.0.
    - **Possible Errors**: `FileNotFoundError`, `ValidationError` (schema mismatch), `ValueError` (invalid probability sums).

### 2. Utility Functions
*   **Function Name**: `initialize_generators`
    - **Purpose**: Instantiate Faker and set global seeds for reproducible data generation.
    - **Inputs**: `seed: int`
    - **Outputs**: `tuple[Faker, numpy.random.Generator]`
    - **Dependencies**: `faker`, `numpy`
    - **Validation**: Ensure seed is a non-negative integer.
    - **Possible Errors**: `TypeError` (invalid seed type).

### 3. Generators (Core Engine)
*   **Function Name**: `generate_demographics`
    - **Purpose**: Generate age, gender, and education level for a user.
    - **Inputs**: `faker_inst: Faker`, `config: dict`
    - **Outputs**: `dict` (containing `gender`, `age`, `education_level`)
    - **Dependencies**: `faker`, `numpy.random`
    - **Validation**: $18 \le \text{age} \le 65$.
    - **Possible Errors**: None.

*   **Function Name**: `generate_employment_and_income`
    - **Purpose**: Generate occupation and monthly income aligned with age and education.
    - **Inputs**: `age: int`, `education: str`, `config: dict`, `rng: numpy.random.Generator`
    - **Outputs**: `tuple[str, int]` (containing `occupation`, `monthly_income`)
    - **Dependencies**: `numpy.random`
    - **Validation**: Students must not exceed INR 25,000; monthly income must be non-negative.
    - **Possible Errors**: `ValueError` (invalid age/education range combinations).

*   **Function Name**: `generate_geography`
    - **Purpose**: Select state, city, and city tier using weighted probabilities.
    - **Inputs**: `config: dict`, `rng: numpy.random.Generator`
    - **Outputs**: `tuple[str, str, str]` (containing `state`, `city`, `city_tier`)
    - **Dependencies**: `numpy.random`
    - **Validation**: Selected city must belong to the selected state; tier must match the city.
    - **Possible Errors**: `KeyError` (missing geography configurations).

*   **Function Name**: `generate_credit_profile`
    - **Purpose**: Generate CIBIL score matching baseline weights, influenced by age, occupation, and income.
    - **Inputs**: `age: int`, `occupation: str`, `income: int`, `config: dict`, `rng: numpy.random.Generator`
    - **Outputs**: `int` (CIBIL score between 300 and 900, or -1)
    - **Dependencies**: `numpy.random`
    - **Validation**: Assert CIBIL is in range $[300, 900] \cup \{-1\}$.
    - **Possible Errors**: None.

*   **Function Name**: `generate_metadata`
    - **Purpose**: Generate acquisition channel, device type, and registration date with seasonal skews.
    - **Inputs**: `income: int`, `cibil: int`, `config: dict`, `rng: numpy.random.Generator`
    - **Outputs**: `dict` (containing `acquisition_channel`, `device`, `registration_date`)
    - **Dependencies**: `numpy.random`, `datetime`
    - **Validation**: Ensure dates fall strictly within bounds; device mapping matches income guidelines.
    - **Possible Errors**: None.

*   **Function Name**: `generate_single_record`
    - **Purpose**: orchestrate generation of all components for a single user record.
    - **Inputs**: `user_id: str`, `faker_inst: Faker`, `config: dict`, `rng: numpy.random.Generator`
    - **Outputs**: `dict` (complete user record map)
    - **Dependencies**: `generate_demographics`, `generate_employment_and_income`, `generate_geography`, `generate_credit_profile`, `generate_metadata`
    - **Validation**: Ensure output dictionary schema keys are complete.
    - **Possible Errors**: None.

### 4. Validators
*   **Function Name**: `validate_record_integrity`
    - **Purpose**: Validate single record business rules.
    - **Inputs**: `record: dict`
    - **Outputs**: `bool`
    - **Dependencies**: None
    - **Validation**: Logical consistency check (e.g., student income limit, city-state mapping).
    - **Possible Errors**: None (returns `False` if validation fails).

*   **Function Name**: `validate_dataset_distributions`
    - **Purpose**: Check aggregate dataset metrics against configurations (e.g., actual vs expected distributions).
    - **Inputs**: `df: pandas.DataFrame`, `config: dict`
    - **Outputs**: `dict` (status flags and deviation metrics)
    - **Dependencies**: `pandas`, `scipy.stats`
    - **Validation**: Performs statistical checks (e.g. Chi-Square goodness-of-fit) on distributions.
    - **Possible Errors**: `ValueError` (empty dataset).

### 5. Export Layer
*   **Function Name**: `export_dataset`
    - **Purpose**: Save the generated data to a CSV file and output a statistical quality report.
    - **Inputs**: `df: pandas.DataFrame`, `output_path: str`, `report_path: str`
    - **Outputs**: `None`
    - **Dependencies**: `pandas`
    - **Validation**: Confirms file write permissions and directory existence.
    - **Possible Errors**: `IOError`, `PermissionError`.

---

## PART 3 — Algorithm Design

Below is the structured pseudocode for the primary generation engine.

```python
"""
ALGORITHM: generate_users_dataset
INPUT: config_path (string)
OUTPUT: Raw CSV file and summary statistics report
"""

Start
    # Step 1: Load Configuration
    # WHY: Configuration centralizes environment values, weights, and rules, preventing hardcoding.
    config = load_config(config_path)
    
    # Step 2: Set Seed & Setup Logging
    # WHY: Seed guarantees output reproducibility across runs; logging provides execution monitoring.
    setup_logging(config.LOG_LEVEL)
    rng, faker_inst = initialize_generators(config.SEED)
    
    # Initialize empty memory buffer
    dataset_records = []
    
    # Step 3: Run Main Generation Loop
    # WHY: Iterate user-by-user to populate target volume (e.g., 100,000).
    For index = 1 To config.NUMBER_OF_USERS:
        # Step 3a: Generate Unique PK
        # WHY: Downstream tables join on user_id; format must be standardized (usr_XXXXXXX).
        user_id = f"usr_{index:07d}"
        
        # Step 3b: Generate Basic Demographics
        # WHY: Gender, age, and education are baseline variables that drive downstream logic.
        gender = rng.choice(config.GENDERS, p=config.GENDER_WEIGHTS)
        age = rng.integers(18, 65, endpoint=True)
        education_level = rng.choice(config.EDUCATION_LEVELS, p=config.EDUCATION_WEIGHTS)
        
        # Step 3c: Generate Occupation (Dependent on Age and Education)
        # WHY: A Doctorate or Graduate profile should skew away from 'Student' or lower-paid categories.
        occupation_weights = calculate_occupation_weights(age, education_level, config)
        occupation = rng.choice(config.OCCUPATIONS, p=occupation_weights)
        
        # Step 3d: Generate Income (Log-normal distribution dependent on Occupation & Education)
        # WHY: income depends on professional level. We scale log-normal values using occupation-specific params.
        income_params = config.INCOME_PARAMS[occupation]
        # Adjust income parameters upward if education level is high (Graduate, PG, Doctorate)
        adjusted_median = scale_income_by_education(income_params.median, education_level)
        monthly_income = sample_log_normal(adjusted_median, income_params.variance, rng)
        
        # Clip student income to maximum INR 25,000
        If occupation == "Student" And monthly_income > 25000:
            monthly_income = rng.integers(5000, 25000)
            
        # Step 3e: Generate Geographic Attributes
        # WHY: Geographic attributes are mapped using single-draw weighted probability from State-City matrix.
        state, city, city_tier = select_geography(config.GEOGRAPHY_PROBABILITIES, rng)
        
        # Step 3f: Generate CIBIL Score (Dependent on Age, Occupation, Income)
        # WHY: In reality, income and age heavily correlate with credit risk and history availability.
        cibil_score = calculate_cibil_score(age, occupation, monthly_income, config, rng)
        
        # Step 3g: Assign Device Class (Skewed by Income)
        # WHY: Higher income tiers have a significantly higher rate of iOS device usage.
        device = select_device_class(monthly_income, config, rng)
        
        # Step 3h: Assign Acquisition Channel
        # WHY: Marketing channels have different cost, demographic, and credit score biases.
        acquisition_channel = select_acquisition_channel(monthly_income, cibil_score, config, rng)
        
        # Step 3i: Generate Registration Date (Incorporating growth and day-of-week seasonality)
        # WHY: Simulates compounding growth and weekend transaction drops observed in production apps.
        registration_date = sample_registration_date(config.START_DATE, config.END_DATE, config.GROWTH_RATE, rng)
        
        # Step 3j: Construct Record Dict
        record = {
            "user_id": user_id,
            "gender": gender,
            "age": age,
            "education_level": education_level,
            "state": state,
            "city": city,
            "city_tier": city_tier,
            "occupation": occupation,
            "monthly_income": monthly_income,
            "cibil_score": cibil_score,
            "acquisition_channel": acquisition_channel,
            "device": device,
            "registration_date": registration_date
        }
        
        # Step 3k: Record-Level Validation
        # WHY: Prevents corrupted or invalid records from entering the output dataset.
        If validate_record_integrity(record):
            dataset_records.append(record)
        Else:
            log_warning(f"Record {user_id} failed integrity constraints. Regenerating.")
            index = index - 1 # Retry generation for this slot
            
    # Step 4: Convert Buffer to DataFrame
    # WHY: Facilitates vector operations, statistical validations, and file exporting.
    df = convert_to_dataframe(dataset_records)
    
    # Step 5: Dataset-Level Validation
    # WHY: Validates aggregate statistics and checks if actual distributions match target weights.
    validation_passed = validate_dataset_distributions(df, config)
    
    # Step 6: Export Data & Write Quality Report
    # WHY: Formats output for consumer systems and provides transparency into the synthetic data quality.
    If validation_passed:
        export_dataset(df, config.OUTPUT_FILE_PATH, config.REPORT_FILE_PATH)
        log_info("Pipeline completed successfully. Dataset generated and validated.")
    Else:
        log_error("Dataset-level validation failed to meet tolerance bounds.")
        Raise ExecutionError("Validation failed.")
        
End
```

---

## PART 4 — Software Architecture

For production scalability, the pipeline is organized in a modular structure:

```
insightflow/
│
├── config/
│   ├── settings.yaml          # Configurable parameters, parameters and probability weights
│   └── __init__.py
│
├── src/
│   ├── data_generation/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration loader and parser using Pydantic
│   │   ├── constants.py       # Global enums and static lookup schemas
│   │   ├── demographics.py    # Logic for generating age, gender, education
│   │   ├── geography.py       # State, City, RBI Tier mapping logic
│   │   ├── finance.py         # Occupation, Log-Normal Income, CIBIL generators
│   │   ├── acquisition.py     # Channel and device assignment logic
│   │   ├── validators.py      # Quality assurance validations (rules, chi-square)
│   │   ├── exporter.py        # CSV export and HTML/Markdown summary reporting
│   │   ├── logging_config.py  # Centralized application logging configurations
│   │   └── generate_users.py  # Main pipeline orchestration entrypoint
│   │
│   └── __init__.py
│
├── tests/
│   ├── __init__.py
│   ├── test_demographics.py   # Unit tests for age/education distributions
│   ├── test_geography.py      # Unit tests for city-state mapping accuracy
│   ├── test_finance.py        # Unit tests for lognormal income constraints
│   ├── test_validators.py     # Unit tests for dataset validation functions
│   └── test_integration.py    # E2E pipeline checks
│
├── data/
│   └── raw/                   # Output folder for generated CSV files
│
├── logs/
│   └── pipeline.log           # Output log file location
│
├── requirements.txt           # Environment dependencies
├── README.md                  # Project overview and run commands
└── pytest.ini                 # Pytest configuration settings
```

---

## PART 5 — Configuration Design

All primary rules, distributions, and limits will be dynamic. The table below outlines the core configurable items and the business rationale for their flexibility:

| Parameter | Configuration Scope | Business Rationale for Configurability |
| :--- | :--- | :--- |
| `NUMBER_OF_USERS` | Integer (e.g. `100000`) | Enables quick local testing at lower volumes (e.g. `1,000`) and high-volume load testing (e.g. `1,000,000`). |
| `SEED` | Integer (e.g. `42`) | Ensures reproducibility across environments; changing it allows generating alternate runs of synthetic users. |
| `STATE_DISTRIBUTION` | Map of floats | Allows modeling shifts in target markets (e.g., expanding South region weight or focusing strictly on West region). |
| `CITY_MAPPING` | Map of strings to lists | Supports updates to RBI city classifications and allows adding/removing cities without code modifications. |
| `OCCUPATION_MAPPING` | Map of strings to floats | Enables simulating shifts in the employment market (e.g., rising Gig economy / self-employed shares). |
| `INCOME_RANGES` | Map of structs | Facilitates income adjustments due to inflation or scaling up target borrower segments (e.g. premium segment). |
| `CIBIL_DISTRIBUTION` | Map of floats | Simulates shifts in credit risk appetite (e.g., tightening rules to generate more prime/super-prime profiles). |
| `DEVICE_DISTRIBUTION` | Map of floats | Allows adaptation to changing mobile OS market shares over time. |
| `CHANNEL_DISTRIBUTION` | Map of floats | Simulates varying marketing spend allocations across channels (e.g., pausing affiliate acquisition). |
| `DATE_RANGE` | Dates (Start, End) | Allows shifting the simulation time-window (e.g., simulating a historic year vs. next year's forecast). |
| `VALIDATION_TOLERANCE` | Float (e.g. `0.02`) | Adjusts acceptable percentage deviations for actual vs configured distribution weights during QA checks. |

---

## PART 6 — Validation Strategy

The validation layer will act as a gatekeeper, testing every generated record against specific criteria.

### Validation Checklist

- [ ] **Uniqueness Constraints**: The column `user_id` contains zero duplicate entries.
- [ ] **Completeness Checks**: Every column across all rows contains zero null, empty, or `NaN` values.
- [ ] **Geographic Integrity**:
  - `city` maps to the correct parent `state` in the lookup table.
  - `city_tier` maps correctly to the RBI list for that specific `city`.
- [ ] **Employment & Income Consistency**:
  - Users with `occupation` == `Student` have `monthly_income` $\le$ INR 25,000.
  - Users with `occupation` == `Retired` have `monthly_income` $\le$ INR 80,000.
  - Users with `monthly_income` == 0 are strictly limited to `Student` or `Retired`.
- [ ] **Education & Age Alignment**:
  - Users with `education_level` in `['Postgraduate', 'Doctorate']` have an `age` $\ge 22$.
  - Users under 21 cannot have an `education_level` of `Doctorate`.
- [ ] **Credit Risk Limits**:
  - `cibil_score` falls strictly in $[300, 900] \cup \{-1\}$.
  - Users under 22 or with `occupation` == `Student` have a CIBIL score of `-1` in at least 80% of samples.
- [ ] **OS Device Allocation Alignment**:
  - Users with `device` in `['Mobile-iOS', 'Desktop-MacOS']` have a positive correlation with monthly incomes $\ge$ INR 100,000.
- [ ] **Temporal Accuracy**:
  - `registration_date` falls strictly within the interval `[2025-07-01, 2026-06-30]`.
- [ ] **Statistical Distribution Chi-Square Test**:
  - The generated distributions for `gender`, `state`, `cibil_score` tiers, `acquisition_channel`, and `device` must match configured weights within a 2.0% tolerance margin.

---

## PART 7 — Testing Strategy

Before shipping the generation engine to production, we will run automated tests to verify stability, logic, and scalability.

### Testing Checklist

- [ ] **Unit Tests**:
  - Verify `load_config` handles invalid JSON/YAML and schema anomalies.
  - Verify `initialize_generators` correctly binds the random state and reproduces matching records under identical seeds.
  - Test individual generator functions with edge case inputs (e.g., testing `generate_employment_and_income` with boundary ages like 18 and 65).
- [ ] **Integration Tests**:
  - Run the entire E2E generation pipeline on a test limit of `1,000` records and verify output files are created successfully in `data/raw/`.
- [ ] **Null and Data Type Verification**:
  - Check that pandas DataFrame schema types match the database definitions (`int64`, `object`/`string`, `datetime64[ns]`).
  - Validate that `df.isnull().sum().sum()` returns exactly 0.
- [ ] **Distribution and Statistical Testing**:
  - Assert that a Chi-Square goodness-of-fit test passes for the generated CIBIL tiers and Geographic state weights against configurations ($\alpha = 0.05$).
- [ ] **Performance Testing**:
  - Execute a benchmark run for `100,000` records. Target threshold: execution time under 30 seconds, memory footprint under 500MB.

---

## PART 8 — Industry Best Practices

To deliver an enterprise-grade Analytics Engineering tool, we incorporate several software engineering standards:

1.  **Config-Driven Architecture**: Hardcoded defaults are prohibited. System behavior is modified by updating `settings.yaml`.
2.  **Reproducibility via Random State Propagation**: Instead of using global random states (e.g. `numpy.random.seed`), we instantiate independent generator objects (`numpy.random.Generator`) and pass them explicitly to generators to support clean multiprocessing.
3.  **Type Hinting & Schemas**: All functions implement Python PEP 484 type annotations. Config files are read and parsed using `pydantic` schemas for immediate runtime errors on configuration mistakes.
4.  **Vectorized Operations**: Where possible, we utilize NumPy and Pandas operations rather than slow row-by-row loops, keeping the platform performant up to millions of records.
5.  **Robust Logging**: Log files capture warning and error events with timestamps, module names, and error stack traces.

---

## PART 9 — Readiness Review

### Is this design ready for implementation?
**YES.** The design is fully specified, the dependencies are defined in `requirements.txt`, the database schemas are aligned, and the business rules reflect realistic market patterns.

#### Next Steps to Begin Development:
1.  Initialize the production directory structure.
2.  Write the `config/settings.yaml` configuration parameters based on the final design weights.
3.  Implement the configuration loader and validation code in `src/data_generation/config.py`.
4.  Implement the generator modules sequentially.
5.  Write unit and integration tests under `tests/` and run `pytest`.
