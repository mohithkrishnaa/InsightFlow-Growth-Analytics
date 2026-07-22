"""
Sidebar Navigation Component for the InsightFlow Dashboard.
Provides a fixed, Linear-inspired navigation menu and branding panel using query parameters.
"""

import os
import base64
import streamlit as st

def get_image_base64(path: str) -> str:
    """Reads a local image file and returns its Base64 encoding for inline data URI usage."""
    candidates = [
        path,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", path)),
        os.path.abspath(os.path.join(os.getcwd(), path)),
        os.path.abspath(path),
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
    return ""

def render_sidebar() -> str:
    """
    Renders a custom fixed sidebar navigation using HTML and query parameters.
    
    Returns:
        str: Selected page name.
    """
    # 1. Read query parameters
    query_params = st.query_params
    current_page = query_params.get("page", "Executive Overview")
    theme = query_params.get("theme", "dark")
    
    # 2. Get base64 string of the official logo
    logo_base64 = get_image_base64("assets/logo.png")
    
    # Define navigation options with page names, icons, and categories
    nav_structure = {
        "OVERVIEW": [
            ("Executive Overview", "📊")
        ],
        "ANALYTICS": [
            ("Funnel Analytics", "🌪️"),
            ("Marketing Attribution", "📢"),
            ("Customer Analytics", "👥"),
            ("Revenue & Loans", "💰")
        ],
        "EXPERIMENTS": [
            ("Experiment Analytics", "📈")
        ],
        "SYSTEM": [
            ("Settings", "⚙️")
        ]
    }
    
    # 3. Build sidebar HTML
    sidebar_html = f"""
    <div class="custom-sidebar">
        <div class="sidebar-top">
            <div class="brand-container">
                <img src="data:image/png;base64,{logo_base64}" class="sidebar-logo" alt="InsightFlow" />
            </div>
            
            <div class="nav-groups-container">
    """
    
    # Add navigation links group by group
    for group_name, items in nav_structure.items():
        sidebar_html += f"""
        <div class="nav-group">
            <span class="nav-group-title">{group_name}</span>
            <div class="nav-group-items">
        """
        for page_name, icon in items:
            is_active = (page_name == current_page)
            active_class = "active" if is_active else ""
            # Link carries current page and current theme
            href = f"?page={page_name.replace(' ', '+')}&theme={theme}"
            sidebar_html += f"""
                <a href="{href}" target="_self" class="nav-item {active_class}">
                    <span class="nav-item-icon">{icon}</span>
                    <span class="nav-item-text">{page_name}</span>
                </a>
            """
        sidebar_html += """
            </div>
        </div>
        """
        
    # Build theme toggle active classes
    light_active = "active" if theme == "light" else ""
    dark_active = "active" if theme == "dark" else ""
    
    # Add bottom profile and theme toggle
    sidebar_html += f"""
            </div>
        </div>
        
        <div class="sidebar-bottom">
            <div class="profile-card">
                <div class="profile-card-left">
                    <div class="profile-avatar-circle">MK</div>
                    <div class="profile-info">
                        <span class="profile-name">Mohith Krishna</span>
                        <span class="profile-role">Data Analyst</span>
                    </div>
                </div>
                <span class="profile-dropdown-arrow">▼</span>
            </div>
            
            <div class="theme-toggle-row">
                <a href="?page={current_page.replace(' ', '+')}&theme=light" target="_self" class="theme-toggle-btn {light_active}">☀️ Light</a>
                <a href="?page={current_page.replace(' ', '+')}&theme=dark" target="_self" class="theme-toggle-btn {dark_active}">🌙 Dark</a>
            </div>
            
            <div class="sidebar-copyright-info">
                InsightFlow v1.0.0<br>
                © 2026 InsightFlow
            </div>
        </div>
    </div>
    """
    
    # Inject the HTML
    st.markdown("\n".join(line.strip() for line in sidebar_html.strip().split("\n")), unsafe_allow_html=True)
    
    return current_page
