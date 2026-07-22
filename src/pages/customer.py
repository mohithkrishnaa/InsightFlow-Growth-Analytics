"""
Customer Portfolio and Risk Analytics Dashboard Page.
Renders demographic breakdowns, credit rating distributions, and geo/device usage.
"""

import streamlit as st
import pandas as pd
from src.components.cards import render_kpi_card
from src.services.analytics import AnalyticsService
from src.components.charts import plot_histogram, plot_pie, plot_bar_vertical, plot_bar_horizontal

def render_page() -> None:
    """Renders the layout and elements of the Customer Analytics dashboard page."""
    st.title("Customer Portfolio Analytics")
    st.subheader("Analyze portfolio risk tiers, regional density, and demographic segments")
    
    st.markdown("---")
    
    # Initialize service and load metrics
    service = AnalyticsService()
    
    try:
        kpi_df = service.get_customer_kpis()
        cibil_df = service.get_cibil_distribution()
        income_df = service.get_income_distribution()
        state_df = service.get_state_distribution()
        occupation_df = service.get_occupation_distribution()
        device_df = service.get_device_distribution()
        age_df = service.get_age_distribution()
    except Exception as e:
        st.error(f"Error fetching live customer portfolio metrics: {e}")
        return

    # Extract KPI card values
    if not kpi_df.empty:
        total_customers = int(kpi_df["total_customers"].iloc[0])
        avg_income = float(kpi_df["avg_income"].iloc[0]) if pd.notnull(kpi_df["avg_income"].iloc[0]) else 0.0
        avg_cibil = float(kpi_df["avg_cibil"].iloc[0]) if pd.notnull(kpi_df["avg_cibil"].iloc[0]) else 0.0
        active_states = int(kpi_df["active_states"].iloc[0])
    else:
        total_customers, avg_income, avg_cibil, active_states = 0, 0.0, 0.0, 0

    # 1. KPI Metric Cards row (4 Columns)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card(
            title="Total Customers",
            value=f"{total_customers:,}",
            icon="👥"
        )
    with col2:
        render_kpi_card(
            title="Average Income",
            value=f"INR {avg_income:,.2f}",
            icon="💰"
        )
    with col3:
        render_kpi_card(
            title="Average CIBIL",
            value=f"{avg_cibil:.1f}" if avg_cibil > 0 else "N/A",
            icon="📊"
        )
    with col4:
        render_kpi_card(
            title="Active States",
            value=f"{active_states}",
            icon="🗺️"
        )
        
    st.markdown("---")
    
    # 2. Render Plotly Charts (2 Column Grids)
    row1_left, row1_right = st.columns(2)
    with row1_left:
        cibil_fig = plot_histogram(cibil_df, "cibil_score", "CIBIL Score Distribution", "CIBIL Score", nbins=20)
        st.plotly_chart(cibil_fig, use_container_width=True)
        
    with row1_right:
        income_fig = plot_histogram(income_df, "monthly_income", "Monthly Income Distribution", "Income (INR)", nbins=25)
        st.plotly_chart(income_fig, use_container_width=True)
        
    st.markdown("---")
    
    row2_left, row2_right = st.columns(2)
    with row2_left:
        occ_fig = plot_bar_horizontal(occupation_df, "user_count", "occupation", "Occupation Distribution", "User Count", "Occupation")
        st.plotly_chart(occ_fig, use_container_width=True)
        
    with row2_right:
        state_fig = plot_bar_vertical(state_df, "state", "user_count", "State-wise Customer Volume", "State", "User Count")
        st.plotly_chart(state_fig, use_container_width=True)
        
    st.markdown("---")
    
    row3_left, row3_right = st.columns(2)
    with row3_left:
        dev_fig = plot_pie(device_df, "user_count", "device_platform", "Device Platform Usage")
        st.plotly_chart(dev_fig, use_container_width=True)
        
    with row3_right:
        age_fig = plot_histogram(age_df, "age", "User Age Distribution", "Age", nbins=15)
        st.plotly_chart(age_fig, use_container_width=True)
        
    st.markdown("---")
    
    # 3. Executive Insights Section
    st.subheader("💡 Customer Insights & Strategic Demographics")
    
    # Programmatic insights based on distributions
    if not state_df.empty and not occupation_df.empty:
        top_state = state_df.iloc[0]["state"]
        top_state_count = state_df.iloc[0]["user_count"]
        top_state_pct = (top_state_count / total_customers) * 100 if total_customers > 0 else 0.0
        
        top_occupation = occupation_df.iloc[0]["occupation"]
        top_occupation_count = occupation_df.iloc[0]["user_count"]
        top_occupation_pct = (top_occupation_count / total_customers) * 100 if total_customers > 0 else 0.0
        
        top_device_platform = "Android"
        if not device_df.empty:
            top_device_platform = device_df.loc[device_df["user_count"].idxmax()]["device_platform"]

        st.markdown(f"""
        - **State Concentration:** **{top_state}** has the highest customer concentration with **{top_state_count:,}** registered users (**{top_state_pct:.1f}%** of portfolio).
        - **Largest Occupational Cohort:** **{top_occupation}** constitutes the largest demographic segment with **{top_occupation_count:,}** registered users (**{top_occupation_pct:.1f}%** of portfolio).
        - **Average Credit Rating:** The portfolio average CIBIL rating sits at **{avg_cibil:.1f}** for customers with active credit files.
        """)
        
        st.markdown("**Suggested Marketing & Product Focus:**")
        st.info(f"""
        Based on demographic density, marketing campaigns should run localized target promotions in **{top_state}** designed for **{top_occupation}** professionals. 
        Additionally, ensuring seamless app performance on **{top_device_platform}** is critical as it represents the dominant mobile user interface in this segment.
        """)
    else:
        st.write("No demographic statistics available to generate insights.")
