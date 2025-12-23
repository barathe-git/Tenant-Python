import streamlit as st
import requests
from frontend.components.auth import get_api_url, get_auth_headers, is_admin


def render_client_form():
    """Render client management form (Admin only)"""
    if not is_admin():
        st.error("Access denied. Admin privileges required.")
        return

    st.title("👥 Client Management")

    API_BASE_URL = get_api_url()
    headers = get_auth_headers()

    # Initialize tab state
    if 'client_active_tab' not in st.session_state:
        st.session_state['client_active_tab'] = "Manage Clients"

    # Tab selection
    selected_tab = st.radio(
        "Select Action",
        ["Add Client", "Manage Clients"],
        index=0 if st.session_state['client_active_tab'] == "Add Client" else 1,
        horizontal=True,
        key="client_tab_selector",
        label_visibility="collapsed"
    )
    st.session_state['client_active_tab'] = selected_tab

    st.divider()

    if selected_tab == "Add Client":
        st.subheader("Add New Client")

        with st.form("add_client_form"):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Username *", placeholder="Enter unique username")
                name = st.text_input("Full Name *", placeholder="Enter client name")
                email = st.text_input("Email", placeholder="Enter email (optional)")
            with col2:
                password = st.text_input("Password *", type="password", placeholder="Enter password")
                phone = st.text_input("Phone", placeholder="Enter phone (optional)")
                role = st.selectbox("Role", options=["client", "admin"], index=0)

            submitted = st.form_submit_button("Create Client", use_container_width=True)

            if submitted:
                if not username or not password or not name:
                    st.error("Please fill in all required fields")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/api/auth/clients",
                            headers=headers,
                            json={
                                "username": username,
                                "password": password,
                                "name": name,
                                "email": email if email else None,
                                "phone": phone if phone else None,
                                "role": role
                            }
                        )

                        if response.status_code == 200:
                            st.success(f"Client '{name}' created successfully!")
                            st.rerun()
                        else:
                            error_msg = response.json().get("detail", "Error creating client")
                            st.error(error_msg)
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to backend API.")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")

    else:  # Manage Clients
        st.subheader("Manage Clients")

        try:
            response = requests.get(f"{API_BASE_URL}/api/auth/clients", headers=headers, timeout=10)

            if response.status_code == 200:
                clients = response.json()

                if clients:
                    # Summary
                    total_clients = len(clients)
                    admin_count = sum(1 for c in clients if c.get('role') == 'admin')
                    active_count = sum(1 for c in clients if c.get('is_active', True))

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Clients", total_clients)
                    col2.metric("Admins", admin_count)
                    col3.metric("Active", active_count)

                    st.divider()

                    for client in clients:
                        client_id = client.get('client_id')
                        client_name = client.get('name', 'N/A')
                        client_username = client.get('username', 'N/A')
                        client_role = client.get('role', 'client')
                        is_active = client.get('is_active', True)

                        status_icon = "🟢" if is_active else "🔴"
                        role_badge = "👑" if client_role == "admin" else "👤"

                        with st.expander(f"{status_icon} {role_badge} {client_name} (@{client_username})"):
                            edit_key = f"edit_client_{client_id}"

                            if st.session_state.get(edit_key, False):
                                # Edit mode
                                with st.form(f"edit_client_form_{client_id}"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        edit_name = st.text_input("Name", value=client_name, key=f"edit_cname_{client_id}")
                                        edit_email = st.text_input("Email", value=client.get('email', '') or '', key=f"edit_cemail_{client_id}")
                                    with col2:
                                        edit_phone = st.text_input("Phone", value=client.get('phone', '') or '', key=f"edit_cphone_{client_id}")
                                        edit_role = st.selectbox(
                                            "Role",
                                            options=["client", "admin"],
                                            index=0 if client_role == "client" else 1,
                                            key=f"edit_crole_{client_id}"
                                        )

                                    edit_active = st.checkbox("Active", value=is_active, key=f"edit_cactive_{client_id}")

                                    col1, col2 = st.columns(2)
                                    with col1:
                                        save_btn = st.form_submit_button("Save Changes", use_container_width=True)
                                    with col2:
                                        cancel_btn = st.form_submit_button("Cancel", use_container_width=True)

                                    if save_btn:
                                        try:
                                            update_data = {
                                                "name": edit_name,
                                                "email": edit_email if edit_email else None,
                                                "phone": edit_phone if edit_phone else None,
                                                "role": edit_role,
                                                "is_active": edit_active
                                            }
                                            update_resp = requests.put(
                                                f"{API_BASE_URL}/api/auth/clients/{client_id}",
                                                headers=headers,
                                                json=update_data
                                            )
                                            if update_resp.status_code == 200:
                                                st.success("Client updated successfully!")
                                                st.session_state[edit_key] = False
                                                st.rerun()
                                            else:
                                                st.error(f"Failed to update: {update_resp.json().get('detail', 'Unknown error')}")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")

                                    if cancel_btn:
                                        st.session_state[edit_key] = False
                                        st.rerun()

                                # Password reset section
                                st.markdown("---")
                                st.markdown("**Reset Password**")
                                new_password = st.text_input(
                                    "New Password",
                                    type="password",
                                    key=f"reset_pwd_{client_id}",
                                    placeholder="Enter new password (min 6 characters)"
                                )
                                if st.button("Reset Password", key=f"reset_btn_{client_id}"):
                                    if len(new_password) < 6:
                                        st.error("Password must be at least 6 characters")
                                    else:
                                        try:
                                            reset_resp = requests.post(
                                                f"{API_BASE_URL}/api/auth/clients/{client_id}/reset-password",
                                                headers=headers,
                                                params={"new_password": new_password}
                                            )
                                            if reset_resp.status_code == 200:
                                                st.success("Password reset successfully!")
                                            else:
                                                st.error("Failed to reset password")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")

                            else:
                                # View mode
                                col1, col2, col3 = st.columns([2, 2, 1])

                                with col1:
                                    st.markdown(f"""
                                    **Account Details**
                                    - Username: {client_username}
                                    - Role: {client_role.upper()}
                                    - Status: {'Active' if is_active else 'Inactive'}
                                    """)

                                with col2:
                                    st.markdown(f"""
                                    **Contact Info**
                                    - Email: {client.get('email', 'N/A') or 'N/A'}
                                    - Phone: {client.get('phone', 'N/A') or 'N/A'}
                                    """)

                                with col3:
                                    if st.button("Edit", key=f"edit_btn_c_{client_id}", use_container_width=True):
                                        st.session_state[edit_key] = True
                                        st.rerun()

                                    # Don't allow deleting yourself
                                    if client_id != st.session_state.get('client_id'):
                                        if st.button("Delete", key=f"delete_client_{client_id}", type="primary", use_container_width=True):
                                            try:
                                                delete_response = requests.delete(
                                                    f"{API_BASE_URL}/api/auth/clients/{client_id}",
                                                    headers=headers
                                                )
                                                if delete_response.status_code == 200:
                                                    st.success("Client deleted successfully!")
                                                    st.rerun()
                                                else:
                                                    error_msg = delete_response.json().get('detail', 'Failed to delete')
                                                    st.error(error_msg)
                                            except Exception as e:
                                                st.error(f"Error: {str(e)}")
                else:
                    st.info("No clients found.")

            elif response.status_code == 401:
                st.error("Authentication expired. Please login again.")
            else:
                st.error("Failed to load clients")

        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend API.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
