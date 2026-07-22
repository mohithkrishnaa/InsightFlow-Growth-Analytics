"""
Main Entry Point for the InsightFlow Streamlit Application.
Sets up Streamlit configurations, loads stylesheets, renders navigation header,
and routes to the appropriate dashboard pages.
"""

import os
import streamlit as st
from src.components.sidebar import render_sidebar
import src.pages.executive as executive
import src.pages.funnel as funnel
import src.pages.marketing as marketing
import src.pages.customer as customer
import src.pages.experiments as experiments

def clean_html(s: str) -> str:
    """Strips all leading/trailing whitespace from every line of HTML to prevent Markdown parser code-block bugs."""
    return "\n".join(line.strip() for line in s.strip().split("\n"))

def load_css(file_name: str) -> None:
    """
    Loads custom CSS styles and injects them into the Streamlit session.
    
    Args:
        file_name (str): Relative path to the CSS file.
    """
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def render_mock_page(title: str) -> None:
    """Renders a beautiful placeholder page for mock routes in the design hierarchy."""
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    st.markdown("<p class='page-subtitle'>Enterprise-grade automated intelligence and transaction routing statistics</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.info(f"The **{title}** analytical engine is currently synchronizing with the production PostgreSQL warehouse. Automated predictions, cohort classifications, and alert triggers will be available in the next release.")

def main() -> None:
    """Main routing and initial configuration wrapper."""
    # 1. Streamlit Config
    # Uses assets/logo.png as page icon (favicon) and sets page title to InsightFlow
    st.set_page_config(
        page_title="InsightFlow",
        page_icon="assets/logo.png",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # 2. Inject global styling
    css_path = os.path.join("assets", "styles.css")
    load_css(css_path)
    
    # 3. Read query parameters for page routing and theme toggling
    query_params = st.query_params
    selected_page = query_params.get("page", "Executive Overview")
    theme = query_params.get("theme", "dark")
    
    # 4. Inject Light Mode overrides if light mode is selected
    if theme == "light":
        st.markdown("""
        <style>
        :root {
            --bg-primary: #F9F9FB !important;
            --bg-sidebar: #F3F3F5 !important;
            --bg-card: #FFFFFF !important;
            --bg-hover: #EFEFF3 !important;
            --border: rgba(0, 0, 0, 0.08) !important;
            --divider: rgba(0, 0, 0, 0.04) !important;
            --text-primary: #1C1C1E !important;
            --text-secondary: #636366 !important;
            --text-muted: #8E8E93 !important;
        }
        [data-testid="column"] {
            background-color: transparent !important;
        }
        .top-nav-anchor + div div[data-testid="stTextInput"] input {
            background-color: #EFEFF3 !important;
            color: #1C1C1E !important;
        }
        .top-nav-anchor + div div[data-testid="stSelectbox"] > div > div {
            background-color: #EFEFF3 !important;
            color: #1C1C1E !important;
        }
        .top-nav-anchor + div button {
            background-color: #EFEFF3 !important;
            color: #636366 !important;
        }
        th {
            background-color: #EFEFF3 !important;
            color: #1C1C1E !important;
        }
        .notification-drawer, .profile-menu {
            background-color: rgba(255, 255, 255, 0.96) !important;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15) !important;
        }
        .drawer-header h4, .profile-menu-name, .alert-text {
            color: #1C1C1E !important;
        }
        .theme-toggle-row {
            background-color: #EFEFF3 !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # 5. Initialize session state variables for search, notify, and profile controls
    if "show_notifications" not in st.session_state:
        st.session_state.show_notifications = False
    if "show_profile" not in st.session_state:
        st.session_state.show_profile = False
        
    # 6. Render Custom Fixed Sidebar Navigation (which sets up sidebar navigation panel)
    render_sidebar()
    
    # 7. Render Top Navigation Bar (with status dot, notify drawer trigger, profile dropdown trigger, date picker, refresh button)
    st.markdown('<div class="top-nav-anchor"></div>', unsafe_allow_html=True)
    top_col1, top_col2, top_col3, top_col4, top_col5, top_col6 = st.columns([5.5, 1.2, 1.1, 1.1, 2.5, 1.2])
    
    with top_col1:
        st.markdown(f"<div style='display:flex;align-items:center;height:38px;'><span style='font-size:14px;color:var(--text-muted);font-weight:500;'>InsightFlow / </span><span style='font-size:14px;color:var(--text-primary);font-weight:600;margin-left:4px;'>{selected_page}</span></div>", unsafe_allow_html=True)
        
    with top_col2:
        st.markdown('<div style="display:flex;align-items:center;height:38px;"><div class="live-badge"><span class="live-dot"></span><span>Live</span></div></div>', unsafe_allow_html=True)
        
    with top_col3:
        if st.button("🔔 3", key="btn_notify"):
            st.session_state.show_notifications = not st.session_state.show_notifications
            st.session_state.show_profile = False
            st.rerun()
            
    with top_col4:
        if st.button("MK", key="btn_profile"):
            st.session_state.show_profile = not st.session_state.show_profile
            st.session_state.show_notifications = False
            st.rerun()
            
    with top_col5:
        date_range = st.selectbox(
            "Date Range",
            options=["Jul 13 - Jul 19, 2026", "Jul 06 - Jul 12, 2026"],
            label_visibility="collapsed"
        )
        st.session_state.date_range = date_range
        
    with top_col6:
        if st.button("Refresh", key="btn_refresh"):
            st.cache_data.clear()
            st.toast("Dashboard cache refreshed successfully!", icon="✅")
            st.rerun()
            
    # 8. Render notification list drawer overlay
    if st.session_state.show_notifications:
        notifications_html = """
        <div class="notification-drawer">
            <div class="drawer-header">
                <h4>Notifications</h4>
                <span class="drawer-close" onclick="window.location.reload()">✕</span>
            </div>
            <div class="drawer-body">
                <div class="alert-item unread">
                    <span class="alert-indicator success">●</span>
                    <div class="alert-info">
                        <p class="alert-text">Conversion spike detected in Maharashtra (+23.4%)</p>
                        <span class="alert-time">2m ago</span>
                    </div>
                </div>
                <div class="alert-item unread">
                    <span class="alert-indicator danger">●</span>
                    <div class="alert-info">
                        <p class="alert-text">Drop in KYC completion rate in Bihar (-15.6%)</p>
                        <span class="alert-time">15m ago</span>
                    </div>
                </div>
                <div class="alert-item">
                    <span class="alert-indicator warning">●</span>
                    <div class="alert-info">
                        <p class="alert-text">High app uninstall rate detected on Android 12</p>
                        <span class="alert-time">32m ago</span>
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(clean_html(notifications_html), unsafe_allow_html=True)
        
    # 9. Render profile menu list overlay
    if st.session_state.show_profile:
        profile_menu_html = f"""
        <div class="profile-menu">
            <div class="profile-menu-header">
                <div class="profile-avatar-circle">MK</div>
                <div class="profile-menu-info">
                    <span class="profile-menu-name">Mohith Krishna</span>
                    <span class="profile-menu-email">mohith@insightflow.io</span>
                </div>
            </div>
            <hr class="menu-divider">
            <a href="?page=Settings&theme={theme}" target="_self" class="menu-item">⚙️ Settings</a>
            <a href="#" class="menu-item">🔑 Security</a>
            <a href="#" class="menu-item">📈 Billing & Plan</a>
            <hr class="menu-divider">
            <a href="?page=Executive+Overview&theme={theme}" target="_self" class="menu-item logout">🚪 Sign Out</a>
        </div>
        """
        st.markdown(clean_html(profile_menu_html), unsafe_allow_html=True)

    # 10. Route and render page modules
    if selected_page == "Executive Overview":
        executive.render_page()
    elif selected_page == "Funnel Analytics":
        funnel.render_page()
    elif selected_page == "Marketing Attribution":
        marketing.render_page()
    elif selected_page == "Customer Analytics":
        customer.render_page()
    elif selected_page in ["A/B Testing", "Experiment Analytics"]:
        experiments.render_page()
    else:
        render_mock_page(selected_page)

if __name__ == "__main__":
    main()
