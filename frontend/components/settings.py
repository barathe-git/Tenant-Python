import streamlit as st
import requests
from frontend.components.auth import get_api_url, get_auth_headers


def render_settings():
    """Render settings page"""
    st.title("⚙️ Settings")

    # Change Password Section
    st.subheader("🔐 Change Password")

    with st.form("change_password_form"):
        current_password = st.text_input(
            "Current Password *",
            type="password",
            placeholder="Enter your current password"
        )
        new_password = st.text_input(
            "New Password *",
            type="password",
            placeholder="Enter new password (min 6 characters)"
        )
        confirm_password = st.text_input(
            "Confirm New Password *",
            type="password",
            placeholder="Confirm your new password"
        )

        if st.form_submit_button("Change Password", use_container_width=True, type="primary"):
            if not current_password or not new_password or not confirm_password:
                st.error("Please fill in all password fields")
            elif len(new_password) < 6:
                st.error("New password must be at least 6 characters")
            elif new_password != confirm_password:
                st.error("New passwords do not match")
            else:
                try:
                    api_url = get_api_url()
                    headers = get_auth_headers()
                    response = requests.put(
                        f"{api_url}/api/auth/me/password",
                        json={
                            "current_password": current_password,
                            "new_password": new_password
                        },
                        headers=headers,
                        timeout=10
                    )

                    if response.status_code == 200:
                        st.success("Password changed successfully!")
                    else:
                        error_msg = response.json().get("detail", "Failed to change password")
                        st.error(error_msg)
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend API. Please ensure the server is running.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

    st.divider()

    # API Configuration
    st.subheader("🔗 API Configuration")

    with st.form("api_settings"):
        api_url = st.text_input(
            "Backend API URL",
            value=st.session_state.get('API_BASE_URL', 'http://localhost:8000'),
            help="The URL where your FastAPI backend is running"
        )

        if st.form_submit_button("Save API Settings", use_container_width=True):
            st.session_state['API_BASE_URL'] = api_url
            st.success("API URL updated successfully!")

    # Test Connection
    st.subheader("📡 Connection Status")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Test Connection", use_container_width=True):
            try:
                API_BASE_URL = get_api_url()
                response = requests.get(f"{API_BASE_URL}/api/owners/", params={"limit": 1}, timeout=5)
                if response.status_code == 200:
                    st.success("Connected to backend successfully!")
                else:
                    st.error(f"Backend returned status {response.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend. Please check if the server is running.")
            except requests.exceptions.Timeout:
                st.error("Connection timed out. Backend may be slow or unreachable.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    with col1:
        st.info(f"Current API URL: `{get_api_url()}`")

    st.divider()

    # Cache Management
    st.subheader("🗑️ Cache Management")

    st.markdown("""
    The application caches API responses to improve performance.
    Clear the cache if you're seeing stale data.
    """)

    if st.button("Clear All Cache", use_container_width=False):
        st.cache_data.clear()
        st.success("Cache cleared successfully!")
        st.rerun()

    st.divider()

    # About
    st.subheader("ℹ️ About")

    st.markdown("""
    **Tenant Management System** v2.0.0

    A comprehensive solution for managing rental properties, tenants, and agreements.

    **Features:**
    - Multi-client support with authentication
    - Owner management
    - Building & portion tracking
    - Tenant records with rent breakdown (rent, water, maintenance)
    - Advance amount tracking
    - PDF document storage (Agreements & Aadhar)
    - Agreement expiry alerts
    - Dashboard analytics

    Built with Streamlit & FastAPI
    """)
