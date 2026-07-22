"""
Experiment Analytics Dashboard Page.
Renders A/B testing exposures, conversion lifts, z-scores significance, and launch recommendation panels.
"""

import streamlit as st
import pandas as pd
from src.components.cards import render_kpi_card
from src.services.analytics import AnalyticsService
from src.components.charts import (
    plot_experiment_comparison,
    plot_experiment_lift,
    plot_revenue_lift,
    plot_confidence_scores
)

def render_page() -> None:
    """Renders the layout and elements of the Experiment Analytics dashboard page."""
    st.title("Product Experimentation & A/B Testing")
    st.subheader("Evaluate conversion lift, statistical significance, and incremental revenue yields")
    
    st.markdown("---")
    
    # Initialize service and load metrics
    service = AnalyticsService()
    
    try:
        kpi_df = service.get_experiment_kpis()
        results_df = service.get_experiment_results()
        lift_df = service.get_conversion_lift()
        rev_lift_df = service.get_revenue_lift()
        confidence_df = service.get_confidence_scores()
    except Exception as e:
        st.error(f"Error fetching live experiment analytics metrics: {e}")
        return

    # Extract KPI card values
    if not kpi_df.empty:
        active_experiments = int(kpi_df["total_experiments"].iloc[0])
        winning_variants = int(kpi_df["winning_variants"].iloc[0])
        avg_lift = float(kpi_df["avg_lift_pct"].iloc[0]) if pd.notnull(kpi_df["avg_lift_pct"].iloc[0]) else 0.0
        total_revenue_lift = float(kpi_df["total_revenue_lift"].iloc[0]) if pd.notnull(kpi_df["total_revenue_lift"].iloc[0]) else 0.0
    else:
        active_experiments, winning_variants, avg_lift, total_revenue_lift = 0, 0, 0.0, 0.0

    # 1. KPI Metric Cards row (4 Columns)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card(
            title="Active Experiments",
            value=f"{active_experiments}",
            icon="🧪"
        )
    with col2:
        render_kpi_card(
            title="Winning Variants",
            value=f"{winning_variants}",
            icon="🏆"
        )
    with col3:
        render_kpi_card(
            title="Average Lift",
            value=f"+{avg_lift:.2f}%" if avg_lift >= 0 else f"{avg_lift:.2f}%",
            icon="📈"
        )
    with col4:
        render_kpi_card(
            title="Revenue Lift",
            value=f"INR {total_revenue_lift:,.2f}",
            icon="💰"
        )
        
    st.markdown("---")
    
    # 2. Render Plotly Charts (2 Column Grids)
    row1_left, row1_right = st.columns(2)
    with row1_left:
        comp_fig = plot_experiment_comparison(results_df)
        st.plotly_chart(comp_fig, use_container_width=True)
        
        lift_fig = plot_experiment_lift(lift_df)
        st.plotly_chart(lift_fig, use_container_width=True)
        
    with row1_right:
        rev_fig = plot_revenue_lift(rev_lift_df)
        st.plotly_chart(rev_fig, use_container_width=True)
        
        conf_fig = plot_confidence_scores(confidence_df)
        st.plotly_chart(conf_fig, use_container_width=True)
        
    st.markdown("---")
    
    # 3. Experiment Scorecard Table
    st.subheader("📊 Detailed Experiment Scorecard")
    if not confidence_df.empty and not lift_df.empty and not rev_lift_df.empty:
        # Merge all into one consolidated scorecard table
        scorecard = confidence_df.merge(lift_df, on="experiment_name")
        scorecard = scorecard.merge(rev_lift_df, on="experiment_name")
        
        formatted_scorecard = scorecard.copy()
        formatted_scorecard["lift_pct"] = formatted_scorecard["lift_pct"].apply(lambda x: f"+{x:.2f}%" if x >= 0 else f"{x:.2f}%")
        formatted_scorecard["incremental_revenue"] = formatted_scorecard["incremental_revenue"].apply(lambda x: f"INR {x:,.2f}")
        
        st.dataframe(
            formatted_scorecard,
            column_config={
                "experiment_name": "Experiment Name",
                "z_score": "Z-Score",
                "significance_status": "Confidence Status",
                "recommendation": "Launch Recommendation",
                "lift_pct": "Conversion Lift",
                "incremental_revenue": "Incremental Revenue"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.write("No scorecard statistics available.")

    st.markdown("---")
    
    # 4. Executive Recommendations Panel
    st.subheader("💡 Experimentation Insights & Rollout Recommendations")
    
    if not lift_df.empty and not rev_lift_df.empty and not confidence_df.empty:
        best_lift_row = lift_df.loc[lift_df["lift_pct"].idxmax()]
        best_lift_exp = best_lift_row["experiment_name"]
        best_lift_val = best_lift_row["lift_pct"]
        
        best_rev_row = rev_lift_df.loc[rev_lift_df["incremental_revenue"].idxmax()]
        best_rev_exp = best_rev_row["experiment_name"]
        best_rev_val = best_rev_row["incremental_revenue"]
        
        # Count status
        ships = sum(confidence_df["recommendation"] == "Ship")
        monitors = sum(confidence_df["recommendation"] == "Monitor")
        rejects = sum(confidence_df["recommendation"] == "Reject")
        
        st.markdown(f"""
        - **Best Performing Variant (Conversion Lift):** **{best_lift_exp}** drove the highest conversion improvement of **+{best_lift_val:.2f}%** over the Control group.
        - **Highest Value Variant (Revenue Lift):** **{best_rev_exp}** contributed the greatest business impact, generating **INR {best_rev_val:,.2f}** in incremental revenues.
        - **Significant Rollout Decisions:** Out of **{active_experiments}** active tests, **{ships}** are ready to Ship, **{monitors}** require further monitoring, and **{rejects}** should be rejected/rolled back.
        """)
        
        st.markdown("**Executive Launch Decisions:**")
        # List actual ship recommendations
        ship_list = confidence_df[confidence_df["recommendation"] == "Ship"]["experiment_name"].tolist()
        reject_list = confidence_df[confidence_df["recommendation"] == "Reject"]["experiment_name"].tolist()
        monitor_list = confidence_df[confidence_df["recommendation"] == "Monitor"]["experiment_name"].tolist()
        
        if ship_list:
            st.success(f"🚀 **Action - SHIP (Roll out to 100%):** {', '.join(ship_list)}. These experiments have cleared the 95% confidence threshold (Z >= 1.96) with positive conversion rates.")
        if monitor_list:
            st.info(f"⏳ **Action - MONITOR (Gather More Data):** {', '.join(monitor_list)}. These changes show promising trends but require more sample size to rule out random variance.")
        if reject_list:
            st.error(f"🛑 **Action - REJECT (Roll back):** {', '.join(reject_list)}. These experiments showed statistically significant negative conversion rates or no value, roll back immediately.")
    else:
        st.write("No experimentation metrics available to generate insights.")
