-- ============================================================================
-- InsightFlow Funnel Analytics Queries
-- ============================================================================
-- This file contains production-ready PostgreSQL 17 optimized queries designed
-- to analyze customer progression and friction across all stages of the funnel.
--
-- The queries leverage existing table indexes (e.g. idx_app_event, idx_loan_status)
-- to ensure optimal performance when executing analytics over large datasets.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- Query 1: Overall Funnel - User Volume and Stage-to-Stage Conversions
-- ----------------------------------------------------------------------------
-- Business Objective: Determine how many unique users reach each stage of the 
-- customer lifecycle, from initial ad impressions to final loan disbursement.
-- BI Dashboard Usage: Top-level funnel progression bar chart showing drop-off and conversion rates.
-- ----------------------------------------------------------------------------
WITH funnel_volumes AS (
    SELECT 1 AS stage_num, 'Marketing Impression' AS stage_name, COUNT(DISTINCT user_id) AS unique_users
    FROM marketing_events WHERE event_type = 'Impression'
    UNION ALL
    SELECT 2, 'Marketing Click', COUNT(DISTINCT user_id)
    FROM marketing_events WHERE event_type = 'Click'
    UNION ALL
    SELECT 3, 'Marketing Install', COUNT(DISTINCT user_id)
    FROM marketing_events WHERE event_type = 'Install'
    UNION ALL
    SELECT 4, 'App Open', COUNT(DISTINCT user_id)
    FROM app_events WHERE event_name = 'App Open'
    UNION ALL
    SELECT 5, 'Signup', COUNT(DISTINCT user_id)
    FROM app_events WHERE event_name = 'Signup'
    UNION ALL
    SELECT 6, 'OTP Verification', COUNT(DISTINCT user_id)
    FROM app_events WHERE event_name = 'OTP Verification'
    UNION ALL
    SELECT 7, 'KYC Start', COUNT(DISTINCT user_id)
    FROM app_events WHERE event_name = 'KYC Start'
    UNION ALL
    SELECT 8, 'KYC Complete', COUNT(DISTINCT user_id)
    FROM app_events WHERE event_name = 'KYC Complete'
    UNION ALL
    SELECT 9, 'Loan Apply', COUNT(DISTINCT user_id)
    FROM app_events WHERE event_name = 'Loan Apply'
    UNION ALL
    SELECT 10, 'Loan Approved', COUNT(DISTINCT user_id)
    FROM loan_events WHERE approval_status = 'Approved'
    UNION ALL
    SELECT 11, 'Loan Disbursed', COUNT(DISTINCT user_id)
    FROM loan_events WHERE approval_status = 'Disbursed'
)
SELECT 
    stage_num,
    stage_name,
    unique_users,
    ROUND(unique_users::numeric / FIRST_VALUE(unique_users) OVER (ORDER BY stage_num) * 100, 2) AS pct_of_tof,
    ROUND(unique_users::numeric / LAG(unique_users, 1, unique_users) OVER (ORDER BY stage_num) * 100, 2) AS pct_of_previous
FROM funnel_volumes
ORDER BY stage_num;


-- ----------------------------------------------------------------------------
-- Query 2: Funnel Leakage (Absolute and Relative Drop-offs)
-- ----------------------------------------------------------------------------
-- Business Objective: Identify exact transition points where we experience the 
-- greatest friction (user loss) to target product optimizations.
-- BI Dashboard Usage: Funnel leakage visualization highlighting underperforming transitions.
-- ----------------------------------------------------------------------------
WITH adjacent_stages AS (
    SELECT 
        u.user_id,
        MAX(CASE WHEN ae.event_name = 'App Open' THEN 1 ELSE 0 END) as app_open,
        MAX(CASE WHEN ae.event_name = 'Signup' THEN 1 ELSE 0 END) as signup,
        MAX(CASE WHEN ae.event_name = 'OTP Verification' THEN 1 ELSE 0 END) as otp_verified,
        MAX(CASE WHEN ae.event_name = 'KYC Start' THEN 1 ELSE 0 END) as kyc_started,
        MAX(CASE WHEN ae.event_name = 'KYC Complete' THEN 1 ELSE 0 END) as kyc_completed,
        MAX(CASE WHEN ae.event_name = 'Loan Apply' THEN 1 ELSE 0 END) as loan_applied,
        MAX(CASE WHEN le.approval_status = 'Approved' THEN 1 ELSE 0 END) as loan_approved,
        MAX(CASE WHEN le.approval_status = 'Disbursed' THEN 1 ELSE 0 END) as loan_disbursed
    FROM users u
    LEFT JOIN app_events ae ON u.user_id = ae.user_id
    LEFT JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY u.user_id
),
totals AS (
    SELECT
        SUM(app_open) AS s1_app_open,
        SUM(signup) AS s2_signup,
        SUM(otp_verified) AS s3_otp,
        SUM(kyc_started) AS s4_kyc_start,
        SUM(kyc_completed) AS s5_kyc_complete,
        SUM(loan_applied) AS s6_loan_apply,
        SUM(loan_approved) AS s7_loan_approve,
        SUM(loan_disbursed) AS s8_loan_disburse
    FROM adjacent_stages
)
SELECT 
    'App Open -> Signup' AS transition,
    s1_app_open - s2_signup AS users_lost,
    ROUND((1.0 - (s2_signup::numeric / NULLIF(s1_app_open, 0))) * 100, 2) AS dropoff_rate
FROM totals
UNION ALL
SELECT 'Signup -> OTP Verification', s2_signup - s3_otp, ROUND((1.0 - (s3_otp::numeric / NULLIF(s2_signup, 0))) * 100, 2) FROM totals
UNION ALL
SELECT 'OTP Verification -> KYC Start', s3_otp - s4_kyc_start, ROUND((1.0 - (s4_kyc_start::numeric / NULLIF(s3_otp, 0))) * 100, 2) FROM totals
UNION ALL
SELECT 'KYC Start -> KYC Complete', s4_kyc_start - s5_kyc_complete, ROUND((1.0 - (s5_kyc_complete::numeric / NULLIF(s4_kyc_start, 0))) * 100, 2) FROM totals
UNION ALL
SELECT 'KYC Complete -> Loan Apply', s5_kyc_complete - s6_loan_apply, ROUND((1.0 - (s6_loan_apply::numeric / NULLIF(s5_kyc_complete, 0))) * 100, 2) FROM totals
UNION ALL
SELECT 'Loan Apply -> Loan Approved', s6_loan_apply - s7_loan_approve, ROUND((1.0 - (s7_loan_approve::numeric / NULLIF(s6_loan_apply, 0))) * 100, 2) FROM totals
UNION ALL
SELECT 'Loan Approved -> Loan Disbursed', s7_loan_approve - s8_loan_disburse, ROUND((1.0 - (s8_loan_disburse::numeric / NULLIF(s7_loan_approve, 0))) * 100, 2) FROM totals;


-- ----------------------------------------------------------------------------
-- Query 3: KYC Step-by-Step Micro-Funnel Conversion
-- ----------------------------------------------------------------------------
-- Business Objective: Pinpoint steps inside the identity verification (KYC) flow
-- where users drop off, distinguishing between Face Match and PAN validation errors.
-- BI Dashboard Usage: KYC funnel dashboard to track identity verification performance.
-- ----------------------------------------------------------------------------
WITH kyc_steps AS (
    SELECT
        user_id,
        MIN(CASE WHEN event_name = 'KYC Start' THEN timestamp END) as kyc_start_ts,
        MIN(CASE WHEN event_name = 'Face Match' THEN timestamp END) as face_match_ts,
        MIN(CASE WHEN event_name = 'PAN Verification' THEN timestamp END) as pan_verify_ts,
        MIN(CASE WHEN event_name = 'KYC Complete' THEN timestamp END) as kyc_complete_ts
    FROM app_events
    WHERE event_name IN ('KYC Start', 'Face Match', 'PAN Verification', 'KYC Complete')
    GROUP BY user_id
),
metrics AS (
    SELECT
        COUNT(DISTINCT CASE WHEN kyc_start_ts IS NOT NULL THEN user_id END) as started,
        COUNT(DISTINCT CASE WHEN face_match_ts IS NOT NULL AND kyc_start_ts IS NOT NULL THEN user_id END) as face_matched,
        COUNT(DISTINCT CASE WHEN pan_verify_ts IS NOT NULL AND face_match_ts IS NOT NULL THEN user_id END) as pan_verified,
        COUNT(DISTINCT CASE WHEN kyc_complete_ts IS NOT NULL AND pan_verify_ts IS NOT NULL THEN user_id END) as completed
    FROM kyc_steps
)
SELECT
    started AS kyc_started_users,
    face_matched AS face_matched_users,
    ROUND((face_matched::numeric / NULLIF(started, 0)) * 100, 2) AS face_match_conv_rate,
    pan_verified AS pan_verified_users,
    ROUND((pan_verified::numeric / NULLIF(face_matched, 0)) * 100, 2) AS pan_verify_conv_rate,
    completed AS kyc_completed_users,
    ROUND((completed::numeric / NULLIF(pan_verified, 0)) * 100, 2) AS kyc_complete_conv_rate,
    ROUND((completed::numeric / NULLIF(started, 0)) * 100, 2) AS overall_kyc_completion_rate
FROM metrics;


-- ----------------------------------------------------------------------------
-- Query 4: Loan Application Rate by Age & Income Segments
-- ----------------------------------------------------------------------------
-- Business Objective: Analyze the rate at which verified (KYC-completed) users
-- apply for a loan, segmented by age and monthly income.
-- BI Dashboard Usage: Customer segmentation heatmaps indicating intent and product fit.
-- ----------------------------------------------------------------------------
WITH user_kyc_status AS (
    SELECT 
        u.user_id,
        u.age,
        u.monthly_income,
        MAX(CASE WHEN ae.event_name = 'KYC Complete' THEN 1 ELSE 0 END) as has_completed_kyc,
        MAX(CASE WHEN ae.event_name = 'Loan Apply' THEN 1 ELSE 0 END) as has_applied_loan
    FROM users u
    JOIN app_events ae ON u.user_id = ae.user_id
    GROUP BY u.user_id, u.age, u.monthly_income
),
segmented_users AS (
    SELECT 
        user_id,
        has_completed_kyc,
        has_applied_loan,
        CASE 
            WHEN age < 25 THEN '18-24'
            WHEN age < 35 THEN '25-34'
            WHEN age < 50 THEN '35-49'
            ELSE '50+'
        END AS age_group,
        CASE 
            WHEN monthly_income < 30000 THEN 'Low (<30k)'
            WHEN monthly_income < 75000 THEN 'Medium (30k-75k)'
            ELSE 'High (75k+)'
        END AS income_segment
    FROM user_kyc_status
    WHERE has_completed_kyc = 1
)
SELECT 
    age_group,
    income_segment,
    COUNT(DISTINCT user_id) as kyc_completed_users,
    SUM(has_applied_loan) as loan_applied_users,
    ROUND((SUM(has_applied_loan)::numeric / COUNT(DISTINCT user_id)) * 100, 2) as kyc_to_apply_rate
FROM segmented_users
GROUP BY age_group, income_segment
ORDER BY age_group, income_segment;


-- ----------------------------------------------------------------------------
-- Query 5: Loan Approval Rate & Rejection Reason Analysis by CIBIL Segment
-- ----------------------------------------------------------------------------
-- Business Objective: Determine how credit profiles impact underwriting decisions
-- and identify primary rejection reasons for poor credit segments.
-- BI Dashboard Usage: Credit underwriting table showing approval rate and rejection reasons.
-- ----------------------------------------------------------------------------
WITH loan_reviews AS (
    SELECT 
        le.user_id,
        le.approval_status,
        le.rejection_reason,
        u.cibil_score,
        u.has_credit_history,
        CASE 
            WHEN NOT u.has_credit_history OR u.cibil_score IS NULL THEN 'New to Credit (NTC)'
            WHEN u.cibil_score < 550 THEN 'Poor (<550)'
            WHEN u.cibil_score < 650 THEN 'Fair (550-649)'
            WHEN u.cibil_score < 750 THEN 'Good (650-749)'
            ELSE 'Excellent (750+)'
        END AS cibil_segment
    FROM loan_events le
    JOIN users u ON le.user_id = u.user_id
    WHERE le.approval_status IN ('Approved', 'Rejected')
),
segment_totals AS (
    SELECT 
        cibil_segment,
        COUNT(*) as total_decisions,
        SUM(CASE WHEN approval_status = 'Approved' THEN 1 ELSE 0 END) as approved_count,
        SUM(CASE WHEN approval_status = 'Rejected' THEN 1 ELSE 0 END) as rejected_count
    FROM loan_reviews
    GROUP BY cibil_segment
),
top_reasons AS (
    SELECT 
        cibil_segment,
        rejection_reason,
        COUNT(*) as reason_count,
        ROW_NUMBER() OVER(PARTITION BY cibil_segment ORDER BY COUNT(*) DESC) as rank
    FROM loan_reviews
    WHERE approval_status = 'Rejected' AND rejection_reason <> ''
    GROUP BY cibil_segment, rejection_reason
)
SELECT 
    t.cibil_segment,
    t.total_decisions,
    t.approved_count,
    ROUND((t.approved_count::numeric / t.total_decisions) * 100, 2) as approval_rate,
    r.rejection_reason as primary_rejection_reason,
    r.reason_count as primary_rejection_reason_count,
    ROUND((r.reason_count::numeric / NULLIF(t.rejected_count, 0)) * 100, 2) as primary_reason_pct_of_rejections
FROM segment_totals t
LEFT JOIN top_reasons r ON t.cibil_segment = r.cibil_segment AND r.rank = 1
ORDER BY approval_rate DESC;


-- ----------------------------------------------------------------------------
-- Query 6: Loan Disbursement Funnel and Average Time-To-Disburse
-- ----------------------------------------------------------------------------
-- Business Objective: Measure the time lag and efficiency of operational
-- processes between loan approval and loan disbursement.
-- BI Dashboard Usage: KPI card showing average/median hours to disburse.
-- ----------------------------------------------------------------------------
WITH loan_timestamps AS (
    SELECT 
        user_id,
        MIN(CASE WHEN approval_status = 'Approved' THEN timestamp END) as approved_ts,
        MIN(CASE WHEN approval_status = 'Disbursed' THEN timestamp END) as disbursed_ts
    FROM loan_events
    WHERE approval_status IN ('Approved', 'Disbursed')
    GROUP BY user_id
),
durations AS (
    SELECT 
        user_id,
        approved_ts,
        disbursed_ts,
        CASE WHEN disbursed_ts IS NOT NULL THEN 1 ELSE 0 END as is_disbursed,
        EXTRACT(EPOCH FROM (disbursed_ts - approved_ts)) / 3600.0 as hours_to_disburse
    FROM loan_timestamps
    WHERE approved_ts IS NOT NULL
)
SELECT 
    COUNT(DISTINCT user_id) as approved_loans,
    SUM(is_disbursed) as disbursed_loans,
    ROUND((SUM(is_disbursed)::numeric / COUNT(DISTINCT user_id)) * 100, 2) as disbursement_rate,
    ROUND(AVG(hours_to_disburse)::numeric, 2) as avg_hours_to_disburse,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY hours_to_disburse)::numeric, 2) as median_hours_to_disburse
FROM durations;


-- ----------------------------------------------------------------------------
-- Query 7: Device-wise Funnel and Conversion Rates
-- ----------------------------------------------------------------------------
-- Business Objective: Determine whether Android or iOS exhibits higher friction
-- during signups, KYC flow, and loan applications.
-- BI Dashboard Usage: Funnel analysis side-by-side comparison filters for device.
-- ----------------------------------------------------------------------------
WITH user_devices AS (
    SELECT 
        user_id,
        CASE 
            WHEN device LIKE '%Android%' THEN 'Android'
            WHEN device LIKE '%iPhone%' OR device LIKE '%iOS%' OR device LIKE '%iPad%' THEN 'iOS'
            ELSE 'Other'
        END AS device_platform
    FROM users
),
stage_events AS (
    SELECT 
        ud.device_platform,
        COUNT(DISTINCT u.user_id) as total_users,
        COUNT(DISTINCT CASE WHEN ae.event_name = 'App Open' THEN u.user_id END) as app_opens,
        COUNT(DISTINCT CASE WHEN ae.event_name = 'Signup' THEN u.user_id END) as signups,
        COUNT(DISTINCT CASE WHEN ae.event_name = 'KYC Complete' THEN u.user_id END) as kyc_completes,
        COUNT(DISTINCT CASE WHEN ae.event_name = 'Loan Apply' THEN u.user_id END) as loan_applies,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN u.user_id END) as disbursements
    FROM user_devices ud
    JOIN users u ON ud.user_id = u.user_id
    LEFT JOIN app_events ae ON u.user_id = ae.user_id
    LEFT JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY ud.device_platform
)
SELECT 
    device_platform,
    app_opens,
    signups,
    ROUND((signups::numeric / NULLIF(app_opens, 0)) * 100, 2) as app_open_to_signup_pct,
    kyc_completes,
    ROUND((kyc_completes::numeric / NULLIF(signups, 0)) * 100, 2) as signup_to_kyc_pct,
    loan_applies,
    ROUND((loan_applies::numeric / NULLIF(kyc_completes, 0)) * 100, 2) as kyc_to_apply_pct,
    disbursements,
    ROUND((disbursements::numeric / NULLIF(loan_applies, 0)) * 100, 2) as apply_to_disbursement_pct,
    ROUND((disbursements::numeric / NULLIF(app_opens, 0)) * 100, 2) as overall_funnel_efficiency_pct
FROM stage_events
WHERE device_platform <> 'Other'
ORDER BY overall_funnel_efficiency_pct DESC;


-- ----------------------------------------------------------------------------
-- Query 8: State-wise Funnel Conversion & Underperforming Geographies
-- ----------------------------------------------------------------------------
-- Business Objective: Identify geo-distribution conversion rates to optimize
-- local operations and targeted promotions.
-- BI Dashboard Usage: Geospatial choropleth maps displaying conversion efficiency by state.
-- ----------------------------------------------------------------------------
WITH state_volumes AS (
    SELECT 
        u.state,
        COUNT(DISTINCT u.user_id) as registered_users,
        COUNT(DISTINCT CASE WHEN ae.event_name = 'App Open' THEN u.user_id END) as app_opens,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN u.user_id END) as disbursed_users
    FROM users u
    LEFT JOIN app_events ae ON u.user_id = ae.user_id
    LEFT JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY u.state
)
SELECT 
    state,
    registered_users,
    app_opens,
    disbursed_users,
    ROUND((disbursed_users::numeric / NULLIF(app_opens, 0)) * 100, 2) as app_open_to_disbursed_rate,
    RANK() OVER (ORDER BY (disbursed_users::numeric / NULLIF(app_opens, 0)) DESC) as conversion_rank
FROM state_volumes
WHERE app_opens >= 50
ORDER BY app_open_to_disbursed_rate DESC;


-- ----------------------------------------------------------------------------
-- Query 9: Acquisition Channel Performance and CAC Efficiency
-- ----------------------------------------------------------------------------
-- Business Objective: Determine which acquisition channel is the most cost-effective
-- by calculating signup-to-disbursed conversion and Customer Acquisition Cost (CAC).
-- BI Dashboard Usage: Marketing attribution ROI table for budgeting.
-- ----------------------------------------------------------------------------
WITH channel_disbursements AS (
    SELECT 
        u.acquisition_channel,
        COUNT(DISTINCT u.user_id) as total_signups,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN u.user_id END) as disbursed_users
    FROM users u
    LEFT JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY u.acquisition_channel
),
channel_costs AS (
    SELECT 
        channel,
        SUM(cost) as total_marketing_spend
    FROM marketing_events
    GROUP BY channel
)
SELECT 
    d.acquisition_channel,
    d.total_signups,
    d.disbursed_users,
    ROUND((d.disbursed_users::numeric / NULLIF(d.total_signups, 0)) * 100, 2) as signup_to_disbursement_rate,
    COALESCE(c.total_marketing_spend, 0) as marketing_spend,
    CASE 
        WHEN d.disbursed_users > 0 THEN ROUND((COALESCE(c.total_marketing_spend, 0)::numeric / d.disbursed_users), 2)
        ELSE 0.00
    END as estimated_cac
FROM channel_disbursements d
LEFT JOIN channel_costs c ON d.acquisition_channel = c.channel
ORDER BY signup_to_disbursement_rate DESC;


-- ----------------------------------------------------------------------------
-- Query 10: KYC-to-Disbursement Drop-off and Time Lag Analysis
-- ----------------------------------------------------------------------------
-- Business Objective: Track milestones and lag times between completing KYC
-- and obtaining disbursement to uncover drop-off points.
-- BI Dashboard Usage: Operational milestones tracking chart.
-- ----------------------------------------------------------------------------
WITH user_milestones AS (
    SELECT 
        user_id,
        MIN(CASE WHEN event_name = 'KYC Complete' THEN timestamp END) as kyc_complete_ts,
        MIN(CASE WHEN event_name = 'Loan Apply' THEN timestamp END) as loan_apply_ts
    FROM app_events
    WHERE event_name IN ('KYC Complete', 'Loan Apply')
    GROUP BY user_id
),
loan_decisions AS (
    SELECT 
        user_id,
        MIN(CASE WHEN approval_status = 'Approved' THEN timestamp END) as approved_ts,
        MIN(CASE WHEN approval_status = 'Disbursed' THEN timestamp END) as disbursed_ts
    FROM loan_events
    WHERE approval_status IN ('Approved', 'Disbursed')
    GROUP BY user_id
),
combined_milestones AS (
    SELECT 
        u.user_id,
        m.kyc_complete_ts,
        m.loan_apply_ts,
        d.approved_ts,
        d.disbursed_ts
    FROM users u
    JOIN user_milestones m ON u.user_id = m.user_id
    LEFT JOIN loan_decisions d ON u.user_id = d.user_id
    WHERE m.kyc_complete_ts IS NOT NULL
)
SELECT 
    COUNT(DISTINCT user_id) as kyc_completed_users,
    
    COUNT(DISTINCT CASE WHEN loan_apply_ts IS NOT NULL THEN user_id END) as loan_applied_users,
    ROUND((COUNT(DISTINCT CASE WHEN loan_apply_ts IS NOT NULL THEN user_id END)::numeric / COUNT(DISTINCT user_id)) * 100, 2) as kyc_to_apply_rate,
    ROUND(AVG(EXTRACT(EPOCH FROM (loan_apply_ts - kyc_complete_ts)) / 3600.0)::numeric, 2) as avg_hours_to_apply,
    
    COUNT(DISTINCT CASE WHEN approved_ts IS NOT NULL THEN user_id END) as loan_approved_users,
    ROUND((COUNT(DISTINCT CASE WHEN approved_ts IS NOT NULL THEN user_id END)::numeric / NULLIF(COUNT(DISTINCT CASE WHEN loan_apply_ts IS NOT NULL THEN user_id END), 0)) * 100, 2) as apply_to_approval_rate,
    
    COUNT(DISTINCT CASE WHEN disbursed_ts IS NOT NULL THEN user_id END) as loan_disbursed_users,
    ROUND((COUNT(DISTINCT CASE WHEN disbursed_ts IS NOT NULL THEN user_id END)::numeric / NULLIF(COUNT(DISTINCT CASE WHEN approved_ts IS NOT NULL THEN user_id END), 0)) * 100, 2) as approval_to_disbursement_rate,
    
    ROUND((COUNT(DISTINCT CASE WHEN disbursed_ts IS NOT NULL THEN user_id END)::numeric / COUNT(DISTINCT user_id)) * 100, 2) as kyc_to_disbursement_rate
FROM combined_milestones;
