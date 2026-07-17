-- ============================================================================
-- InsightFlow A/B Experiment Analytics Queries
-- ============================================================================
-- This file contains production-ready PostgreSQL 17 optimized queries designed
-- to evaluate A/B testing exposures, conversion rates, statistical z-scores, 
-- revenue lift, and launch recommendations.
--
-- The queries leverage indexes (e.g. idx_experiment_user, idx_experiment_name)
-- to ensure optimal execution performance over large datasets.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- Query 1: Overall Experiment Performance (Exposure & Conversion Volume)
-- ----------------------------------------------------------------------------
-- Business Objective: Summarize baseline metrics for each experiment (sample size,
-- conversion volume, overall conversion rate, and total revenue).
-- BI Dashboard Widget: General experiment overview table.
-- ----------------------------------------------------------------------------
SELECT 
    experiment_name,
    COUNT(DISTINCT user_id) as total_exposures,
    SUM(CASE WHEN converted = TRUE THEN 1 ELSE 0 END) as total_conversions,
    ROUND((SUM(CASE WHEN converted = TRUE THEN 1 ELSE 0 END)::numeric / COUNT(DISTINCT user_id)) * 100, 2) as overall_conversion_rate_pct,
    SUM(revenue_generated) as total_revenue
FROM experiments
GROUP BY experiment_name
ORDER BY total_exposures DESC;


-- ----------------------------------------------------------------------------
-- Query 2: Control vs. Treatment Comparison
-- ----------------------------------------------------------------------------
-- Business Objective: Break down sample sizes and conversion counts between 
-- the Control and Treatment groups to inspect cohort balance.
-- BI Dashboard Widget: Group-level conversion comparison table.
-- ----------------------------------------------------------------------------
SELECT 
    experiment_name,
    SUM(CASE WHEN variant = 'Control' THEN 1 ELSE 0 END) as control_size,
    SUM(CASE WHEN variant = 'Control' AND converted = TRUE THEN 1 ELSE 0 END) as control_conversions,
    ROUND((SUM(CASE WHEN variant = 'Control' AND converted = TRUE THEN 1 ELSE 0 END)::numeric / 
        NULLIF(SUM(CASE WHEN variant = 'Control' THEN 1 ELSE 0 END), 0)) * 100, 2) as control_conversion_rate_pct,
    SUM(CASE WHEN variant = 'Treatment' THEN 1 ELSE 0 END) as treatment_size,
    SUM(CASE WHEN variant = 'Treatment' AND converted = TRUE THEN 1 ELSE 0 END) as treatment_conversions,
    ROUND((SUM(CASE WHEN variant = 'Treatment' AND converted = TRUE THEN 1 ELSE 0 END)::numeric / 
        NULLIF(SUM(CASE WHEN variant = 'Treatment' THEN 1 ELSE 0 END), 0)) * 100, 2) as treatment_conversion_rate_pct
FROM experiments
GROUP BY experiment_name
ORDER BY experiment_name;


-- ----------------------------------------------------------------------------
-- Query 3: Conversion Lift % (Variant Outperformance)
-- ----------------------------------------------------------------------------
-- Business Objective: Quantify the relative conversion lift rate of the Treatment
-- group over the Control group to assess product performance gains.
-- BI Dashboard Widget: Conversion Lift Leaderboard (Vertical Bar Chart).
-- ----------------------------------------------------------------------------
WITH variant_rates AS (
    SELECT 
        experiment_name,
        SUM(CASE WHEN variant = 'Control' THEN 1 ELSE 0 END) as control_size,
        SUM(CASE WHEN variant = 'Control' AND converted = TRUE THEN 1 ELSE 0 END) as control_convs,
        SUM(CASE WHEN variant = 'Treatment' THEN 1 ELSE 0 END) as treatment_size,
        SUM(CASE WHEN variant = 'Treatment' AND converted = TRUE THEN 1 ELSE 0 END) as treatment_convs
    FROM experiments
    GROUP BY experiment_name
)
SELECT 
    experiment_name,
    ROUND((control_convs::numeric / NULLIF(control_size, 0)) * 100, 2) as control_rate_pct,
    ROUND((treatment_convs::numeric / NULLIF(treatment_size, 0)) * 100, 2) as treatment_rate_pct,
    ROUND(
        (
            (treatment_convs::numeric / NULLIF(treatment_size, 0)) - 
            (control_convs::numeric / NULLIF(control_size, 0))
        ) / 
        (control_convs::numeric / NULLIF(control_size, 0)) * 100, 
        2
    ) as relative_lift_pct
FROM variant_rates
ORDER BY relative_lift_pct DESC;


-- ----------------------------------------------------------------------------
-- Query 4: Revenue Lift & Incremental Value
-- ----------------------------------------------------------------------------
-- Business Objective: Calculate the financial impact of the Treatment variant by
-- comparing Average Revenue Per User (ARPU) and determining incremental revenue.
-- BI Dashboard Widget: Incremental Revenue KPI Card.
-- ----------------------------------------------------------------------------
WITH revenue_stats AS (
    SELECT 
        experiment_name,
        SUM(CASE WHEN variant = 'Control' THEN 1 ELSE 0 END) as control_users,
        SUM(CASE WHEN variant = 'Control' THEN revenue_generated ELSE 0 END) as control_revenue,
        SUM(CASE WHEN variant = 'Treatment' THEN 1 ELSE 0 END) as treatment_users,
        SUM(CASE WHEN variant = 'Treatment' THEN revenue_generated ELSE 0 END) as treatment_revenue
    FROM experiments
    GROUP BY experiment_name
)
SELECT 
    experiment_name,
    control_revenue,
    ROUND(control_revenue / NULLIF(control_users, 0), 2) as control_arpu,
    treatment_revenue,
    ROUND(treatment_revenue / NULLIF(treatment_users, 0), 2) as treatment_arpu,
    ROUND(
        treatment_revenue - (control_revenue * (treatment_users::numeric / NULLIF(control_users, 0))),
        2
    ) as incremental_revenue
FROM revenue_stats
ORDER BY incremental_revenue DESC;


-- ----------------------------------------------------------------------------
-- Query 5: Statistical Significance Summary (Two-Proportion Z-Test)
-- ----------------------------------------------------------------------------
-- Business Objective: Calculate the two-proportion z-score for each experiment to 
-- determine whether the conversion lift is statistically significant (95% confidence).
-- BI Dashboard Widget: A/B Test Confidence Gauge / Grid.
-- ----------------------------------------------------------------------------
WITH stats AS (
    SELECT 
        experiment_name,
        SUM(CASE WHEN variant = 'Control' THEN 1.0 ELSE 0.0 END) as nc,
        SUM(CASE WHEN variant = 'Control' AND converted = TRUE THEN 1.0 ELSE 0.0 END) as xc,
        SUM(CASE WHEN variant = 'Treatment' THEN 1.0 ELSE 0.0 END) as nt,
        SUM(CASE WHEN variant = 'Treatment' AND converted = TRUE THEN 1.0 ELSE 0.0 END) as xt
    FROM experiments
    GROUP BY experiment_name
),
z_score_inputs AS (
    SELECT 
        experiment_name,
        nc, xc, nt, xt,
        (xc / nc) as pc,
        (xt / nt) as pt,
        ((xc + xt) / (nc + nt)) as p_pooled
    FROM stats
    WHERE nc > 0 AND nt > 0
),
z_scores AS (
    SELECT 
        experiment_name,
        pc, pt, nc, nt,
        (pt - pc) / NULLIF(SQRT(p_pooled * (1.0 - p_pooled) * (1.0 / nc + 1.0 / nt)), 0) as z_val
    FROM z_score_inputs
)
SELECT 
    experiment_name,
    ROUND(pc * 100, 2) as control_rate_pct,
    ROUND(pt * 100, 2) as treatment_rate_pct,
    ROUND(((pt - pc) / NULLIF(pc, 0)) * 100, 2) as lift_pct,
    ROUND(z_val, 2) as z_score,
    CASE 
        WHEN ABS(z_val) >= 1.96 THEN 'Statistically Significant'
        ELSE 'Not Significant'
    END as significance_status
FROM z_scores
ORDER BY ABS(z_val) DESC;


-- ----------------------------------------------------------------------------
-- Query 6: Device-wise Experiment Performance
-- ----------------------------------------------------------------------------
-- Business Objective: Compare conversion lift and statistical significance between
-- Android and iOS mobile platforms to evaluate device-specific experiences.
-- BI Dashboard Widget: Device conversion split table.
-- ----------------------------------------------------------------------------
WITH stats AS (
    SELECT 
        experiment_name,
        device as device_platform,
        SUM(CASE WHEN variant = 'Control' THEN 1.0 ELSE 0.0 END) as nc,
        SUM(CASE WHEN variant = 'Control' AND converted = TRUE THEN 1.0 ELSE 0.0 END) as xc,
        SUM(CASE WHEN variant = 'Treatment' THEN 1.0 ELSE 0.0 END) as nt,
        SUM(CASE WHEN variant = 'Treatment' AND converted = TRUE THEN 1.0 ELSE 0.0 END) as xt
    FROM experiments
    GROUP BY experiment_name, device
),
z_scores AS (
    SELECT 
        experiment_name,
        device_platform,
        (xc / NULLIF(nc, 0)) as pc,
        (xt / NULLIF(nt, 0)) as pt,
        (xt / NULLIF(nt, 0) - xc / NULLIF(nc, 0)) / 
            NULLIF(SQRT(((xc + xt) / NULLIF(nc + nt, 0)) * (1.0 - ((xc + xt) / NULLIF(nc + nt, 0))) * (1.0 / NULLIF(nc, 0) + 1.0 / NULLIF(nt, 0))), 0) as z_val
    FROM stats
    WHERE nc > 0 AND nt > 0
)
SELECT 
    experiment_name,
    device_platform,
    ROUND(pc * 100, 2) as control_rate_pct,
    ROUND(pt * 100, 2) as treatment_rate_pct,
    ROUND(((pt - pc) / NULLIF(pc, 0)) * 100, 2) as lift_pct,
    ROUND(z_val, 2) as z_score,
    CASE 
        WHEN ABS(z_val) >= 1.96 THEN 'Significant'
        ELSE 'Not Significant'
    END as significance
FROM z_scores
ORDER BY experiment_name, device_platform;


-- ----------------------------------------------------------------------------
-- Query 7: City-tier Experiment Performance
-- ----------------------------------------------------------------------------
-- Business Objective: Audit conversion lift and Z-scores across Tier-1, Tier-2, 
-- and Tier-3 cities to identify metropolitan vs. regional bias.
-- BI Dashboard Widget: Segmented conversion chart by City Tier.
-- ----------------------------------------------------------------------------
WITH stats AS (
    SELECT 
        experiment_name,
        city_tier,
        SUM(CASE WHEN variant = 'Control' THEN 1.0 ELSE 0.0 END) as nc,
        SUM(CASE WHEN variant = 'Control' AND converted = TRUE THEN 1.0 ELSE 0.0 END) as xc,
        SUM(CASE WHEN variant = 'Treatment' THEN 1.0 ELSE 0.0 END) as nt,
        SUM(CASE WHEN variant = 'Treatment' AND converted = TRUE THEN 1.0 ELSE 0.0 END) as xt
    FROM experiments
    GROUP BY experiment_name, city_tier
),
z_scores AS (
    SELECT 
        experiment_name,
        city_tier,
        (xc / NULLIF(nc, 0)) as pc,
        (xt / NULLIF(nt, 0)) as pt,
        (xt / NULLIF(nt, 0) - xc / NULLIF(nc, 0)) / 
            NULLIF(SQRT(((xc + xt) / NULLIF(nc + nt, 0)) * (1.0 - ((xc + xt) / NULLIF(nc + nt, 0))) * (1.0 / NULLIF(nc, 0) + 1.0 / NULLIF(nt, 0))), 0) as z_val
    FROM stats
    WHERE nc > 0 AND nt > 0
)
SELECT 
    experiment_name,
    city_tier,
    ROUND(pc * 100, 2) as control_rate_pct,
    ROUND(pt * 100, 2) as treatment_rate_pct,
    ROUND(((pt - pc) / NULLIF(pc, 0)) * 100, 2) as lift_pct,
    ROUND(z_val, 2) as z_score,
    CASE 
        WHEN ABS(z_val) >= 1.96 THEN 'Significant'
        ELSE 'Not Significant'
    END as significance
FROM z_scores
ORDER BY experiment_name, city_tier;


-- ----------------------------------------------------------------------------
-- Query 8: Income-segment Experiment Performance
-- ----------------------------------------------------------------------------
-- Business Objective: Determine whether conversion lift varies by target affluence
-- brackets (Low, Medium, and High monthly income groups).
-- BI Dashboard Widget: Conversion lift split by income bracket.
-- ----------------------------------------------------------------------------
WITH stats AS (
    SELECT 
        experiment_name,
        income_segment,
        SUM(CASE WHEN variant = 'Control' THEN 1.0 ELSE 0.0 END) as nc,
        SUM(CASE WHEN variant = 'Control' AND converted = TRUE THEN 1.0 ELSE 0.0 END) as xc,
        SUM(CASE WHEN variant = 'Treatment' THEN 1.0 ELSE 0.0 END) as nt,
        SUM(CASE WHEN variant = 'Treatment' AND converted = TRUE THEN 1.0 ELSE 0.0 END) as xt
    FROM experiments
    GROUP BY experiment_name, income_segment
),
z_scores AS (
    SELECT 
        experiment_name,
        income_segment,
        (xc / NULLIF(nc, 0)) as pc,
        (xt / NULLIF(nt, 0)) as pt,
        (xt / NULLIF(nt, 0) - xc / NULLIF(nc, 0)) / 
            NULLIF(SQRT(((xc + xt) / NULLIF(nc + nt, 0)) * (1.0 - ((xc + xt) / NULLIF(nc + nt, 0))) * (1.0 / NULLIF(nc, 0) + 1.0 / NULLIF(nt, 0))), 0) as z_val
    FROM stats
    WHERE nc > 0 AND nt > 0
)
SELECT 
    experiment_name,
    income_segment,
    ROUND(pc * 100, 2) as control_rate_pct,
    ROUND(pt * 100, 2) as treatment_rate_pct,
    ROUND(((pt - pc) / NULLIF(pc, 0)) * 100, 2) as lift_pct,
    ROUND(z_val, 2) as z_score,
    CASE 
        WHEN ABS(z_val) >= 1.96 THEN 'Significant'
        ELSE 'Not Significant'
    END as significance
FROM z_scores
ORDER BY experiment_name, income_segment;


-- ----------------------------------------------------------------------------
-- Query 9: Winning Experiment Ranking (Financial Contribution)
-- ----------------------------------------------------------------------------
-- Business Objective: Rank A/B experiments by absolute incremental revenue
-- generated to establish clear product investment and feature prioritization.
-- BI Dashboard Widget: Incremental Revenue Leaderboard bar chart.
-- ----------------------------------------------------------------------------
WITH variant_arpu AS (
    SELECT 
        experiment_name,
        SUM(CASE WHEN variant = 'Control' THEN 1 ELSE 0 END) as control_users,
        SUM(CASE WHEN variant = 'Control' THEN revenue_generated ELSE 0 END) as control_revenue,
        SUM(CASE WHEN variant = 'Treatment' THEN 1 ELSE 0 END) as treatment_users,
        SUM(CASE WHEN variant = 'Treatment' THEN revenue_generated ELSE 0 END) as treatment_revenue
    FROM experiments
    GROUP BY experiment_name
),
gains AS (
    SELECT 
        experiment_name,
        ROUND(treatment_revenue - (control_revenue * (treatment_users::numeric / NULLIF(control_users, 0))), 2) as incremental_revenue
    FROM variant_arpu
)
SELECT 
    experiment_name,
    incremental_revenue,
    RANK() OVER (ORDER BY incremental_revenue DESC) as revenue_gain_rank
FROM gains;


-- ----------------------------------------------------------------------------
-- Query 10: Executive Experiment Scorecard (Launch Recommendation Engine)
-- ----------------------------------------------------------------------------
-- Business Objective: Provide an executive dashboard scorecard summarizing all 
-- experiments and automatically delivering a Ship/Reject/Monitor launch decision.
-- BI Dashboard Widget: Executive A/B Launch Control Scorecard Grid.
-- ----------------------------------------------------------------------------
WITH stats AS (
    SELECT 
        experiment_name,
        SUM(CASE WHEN variant = 'Control' THEN 1.0 ELSE 0.0 END) as nc,
        SUM(CASE WHEN variant = 'Control' AND converted = TRUE THEN 1.0 ELSE 0.0 END) as xc,
        SUM(CASE WHEN variant = 'Treatment' THEN 1.0 ELSE 0.0 END) as nt,
        SUM(CASE WHEN variant = 'Treatment' AND converted = TRUE THEN 1.0 ELSE 0.0 END) as xt,
        SUM(revenue_generated) as total_rev
    FROM experiments
    GROUP BY experiment_name
),
calculations AS (
    SELECT 
        experiment_name,
        (xc / nc) as pc,
        (xt / nt) as pt,
        (xt - xc * (nt / nc)) as incremental_convs,
        (pt - pc) / NULLIF(SQRT(((xc + xt) / (nc + nt)) * (1.0 - ((xc + xt) / (nc + nt))) * (1.0 / nc + 1.0 / nt)), 0) as z_val,
        total_rev
    FROM stats
)
SELECT 
    experiment_name,
    ROUND((nc + nt), 0) as total_sample_size,
    ROUND(((pt - pc) / NULLIF(pc, 0)) * 100, 2) as lift_pct,
    ROUND(z_val, 2) as z_score,
    CASE 
        WHEN z_val >= 1.96 AND (pt - pc) > 0.0 THEN 'SHIP (Rollout to 100%)'
        WHEN z_val <= -1.96 THEN 'REJECT (Rollback)'
        ELSE 'MONITOR (Gather More Data)'
    END as executive_recommendation
FROM calculations
ORDER BY z_score DESC;
