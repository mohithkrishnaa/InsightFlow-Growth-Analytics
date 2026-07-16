-- =====================================================
-- InsightFlow Database Schema
-- =====================================================

CREATE TABLE users (
    user_id VARCHAR(20) PRIMARY KEY,
    gender VARCHAR(20) NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 18),
    education_level VARCHAR(50),
    state VARCHAR(100),
    city VARCHAR(100),
    city_tier VARCHAR(20),
    occupation VARCHAR(100),
    monthly_income NUMERIC(12,2),
    cibil_score INTEGER CHECK (cibil_score BETWEEN 300 AND 900),
    acquisition_channel VARCHAR(50),
    device VARCHAR(50),
    registration_date TIMESTAMP
);

CREATE TABLE marketing_events (
    event_id VARCHAR(30) PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    campaign VARCHAR(100),
    channel VARCHAR(50),
    ad_group VARCHAR(100),
    device VARCHAR(50),
    state VARCHAR(100),
    cost NUMERIC(10,2),
    timestamp TIMESTAMP,

    CONSTRAINT fk_marketing_user
        FOREIGN KEY(user_id)
        REFERENCES users(user_id)
);

CREATE TABLE app_events (
    event_id VARCHAR(30) PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    session_id VARCHAR(50),
    platform VARCHAR(50),
    event_name VARCHAR(100),
    timestamp TIMESTAMP,

    CONSTRAINT fk_app_user
        FOREIGN KEY(user_id)
        REFERENCES users(user_id)
);

CREATE TABLE loan_events (
    event_id VARCHAR(30) PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    loan_amount NUMERIC(12,2),
    approval_status VARCHAR(30),
    rejection_reason VARCHAR(255),
    interest_rate NUMERIC(5,2),
    timestamp TIMESTAMP,

    CONSTRAINT fk_loan_user
        FOREIGN KEY(user_id)
        REFERENCES users(user_id)
);

CREATE TABLE experiments (
    experiment_id VARCHAR(30),
    user_id VARCHAR(20),
    experiment_name VARCHAR(100),
    experiment_type VARCHAR(50),
    hypothesis TEXT,
    success_metric VARCHAR(100),
    variant VARCHAR(20),
    exposure_timestamp TIMESTAMP,
    converted BOOLEAN,
    conversion_event VARCHAR(100),
    conversion_timestamp TIMESTAMP,
    revenue_generated NUMERIC(12,2),
    device VARCHAR(50),
    city_tier VARCHAR(20),
    income_segment VARCHAR(20),
    experiment_status VARCHAR(20),
    statistical_significance VARCHAR(20),

    PRIMARY KEY(experiment_id, user_id),

    CONSTRAINT fk_experiment_user
        FOREIGN KEY(user_id)
        REFERENCES users(user_id)
);
