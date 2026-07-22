"""
About Information Page for the InsightFlow Dashboard.
"""

import streamlit as st

def render_page() -> None:
    """Renders the About details page."""
    st.title("About InsightFlow")
    st.markdown("""
    **InsightFlow** is an enterprise-grade customer lifecycle and analytics dashboard platform.
    
    ### Key Modules & Capabilities
    - **Executive Overview**: High-level summaries of business operations and loan portfolios.
    - **Funnel Analytics**: Operational insights into customer transition steps and leakage.
    - **Marketing Attribution**: ROI calculations, CPA analysis, and channel attribution.
    - **Customer Analytics**: Credit health brackets, demographics, and risk profiles.
    - **Experiment Analytics**: High-fidelity A/B testing z-scores and rollout controls.
    """)
