import streamlit as st
import requests
from frontend.components.auth import get_api_url, get_auth_headers, get_current_client_id


def get_token():
    """Get just the token for cache key"""
    return st.session_state.get('access_token', '')


# Cached API calls - longer TTL for better performance
# Using token as cache key instead of full headers tuple for more reliable caching
@st.cache_data(ttl=300, show_spinner=False)
def fetch_owners(token, api_url, search_term=None, client_id=None):
    """Fetch owners with caching"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    params = {"limit": 100}
    if search_term:
        params["search"] = search_term
    if client_id:
        params["client_id"] = client_id
    response = requests.get(f"{api_url}/api/owners/", params=params, headers=headers, timeout=10)
    return response.json() if response.status_code == 200 else []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_all_buildings(token, api_url, client_id=None):
    """Fetch all buildings at once"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    params = {"limit": 1000}
    if client_id:
        params["client_id"] = client_id
    response = requests.get(f"{api_url}/api/buildings/", params=params, headers=headers, timeout=10)
    return response.json() if response.status_code == 200 else []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_all_tenants(token, api_url, client_id=None):
    """Fetch all tenants at once"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    params = {"limit": 1000}
    if client_id:
        params["client_id"] = client_id
    response = requests.get(f"{api_url}/api/tenants/", params=params, headers=headers, timeout=10)
    return response.json() if response.status_code == 200 else []


def clear_owner_cache():
    """Clear owner-related caches"""
    fetch_owners.clear()
    fetch_all_buildings.clear()
    fetch_all_tenants.clear()


def render_owner_form():
    """Render owner management form"""
    st.title("Owner Management")

    # Custom CSS for modern styling
    st.markdown("""
    <style>
        .streamlit-expanderHeader {
            background: #f8fafc !important;
            border-radius: 10px !important;
            border: 1px solid #e2e8f0 !important;
        }
        .streamlit-expanderHeader:hover {
            background: #f1f5f9 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    API_BASE_URL = get_api_url()
    headers = get_auth_headers()
    token = get_token()
    client_id = get_current_client_id()

    # Initialize tab state
    if 'owner_active_tab' not in st.session_state:
        st.session_state['owner_active_tab'] = "Manage Owners"

    selected_tab = st.radio(
        "Select Action",
        ["Add Owner", "Manage Owners"],
        index=0 if st.session_state['owner_active_tab'] == "Add Owner" else 1,
        horizontal=True,
        key="owner_tab_selector",
        label_visibility="collapsed"
    )
    st.session_state['owner_active_tab'] = selected_tab

    st.divider()

    if selected_tab == "Add Owner":
        st.subheader("Add New Owner")
        with st.form("owner_form"):
            name = st.text_input("Owner Name *", placeholder="Enter owner name")
            phone = st.text_input("Phone Number *", placeholder="Enter phone number")
            email = st.text_input("Email *", placeholder="Enter email address")
            aadhar_number = st.text_input("Aadhar Number", placeholder="Enter 12-digit Aadhar number", max_chars=12)
            address = st.text_area("Address", placeholder="Enter address")

            submitted = st.form_submit_button("Add Owner", use_container_width=True)

            if submitted:
                if not name or not phone or not email:
                    st.error("Please fill in all required fields (*)")
                elif aadhar_number and len(aadhar_number) != 12:
                    st.error("Aadhar number must be exactly 12 digits")
                else:
                    try:
                        data = {
                            "name": name,
                            "phone": phone,
                            "email": email,
                            "aadhar_number": aadhar_number if aadhar_number else None,
                            "address": address if address else None
                        }
                        response = requests.post(f"{API_BASE_URL}/api/owners/", json=data, headers=headers)

                        if response.status_code == 201:
                            st.success("Owner added successfully!")
                            clear_owner_cache()
                            st.rerun()
                        elif response.status_code == 400:
                            error_msg = response.json().get("detail", "Error adding owner")
                            st.error(error_msg)
                        else:
                            st.error(f"Error: {response.status_code}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to backend API. Please ensure the server is running.")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")

    else:  # Manage Owners tab
        st.subheader("Manage Owners")

        # Search functionality
        search_term = st.text_input("Search owners", placeholder="Search by name, email, or phone", key="owner_search")

        try:
            owners = fetch_owners(token, API_BASE_URL, search_term if search_term else None, client_id)

            if owners:
                # Summary stats
                st.markdown(f"**Total Owners:** {len(owners)}")
                st.divider()

                # Batch fetch all buildings and tenants (2 API calls instead of 2*N)
                all_buildings = fetch_all_buildings(token, API_BASE_URL, client_id)
                all_tenants = fetch_all_tenants(token, API_BASE_URL, client_id)

                # Pre-compute counts per owner
                owner_stats = {}
                for owner in owners:
                    oid = owner.get('owner_id')
                    owner_stats[oid] = {
                        'building_count': sum(1 for b in all_buildings if b.get('owner_id') == oid),
                        'tenant_count': sum(1 for t in all_tenants if t.get('owner_id') == oid)
                    }

                for owner in owners:
                    owner_id = owner.get('owner_id')
                    stats = owner_stats.get(owner_id, {'building_count': 0, 'tenant_count': 0})
                    building_count = stats['building_count']
                    tenant_count = stats['tenant_count']

                    with st.expander(f"👤 {owner.get('name', 'N/A')} | {building_count} Buildings | {tenant_count} Tenants"):
                        # Check if we're in edit mode for this owner
                        edit_key = f"edit_owner_{owner_id}"

                        if st.session_state.get(edit_key, False):
                            # Edit mode
                            with st.form(f"edit_form_{owner_id}"):
                                st.markdown("**Edit Owner Details**")
                                edit_name = st.text_input("Name", value=owner.get('name', ''), key=f"edit_name_{owner_id}")
                                edit_phone = st.text_input("Phone", value=owner.get('phone', ''), key=f"edit_phone_{owner_id}")
                                edit_email = st.text_input("Email", value=owner.get('email', ''), key=f"edit_email_{owner_id}")
                                edit_aadhar = st.text_input("Aadhar Number", value=owner.get('aadhar_number', '') or '', max_chars=12, key=f"edit_aadhar_{owner_id}")
                                edit_address = st.text_area("Address", value=owner.get('address', '') or '', key=f"edit_address_{owner_id}")

                                col1, col2 = st.columns(2)
                                with col1:
                                    save_btn = st.form_submit_button("Save Changes", use_container_width=True)
                                with col2:
                                    cancel_btn = st.form_submit_button("Cancel", use_container_width=True)

                                if save_btn:
                                    try:
                                        update_data = {
                                            "name": edit_name,
                                            "phone": edit_phone,
                                            "email": edit_email,
                                            "aadhar_number": edit_aadhar if edit_aadhar else None,
                                            "address": edit_address if edit_address else None
                                        }
                                        update_resp = requests.put(f"{API_BASE_URL}/api/owners/{owner_id}", json=update_data, headers=headers)
                                        if update_resp.status_code == 200:
                                            st.success("Owner updated successfully!")
                                            st.session_state[edit_key] = False
                                            clear_owner_cache()
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to update: {update_resp.json().get('detail', 'Unknown error')}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")

                                if cancel_btn:
                                    st.session_state[edit_key] = False
                                    st.rerun()
                        else:
                            # View mode
                            col1, col2 = st.columns([3, 1])

                            with col1:
                                st.markdown(f"""
                                | Field | Value |
                                |-------|-------|
                                | **Phone** | {owner.get('phone', 'N/A')} |
                                | **Email** | {owner.get('email', 'N/A')} |
                                | **Aadhar** | {owner.get('aadhar_number', 'N/A') or 'N/A'} |
                                | **Address** | {owner.get('address', 'N/A') or 'N/A'} |
                                | **Owner ID** | {owner_id} |
                                | **Buildings** | {building_count} |
                                | **Tenants** | {tenant_count} |
                                """)

                            with col2:
                                if st.button("Edit", key=f"edit_btn_{owner_id}", use_container_width=True):
                                    st.session_state[edit_key] = True
                                    st.session_state['owner_active_tab'] = "Manage Owners"
                                    st.rerun()

                                if st.button("Delete", key=f"delete_{owner_id}", type="primary", use_container_width=True):
                                    if building_count > 0 or tenant_count > 0:
                                        st.error("Cannot delete owner with buildings or tenants. Remove them first.")
                                    else:
                                        try:
                                            delete_response = requests.delete(f"{API_BASE_URL}/api/owners/{owner_id}", headers=headers)
                                            if delete_response.status_code == 204:
                                                st.success("Owner deleted successfully!")
                                                clear_owner_cache()
                                                st.rerun()
                                            else:
                                                st.error("Failed to delete owner")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
            else:
                st.info("No owners found. Add your first owner using the 'Add Owner' tab.")

        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend API. Please ensure the server is running.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
