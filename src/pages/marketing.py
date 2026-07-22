"""
Marketing Attribution Analytics Dashboard Page.
Renders campaign performances, channels ROI metrics, and acquisition unit costs (CAC).
"""

import streamlit as st
from src.components.cards import render_kpi_card
from src.services.analytics import AnalyticsService
from src.components.charts import plot_channel_roi, plot_spend_vs_revenue, plot_channel_cac

def render_page() -> None:
    """Renders the layout and elements of the Marketing Attribution page."""
    st.title("Marketing Attribution & ROI Analysis")
    st.subheader("Evaluate channel returns, budget efficiency, and campaign conversions")
    
    st.markdown("---")
    
    # Initialize service and load metrics
    service = AnalyticsService()
    
    try:
        kpi_df = service.get_marketing_kpis()
        roi_df = service.get_roi_by_channel()
        spend_rev_df = service.get_spend_vs_revenue()
        cac_df = service.get_cac_by_channel()
        campaigns_df = service.get_campaign_performance()
    except Exception as e:
        st.error(f"Error fetching live marketing attribution metrics: {e}")
        return

    # Extract KPI card values
    if not kpi_df.empty:
        total_campaigns = int(kpi_df["total_campaigns"].iloc[0])
        total_spend = float(kpi_df["total_spend"].iloc[0])
        overall_roi = float(kpi_df["overall_roi_pct"].iloc[0])
        average_cac = float(kpi_df["average_cac"].iloc[0])
    else:
        total_campaigns, total_spend, overall_roi, average_cac = 0, 0.0, 0.0, 0.0

    # 1. Render KPI Metric Cards row (4 Columns)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card(
            title="Total Campaigns",
            value=f"{total_campaigns}",
            icon="📢"
        )
    with col2:
        render_kpi_card(
            title="Marketing Spend",
            value=f"INR {total_spend:,.2f}",
            icon="💸"
        )
    with col3:
        render_kpi_card(
            title="Overall ROI",
            value=f"{overall_roi:.2f}%",
            icon="📈"
        )
    with col4:
        render_kpi_card(
            title="Average CAC",
            value=f"INR {average_cac:,.2f}",
            icon="🎯"
        )
        
    st.markdown("---")
    
    # 2. Render Plotly Charts (2 Column Layout)
    col_chart_left, col_chart_right = st.columns(2)
    with col_chart_left:
        roi_fig = plot_channel_roi(roi_df)
        st.plotly_chart(roi_fig, use_container_width=True)
        
        cac_fig = plot_channel_cac(cac_df)
        st.plotly_chart(cac_fig, use_container_width=True)
        
    with col_chart_right:
        spend_rev_fig = plot_spend_vs_revenue(spend_rev_df)
        st.plotly_chart(spend_rev_fig, use_container_width=True)
        
    st.markdown("---")
    
    # 3. Campaign Performance Table
    st.subheader("📊 Detailed Campaign Performance")
    if not campaigns_df.empty:
        # Format columns for display
        formatted_df = campaigns_df.copy()
        formatted_df["campaign_spend"] = formatted_df["campaign_spend"].apply(lambda x: f"INR {x:,.2f}")
        formatted_df["cac"] = formatted_df["cac"].apply(lambda x: f"INR {x:,.2f}")
        formatted_df["install_to_signup_rate_pct"] = formatted_df["install_to_signup_rate_pct"].apply(lambda x: f"{x:.2f}%")
        formatted_df["signup_to_disbursed_rate_pct"] = formatted_df["signup_to_disbursed_rate_pct"].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(
            formatted_df,
            column_config={
                "campaign": "Campaign Name",
                "channel": "Channel",
                "campaign_spend": "Spend",
                "total_installs": "Installs",
                "signups": "Signups",
                "disbursements": "Disbursed",
                "cac": "Campaign CAC",
                "install_to_signup_rate_pct": "Install-to-Signup",
                "signup_to_disbursed_rate_pct": "Signup-to-Disbursed"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.write("No campaign performance data available.")

    st.markdown("---")

    # 4. Executive Recommendations
    st.subheader("💡 Marketing Executive Insights & Budget Reallocation")
    
    # Programmatic insights based on data
    if not roi_df.empty and not cac_df.empty:
        highest_roi_row = roi_df.loc[roi_df["roi_pct"].idxmax()]
        lowest_roi_row = roi_df.loc[roi_df["roi_pct"].idxmin()]
        highest_cac_row = cac_df.loc[cac_df["customer_acquisition_cost"].idxmax()]
        
        highest_roi_channel = highest_roi_row["acquisition_channel"]
        highest_roi_val = highest_roi_row["roi_pct"]
        
        lowest_roi_channel = lowest_roi_row["acquisition_channel"]
        lowest_roi_val = lowest_roi_row["roi_pct"]
        
        highest_cac_channel = highest_cac_row["acquisition_channel"]
        highest_cac_val = highest_cac_row["customer_acquisition_cost"]
        
        st.markdown(f"""
        - **Highest Performing Channel (ROI):** **{highest_roi_channel}** yields the highest financial return at **{highest_roi_val:.2f}%** ROI.
        - **Lowest Performing Channel (ROI):** **{lowest_roi_channel}** is underperforming at **{lowest_roi_val:.2f}%** ROI.
        - **Highest Cost Channel (CAC):** **{highest_cac_channel}** represents the highest customer acquisition friction with a unit CAC of **INR {highest_cac_val:,.2f}**.
        """)
        
        st.markdown("**Suggested Budget Reallocation Strategy:**")
        st.success(f"""
        We recommend decreasing ad spend allocation on the underperforming **{lowest_roi_channel}** channel and reallocating the freed capital to **{highest_roi_channel}**. 
        Additionally, the campaign and bidding settings for **{highest_cac_channel}** should be audited to optimize conversion rates and reduce the acquisition cost per borrower.
        """)
    else:
        st.write("No performance data available to generate insights.")
