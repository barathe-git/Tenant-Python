import streamlit as st
import requests


def get_api_url():
    """Get API base URL from session state or defaults"""
    if 'API_BASE_URL' in st.session_state:
        return st.session_state['API_BASE_URL']
    try:
        return st.secrets.get("API_BASE_URL", "http://localhost:8000")
    except (FileNotFoundError, AttributeError):
        return "http://localhost:8000"


def get_auth_headers():
    """Get authorization headers for API requests"""
    token = st.session_state.get('access_token')
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def is_authenticated():
    """Check if user is authenticated"""
    return 'access_token' in st.session_state and st.session_state['access_token'] is not None


def is_admin():
    """Check if current user is admin"""
    return st.session_state.get('user_role') == 'admin'


def get_current_client_id():
    """Get the currently selected client ID (for admin viewing specific client)"""
    if is_admin() and 'selected_client_id' in st.session_state:
        return st.session_state['selected_client_id']
    return st.session_state.get('client_id')


def logout():
    """Clear session and logout"""
    keys_to_clear = ['access_token', 'client_id', 'username', 'user_name', 'user_role',
                     'selected_client_id', 'current_page']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def check_initial_setup():
    """Check if initial setup is needed (no admin exists)"""
    try:
        api_url = get_api_url()
        # Try to access an endpoint that would fail if no users exist
        response = requests.get(f"{api_url}/api/auth/clients", timeout=5)
        # If we get 401, it means we need authentication - so users exist
        return response.status_code != 401
    except:
        return True  # Assume setup is needed if we can't connect


def render_initial_setup():
    """Render initial admin setup page"""
    st.title("Initial Setup")
    st.markdown("Welcome! Let's create your admin account to get started.")

    with st.form("setup_form"):
        username = st.text_input("Admin Username *", placeholder="Enter username")
        password = st.text_input("Password *", type="password", placeholder="Enter password")
        confirm_password = st.text_input("Confirm Password *", type="password", placeholder="Confirm password")
        name = st.text_input("Full Name *", placeholder="Enter your name")
        email = st.text_input("Email", placeholder="Enter email (optional)")
        phone = st.text_input("Phone", placeholder="Enter phone (optional)")

        submitted = st.form_submit_button("Create Admin Account", use_container_width=True)

        if submitted:
            if not username or not password or not name:
                st.error("Please fill in all required fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                try:
                    api_url = get_api_url()
                    response = requests.post(
                        f"{api_url}/api/auth/setup",
                        json={
                            "username": username,
                            "password": password,
                            "name": name,
                            "email": email if email else None,
                            "phone": phone if phone else None,
                            "role": "admin"
                        }
                    )

                    if response.status_code == 200:
                        st.success("Admin account created successfully! Please login.")
                        st.rerun()
                    else:
                        error_msg = response.json().get("detail", "Setup failed")
                        st.error(error_msg)
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend API. Please ensure the server is running.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")


def render_login_page():
    """Render login page"""
    # Custom CSS for login page
    st.markdown("""
    <style>
        .login-container {
            max-width: 420px;
            margin: 0 auto;
            padding: 40px;
        }
        .login-header {
            text-align: center;
            margin-bottom: 40px;
        }
        .login-logo {
            font-size: 64px;
            margin-bottom: 16px;
        }
        .login-title {
            font-size: 28px;
            font-weight: 700;
            color: #1a1a2e;
            margin: 0 0 8px;
        }
        .login-subtitle {
            font-size: 14px;
            color: #6b7280;
            margin: 0;
        }
        .login-card {
            background: white;
            border-radius: 16px;
            padding: 32px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
            border: 1px solid #f0f0f0;
        }
    </style>
    """, unsafe_allow_html=True)

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Header
        st.markdown("""
        <div class="login-header">
            <div class="login-logo">🏠</div>
            <h1 class="login-title">Tenant Manager</h1>
            <p class="login-subtitle">Sign in to your account</p>
        </div>
        """, unsafe_allow_html=True)

        # Login form
        with st.form("login_form"):
            st.markdown("##### Username")
            username = st.text_input("Username", placeholder="Enter your username", label_visibility="collapsed")

            st.markdown("##### Password")
            password = st.text_input("Password", type="password", placeholder="Enter your password", label_visibility="collapsed")

            st.markdown("")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

            if submitted:
                if not username or not password:
                    st.error("Please enter username and password")
                else:
                    try:
                        api_url = get_api_url()
                        response = requests.post(
                            f"{api_url}/api/auth/login",
                            json={"username": username, "password": password}
                        )

                        if response.status_code == 200:
                            data = response.json()
                            st.session_state['access_token'] = data['access_token']
                            st.session_state['client_id'] = data['client_id']
                            st.session_state['username'] = data['username']
                            st.session_state['user_name'] = data['name']
                            st.session_state['user_role'] = data['role']
                            st.success(f"Welcome, {data['name']}!")
                            st.rerun()
                        else:
                            error_msg = response.json().get("detail", "Login failed")
                            st.error(error_msg)
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to backend API. Please ensure the server is running.")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")

        # Footer
        st.markdown("""
        <div style="text-align: center; margin-top: 32px; color: #9ca3af; font-size: 12px;">
            <p style="margin: 0;">Property Management System v2.0</p>
        </div>
        """, unsafe_allow_html=True)


def render_client_selector():
    """Render client selector for admin users"""
    if not is_admin():
        return

    api_url = get_api_url()
    headers = get_auth_headers()

    try:
        response = requests.get(f"{api_url}/api/auth/clients", headers=headers, timeout=10)
        if response.status_code == 200:
            clients = response.json()

            # Build options
            options = {"All Clients": None}
            for client in clients:
                options[f"{client['name']} ({client['username']})"] = client['client_id']

            # Get current selection
            current_selection = "All Clients"
            for name, cid in options.items():
                if cid == st.session_state.get('selected_client_id'):
                    current_selection = name
                    break

            selected = st.selectbox(
                "View as Client",
                options=list(options.keys()),
                index=list(options.keys()).index(current_selection),
                key="client_selector"
            )

            new_client_id = options[selected]
            if new_client_id != st.session_state.get('selected_client_id'):
                st.session_state['selected_client_id'] = new_client_id
                # Clear caches
                st.cache_data.clear()
                st.rerun()

    except Exception as e:
        st.warning(f"Could not load clients: {str(e)}")


def render_user_menu():
    """Render user menu in sidebar"""
    user_name = st.session_state.get('user_name', 'User')
    user_role = st.session_state.get('user_role', 'client')

    st.markdown(f"""
    <div style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px; margin-bottom: 10px;">
        <p style="margin: 0; font-weight: 600; color: white;">{user_name}</p>
        <p style="margin: 0; font-size: 12px; color: #aaa;">{user_role.upper()}</p>
    </div>
    """, unsafe_allow_html=True)

    if is_admin():
        render_client_selector()
        st.markdown("---")

    if st.button("Logout", key="logout_btn", use_container_width=True):
        logout()
