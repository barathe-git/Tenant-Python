import streamlit as st
import os
import sys
from pathlib import Path

# Ensure project root is in Python path for imports
frontend_dir = Path(__file__).parent
project_root = frontend_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import components
from frontend.components import dashboard, owner_form, building_form, tenant_form, pdf_viewer, settings
from frontend.components.auth import (
    is_authenticated, render_login_page, render_user_menu,
    is_admin, get_api_url, check_initial_setup, render_initial_setup,
    logout, render_client_selector
)

# Page configuration
st.set_page_config(
    page_title="Tenant Management System",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize API URL if not set
if 'API_BASE_URL' not in st.session_state:
    st.session_state['API_BASE_URL'] = "http://localhost:8000"

# Custom CSS for modern UI
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Main app background - white */
    .stApp {
        background: #ffffff;
    }

    [data-testid="stAppViewContainer"] {
        background: #ffffff;
    }

    [data-testid="stHeader"] {
        background: #ffffff;
    }

    .main .block-container {
        background: #ffffff;
    }

    /* All text in black */
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #000000;
    }

    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span {
        color: #000000;
    }

    /* Metric labels and values in black */
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        color: #000000 !important;
    }

    [data-testid="stMetricLabel"] p, [data-testid="stMetricValue"] div {
        color: #000000 !important;
    }

    /* Sidebar styling - white background */
    [data-testid="stSidebar"] {
        background: #ffffff;
        padding-top: 20px;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #000000;
    }

    [data-testid="stSidebar"] hr {
        border-color: #f3f4f6;
        margin: 8px 16px;
    }

    /* Hide default button borders and shadows */
    [data-testid="stSidebar"] .stButton {
        margin-bottom: 4px;
    }

    /* Sidebar navigation */
    .sidebar-nav {
        padding: 16px 12px;
    }

    .nav-section-title {
        color: #6b7280;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 16px 12px 8px;
        margin: 0;
    }

    .nav-item {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        margin: 4px 8px;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
        color: #000000;
        font-size: 14px;
        font-weight: 500;
    }

    .nav-item:hover {
        background: #f3f4f6;
        color: #000000;
    }

    .nav-item.active {
        background: #e0e7ff;
        color: #000000;
    }

    .nav-icon {
        margin-right: 12px;
        font-size: 18px;
        width: 24px;
        text-align: center;
    }

    /* Card styling */
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
    }

    /* Button styling improvements */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* Sidebar button override - clean minimal style */
    [data-testid="stSidebar"] .stButton > button {
        background: transparent;
        border: none;
        color: #374151;
        font-weight: 500;
        text-align: left;
        padding: 12px 16px;
        border-radius: 8px;
        justify-content: flex-start;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: #f3f4f6;
        border: none;
        color: #111827;
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: #f3f4f6;
        border: 1px solid #e5e7eb;
        color: #000000;
        font-weight: 600;
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: #e5e7eb;
        color: #000000;
    }

    /* Remove button shadow in sidebar */
    [data-testid="stSidebar"] .stButton > button:focus {
        box-shadow: none;
    }

    /* Footer styling */
    .footer {
        text-align: center;
        color: #9ca3af;
        padding: 2rem 1rem;
        font-size: 13px;
        border-top: 1px solid #f0f0f0;
        margin-top: 2rem;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: #f8fafc;
        border-radius: 8px;
    }

    /* Remove white box and border from Plotly charts */
    [data-testid="stPlotlyChart"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    [data-testid="stPlotlyChart"] > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    .js-plotly-plot, .plotly, .plot-container {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    .js-plotly-plot .plotly .main-svg {
        background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# Load custom CSS file if exists
css_file = Path(__file__).parent.parent / "static" / "style.css"
if css_file.exists():
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Check if user needs to login
if not is_authenticated():
    # Check if initial setup is needed
    try:
        import requests
        api_url = get_api_url()
        response = requests.post(
            f"{api_url}/api/auth/setup",
            json={"username": "test", "password": "test", "name": "test"},
            timeout=5
        )
        # If we get 400 with "already completed", setup is done
        if response.status_code == 400 and "already completed" in response.text:
            render_login_page()
        elif response.status_code == 200:
            render_initial_setup()
        else:
            render_login_page()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend API. Please ensure the server is running on " + api_url)
        st.info("Start the backend with: `python -m uvicorn backend.main:app --reload`")
    except Exception as e:
        render_login_page()
    st.stop()


# Get user info
user_name = st.session_state.get('user_name', 'User')
user_role = st.session_state.get('user_role', 'client')
user_initials = ''.join([n[0].upper() for n in user_name.split()[:2]]) if user_name else 'U'

# Navigation items
NAV_ITEMS = [
    {"icon": "📊", "label": "Dashboard", "key": "Dashboard"},
    {"icon": "👤", "label": "Owners", "key": "Owners"},
    {"icon": "🏢", "label": "Buildings", "key": "Buildings"},
    {"icon": "🏠", "label": "Tenants", "key": "Tenants"},
]

# Add admin-only menu items
if is_admin():
    NAV_ITEMS.append({"icon": "👥", "label": "Clients", "key": "Clients"})

# Initialize current page
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'Dashboard'

# Sidebar
with st.sidebar:
    # Logo/Brand
    st.markdown("""
    <div style="text-align: center; padding: 20px 16px 30px;">
        <div style="font-size: 42px; margin-bottom: 8px;">🏠</div>
        <h2 style="color: #000000; margin: 0; font-size: 22px; font-weight: 700;">Tenant Manager</h2>
        <p style="color: #000000; margin: 4px 0 0; font-size: 12px;">Property Management</p>
    </div>
    """, unsafe_allow_html=True)

    # User info card
    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 14px 16px; margin: 0 8px 20px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 38px; height: 38px; background: #ffffff; border: 1px solid #e5e7eb;
                        border-radius: 10px; display: flex; align-items: center; justify-content: center;
                        color: #000000; font-weight: 600; font-size: 14px;">{user_initials}</div>
            <div>
                <p style="margin: 0; color: #000000; font-weight: 600; font-size: 14px;">{user_name}</p>
                <p style="margin: 4px 0 0; background: #ffffff; border: 1px solid #e5e7eb; color: #000000; font-size: 10px;
                   font-weight: 600; padding: 2px 8px; border-radius: 4px; display: inline-block;
                   text-transform: uppercase; letter-spacing: 0.5px;">{user_role}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Client selector for admin
    if is_admin():
        render_client_selector()
        st.markdown("")

    # Navigation section title
    st.markdown("""
    <p style="color: #000000; font-size: 10px; font-weight: 600; text-transform: uppercase;
              letter-spacing: 1.5px; padding: 16px 16px 8px; margin: 0;">Menu</p>
    """, unsafe_allow_html=True)

    # Navigation buttons
    for item in NAV_ITEMS:
        is_active = st.session_state['current_page'] == item['key']

        if st.button(
            f"{item['icon']}  {item['label']}",
            key=f"nav_{item['key']}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state['current_page'] = item['key']
            # Clear PDF viewer state when navigating away
            if item['key'] != 'Tenants':
                st.session_state.pop('view_pdf_tenant_id', None)
                st.session_state.pop('view_pdf_type', None)
            st.rerun()

    # Bottom section - Settings and Logout
    st.markdown("""
    <p style="color: #000000; font-size: 10px; font-weight: 600; text-transform: uppercase;
              letter-spacing: 1.5px; padding: 24px 16px 8px; margin: 0;">Account</p>
    """, unsafe_allow_html=True)

    # Settings button
    is_settings_active = st.session_state['current_page'] == 'Settings'
    if st.button(
        "⚙️  Settings",
        key="nav_Settings",
        use_container_width=True,
        type="primary" if is_settings_active else "secondary"
    ):
        st.session_state['current_page'] = 'Settings'
        st.rerun()

    # Logout button
    if st.button(
        "🚪  Logout",
        key="nav_Logout",
        use_container_width=True,
        type="secondary"
    ):
        logout()

    # Version info
    st.markdown("""
    <div style="text-align: center; padding: 16px 16px 8px;">
        <p style="color: #000000; font-size: 11px; margin: 0;">Version 2.0.0</p>
    </div>
    """, unsafe_allow_html=True)

# Main content area
page = st.session_state.get('current_page', 'Dashboard')

if page == "Dashboard":
    dashboard.render_dashboard()
elif page == "Owners":
    owner_form.render_owner_form()
elif page == "Buildings":
    building_form.render_building_form()
elif page == "Tenants":
    # Check if PDF viewer should be shown
    if 'view_pdf_tenant_id' in st.session_state:
        tenant_id = st.session_state['view_pdf_tenant_id']
        file_type = st.session_state.get('view_pdf_type', 'agreement')
        pdf_viewer.render_pdf_viewer(tenant_id, file_type)
    else:
        tenant_form.render_tenant_form()
elif page == "Clients":
    if is_admin():
        from frontend.components import client_form
        client_form.render_client_form()
    else:
        st.error("Access denied. Admin privileges required.")
elif page == "Settings":
    settings.render_settings()

# Footer
st.markdown("""
<div class='footer'>
    <p style="margin: 0;">Tenant Management System</p>
    <p style="margin: 4px 0 0; font-size: 11px; color: #9ca3af;">Built with Streamlit & FastAPI</p>
</div>
""", unsafe_allow_html=True)
