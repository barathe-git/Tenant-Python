import streamlit as st
import requests
from frontend.components.auth import get_api_url, get_auth_headers, get_current_client_id


def get_token():
    """Get just the token for cache key"""
    return st.session_state.get('access_token', '')


# Cached API calls - longer TTL for better performance
# Using token as cache key instead of full headers tuple for more reliable caching
@st.cache_data(ttl=300, show_spinner=False)
def fetch_owners(token, api_url, client_id=None):
    """Fetch owners with caching"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    params = {"limit": 1000}
    if client_id:
        params["client_id"] = client_id
    response = requests.get(f"{api_url}/api/owners/", params=params, headers=headers, timeout=10)
    return response.json() if response.status_code == 200 else []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_buildings(token, api_url, owner_id=None, building_type=None, client_id=None):
    """Fetch buildings with caching"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    params = {"limit": 1000}
    if owner_id:
        params["owner_id"] = owner_id
    if building_type:
        params["building_type"] = building_type
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


def clear_building_cache():
    """Clear building-related caches"""
    fetch_buildings.clear()
    fetch_all_tenants.clear()
    fetch_owners.clear()


def render_building_form():
    """Render building management form"""
    st.title("Building Management")

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

    # Fetch owners for dropdown
    try:
        owners = fetch_owners(token, API_BASE_URL, client_id)

        if not owners:
            st.warning("Please add at least one owner before adding buildings.")
            return

        owner_dict = {f"{owner['name']} (ID: {owner['owner_id']})": owner['owner_id'] for owner in owners}
        owner_id_to_name = {owner['owner_id']: owner['name'] for owner in owners}

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend API. Please ensure the server is running.")
        return
    except Exception as e:
        st.error(f"Error loading owners: {str(e)}")
        return

    # Initialize tab state
    if 'building_active_tab' not in st.session_state:
        st.session_state['building_active_tab'] = "Manage Buildings"

    selected_tab = st.radio(
        "Select Action",
        ["Add Building", "Manage Buildings"],
        index=0 if st.session_state['building_active_tab'] == "Add Building" else 1,
        horizontal=True,
        key="building_tab_selector",
        label_visibility="collapsed"
    )
    st.session_state['building_active_tab'] = selected_tab

    st.divider()

    if selected_tab == "Add Building":
        st.subheader("Add New Building")
        with st.form("building_form"):
            selected_owner = st.selectbox("Owner *", options=list(owner_dict.keys()))
            owner_id = owner_dict[selected_owner]

            # Get owner details to access address
            selected_owner_data = None
            for owner in owners:
                if owner['owner_id'] == owner_id:
                    selected_owner_data = owner
                    break

            building_name = st.text_input("Building Name *", placeholder="Enter building name")
            building_type = st.selectbox("Building Type *", options=["Residence", "Commercial"])
            number_of_portions = st.number_input("Number of Portions *", min_value=1, value=1, step=1)

            # Checkbox to use owner address
            use_owner_address = False
            owner_address = selected_owner_data.get('address', '') if selected_owner_data else ''

            if owner_address:
                use_owner_address = st.checkbox(
                    "Use owner's address as building location",
                    value=False,
                    help="Check this if the building is located at the same address as the owner"
                )

            # Location input - disabled if using owner address
            if use_owner_address and owner_address:
                location = owner_address
                st.text_input(
                    "Location",
                    value=owner_address,
                    disabled=True,
                    help="Using owner's address"
                )
            else:
                location = st.text_input("Location", placeholder="Enter location")

            submitted = st.form_submit_button("Add Building", use_container_width=True)

            if submitted:
                if not building_name:
                    st.error("Please fill in all required fields (*)")
                else:
                    try:
                        # Use owner address if checkbox is checked
                        final_location = owner_address if (use_owner_address and owner_address) else (location if location else None)

                        data = {
                            "owner_id": owner_id,
                            "building_name": building_name,
                            "building_type": building_type,
                            "number_of_portions": number_of_portions,
                            "location": final_location
                        }
                        response = requests.post(f"{API_BASE_URL}/api/buildings/", json=data, headers=headers)

                        if response.status_code == 201:
                            st.success("Building added successfully!")
                            clear_building_cache()
                            st.rerun()
                        elif response.status_code == 404:
                            st.error("Owner not found.")
                        else:
                            error_msg = response.json().get("detail", "Error adding building")
                            st.error(error_msg)
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to backend API. Please ensure the server is running.")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")

    else:  # Manage Buildings tab
        st.subheader("Manage Buildings")

        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            filter_owner = st.selectbox(
                "Filter by Owner",
                options=["All"] + list(owner_dict.keys()),
                key="building_filter"
            )
        with col2:
            filter_type = st.selectbox(
                "Filter by Type",
                options=["All", "Residence", "Commercial"],
                key="building_type_filter"
            )

        try:
            # Use cached fetch
            owner_id_filter = owner_dict[filter_owner] if filter_owner != "All" else None
            type_filter = filter_type if filter_type != "All" else None
            buildings = fetch_buildings(token, API_BASE_URL, owner_id_filter, type_filter, client_id)

            if buildings:
                # Summary stats
                total_portions = sum(b.get('number_of_portions', 0) for b in buildings)
                residence_count = sum(1 for b in buildings if b.get('building_type') == 'Residence')
                commercial_count = sum(1 for b in buildings if b.get('building_type') == 'Commercial')

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Buildings", len(buildings))
                col2.metric("Total Portions", total_portions)
                col3.metric("Residential", residence_count)
                col4.metric("Commercial", commercial_count)

                st.divider()

                # Batch fetch all tenants (single API call)
                all_tenants = fetch_all_tenants(token, API_BASE_URL, client_id)

                # Pre-compute tenant counts per building
                building_stats = {}
                for building in buildings:
                    bid = building.get('building_id')
                    building_tenants = [t for t in all_tenants if t.get('building_id') == bid]
                    occupied_portions = len(set(t.get('portion_number') for t in building_tenants))
                    building_stats[bid] = {
                        'tenant_count': len(building_tenants),
                        'occupied_portions': occupied_portions
                    }

                for building in buildings:
                    building_id = building.get('building_id')
                    owner_name = owner_id_to_name.get(building.get('owner_id'), 'N/A')
                    stats = building_stats.get(building_id, {'tenant_count': 0, 'occupied_portions': 0})
                    tenant_count = stats['tenant_count']
                    occupied_portions = stats['occupied_portions']
                    total_portions = building.get('number_of_portions', 0)
                    occupancy = f"{occupied_portions}/{total_portions}" if total_portions > 0 else "N/A"

                    # Building type icon
                    type_icon = "🏠" if building.get('building_type') == 'Residence' else "🏪"

                    with st.expander(f"{type_icon} {building.get('building_name', 'N/A')} | {occupancy} Occupied | {tenant_count} Tenants"):
                        edit_key = f"edit_building_{building_id}"

                        if st.session_state.get(edit_key, False):
                            # Edit mode
                            with st.form(f"edit_building_form_{building_id}"):
                                st.markdown("**Edit Building Details**")

                                edit_name = st.text_input("Building Name", value=building.get('building_name', ''), key=f"edit_bname_{building_id}")
                                edit_type = st.selectbox(
                                    "Building Type",
                                    options=["Residence", "Commercial"],
                                    index=0 if building.get('building_type') == 'Residence' else 1,
                                    key=f"edit_btype_{building_id}"
                                )
                                edit_portions = st.number_input(
                                    "Number of Portions",
                                    min_value=1,
                                    value=building.get('number_of_portions', 1),
                                    key=f"edit_portions_{building_id}"
                                )
                                edit_location = st.text_input("Location", value=building.get('location', '') or '', key=f"edit_location_{building_id}")

                                col1, col2 = st.columns(2)
                                with col1:
                                    save_btn = st.form_submit_button("Save Changes", use_container_width=True)
                                with col2:
                                    cancel_btn = st.form_submit_button("Cancel", use_container_width=True)

                                if save_btn:
                                    try:
                                        update_data = {
                                            "building_name": edit_name,
                                            "building_type": edit_type,
                                            "number_of_portions": edit_portions,
                                            "location": edit_location if edit_location else None
                                        }
                                        update_resp = requests.put(f"{API_BASE_URL}/api/buildings/{building_id}", json=update_data, headers=headers)
                                        if update_resp.status_code == 200:
                                            st.success("Building updated successfully!")
                                            st.session_state[edit_key] = False
                                            clear_building_cache()
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
                                | **Owner** | {owner_name} |
                                | **Type** | {building.get('building_type', 'N/A')} |
                                | **Total Portions** | {total_portions} |
                                | **Occupied** | {occupied_portions} |
                                | **Vacant** | {total_portions - occupied_portions} |
                                | **Tenants** | {tenant_count} |
                                | **Location** | {building.get('location', 'N/A') or 'N/A'} |
                                | **Building ID** | {building_id} |
                                """)

                            with col2:
                                if st.button("Edit", key=f"edit_btn_b_{building_id}", use_container_width=True):
                                    st.session_state[edit_key] = True
                                    st.session_state['building_active_tab'] = "Manage Buildings"
                                    st.rerun()

                                if st.button("Delete", key=f"delete_building_{building_id}", type="primary", use_container_width=True):
                                    if tenant_count > 0:
                                        st.error("Cannot delete building with tenants. Remove tenants first.")
                                    else:
                                        try:
                                            delete_response = requests.delete(f"{API_BASE_URL}/api/buildings/{building_id}", headers=headers)
                                            if delete_response.status_code == 204:
                                                st.success("Building deleted successfully!")
                                                clear_building_cache()
                                                st.rerun()
                                            else:
                                                st.error("Failed to delete building")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
            else:
                st.info("No buildings found. Add your first building using the 'Add Building' tab.")

        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend API. Please ensure the server is running.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
