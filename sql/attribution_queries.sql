-- ============================================================================
-- InsightFlow Marketing Attribution Analytics Queries
-- ============================================================================
-- This file contains production-ready PostgreSQL 17 optimized queries designed
-- to analyze marketing spend, campaign performance, CAC, CPA, and ROI.
--
-- The queries leverage indexes (e.g. idx_marketing_user, idx_marketing_channel)
-- to ensure optimal execution performance over large datasets.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- Query 1: Acquisition Channel Performance (Traffic & Engagement Volumes)
-- ----------------------------------------------------------------------------
-- Business Objective: Measure the volumes of impressions, clicks, installs, and 
-- registrations across all acquisition channels to determine engagement efficiency.
-- BI Dashboard Widget: Channel traffic and conversion rate grid.
-- ----------------------------------------------------------------------------
WITH normalized_marketing AS (
    SELECT 
        channel,
        CASE 
            WHEN row_num = 1 THEN 'Impression'
            WHEN row_num = 2 THEN 'Click'
            WHEN row_num = 3 THEN 'Install'
        END AS event_type
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_id ASC) as row_num
        FROM marketing_events
    ) sub
),
marketing_summary AS (
    SELECT 
        channel,
        SUM(CASE WHEN event_type = 'Impression' THEN 1 ELSE 0 END) as impressions,
        SUM(CASE WHEN event_type = 'Click' THEN 1 ELSE 0 END) as clicks,
        SUM(CASE WHEN event_type = 'Install' THEN 1 ELSE 0 END) as installs
    FROM normalized_marketing
    GROUP BY channel
),
signup_summary AS (
    SELECT 
        acquisition_channel,
        COUNT(DISTINCT user_id) as signups
    FROM users
    GROUP BY acquisition_channel
)
SELECT 
    m.channel,
    m.impressions,
    m.clicks,
    m.installs,
    COALESCE(s.signups, 0) as signups,
    ROUND((m.clicks::numeric / NULLIF(m.impressions, 0)) * 100, 2) as click_through_rate_pct,
    ROUND((COALESCE(s.signups, 0)::numeric / NULLIF(m.installs, 0)) * 100, 2) as install_to_signup_rate_pct
FROM marketing_summary m
LEFT JOIN signup_summary s ON m.channel = s.acquisition_channel
ORDER BY signups DESC;


-- ----------------------------------------------------------------------------
-- Query 2: Campaign Performance Analysis (Spend and Installs)
-- ----------------------------------------------------------------------------
-- Business Objective: Track impressions, clicks, installs, and total spend at
-- the campaign level to evaluate top-of-funnel efficiency.
-- BI Dashboard Widget: Top Campaigns by Spend and Cost Per Install (CPI) Chart.
-- ----------------------------------------------------------------------------
WITH normalized_marketing AS (
    SELECT 
        campaign,
        channel,
        cost,
        CASE 
            WHEN row_num = 1 THEN 'Impression'
            WHEN row_num = 2 THEN 'Click'
            WHEN row_num = 3 THEN 'Install'
        END AS event_type
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_id ASC) as row_num
        FROM marketing_events
    ) sub
)
SELECT 
    campaign,
    channel,
    SUM(CASE WHEN event_type = 'Impression' THEN 1 ELSE 0 END) as impressions,
    SUM(CASE WHEN event_type = 'Click' THEN 1 ELSE 0 END) as clicks,
    SUM(CASE WHEN event_type = 'Install' THEN 1 ELSE 0 END) as installs,
    SUM(cost) as total_spend,
    ROUND((SUM(CASE WHEN event_type = 'Click' THEN 1 ELSE 0 END)::numeric / NULLIF(SUM(CASE WHEN event_type = 'Impression' THEN 1 ELSE 0 END), 0)) * 100, 2) as ctr_pct,
    ROUND(SUM(cost) / NULLIF(SUM(CASE WHEN event_type = 'Install' THEN 1 ELSE 0 END), 0), 2) as cost_per_install
FROM normalized_marketing
GROUP BY campaign, channel
ORDER BY total_spend DESC;


-- ----------------------------------------------------------------------------
-- Query 3: Conversion Rate by Campaign (Signup-to-Disbursement Funnel)
-- ----------------------------------------------------------------------------
-- Business Objective: Assess which individual campaigns drive high-value downstream
-- conversions, tracking the rate from signup to loan disbursement.
-- BI Dashboard Widget: Campaign Conversion Pipeline Funnel.
-- ----------------------------------------------------------------------------
WITH normalized_marketing AS (
    SELECT 
        user_id,
        campaign,
        channel,
        timestamp,
        CASE 
            WHEN row_num = 1 THEN 'Impression'
            WHEN row_num = 2 THEN 'Click'
            WHEN row_num = 3 THEN 'Install'
        END AS event_type
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_id ASC) as row_num
        FROM marketing_events
    ) sub
),
user_campaign AS (
    SELECT DISTINCT ON (user_id) 
        user_id,
        campaign,
        channel
    FROM normalized_marketing
    WHERE event_type = 'Install'
    ORDER BY user_id, timestamp ASC
),
campaign_funnel AS (
    SELECT 
        uc.campaign,
        uc.channel,
        COUNT(DISTINCT uc.user_id) as total_installs,
        COUNT(DISTINCT u.user_id) as signups,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN u.user_id END) as disbursements
    FROM user_campaign uc
    JOIN users u ON uc.user_id = u.user_id
    LEFT JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY uc.campaign, uc.channel
)
SELECT 
    campaign,
    channel,
    total_installs,
    signups,
    disbursements,
    ROUND((signups::numeric / NULLIF(total_installs, 0)) * 100, 2) as install_to_signup_rate_pct,
    ROUND((disbursements::numeric / NULLIF(signups, 0)) * 100, 2) as signup_to_disbursed_rate_pct,
    ROUND((disbursements::numeric / NULLIF(total_installs, 0)) * 100, 2) as install_to_disbursed_rate_pct
FROM campaign_funnel
ORDER BY disbursements DESC;


-- ----------------------------------------------------------------------------
-- Query 4: Revenue Generated by Acquisition Channel
-- ----------------------------------------------------------------------------
-- Business Objective: Calculate the total disbursed loan volume and projected
-- fees/interest revenue generated by customers of each acquisition channel.
-- BI Dashboard Widget: Revenue Breakdown by Marketing Channel Pie Chart.
-- ----------------------------------------------------------------------------
WITH channel_loans AS (
    SELECT 
        u.acquisition_channel,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN le.user_id END) as disbursed_loans_count,
        SUM(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount ELSE 0 END) as total_disbursed_volume,
        SUM(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount * 0.02 ELSE 0 END) as total_processing_fees,
        SUM(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount * (le.interest_rate / 100.0) ELSE 0 END) as projected_interest_revenue
    FROM users u
    JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY u.acquisition_channel
)
SELECT 
    acquisition_channel,
    disbursed_loans_count,
    total_disbursed_volume,
    ROUND(total_processing_fees, 2) as estimated_processing_fees,
    ROUND(projected_interest_revenue, 2) as estimated_interest_revenue,
    ROUND(total_processing_fees + projected_interest_revenue, 2) as total_estimated_channel_revenue
FROM channel_loans
ORDER BY total_estimated_channel_revenue DESC;


-- ----------------------------------------------------------------------------
-- Query 5: Customer Acquisition Cost (CAC) by Channel
-- ----------------------------------------------------------------------------
-- Business Objective: Calculate CAC per channel, defined as total marketing spend
-- divided by the number of unique disbursed customers.
-- BI Dashboard Widget: CAC KPI Cards and Comparison Bar Chart.
-- ----------------------------------------------------------------------------
WITH channel_spend AS (
    SELECT 
        channel,
        SUM(cost) as total_spend
    FROM marketing_events
    GROUP BY channel
),
channel_acquisitions AS (
    SELECT 
        u.acquisition_channel,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN u.user_id END) as acquired_customers
    FROM users u
    JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY u.acquisition_channel
)
SELECT 
    cs.channel as acquisition_channel,
    cs.total_spend as marketing_spend,
    COALESCE(ca.acquired_customers, 0) as acquired_customers,
    CASE 
        WHEN COALESCE(ca.acquired_customers, 0) > 0 
        THEN ROUND((cs.total_spend / ca.acquired_customers), 2)
        ELSE 0.00
    END as customer_acquisition_cost
FROM channel_spend cs
LEFT JOIN channel_acquisitions ca ON cs.channel = ca.acquisition_channel
ORDER BY customer_acquisition_cost ASC;


-- ----------------------------------------------------------------------------
-- Query 6: Cost per Approved Loan (CPA) by Campaign
-- ----------------------------------------------------------------------------
-- Business Objective: Evaluate marketing efficiency relative to credit risk by 
-- calculating the CPA for each campaign (spend divided by approved loans).
-- BI Dashboard Widget: Campaign Cost Per Approval (CPA) Table.
-- ----------------------------------------------------------------------------
WITH campaign_spend AS (
    SELECT 
        campaign,
        channel,
        SUM(cost) as total_spend
    FROM marketing_events
    GROUP BY campaign, channel
),
normalized_marketing AS (
    SELECT 
        user_id,
        campaign,
        channel,
        CASE 
            WHEN row_num = 1 THEN 'Impression'
            WHEN row_num = 2 THEN 'Click'
            WHEN row_num = 3 THEN 'Install'
        END AS event_type
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_id ASC) as row_num
        FROM marketing_events
    ) sub
),
campaign_approvals AS (
    SELECT 
        me.campaign,
        me.channel,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Approved' THEN le.user_id END) as approved_loans
    FROM normalized_marketing me
    JOIN loan_events le ON me.user_id = le.user_id
    WHERE me.event_type = 'Install'
    GROUP BY me.campaign, me.channel
)
SELECT 
    cs.campaign,
    cs.channel,
    cs.total_spend as campaign_spend,
    COALESCE(ca.approved_loans, 0) as approved_loans,
    CASE 
        WHEN COALESCE(ca.approved_loans, 0) > 0 
        THEN ROUND((cs.total_spend / ca.approved_loans), 2)
        ELSE 0.00
    END as cost_per_approved_loan
FROM campaign_spend cs
LEFT JOIN campaign_approvals ca ON cs.campaign = ca.campaign AND cs.channel = ca.channel
ORDER BY cost_per_approved_loan ASC;


-- ----------------------------------------------------------------------------
-- Query 7: Return on Investment (ROI) by Marketing Channel
-- ----------------------------------------------------------------------------
-- Business Objective: Determine the financial return of marketing spend per channel
-- calculated as (Projected Revenue - Marketing Spend) / Marketing Spend.
-- BI Dashboard Widget: Marketing Channel ROI Rank Table.
-- ----------------------------------------------------------------------------
WITH channel_spend AS (
    SELECT 
        channel,
        SUM(cost) as total_spend
    FROM marketing_events
    GROUP BY channel
),
channel_revenue AS (
    SELECT 
        u.acquisition_channel,
        SUM(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount * 0.02 + le.loan_amount * (le.interest_rate / 100.0) ELSE 0 END) as total_revenue
    FROM users u
    JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY u.acquisition_channel
)
SELECT 
    cs.channel as acquisition_channel,
    cs.total_spend as marketing_spend,
    ROUND(COALESCE(cr.total_revenue, 0), 2) as estimated_revenue,
    ROUND(ROUND(COALESCE(cr.total_revenue, 0), 2) - cs.total_spend, 2) as net_profit,
    ROUND(((COALESCE(cr.total_revenue, 0) - cs.total_spend) / cs.total_spend) * 100, 2) as roi_pct
FROM channel_spend cs
LEFT JOIN channel_revenue cr ON cs.channel = cr.acquisition_channel
ORDER BY roi_pct DESC;


-- ----------------------------------------------------------------------------
-- Query 8: Device Performance Within Marketing Channels
-- ----------------------------------------------------------------------------
-- Business Objective: Compare signup and disbursement performance between Android
-- and iOS users within each acquisition channel to tune platform bids.
-- BI Dashboard Widget: Channel-Device Matrix conversion heatmap.
-- ----------------------------------------------------------------------------
WITH device_attribution AS (
    SELECT 
        u.acquisition_channel,
        CASE 
            WHEN u.device LIKE '%Android%' THEN 'Android'
            WHEN u.device LIKE '%iPhone%' OR u.device LIKE '%iOS%' OR u.device LIKE '%iPad%' THEN 'iOS'
            ELSE 'Other'
        END AS device_platform,
        COUNT(DISTINCT u.user_id) as total_signups,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN u.user_id END) as disbursed_users,
        SUM(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount ELSE 0 END) as total_disbursed_volume
    FROM users u
    LEFT JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY u.acquisition_channel, device_platform
)
SELECT 
    acquisition_channel,
    device_platform,
    total_signups,
    disbursed_users,
    ROUND((disbursed_users::numeric / NULLIF(total_signups, 0)) * 100, 2) as signup_to_disbursed_rate_pct,
    total_disbursed_volume,
    ROUND(total_disbursed_volume::numeric / NULLIF(disbursed_users, 0), 2) as avg_disbursed_loan_amount
FROM device_attribution
WHERE device_platform <> 'Other'
ORDER BY acquisition_channel, device_platform;


-- ----------------------------------------------------------------------------
-- Query 9: Geographic Marketing Effectiveness (State-level Spend Efficiency)
-- ----------------------------------------------------------------------------
-- Business Objective: Assess which state-channel combinations yield the highest
-- conversion and largest loan volumes relative to regional marketing spend.
-- BI Dashboard Widget: Geographic map with bubble sizes representing CAC/Volume.
-- ----------------------------------------------------------------------------
WITH geo_channel_spend AS (
    SELECT 
        channel,
        state,
        SUM(cost) as marketing_spend
    FROM marketing_events
    GROUP BY channel, state
),
geo_channel_conversions AS (
    SELECT 
        u.acquisition_channel,
        u.state,
        COUNT(DISTINCT u.user_id) as registered_users,
        COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN le.user_id END) as disbursed_users,
        SUM(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount ELSE 0 END) as disbursed_volume
    FROM users u
    LEFT JOIN loan_events le ON u.user_id = le.user_id
    GROUP BY u.acquisition_channel, u.state
)
SELECT 
    c.acquisition_channel,
    c.state,
    c.registered_users,
    c.disbursed_users,
    ROUND((c.disbursed_users::numeric / NULLIF(c.registered_users, 0)) * 100, 2) as conversion_rate_pct,
    c.disbursed_volume,
    COALESCE(s.marketing_spend, 0) as marketing_spend,
    CASE 
        WHEN c.disbursed_users > 0 
        THEN ROUND((COALESCE(s.marketing_spend, 0)::numeric / c.disbursed_users), 2)
        ELSE 0.00
    END as local_cac
FROM geo_channel_conversions c
LEFT JOIN geo_channel_spend s ON c.acquisition_channel = s.channel AND c.state = s.state
WHERE c.state IS NOT NULL
ORDER BY disbursed_volume DESC
LIMIT 50;


-- ----------------------------------------------------------------------------
-- Query 10: Executive Marketing Scorecard (Ranked Channels)
-- ----------------------------------------------------------------------------
-- Business Objective: Provide an executive overview ranking all channels by 
-- total spend, signups, conversions, revenue, CAC, and ROI.
-- BI Dashboard Widget: Executive Marketing Channel Leaderboard Table.
-- ----------------------------------------------------------------------------
WITH channel_metrics AS (
    SELECT 
        cs.channel as acquisition_channel,
        cs.total_spend as marketing_spend,
        COALESCE(cr.total_signups, 0) as signups,
        COALESCE(cr.disbursed_users, 0) as disbursed_users,
        COALESCE(cr.total_revenue, 0) as estimated_revenue
    FROM (
        SELECT channel, SUM(cost) as total_spend FROM marketing_events GROUP BY channel
    ) cs
    LEFT JOIN (
        SELECT 
            u.acquisition_channel,
            COUNT(DISTINCT u.user_id) as total_signups,
            COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN u.user_id END) as disbursed_users,
            SUM(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount * 0.02 + le.loan_amount * (le.interest_rate / 100.0) ELSE 0 END) as total_revenue
        FROM users u
        LEFT JOIN loan_events le ON u.user_id = le.user_id
        GROUP BY u.acquisition_channel
    ) cr ON cs.channel = cr.acquisition_channel
)
SELECT 
    acquisition_channel,
    marketing_spend,
    signups,
    disbursed_users,
    ROUND((disbursed_users::numeric / NULLIF(signups, 0)) * 100, 2) as signup_to_disbursement_rate_pct,
    estimated_revenue,
    ROUND(estimated_revenue - marketing_spend, 2) as net_profit,
    CASE 
        WHEN disbursed_users > 0 THEN ROUND((marketing_spend / disbursed_users), 2)
        ELSE 0.00
    END as cac,
    ROUND(((estimated_revenue - marketing_spend) / marketing_spend) * 100, 2) as roi_pct,
    DENSE_RANK() OVER (ORDER BY ((estimated_revenue - marketing_spend) / marketing_spend) DESC) as channel_rank
FROM channel_metrics
ORDER BY channel_rank;
