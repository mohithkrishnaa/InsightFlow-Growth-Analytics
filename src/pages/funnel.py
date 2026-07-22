"""
Funnel Analytics Dashboard Page.
Renders lifecycle progression steps, drop-off rates, and step-wise conversion graphs.
"""

import streamlit as st
from src.components.cards import render_kpi_card
from src.services.analytics import AnalyticsService
from src.components.charts import plot_conversion_funnel, plot_stage_conversion

def render_page() -> None:
    """Renders the layout and elements of the Funnel Analytics dashboard page."""
    st.title("Funnel Analytics")
    st.subheader("Deep dive into customer lifecycle progression and journey leakage")
    
    st.markdown("---")
    
    # Initialize service and load metrics
    service = AnalyticsService()
    
    try:
        funnel_data = service.get_funnel_data()
        stage_conv = service.get_stage_conversion()
        overall_df = service.get_overall_conversion()
        
        # Scalar counts for metrics
        applications = service.get_total_applications()
        disbursed = service.get_total_disbursed()
    except Exception as e:
        st.error(f"Error fetching live funnel metrics: {e}")
        return

    # Extract overall metrics
    overall_conv = float(overall_df["conversion_rate"].iloc[0]) if not overall_df.empty else 0.0
    overall_drop = 100.0 - overall_conv

    # 1. KPI Metric Cards row (4 Columns)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card(
            title="Overall Conversion",
            value=f"{overall_conv:.2f}%",
            icon="🔄"
        )
    with col2:
        render_kpi_card(
            title="Overall Drop-off",
            value=f"{overall_drop:.2f}%",
            icon="⚠️"
        )
    with col3:
        render_kpi_card(
            title="Applications",
            value=f"{applications:,}",
            icon="📝"
        )
    with col4:
        render_kpi_card(
            title="Disbursed Loans",
            value=f"{disbursed:,}",
            icon="💰"
        )
        
    st.markdown("---")
    
    # 2. Render Plotly Funnel Left & Custom Conversion Table Right
    col_chart_left, col_chart_right = st.columns([1.15, 0.85])
    with col_chart_left:
        funnel_fig = plot_conversion_funnel(funnel_data)
        funnel_fig.update_layout(height=400, margin=dict(l=135, r=30, t=20, b=20))
        st.plotly_chart(funnel_fig, use_container_width=True, config={'displayModeBar': False})
        
    with col_chart_right:
        # Build table rows dynamically
        table_rows = ""
        if not stage_conv.empty:
            for _, row in stage_conv.iterrows():
                trans = row["transition"]
                rate = float(row["conversion_rate"])
                drop = 100.0 - rate
                table_rows += f"""
                <tr>
                    <td style="padding: 10px 12px; font-size:13px; color:var(--text-secondary); border-bottom:1px solid var(--divider);">{trans}</td>
                    <td style="padding: 10px 12px; font-size:13px; color:var(--success); font-weight:600; text-align:right; border-bottom:1px solid var(--divider);">{rate:.2f}%</td>
                    <td style="padding: 10px 12px; font-size:13px; color:var(--danger); text-align:right; border-bottom:1px solid var(--divider);">{drop:.2f}%</td>
                </tr>
                """
        else:
            table_rows = "<tr><td colspan='3' style='text-align:center;color:var(--text-muted);'>No data available</td></tr>"

        conversion_table_html = f"""
        <div class="dashboard-card" style="height: 400px; display: flex; flex-direction: column; justify-content: space-between; overflow-y: auto;">
            <div>
                <div class="card-header-row" style="margin-bottom: 12px; padding: 4px 6px;">
                    <span class="card-title" style="font-size:14px; font-weight:600; color:var(--text-primary);">Stage-to-Stage Conversion</span>
                </div>
                <table class="metric-table" style="width:100%; border:none;">
                    <thead>
                        <tr style="border-bottom: 1px solid var(--border);">
                            <th style="padding: 8px 12px; border:none; color:var(--text-muted); font-size:12px;">Transition Step</th>
                            <th style="padding: 8px 12px; border:none; color:var(--text-muted); font-size:12px; text-align:right;">Conversion</th>
                            <th style="padding: 8px 12px; border:none; color:var(--text-muted); font-size:12px; text-align:right;">Drop-off</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """
        st.markdown("\n".join(line.strip() for line in conversion_table_html.strip().split("\n")), unsafe_allow_html=True)
        
    st.markdown("---")
    
    # 3. Executive Insights Section
    st.subheader("💡 Executive Insights & Recommendations")
    
    if not stage_conv.empty:
        # Find the worst converting stage transition (i.e. highest drop-off rate)
        min_conv_idx = stage_conv['conversion_rate'].idxmin()
        bottleneck = stage_conv.loc[min_conv_idx]
        transition_name = bottleneck['transition']
        conv_rate = float(bottleneck['conversion_rate'])
        drop_rate = 100.0 - conv_rate
        
        # Display rule-based recommendation based on identified bottleneck
        st.markdown(f"**Primary Lifecycle Bottleneck:**")
        st.warning(f"The largest funnel drop occurs during the transition **{transition_name}**, where **{drop_rate:.1f}%** of users drop off (conversion rate of **{conv_rate:.1f}%**).")
        
        st.markdown("**Actionable Recommendations:**")
        if "App Open -> Signup" in transition_name:
            st.info("- **Target Area:** Onboarding signup flow.\n- **Action:** Simplify social signup options, verify page loads instantly, and reduce mandatory initial fields.")
        elif "Signup -> OTP" in transition_name or "OTP" in transition_name:
            st.info("- **Target Area:** OTP verification delivery and lag.\n- **Action:** Check SMS gateway delivery latency. Implement alternative WhatsApp/Email fallback verification methods to prevent drop-off.")
        elif "KYC" in transition_name:
            st.info("- **Target Area:** Identity verification flow (PAN verification or Face Match).\n- **Action:** Introduce auto-retake tips for camera capture. Add in-app explanations of why permissions (camera/location) are requested.")
        elif "Apply -> Approved" in transition_name or "Approved" in transition_name:
            st.info("- **Target Area:** Credit underwriting algorithms.\n- **Action:** Audit validation score cut-offs. Evaluate if New-to-Credit (NTC) credit policies are rejecting otherwise creditworthy clients.")
        elif "Disbursed" in transition_name:
            st.info("- **Target Area:** Fulfillment operations.\n- **Action:** Improve bank transfer processing times and optimize loan agreement signature UX.")
        else:
            st.info("- **Target Area:** User retention campaign engagement.\n- **Action:** Schedule push notifications or localized email campaigns to re-engage stalled users.")
    else:
        st.write("No stage conversion details available to generate recommendations.")
