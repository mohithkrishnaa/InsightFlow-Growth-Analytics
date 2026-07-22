import streamlit as st
"""
Analytics Service Orchestration layer.
Executes raw SQL queries via pandas.read_sql and prepares structured DataFrames/scalar values.
"""

import pandas as pd
from src.database.connection import get_engine

class AnalyticsService:
    """Service class executing warehouse queries and compiling statistics."""
    
    def __init__(self) -> None:
        """Initializes the analytics service with the global database engine."""
        self.engine = get_engine()
        
    @st.cache_data(ttl=600)
    def get_total_users(_self) -> int:
        """
        Retrieves the total count of registered users.
        
        Returns:
            int: Total registered user count.
        """
        query = "SELECT COUNT(*) as count FROM users;"
        df = pd.read_sql(query, _self.engine)
        val = df["count"].iloc[0]
        return int(val) if pd.notnull(val) else 0

    @st.cache_data(ttl=600)
    def get_total_marketing_events(_self) -> int:
        """
        Retrieves the total count of marketing events.
        
        Returns:
            int: Total marketing event count.
        """
        query = "SELECT COUNT(*) as count FROM marketing_events;"
        df = pd.read_sql(query, _self.engine)
        val = df["count"].iloc[0]
        return int(val) if pd.notnull(val) else 0

    @st.cache_data(ttl=600)
    def get_total_applications(_self) -> int:
        """
        Retrieves the total count of loan applications.
        
        Returns:
            int: Total applications count.
        """
        query = "SELECT COUNT(*) as count FROM app_events WHERE event_name = 'Loan Apply';"
        df = pd.read_sql(query, _self.engine)
        val = df["count"].iloc[0]
        return int(val) if pd.notnull(val) else 0

    @st.cache_data(ttl=600)
    def get_total_disbursed(_self) -> int:
        """
        Retrieves the total number of disbursed loans.
        
        Returns:
            int: Count of disbursed loans.
        """
        query = "SELECT COUNT(*) as count FROM loan_events WHERE approval_status = 'Disbursed';"
        df = pd.read_sql(query, _self.engine)
        val = df["count"].iloc[0]
        return int(val) if pd.notnull(val) else 0

    @st.cache_data(ttl=600)
    def get_approval_rate(_self) -> float:
        """
        Calculates the loan approval rate percentage.
        
        Returns:
            float: Loan approval rate (percentage).
        """
        query = (
            "SELECT (COUNT(CASE WHEN approval_status IN ('Approved', 'Disbursed') THEN 1 END)::float / "
            "NULLIF(COUNT(*), 0)) * 100 as rate FROM loan_events;"
        )
        df = pd.read_sql(query, _self.engine)
        val = df["rate"].iloc[0]
        return float(val) if pd.notnull(val) else 0.0

    @st.cache_data(ttl=600)
    def get_average_loan_amount(_self) -> float:
        """
        Calculates the average loan amount for approved/disbursed loans.
        
        Returns:
            float: Average loan amount.
        """
        query = "SELECT AVG(loan_amount) as avg_amt FROM loan_events WHERE approval_status IN ('Approved', 'Disbursed');"
        df = pd.read_sql(query, _self.engine)
        val = df["avg_amt"].iloc[0]
        return float(val) if pd.notnull(val) else 0.0
    def _get_marketing_events_cte(self) -> str:
        """
        Returns a CTE string acting as a compatibility layer that dynamically
        adds 'event_type' to 'marketing_events' using sequential row number partitioning.
        """
        return """
        normalized_marketing AS (
            SELECT 
                event_id,
                user_id,
                campaign,
                channel,
                ad_group,
                device,
                state,
                cost,
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
        )
        """

    @st.cache_data(ttl=600)
    def get_funnel_data(_self) -> pd.DataFrame:
        """
        Retrieves user volumes and percentage rates across all funnel stages.
        
        Returns:
            pd.DataFrame: DataFrame containing stage_num, stage_name, unique_users, pct_of_tof, pct_of_previous.
        """
        query = f"""
        WITH {_self._get_marketing_events_cte()},
        funnel_volumes AS (
            SELECT 1 AS stage_num, 'Marketing Impression' AS stage_name, COUNT(DISTINCT user_id) AS unique_users
            FROM normalized_marketing WHERE event_type = 'Impression'
            UNION ALL
            SELECT 2, 'Marketing Click', COUNT(DISTINCT user_id)
            FROM normalized_marketing WHERE event_type = 'Click'
            UNION ALL
            SELECT 3, 'Marketing Install', COUNT(DISTINCT user_id)
            FROM normalized_marketing WHERE event_type = 'Install'
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
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_stage_conversion(_self) -> pd.DataFrame:
        """
        Retrieves step-to-step stage conversion rates.
        
        Returns:
            pd.DataFrame: DataFrame containing transition and conversion_rate.
        """
        query = """
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
        SELECT 'App Open -> Signup' AS transition, ROUND((s2_signup::numeric / NULLIF(s1_app_open, 0)) * 100, 2) AS conversion_rate FROM totals
        UNION ALL
        SELECT 'Signup -> OTP Verification', ROUND((s3_otp::numeric / NULLIF(s2_signup, 0)) * 100, 2) FROM totals
        UNION ALL
        SELECT 'OTP Verification -> KYC Start', ROUND((s4_kyc_start::numeric / NULLIF(s3_otp, 0)) * 100, 2) FROM totals
        UNION ALL
        SELECT 'KYC Start -> KYC Complete', ROUND((s5_kyc_complete::numeric / NULLIF(s4_kyc_start, 0)) * 100, 2) FROM totals
        UNION ALL
        SELECT 'KYC Complete -> Loan Apply', ROUND((s6_loan_apply::numeric / NULLIF(s5_kyc_complete, 0)) * 100, 2) FROM totals
        UNION ALL
        SELECT 'Loan Apply -> Loan Approved', ROUND((s7_loan_approve::numeric / NULLIF(s6_loan_apply, 0)) * 100, 2) FROM totals
        UNION ALL
        SELECT 'Loan Approved -> Loan Disbursed', ROUND((s8_loan_disburse::numeric / NULLIF(s7_loan_approve, 0)) * 100, 2) FROM totals;
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_overall_conversion(_self) -> pd.DataFrame:
        """
        Calculates overall funnel conversion rate (App Open to Disbursed).
        
        Returns:
            pd.DataFrame: DataFrame containing overall conversion metrics.
        """
        query = """
        WITH totals AS (
            SELECT 
                COUNT(DISTINCT CASE WHEN ae.event_name = 'App Open' THEN u.user_id END) as app_open,
                COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN u.user_id END) as disbursed
            FROM users u
            LEFT JOIN app_events ae ON u.user_id = ae.user_id
            LEFT JOIN loan_events le ON u.user_id = le.user_id
        )
        SELECT 
            app_open,
            disbursed,
            ROUND((disbursed::numeric / NULLIF(app_open, 0)) * 100, 2) as conversion_rate
        FROM totals;
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_marketing_kpis(_self) -> pd.DataFrame:
        """
        Retrieves high-level marketing metrics: campaigns count, total spend, revenue, overall ROI, and avg CAC.
        
        Returns:
            pd.DataFrame: Single row DataFrame containing marketing KPIs.
        """
        query = """
        WITH spend AS (
            SELECT SUM(cost) as total_spend FROM marketing_events
        ),
        rev_cac AS (
            SELECT 
                COUNT(DISTINCT CASE WHEN le.approval_status = 'Disbursed' THEN u.user_id END) as disbursed_users,
                SUM(CASE WHEN le.approval_status = 'Disbursed' THEN le.loan_amount * 0.02 + le.loan_amount * (le.interest_rate / 100.0) ELSE 0 END) as total_revenue
            FROM users u
            LEFT JOIN loan_events le ON u.user_id = le.user_id
        )
        SELECT 
            (SELECT COUNT(DISTINCT campaign) FROM marketing_events) as total_campaigns,
            s.total_spend,
            rc.total_revenue,
            ROUND(((rc.total_revenue - s.total_spend) / s.total_spend) * 100, 2) as overall_roi_pct,
            CASE WHEN rc.disbursed_users > 0 THEN ROUND((s.total_spend / rc.disbursed_users), 2) ELSE 0.00 END as average_cac
        FROM spend s, rev_cac rc;
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_roi_by_channel(_self) -> pd.DataFrame:
        """
        Retrieves ROI split by marketing channel.
        
        Returns:
            pd.DataFrame: DataFrame containing acquisition_channel and roi_pct.
        """
        query = """
        WITH channel_spend AS (
            SELECT channel, SUM(cost) as total_spend FROM marketing_events GROUP BY channel
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
            ROUND(((COALESCE(cr.total_revenue, 0) - cs.total_spend) / cs.total_spend) * 100, 2) as roi_pct
        FROM channel_spend cs
        LEFT JOIN channel_revenue cr ON cs.channel = cr.acquisition_channel
        ORDER BY roi_pct DESC;
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_spend_vs_revenue(_self) -> pd.DataFrame:
        """
        Retrieves channel-level comparison of marketing spend vs generated revenue.
        
        Returns:
            pd.DataFrame: DataFrame containing acquisition_channel, marketing_spend, and estimated_revenue.
        """
        query = """
        WITH channel_spend AS (
            SELECT channel, SUM(cost) as total_spend FROM marketing_events GROUP BY channel
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
            ROUND(COALESCE(cr.total_revenue, 0), 2) as estimated_revenue
        FROM channel_spend cs
        LEFT JOIN channel_revenue cr ON cs.channel = cr.acquisition_channel
        ORDER BY cs.total_spend DESC;
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_cac_by_channel(_self) -> pd.DataFrame:
        """
        Retrieves Customer Acquisition Cost (CAC) split by channel.
        
        Returns:
            pd.DataFrame: DataFrame containing acquisition_channel and customer_acquisition_cost.
        """
        query = """
        WITH channel_spend AS (
            SELECT channel, SUM(cost) as total_spend FROM marketing_events GROUP BY channel
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
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_campaign_performance(_self) -> pd.DataFrame:
        """
        Retrieves metrics grouped by marketing campaign.
        
        Returns:
            pd.DataFrame: DataFrame containing campaign metrics.
        """
        query = f"""
        WITH {_self._get_marketing_events_cte()},
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
        ),
        campaign_spend AS (
            SELECT 
                campaign,
                channel,
                SUM(cost) as total_spend
            FROM marketing_events
            GROUP BY campaign, channel
        )
        SELECT 
            cf.campaign,
            cf.channel,
            COALESCE(cs.total_spend, 0) as campaign_spend,
            cf.total_installs,
            cf.signups,
            cf.disbursements,
            CASE WHEN cf.disbursements > 0 THEN ROUND((cs.total_spend / cf.disbursements), 2) ELSE 0.00 END as cac,
            ROUND((cf.signups::numeric / NULLIF(cf.total_installs, 0)) * 100, 2) as install_to_signup_rate_pct,
            ROUND((cf.disbursements::numeric / NULLIF(cf.signups, 0)) * 100, 2) as signup_to_disbursed_rate_pct
        FROM campaign_funnel cf
        LEFT JOIN campaign_spend cs ON cf.campaign = cs.campaign AND cf.channel = cs.channel
        ORDER BY disbursements DESC;
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_customer_kpis(_self) -> pd.DataFrame:
        """
        Retrieves high-level portfolio KPIs: total customers, avg income, avg CIBIL, and active states count.
        
        Returns:
            pd.DataFrame: Single row DataFrame containing customer KPIs.
        """
        query = """
        SELECT 
            COUNT(DISTINCT user_id) as total_customers,
            AVG(monthly_income) as avg_income,
            AVG(CASE WHEN has_credit_history = TRUE THEN cibil_score END) as avg_cibil,
            COUNT(DISTINCT state) as active_states
        FROM users;
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_cibil_distribution(_self) -> pd.DataFrame:
        """
        Retrieves the raw CIBIL scores of users with credit history.
        
        Returns:
            pd.DataFrame: DataFrame containing cibil_score.
        """
        query = "SELECT cibil_score FROM users WHERE has_credit_history = TRUE AND cibil_score IS NOT NULL;"
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_income_distribution(_self) -> pd.DataFrame:
        """
        Retrieves the monthly incomes of all users.
        
        Returns:
            pd.DataFrame: DataFrame containing monthly_income.
        """
        query = "SELECT monthly_income FROM users WHERE monthly_income IS NOT NULL;"
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_state_distribution(_self) -> pd.DataFrame:
        """
        Retrieves user counts grouped by state.
        
        Returns:
            pd.DataFrame: DataFrame containing state and user_count.
        """
        query = "SELECT state, COUNT(*) as user_count FROM users WHERE state IS NOT NULL GROUP BY state ORDER BY user_count DESC;"
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_occupation_distribution(_self) -> pd.DataFrame:
        """
        Retrieves user counts grouped by occupation.
        
        Returns:
            pd.DataFrame: DataFrame containing occupation and user_count.
        """
        query = "SELECT occupation, COUNT(*) as user_count FROM users WHERE occupation IS NOT NULL GROUP BY occupation ORDER BY user_count DESC;"
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_device_distribution(_self) -> pd.DataFrame:
        """
        Retrieves user counts grouped by device platform.
        
        Returns:
            pd.DataFrame: DataFrame containing device_platform and user_count.
        """
        query = """
        SELECT 
            CASE 
                WHEN device LIKE '%%Android%%' THEN 'Android'
                WHEN device LIKE '%%iPhone%%' OR device LIKE '%%iOS%%' OR device LIKE '%%iPad%%' THEN 'iOS'
                ELSE 'Other'
            END as device_platform,
            COUNT(*) as user_count
        FROM users
        GROUP BY device_platform;
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_age_distribution(_self) -> pd.DataFrame:
        """
        Retrieves the age of all users.
        
        Returns:
            pd.DataFrame: DataFrame containing age.
        """
        query = "SELECT age FROM users;"
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_experiment_kpis(_self) -> pd.DataFrame:
        """
        Retrieves high-level experiment metrics: active count, winning variants, avg lift, and total revenue lift.
        
        Returns:
            pd.DataFrame: Single row DataFrame containing experiment KPIs.
        """
        query = """
        WITH stats AS (
            SELECT 
                experiment_name,
                SUM(CASE WHEN variant = 'Control' THEN 1.0 ELSE 0.0 END) as nc,
                SUM(CASE WHEN variant = 'Control' AND converted = TRUE THEN 1.0 ELSE 0.0 END) as xc,
                SUM(CASE WHEN variant = 'Treatment' THEN 1.0 ELSE 0.0 END) as nt,
                SUM(CASE WHEN variant = 'Treatment' AND converted = TRUE THEN 1.0 ELSE 0.0 END) as xt,
                (SUM(CASE WHEN variant = 'Control' AND converted = TRUE THEN 1.0 ELSE 0.0 END) / NULLIF(SUM(CASE WHEN variant = 'Control' THEN 1.0 ELSE 0.0 END), 0)) as pc,
                (SUM(CASE WHEN variant = 'Treatment' AND converted = TRUE THEN 1.0 ELSE 0.0 END) / NULLIF(SUM(CASE WHEN variant = 'Treatment' THEN 1.0 ELSE 0.0 END), 0)) as pt,
                SUM(CASE WHEN variant = 'Control' THEN revenue_generated ELSE 0 END) as control_rev,
                SUM(CASE WHEN variant = 'Treatment' THEN revenue_generated ELSE 0 END) as treatment_rev
            FROM experiments
            GROUP BY experiment_name
        ),
        calculations AS (
            SELECT 
                experiment_name,
                nc,
                nt,
                xc,
                xt,
                pc,
                pt,
                control_rev,
                treatment_rev,
                (pt - pc) / NULLIF(SQRT(((xc + xt) / NULLIF(nc + nt, 0)) * (1.0 - ((xc + xt) / NULLIF(nc + nt, 0))) * (1.0 / NULLIF(nc, 0) + 1.0 / NULLIF(nt, 0))), 0) as z_val,
                ROUND(treatment_rev - (control_rev * (nt / NULLIF(nc, 0))), 2) as incremental_revenue
            FROM stats
            WHERE nc > 0 AND nt > 0
        )
        SELECT 
            COUNT(DISTINCT experiment_name) as total_experiments,
            SUM(CASE WHEN z_val >= 1.96 AND pt > pc THEN 1 ELSE 0 END) as winning_variants,
            ROUND(AVG(((pt - pc) / NULLIF(pc, 0)) * 100), 2) as avg_lift_pct,
            SUM(incremental_revenue) as total_revenue_lift
        FROM calculations;
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_experiment_results(_self) -> pd.DataFrame:
        """
        Retrieves Control vs Treatment sample size, conversions, and conversion rates per experiment.
        
        Returns:
            pd.DataFrame: DataFrame containing experiment results.
        """
        query = """
        SELECT 
            experiment_name,
            variant,
            COUNT(DISTINCT user_id) as sample_size,
            SUM(CASE WHEN converted = TRUE THEN 1 ELSE 0 END) as conversions,
            ROUND((SUM(CASE WHEN converted = TRUE THEN 1 ELSE 0 END)::numeric / COUNT(DISTINCT user_id)) * 100, 2) as conversion_rate
        FROM experiments
        GROUP BY experiment_name, variant
        ORDER BY experiment_name, variant;
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_conversion_lift(_self) -> pd.DataFrame:
        """
        Retrieves conversion lift percentage of Treatment over Control.
        
        Returns:
            pd.DataFrame: DataFrame containing experiment_name and lift_pct.
        """
        query = """
        WITH stats AS (
            SELECT 
                experiment_name,
                SUM(CASE WHEN variant = 'Control' THEN 1.0 ELSE 0.0 END) as nc,
                SUM(CASE WHEN variant = 'Control' AND converted = TRUE THEN 1.0 ELSE 0.0 END) as xc,
                SUM(CASE WHEN variant = 'Treatment' THEN 1.0 ELSE 0.0 END) as nt,
                SUM(CASE WHEN variant = 'Treatment' AND converted = TRUE THEN 1.0 ELSE 0.0 END) as xt
            FROM experiments
            GROUP BY experiment_name
        )
        SELECT 
            experiment_name,
            ROUND((((xt / NULLIF(nt, 0)) - (xc / NULLIF(nc, 0))) / NULLIF((xc / NULLIF(nc, 0)), 0)) * 100, 2) as lift_pct
        FROM stats
        ORDER BY lift_pct DESC;
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_revenue_lift(_self) -> pd.DataFrame:
        """
        Retrieves incremental revenue lift per experiment.
        
        Returns:
            pd.DataFrame: DataFrame containing experiment_name and incremental_revenue.
        """
        query = """
        WITH stats AS (
            SELECT 
                experiment_name,
                SUM(CASE WHEN variant = 'Control' THEN 1 ELSE 0 END) as nc,
                SUM(CASE WHEN variant = 'Control' THEN revenue_generated ELSE 0 END) as rc,
                SUM(CASE WHEN variant = 'Treatment' THEN 1 ELSE 0 END) as nt,
                SUM(CASE WHEN variant = 'Treatment' THEN revenue_generated ELSE 0 END) as rt
            FROM experiments
            GROUP BY experiment_name
        )
        SELECT 
            experiment_name,
            ROUND(rt - (rc * (nt::numeric / NULLIF(nc, 0))), 2) as incremental_revenue
        FROM stats
        ORDER BY incremental_revenue DESC;
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_confidence_scores(_self) -> pd.DataFrame:
        """
        Retrieves z-score and statistical significance classifications.
        
        Returns:
            pd.DataFrame: DataFrame containing z_score, significance_status, and recommendation.
        """
        query = """
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
        calculations AS (
            SELECT 
                experiment_name,
                (xc / NULLIF(nc, 0)) as pc,
                (xt / NULLIF(nt, 0)) as pt,
                (xt / NULLIF(nt, 0) - xc / NULLIF(nc, 0)) / 
                    NULLIF(SQRT(((xc + xt) / NULLIF(nc + nt, 0)) * (1.0 - ((xc + xt) / NULLIF(nc + nt, 0))) * (1.0 / NULLIF(nc, 0) + 1.0 / NULLIF(nt, 0))), 0) as z_val
            FROM stats
            WHERE nc > 0 AND nt > 0
        )
        SELECT 
            experiment_name,
            ROUND(z_val, 2) as z_score,
            ROUND(ABS(z_val), 2) as abs_z_score,
            CASE 
                WHEN ABS(z_val) >= 1.96 THEN 'Significant'
                ELSE 'Not Significant'
            END as significance_status,
            CASE 
                WHEN z_val >= 1.96 AND pt > pc THEN 'Ship'
                WHEN z_val <= -1.96 THEN 'Reject'
                ELSE 'Monitor'
            END as recommendation
        FROM calculations
        ORDER BY abs_z_score DESC;
        """
        return pd.read_sql(query, _self.engine)

    @st.cache_data(ttl=600)
    def get_daily_user_trend(_self, start_date: str = '2026-06-24', end_date: str = '2026-06-30') -> pd.DataFrame:
        """
        Retrieves daily registrations and app opens count for the specified date range.
        """
        query = f"""
        SELECT 
            DATE(timestamp) as date,
            COUNT(DISTINCT CASE WHEN event_name = 'Signup' THEN user_id END) as users,
            COUNT(DISTINCT CASE WHEN event_name = 'App Open' THEN user_id END) as app_opens
        FROM app_events
        WHERE timestamp >= '{start_date}' AND timestamp <= '{end_date}'
        GROUP BY DATE(timestamp)
        ORDER BY date ASC;
        """
        return pd.read_sql(query, _self.engine)

