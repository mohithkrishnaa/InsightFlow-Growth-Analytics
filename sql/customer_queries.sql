-- ============================================================================
-- InsightFlow Customer Portfolio Analytics Queries
-- ============================================================================
-- This file contains production-ready PostgreSQL 17 optimized queries designed
-- to analyze customer demographics, credit scores, occupations, geographies, 
-- and device performance metrics.
--
-- The queries leverage indexes (e.g. idx_users_state, idx_app_user, idx_loan_user)
-- to ensure optimal execution performance over large datasets.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- Query 1: Customer Demographic Overview (Baseline Counts & Averages)
-- ----------------------------------------------------------------------------
-- Business Objective: Summarize baseline customer volumes, average ages, and 
-- average monthly incomes, split by gender to inspect product coverage.
-- BI Dashboard Widget: Portfolio Demographics Summary Grid.
-- ----------------------------------------------------------------------------
SELECT 
    gender,
    COUNT(DISTINCT user_id) as total_users,
    ROUND(COUNT(DISTINCT user_id)::numeric / SUM(COUNT(DISTINCT user_id)) OVER () * 100, 2) as gender_pct,
    ROUND(AVG(age), 1) as average_age,
    ROUND(AVG(monthly_income), 2) as average_monthly_income
FROM users
GROUP BY gender
ORDER BY total_users DESC;


-- ----------------------------------------------------------------------------
-- Query 2: Age Group Performance Analysis (User Volume and Conversion)
-- ----------------------------------------------------------------------------
-- Business Objective: Segment the registered user base into distinct age groups
-- to compare product interest (loan application rate) and credit quality (approval).
-- BI Dashboard Widget: Age Segment Conversion pipeline bar-chart.
-- ----------------------------------------------------------------------------
WITH age_groups AS (
    SELECT 
        user_id,
        CASE 
            WHEN age < 25 THEN '18-24'
            WHEN age < 35 THEN '25-34'
            WHEN age < 50 THEN '35-49'
            ELSE '50+'
        END AS age_bracket
    FROM users
),
age_metrics AS (
    SELECT 
        ag.age_bracket,
        COUNT(DISTINCT u.user_id) as total_signups,
        COUNT(DISTINCT CASE WHEN ae.event_name = 'Loan Apply' THEN u.user_id END) as loan_applies,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Approved' THEN u.user_id END) as approved_loans,
        AVG(CASE WHEN le.approval_status = 'Approved' THEN le.loan_amount END) as avg_approved_loan_amount
    FROM age_groups ag
    JOIN users u ON ag.user_id = u.user_id
    LEFT JOIN app_events ae ON u.user_id = ae.user_id
    LEFT JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY ag.age_bracket
)
SELECT 
    age_bracket,
    total_signups,
    loan_applies,
    ROUND((loan_applies::numeric / total_signups) * 100, 2) as signup_to_apply_rate_pct,
    approved_loans,
    ROUND((approved_loans::numeric / NULLIF(loan_applies, 0)) * 100, 2) as approval_rate_pct,
    ROUND(avg_approved_loan_amount, 2) as average_approved_loan_amount
FROM age_metrics
ORDER BY age_bracket;


-- ----------------------------------------------------------------------------
-- Query 3: Monthly Income vs. Loan Approval Behavior
-- ----------------------------------------------------------------------------
-- Business Objective: Bucket customers by monthly income to track app conversion, 
-- average requested/approved loan amounts, and underwriting approval rates.
-- BI Dashboard Widget: Income Segment Underwriting Performance grid/chart.
-- ----------------------------------------------------------------------------
WITH income_brackets AS (
    SELECT 
        u.user_id,
        u.monthly_income,
        CASE 
            WHEN u.monthly_income < 20000 THEN '1. Under 20k'
            WHEN u.monthly_income < 40000 THEN '2. 20k-40k'
            WHEN u.monthly_income < 75000 THEN '3. 40k-75k'
            WHEN u.monthly_income < 120000 THEN '4. 75k-120k'
            ELSE '5. 120k+'
        END AS income_tier
    FROM users u
),
income_metrics AS (
    SELECT 
        ib.income_tier,
        COUNT(DISTINCT ib.user_id) as signed_up_users,
        COUNT(DISTINCT le.user_id) as loan_applicants,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Approved' THEN le.user_id END) as approved_applicants,
        AVG(CASE WHEN le.approval_status = 'Approved' THEN le.loan_amount END) as avg_loan_amount,
        AVG(CASE WHEN le.approval_status = 'Approved' THEN le.interest_rate END) as avg_interest_rate
    FROM income_brackets ib
    LEFT JOIN loan_events le ON ib.user_id = le.user_id
    GROUP BY ib.income_tier
)
SELECT 
    income_tier,
    signed_up_users,
    loan_applicants,
    ROUND((loan_applicants::numeric / signed_up_users) * 100, 2) as applicant_penetration_rate_pct,
    approved_applicants,
    ROUND((approved_applicants::numeric / NULLIF(loan_applicants, 0)) * 100, 2) as approval_rate_pct,
    ROUND(avg_loan_amount, 2) as average_loan_amount,
    ROUND(avg_interest_rate, 2) as average_interest_rate
FROM income_metrics
ORDER BY income_tier;


-- ----------------------------------------------------------------------------
-- Query 4: CIBIL Score Brackets vs. Underwriting Approvals
-- ----------------------------------------------------------------------------
-- Business Objective: Determine underwriting approval rates and average interest 
-- rates charged across credit risk score tiers (including NTC users).
-- BI Dashboard Widget: Underwriting Risk Tier approval matrix.
-- ----------------------------------------------------------------------------
WITH credit_brackets AS (
    SELECT 
        u.user_id,
        u.cibil_score,
        u.has_credit_history,
        CASE 
            WHEN NOT u.has_credit_history OR u.cibil_score IS NULL THEN 'New to Credit (NTC)'
            WHEN u.cibil_score < 550 THEN 'Poor (<550)'
            WHEN u.cibil_score < 650 THEN 'Fair (550-649)'
            WHEN u.cibil_score < 750 THEN 'Good (650-749)'
            ELSE 'Excellent (750+)'
        END AS credit_segment
    FROM users u
),
credit_metrics AS (
    SELECT 
        cb.credit_segment,
        COUNT(DISTINCT le.user_id) as applicants,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Approved' THEN le.user_id END) as approved_users,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN le.user_id END) as disbursed_users,
        AVG(CASE WHEN le.approval_status = 'Approved' THEN le.loan_amount END) as avg_loan_amount,
        AVG(CASE WHEN le.approval_status = 'Approved' THEN le.interest_rate END) as avg_interest_rate
    FROM credit_brackets cb
    JOIN loan_events le ON cb.user_id = le.user_id
    GROUP BY cb.credit_segment
)
SELECT 
    credit_segment,
    applicants,
    approved_users,
    ROUND((approved_users::numeric / NULLIF(applicants, 0)) * 100, 2) as approval_rate_pct,
    disbursed_users,
    ROUND((disbursed_users::numeric / NULLIF(approved_users, 0)) * 100, 2) as disbursement_rate_pct,
    ROUND(avg_loan_amount, 2) as average_loan_amount,
    ROUND(avg_interest_rate, 2) as average_interest_rate
FROM credit_metrics
ORDER BY approval_rate_pct DESC;


-- ----------------------------------------------------------------------------
-- Query 5: State-wise Customer Portfolio Performance
-- ----------------------------------------------------------------------------
-- Business Objective: Compare loan customer penetration, average income, and total
-- disbursed capital across states to identify high-performing regional markets.
-- BI Dashboard Widget: Geographic choropleth map.
-- ----------------------------------------------------------------------------
WITH state_metrics AS (
    SELECT 
        u.state,
        COUNT(DISTINCT u.user_id) as total_customers,
        AVG(u.monthly_income) as avg_income,
        COUNT(DISTINCT le.user_id) as loan_applicants,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN le.user_id END) as disbursed_customers,
        SUM(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount ELSE 0 END) as total_disbursed_capital,
        AVG(CASE WHEN le.approval_status = 'Disbursed' THEN le.interest_rate END) as avg_interest_rate
    FROM users u
    LEFT JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY u.state
)
SELECT 
    state,
    total_customers,
    ROUND(avg_income, 2) as average_income,
    disbursed_customers,
    ROUND((disbursed_customers::numeric / NULLIF(loan_applicants, 0)) * 100, 2) as applicant_to_disbursed_rate_pct,
    total_disbursed_capital,
    ROUND(avg_interest_rate, 2) as average_interest_rate
FROM state_metrics
WHERE state IS NOT NULL
ORDER BY total_disbursed_capital DESC;


-- ----------------------------------------------------------------------------
-- Query 6: City Tier Performance & Risk Dynamics
-- ----------------------------------------------------------------------------
-- Business Objective: Analyze customer profiles, loan metrics, and average interest 
-- rates across Tier-1, Tier-2, and Tier-3 cities.
-- BI Dashboard Widget: Multi-bar comparison chart by City Tier.
-- ----------------------------------------------------------------------------
WITH tier_metrics AS (
    SELECT 
        u.city_tier,
        COUNT(DISTINCT u.user_id) as total_customers,
        AVG(u.monthly_income) as avg_income,
        COUNT(DISTINCT le.user_id) as applicants,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN le.user_id END) as disbursed_customers,
        SUM(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount ELSE 0 END) as total_disbursed_capital,
        AVG(CASE WHEN le.approval_status = 'Disbursed' THEN le.interest_rate END) as avg_interest_rate
    FROM users u
    LEFT JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY u.city_tier
)
SELECT 
    city_tier,
    total_customers,
    ROUND(avg_income, 2) as average_income,
    applicants,
    disbursed_customers,
    ROUND((disbursed_customers::numeric / NULLIF(applicants, 0)) * 100, 2) as applicant_to_disbursed_rate_pct,
    total_disbursed_capital,
    ROUND(avg_interest_rate, 2) as average_interest_rate
FROM tier_metrics
WHERE city_tier IS NOT NULL
ORDER BY city_tier;


-- ----------------------------------------------------------------------------
-- Query 7: Customer Occupation Analysis (Income vs. Capital Allocation)
-- ----------------------------------------------------------------------------
-- Business Objective: Determine which occupational categories yield the highest monthly 
-- income, loan application rate, and total credit disbursed.
-- BI Dashboard Widget: Occupation Segment Breakdown Grid.
-- ----------------------------------------------------------------------------
WITH occupation_metrics AS (
    SELECT 
        u.occupation,
        COUNT(DISTINCT u.user_id) as total_customers,
        AVG(u.monthly_income) as avg_income,
        COUNT(DISTINCT CASE WHEN ae.event_name = 'Loan Apply' THEN u.user_id END) as applicants,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN le.user_id END) as disbursed_customers,
        SUM(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount ELSE 0 END) as total_disbursed_capital,
        AVG(CASE WHEN le.approval_status = 'Disbursed' THEN le.interest_rate END) as avg_interest_rate
    FROM users u
    LEFT JOIN app_events ae ON u.user_id = ae.user_id
    LEFT JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY u.occupation
)
SELECT 
    occupation,
    total_customers,
    ROUND(avg_income, 2) as average_income,
    applicants,
    disbursed_customers,
    ROUND((applicants::numeric / total_customers) * 100, 2) as apply_rate_pct,
    ROUND((disbursed_customers::numeric / NULLIF(applicants, 0)) * 100, 2) as applicant_to_disbursed_rate_pct,
    total_disbursed_capital,
    ROUND(avg_interest_rate, 2) as average_interest_rate
FROM occupation_metrics
WHERE occupation IS NOT NULL
ORDER BY total_disbursed_capital DESC;


-- ----------------------------------------------------------------------------
-- Query 8: Education Level Impact on Credit Quality and Conversion
-- ----------------------------------------------------------------------------
-- Business Objective: Assess the correlation between educational qualifications,
-- credit scores (CIBIL score average), and conversion success rates.
-- BI Dashboard Widget: Education segment summary comparison grid.
-- ----------------------------------------------------------------------------
WITH edu_metrics AS (
    SELECT 
        u.education_level,
        COUNT(DISTINCT u.user_id) as total_customers,
        AVG(u.monthly_income) as avg_income,
        AVG(CASE WHEN u.has_credit_history THEN u.cibil_score END) as avg_cibil,
        COUNT(DISTINCT CASE WHEN ae.event_name = 'Loan Apply' THEN u.user_id END) as applicants,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN le.user_id END) as disbursed_customers
    FROM users u
    LEFT JOIN app_events ae ON u.user_id = ae.user_id
    LEFT JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY u.education_level
)
SELECT 
    education_level,
    total_customers,
    ROUND(avg_income, 2) as average_income,
    ROUND(avg_cibil, 1) as average_cibil_score,
    applicants,
    ROUND((applicants::numeric / total_customers) * 100, 2) as apply_rate_pct,
    disbursed_customers,
    ROUND((disbursed_customers::numeric / NULLIF(applicants, 0)) * 100, 2) as applicant_to_disbursed_rate_pct
FROM edu_metrics
WHERE education_level IS NOT NULL
ORDER BY average_income DESC;


-- ----------------------------------------------------------------------------
-- Query 9: Device Usage and Loan Behavior
-- ----------------------------------------------------------------------------
-- Business Objective: Compare financial characteristics and downstream loan 
-- behavior (disbursement volume and rates) between Android and iOS users.
-- BI Dashboard Widget: Platform portfolio comparison KPIs.
-- ----------------------------------------------------------------------------
WITH device_platforms AS (
    SELECT 
        user_id,
        CASE 
            WHEN device LIKE '%Android%' THEN 'Android'
            WHEN device LIKE '%iPhone%' OR device LIKE '%iOS%' OR device LIKE '%iPad%' THEN 'iOS'
            ELSE 'Other'
        END AS device_platform
    FROM users
),
device_metrics AS (
    SELECT 
        dp.device_platform,
        COUNT(DISTINCT u.user_id) as total_customers,
        AVG(u.monthly_income) as avg_income,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN le.user_id END) as disbursed_customers,
        SUM(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount ELSE 0 END) as total_disbursed_capital,
        AVG(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount END) as avg_loan_amount,
        AVG(CASE WHEN le.approval_status = 'Disbursed' THEN le.interest_rate END) as avg_interest_rate
    FROM device_platforms dp
    JOIN users u ON dp.user_id = u.user_id
    LEFT JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY dp.device_platform
)
SELECT 
    device_platform,
    total_customers,
    ROUND(avg_income, 2) as average_income,
    disbursed_customers,
    ROUND((disbursed_customers::numeric / total_customers) * 100, 2) as overall_disbursement_rate_pct,
    total_disbursed_capital,
    ROUND(avg_loan_amount, 2) as average_loan_amount,
    ROUND(avg_interest_rate, 2) as average_interest_rate
FROM device_metrics
WHERE device_platform <> 'Other'
ORDER BY total_disbursed_capital DESC;


-- ----------------------------------------------------------------------------
-- Query 10: Executive Customer Scorecard (Portfolio KPIs)
-- ----------------------------------------------------------------------------
-- Business Objective: Summarize key performance indicators (KPIs) of the loan
-- portfolio, credit risk profiles, and operational margins.
-- BI Dashboard Widget: Executive Customer Portfolio KPI Scorecard grid.
-- ----------------------------------------------------------------------------
WITH portfolio_summary AS (
    SELECT 
        COUNT(DISTINCT u.user_id) as total_registered_customers,
        AVG(u.age) as average_age,
        AVG(u.monthly_income) as average_income,
        SUM(CASE WHEN u.has_credit_history THEN 1 ELSE 0 END)::numeric / COUNT(DISTINCT u.user_id) * 100 as pct_with_credit_history,
        AVG(CASE WHEN u.has_credit_history THEN u.cibil_score END) as average_cibil_score,
        SUM(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount ELSE 0 END) as total_capital_disbursed,
        AVG(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount END) as average_loan_amount,
        AVG(CASE WHEN le.approval_status = 'Disbursed' THEN le.interest_rate END) as average_interest_rate,
        SUM(CASE WHEN le.approval_status = 'Approved' THEN 1 ELSE 0 END)::numeric / 
            NULLIF(SUM(CASE WHEN le.approval_status IN ('Approved', 'Rejected') THEN 1 ELSE 0 END), 0) * 100 as approval_rate_pct
    FROM users u
    LEFT JOIN loan_events le ON u.user_id = le.user_id
)
SELECT 
    total_registered_customers,
    ROUND(average_age, 1) as average_age,
    ROUND(average_income, 2) as average_income,
    ROUND(pct_with_credit_history, 2) as pct_with_credit_history,
    ROUND(average_cibil_score, 1) as average_cibil_score,
    total_capital_disbursed,
    ROUND(average_loan_amount, 2) as average_loan_amount,
    ROUND(average_interest_rate, 2) as average_interest_rate_pct,
    ROUND(approval_rate_pct, 2) as underwriting_approval_rate_pct
FROM portfolio_summary;
