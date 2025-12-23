import streamlit as st
import requests
from datetime import date
from frontend.components.auth import get_api_url, get_auth_headers, get_current_client_id


def get_headers():
    """Get auth headers for API requests"""
    return get_auth_headers()


def get_token():
    """Get just the token for cache key"""
    return st.session_state.get('access_token', '')


# Cached API calls to prevent repeated requests - longer TTL for better performance
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
def fetch_buildings_for_owner(token, api_url, owner_id):
    """Fetch buildings for a specific owner with caching"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.get(f"{api_url}/api/buildings/owner/{owner_id}", headers=headers, timeout=10)
    return response.json() if response.status_code == 200 else []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_tenants(token, api_url, search_term=None, owner_id=None, client_id=None):
    """Fetch tenants with caching"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    params = {"limit": 1000}
    if search_term:
        params["search"] = search_term
    if owner_id:
        params["owner_id"] = owner_id
    if client_id:
        params["client_id"] = client_id
    response = requests.get(f"{api_url}/api/tenants/", params=params, headers=headers, timeout=10)
    return response.json() if response.status_code == 200 else []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_building(token, api_url, building_id):
    """Fetch a single building with caching"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.get(f"{api_url}/api/buildings/{building_id}", headers=headers, timeout=10)
    return response.json() if response.status_code == 200 else None


@st.cache_data(ttl=300, show_spinner=False)
def fetch_all_buildings(token, api_url, client_id=None):
    """Fetch all buildings at once for batch lookup"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    params = {"limit": 1000}
    if client_id:
        params["client_id"] = client_id
    response = requests.get(f"{api_url}/api/buildings/", params=params, headers=headers, timeout=10)
    return response.json() if response.status_code == 200 else []


def clear_tenant_cache():
    """Clear tenant-related caches"""
    fetch_tenants.clear()
    fetch_building.clear()
    fetch_all_buildings.clear()
    fetch_owners.clear()
    fetch_buildings_for_owner.clear()


def render_tenant_form():
    """Render tenant management form"""
    st.title("Tenant Management")

    # Custom CSS for modern styling
    st.markdown("""
    <style>
        /* Modern expander styling */
        .streamlit-expanderHeader {
            background: #f8fafc !important;
            border-radius: 10px !important;
            border: 1px solid #e2e8f0 !important;
            font-weight: 500 !important;
        }
        .streamlit-expanderHeader:hover {
            background: #f1f5f9 !important;
            border-color: #cbd5e1 !important;
        }
        /* Status indicator dots */
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .status-active { background: #22c55e; }
        .status-warning { background: #f59e0b; }
        .status-danger { background: #ef4444; }
    </style>
    """, unsafe_allow_html=True)

    API_BASE_URL = get_api_url()
    headers = get_headers()
    token = get_token()
    client_id = get_current_client_id()

    # Fetch owners with caching
    try:
        owners = fetch_owners(token, API_BASE_URL, client_id)

        if not owners:
            st.warning("Please add at least one owner before adding tenants.")
            return

        owner_dict = {f"{owner['name']} (ID: {owner['owner_id']})": owner['owner_id'] for owner in owners}
        owner_id_to_name = {owner['owner_id']: owner['name'] for owner in owners}

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend API. Please ensure the server is running.")
        return
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return

    # Initialize tenant tab state
    if 'tenant_active_tab' not in st.session_state:
        st.session_state['tenant_active_tab'] = "Manage Tenants"

    # Tab selection using radio (supports programmatic selection)
    tab_options = ["Add Tenant", "Manage Tenants", "Generate Agreement"]
    tab_index = tab_options.index(st.session_state['tenant_active_tab']) if st.session_state['tenant_active_tab'] in tab_options else 1
    selected_tab = st.radio(
        "Select Action",
        tab_options,
        index=tab_index,
        horizontal=True,
        key="tenant_tab_selector",
        label_visibility="collapsed"
    )
    st.session_state['tenant_active_tab'] = selected_tab

    st.divider()

    if selected_tab == "Add Tenant":
        st.subheader("Add New Tenant")

        # Fetch buildings for selected owner (outside form to avoid st.stop() issues)
        selected_owner_display = st.selectbox("Select Owner *", options=list(owner_dict.keys()), key="tenant_owner_select")
        owner_id = owner_dict[selected_owner_display]

        # Fetch buildings for selected owner with caching
        buildings = fetch_buildings_for_owner(token, API_BASE_URL, owner_id)
        building_dict = {}

        if buildings:
            building_dict = {
                f"{b['building_name']} ({b['building_type']})": b['building_id']
                for b in buildings
            }
        else:
            st.warning("Please add at least one building for this owner before adding tenants.")

        # Only show form if buildings are available
        if buildings:
            with st.form("tenant_form"):
                selected_building = st.selectbox("Building *", options=list(building_dict.keys()), key="tenant_building_select")
                building_id = building_dict[selected_building]

                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Tenant Name *", placeholder="Enter tenant name")
                    phone = st.text_input("Phone Number *", placeholder="Enter phone number")
                with col2:
                    email = st.text_input("Email", placeholder="Enter email address (optional)")
                    portion_number = st.text_input("Portion Number *", placeholder="e.g., A-101")

                address = st.text_area("Permanent Address", placeholder="Enter tenant's permanent/native address")

                # Rent breakdown fields
                st.markdown("**Rent Details**")
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    rent_amount = st.number_input("Base Rent *", min_value=0.0, value=0.0, step=100.0)
                with col2:
                    water_charge = st.number_input("Water Charge", min_value=0.0, value=0.0, step=50.0)
                with col3:
                    maintenance_charge = st.number_input("Maintenance", min_value=0.0, value=0.0, step=50.0)
                with col4:
                    advance_amount = st.number_input("Advance", min_value=0.0, value=0.0, step=1000.0)
                with col5:
                    rent_due_date = st.number_input("Due Date (Day)", min_value=1, max_value=28, value=1, step=1, help="Day of month when rent is due (1-28)")

                total_monthly = rent_amount + water_charge + maintenance_charge
                st.info(f"Total Monthly Rent: Rs. {total_monthly:,.0f} | Due on {rent_due_date}th of each month")

                col1, col2 = st.columns(2)
                with col1:
                    agreement_start_date = st.date_input("Agreement Start Date *", value=date.today())
                with col2:
                    agreement_end_date = st.date_input("Agreement End Date *", value=date.today())

                agreement_pdf = st.file_uploader("Upload Agreement PDF", type=["pdf"], accept_multiple_files=False, key="agreement_pdf")

                st.divider()
                st.markdown("**Aadhar Details (Optional)**")
                aadhar_number = st.text_input("Aadhar Number", placeholder="Enter 12-digit Aadhar number", max_chars=12)
                aadhar_pdf = st.file_uploader("Upload Aadhar Card PDF", type=["pdf"], accept_multiple_files=False, key="aadhar_pdf")

                submitted = st.form_submit_button("Add Tenant", use_container_width=True)

                if submitted:
                    if not name or not phone or not portion_number or rent_amount <= 0:
                        st.error("Please fill in all required fields (*)")
                    elif agreement_start_date >= agreement_end_date:
                        st.error("Agreement end date must be after start date")
                    else:
                        try:
                            data = {
                                "name": name,
                                "phone": phone,
                                "email": email if email else None,
                                "address": address if address else None,
                                "portion_number": portion_number,
                                "rent_amount": float(rent_amount),
                                "water_charge": float(water_charge),
                                "maintenance_charge": float(maintenance_charge),
                                "advance_amount": float(advance_amount),
                                "rent_due_date": int(rent_due_date),
                                "agreement_start_date": agreement_start_date.isoformat(),
                                "agreement_end_date": agreement_end_date.isoformat(),
                                "building_id": building_id,
                                "owner_id": owner_id,
                                "aadhar_number": aadhar_number if aadhar_number else None
                            }

                            response = requests.post(f"{API_BASE_URL}/api/tenants/", json=data, headers=headers)

                            if response.status_code == 201:
                                tenant_data = response.json()
                                tenant_id = tenant_data.get("tenant_id")

                                # Upload Agreement PDF if provided
                                agreement_uploaded = False
                                aadhar_uploaded = False

                                if agreement_pdf is not None:
                                    try:
                                        file_content = agreement_pdf.getvalue()
                                        files = {"file": (agreement_pdf.name, file_content, "application/pdf")}
                                        upload_url = f"{API_BASE_URL}/api/files/upload?tenant_id={tenant_id}&file_type=agreement"
                                        upload_response = requests.post(upload_url, files=files, headers=headers)
                                        agreement_uploaded = upload_response.status_code == 200
                                        if not agreement_uploaded:
                                            st.warning(f"Agreement upload failed: {upload_response.text}")
                                    except Exception as upload_err:
                                        st.warning(f"Agreement upload error: {str(upload_err)}")

                                # Upload Aadhar PDF if provided
                                if aadhar_pdf is not None:
                                    try:
                                        file_content = aadhar_pdf.getvalue()
                                        files = {"file": (aadhar_pdf.name, file_content, "application/pdf")}
                                        upload_url = f"{API_BASE_URL}/api/files/upload?tenant_id={tenant_id}&file_type=aadhar"
                                        upload_response = requests.post(upload_url, files=files, headers=headers)
                                        aadhar_uploaded = upload_response.status_code == 200
                                        if not aadhar_uploaded:
                                            st.warning(f"Aadhar upload failed: {upload_response.text}")
                                    except Exception as upload_err:
                                        st.warning(f"Aadhar upload error: {str(upload_err)}")

                                # Show appropriate success message
                                if agreement_pdf or aadhar_pdf:
                                    upload_status = []
                                    if agreement_pdf:
                                        upload_status.append("Agreement " + ("uploaded" if agreement_uploaded else "failed"))
                                    if aadhar_pdf:
                                        upload_status.append("Aadhar " + ("uploaded" if aadhar_uploaded else "failed"))
                                    st.success(f"Tenant added successfully! {', '.join(upload_status)}")
                                else:
                                    st.success("Tenant added successfully!")

                                # Clear cache and rerun
                                clear_tenant_cache()
                                st.rerun()
                            else:
                                error_msg = response.json().get("detail", "Error adding tenant")
                                st.error(error_msg)
                        except requests.exceptions.ConnectionError:
                            st.error("Cannot connect to backend API. Please ensure the server is running.")
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")

    elif selected_tab == "Manage Tenants":
        st.subheader("Manage Tenants")

        # Search and filter
        col1, col2, col3 = st.columns(3)
        with col1:
            search_term = st.text_input("Search tenants", placeholder="Search by name, phone, portion", key="tenant_search")
        with col2:
            filter_owner = st.selectbox(
                "Filter by Owner",
                options=["All"] + list(owner_dict.keys()),
                key="tenant_filter"
            )
        with col3:
            filter_status = st.selectbox(
                "Filter by Status",
                options=["All", "Active", "Expiring Soon", "Expired"],
                key="tenant_status_filter"
            )

        try:
            # Use cached tenant fetch
            owner_id_filter = owner_dict[filter_owner] if filter_owner != "All" else None
            tenants = fetch_tenants(token, API_BASE_URL, search_term if search_term else None, owner_id_filter, client_id)

            # Filter by status (client-side)
            filtered_tenants = []
            for tenant in tenants:
                try:
                    end_date = date.fromisoformat(tenant.get('agreement_end_date', ''))
                    days_remaining = (end_date - date.today()).days

                    if filter_status == "All":
                        filtered_tenants.append(tenant)
                    elif filter_status == "Active" and days_remaining > 30:
                        filtered_tenants.append(tenant)
                    elif filter_status == "Expiring Soon" and 0 <= days_remaining <= 30:
                        filtered_tenants.append(tenant)
                    elif filter_status == "Expired" and days_remaining < 0:
                        filtered_tenants.append(tenant)
                except:
                    if filter_status == "All":
                        filtered_tenants.append(tenant)

            tenants = filtered_tenants

            if tenants:
                # Summary stats - use total_rent from response
                total_rent = sum(t.get('total_rent', t.get('rent_amount', 0)) for t in tenants)
                total_advance = sum(t.get('advance_amount', 0) for t in tenants)
                active_count = sum(1 for t in tenants if (date.fromisoformat(t.get('agreement_end_date', '2000-01-01')) - date.today()).days > 30)
                expiring_count = sum(1 for t in tenants if 0 <= (date.fromisoformat(t.get('agreement_end_date', '2000-01-01')) - date.today()).days <= 30)
                expired_count = sum(1 for t in tenants if (date.fromisoformat(t.get('agreement_end_date', '2000-01-01')) - date.today()).days < 0)

                # Modern stats cards
                st.markdown(f"""
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;">
                    <div style="background: white; border-radius: 12px; padding: 20px;
                                border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <p style="color: #6b7280; font-size: 13px; margin: 0; font-weight: 500;">Total Tenants</p>
                        <p style="color: #111827; font-size: 28px; margin: 8px 0 0; font-weight: 700;">{len(tenants)}</p>
                    </div>
                    <div style="background: white; border-radius: 12px; padding: 20px;
                                border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <p style="color: #6b7280; font-size: 13px; margin: 0; font-weight: 500;">Monthly Revenue</p>
                        <p style="color: #059669; font-size: 28px; margin: 8px 0 0; font-weight: 700;">Rs.{total_rent:,.0f}</p>
                    </div>
                    <div style="background: white; border-radius: 12px; padding: 20px;
                                border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <p style="color: #6b7280; font-size: 13px; margin: 0; font-weight: 500;">Expiring Soon</p>
                        <p style="color: #f59e0b; font-size: 28px; margin: 8px 0 0; font-weight: 700;">{expiring_count}</p>
                    </div>
                    <div style="background: white; border-radius: 12px; padding: 20px;
                                border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <p style="color: #6b7280; font-size: 13px; margin: 0; font-weight: 500;">Expired</p>
                        <p style="color: #ef4444; font-size: 28px; margin: 8px 0 0; font-weight: 700;">{expired_count}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Pre-fetch all buildings at once (single API call)
                all_buildings = fetch_all_buildings(token, API_BASE_URL, client_id)
                building_names = {b['building_id']: b.get('building_name', 'N/A') for b in all_buildings}

                # Group tenants by building
                tenants_by_building = {}
                for tenant in tenants:
                    building_id = tenant.get('building_id')
                    if building_id not in tenants_by_building:
                        tenants_by_building[building_id] = []
                    tenants_by_building[building_id].append(tenant)

                # Sort buildings by name for consistent display
                sorted_building_ids = sorted(tenants_by_building.keys(), key=lambda bid: building_names.get(bid, 'N/A'))

                for building_id in sorted_building_ids:
                    building_name = building_names.get(building_id, 'N/A')
                    building_tenants = tenants_by_building[building_id]
                    tenant_count = len(building_tenants)
                    building_rent = sum(t.get('total_rent', t.get('rent_amount', 0)) for t in building_tenants)

                    # Modern building header card - single line
                    st.markdown(f"""
                    <div style="background: #1e293b; border-radius: 10px; padding: 14px 20px; margin: 20px 0 10px 0;">
                        <span style="color: white; font-size: 15px; font-weight: 600;">{building_name}</span>
                        <span style="color: #94a3b8; font-size: 14px; margin-left: 12px;">
                            {tenant_count} tenant{'s' if tenant_count > 1 else ''} &bull; Rs. {building_rent:,.0f}/month
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                    for tenant in building_tenants:
                        tenant_id = tenant.get('tenant_id')
                        owner_name = owner_id_to_name.get(tenant.get('owner_id'), 'N/A')

                        # Calculate days until expiry
                        try:
                            end_date = date.fromisoformat(tenant.get('agreement_end_date', ''))
                            days_remaining = (end_date - date.today()).days
                            if days_remaining < 0:
                                status = "Expired"
                                status_icon = "🔴"
                            elif days_remaining <= 30:
                                status = f"{days_remaining} days left"
                                status_icon = "🟡"
                            else:
                                status = f"{days_remaining} days left"
                                status_icon = "🟢"
                        except:
                            status = "N/A"
                            status_icon = ""

                        total_monthly = tenant.get('total_rent', tenant.get('rent_amount', 0))
                        with st.expander(f"{status_icon} {tenant.get('name', 'N/A')} | Portion: {tenant.get('portion_number', 'N/A')} | Rs.{total_monthly:,.0f}/mo"):
                            edit_key = f"edit_tenant_{tenant_id}"

                            if st.session_state.get(edit_key, False):
                                # Edit mode
                                with st.form(f"edit_tenant_form_{tenant_id}"):
                                    st.markdown("**Edit Tenant Details**")

                                    col1, col2 = st.columns(2)
                                    with col1:
                                        edit_name = st.text_input("Name", value=tenant.get('name', ''), key=f"edit_tname_{tenant_id}")
                                        edit_phone = st.text_input("Phone", value=tenant.get('phone', ''), key=f"edit_tphone_{tenant_id}")
                                        edit_portion = st.text_input("Portion", value=tenant.get('portion_number', ''), key=f"edit_tportion_{tenant_id}")
                                    with col2:
                                        edit_email = st.text_input("Email", value=tenant.get('email', '') or '', key=f"edit_temail_{tenant_id}")
                                        edit_aadhar = st.text_input("Aadhar", value=tenant.get('aadhar_number', '') or '', key=f"edit_taadhar_{tenant_id}")

                                    edit_address = st.text_area("Permanent Address", value=tenant.get('address', '') or '', key=f"edit_taddress_{tenant_id}")

                                    st.markdown("**Rent Details**")
                                    col1, col2, col3, col4, col5 = st.columns(5)
                                    with col1:
                                        edit_rent = st.number_input("Base Rent", min_value=0.0, value=float(tenant.get('rent_amount', 0)), key=f"edit_trent_{tenant_id}")
                                    with col2:
                                        edit_water = st.number_input("Water", min_value=0.0, value=float(tenant.get('water_charge', 0)), key=f"edit_twater_{tenant_id}")
                                    with col3:
                                        edit_maintenance = st.number_input("Maintenance", min_value=0.0, value=float(tenant.get('maintenance_charge', 0)), key=f"edit_tmaint_{tenant_id}")
                                    with col4:
                                        edit_advance = st.number_input("Advance", min_value=0.0, value=float(tenant.get('advance_amount', 0)), key=f"edit_tadvance_{tenant_id}")
                                    with col5:
                                        edit_due_date = st.number_input("Due Date", min_value=1, max_value=28, value=int(tenant.get('rent_due_date', 1)), key=f"edit_tdue_{tenant_id}")

                                    col1, col2 = st.columns(2)
                                    with col1:
                                        edit_start = st.date_input("Start Date", value=date.fromisoformat(tenant.get('agreement_start_date', date.today().isoformat())), key=f"edit_tstart_{tenant_id}")
                                    with col2:
                                        edit_end = st.date_input("End Date", value=date.fromisoformat(tenant.get('agreement_end_date', date.today().isoformat())), key=f"edit_tend_{tenant_id}")

                                    col1, col2 = st.columns(2)
                                    with col1:
                                        save_btn = st.form_submit_button("Save Changes", use_container_width=True)
                                    with col2:
                                        cancel_btn = st.form_submit_button("Cancel", use_container_width=True)

                                    if save_btn:
                                        if edit_start >= edit_end:
                                            st.error("End date must be after start date")
                                        else:
                                            try:
                                                update_data = {
                                                    "name": edit_name,
                                                    "phone": edit_phone,
                                                    "email": edit_email if edit_email else None,
                                                    "address": edit_address if edit_address else None,
                                                    "portion_number": edit_portion,
                                                    "rent_amount": edit_rent,
                                                    "water_charge": edit_water,
                                                    "maintenance_charge": edit_maintenance,
                                                    "advance_amount": edit_advance,
                                                    "rent_due_date": int(edit_due_date),
                                                    "aadhar_number": edit_aadhar if edit_aadhar else None,
                                                    "agreement_start_date": edit_start.isoformat(),
                                                    "agreement_end_date": edit_end.isoformat()
                                                }
                                                update_resp = requests.put(f"{API_BASE_URL}/api/tenants/{tenant_id}", json=update_data, headers=headers)
                                                if update_resp.status_code == 200:
                                                    st.success("Tenant updated successfully!")
                                                    st.session_state[edit_key] = False
                                                    clear_tenant_cache()
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
                                col1, col2, col3 = st.columns([2, 2, 1])

                                with col1:
                                    due_day = tenant.get('rent_due_date', 1)
                                    st.markdown(f"""
                                    **Contact Information**
                                    - Phone: {tenant.get('phone', 'N/A')}
                                    - Email: {tenant.get('email', 'N/A') or 'N/A'}
                                    - Aadhar: {tenant.get('aadhar_number', 'N/A') or 'N/A'}
                                    - Address: {tenant.get('address', 'N/A') or 'N/A'}

                                    **Rent Breakdown**
                                    - Base Rent: Rs. {tenant.get('rent_amount', 0):,.0f}
                                    - Water: Rs. {tenant.get('water_charge', 0):,.0f}
                                    - Maintenance: Rs. {tenant.get('maintenance_charge', 0):,.0f}
                                    - **Total: Rs. {total_monthly:,.0f}**
                                    - Advance: Rs. {tenant.get('advance_amount', 0):,.0f}
                                    - Due Date: {due_day}th of each month
                                    """)

                                with col2:
                                    st.markdown(f"""
                                    **Agreement Details**
                                    - Owner: {owner_name}
                                    - Start: {tenant.get('agreement_start_date', 'N/A')}
                                    - End: {tenant.get('agreement_end_date', 'N/A')}
                                    - Status: {status}
                                    """)

                                with col3:
                                    if st.button("Edit", key=f"edit_btn_t_{tenant_id}", use_container_width=True):
                                        st.session_state[edit_key] = True
                                        st.session_state['tenant_active_tab'] = "Manage Tenants"
                                        st.rerun()

                                    if tenant.get('agreement_pdf_path'):
                                        if st.button("Agreement", key=f"view_pdf_{tenant_id}", use_container_width=True):
                                            st.session_state['view_pdf_tenant_id'] = tenant_id
                                            st.session_state['view_pdf_type'] = 'agreement'
                                            st.rerun()

                                    if tenant.get('aadhar_pdf_path'):
                                        if st.button("Aadhar", key=f"view_aadhar_{tenant_id}", use_container_width=True):
                                            st.session_state['view_pdf_tenant_id'] = tenant_id
                                            st.session_state['view_pdf_type'] = 'aadhar'
                                            st.rerun()

                                    if st.button("Delete", key=f"delete_tenant_{tenant_id}", type="primary", use_container_width=True):
                                        try:
                                            delete_response = requests.delete(f"{API_BASE_URL}/api/tenants/{tenant_id}", headers=headers)
                                            if delete_response.status_code == 204:
                                                st.success("Tenant deleted successfully!")
                                                clear_tenant_cache()
                                                st.rerun()
                                            else:
                                                st.error("Failed to delete tenant")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
            else:
                st.info("No tenants found. Add your first tenant using the 'Add Tenant' tab.")

        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend API. Please ensure the server is running.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    else:  # Generate Agreement tab
        st.subheader("Generate Rental Agreement")

        st.markdown("""
        Generate a rental agreement document from template. The system will automatically fill in:
        - Owner and Tenant details
        - Rent breakdown (Base rent, Water, Maintenance)
        - Agreement dates and duration
        - Advance amount
        """)

        # Fetch all tenants for selection
        try:
            all_tenants = fetch_tenants(token, API_BASE_URL, None, None, client_id)
            all_buildings = fetch_all_buildings(token, API_BASE_URL, client_id)
            building_names = {b['building_id']: b.get('building_name', 'N/A') for b in all_buildings}
            building_types = {b['building_id']: b.get('building_type', 'Residence') for b in all_buildings}

            if not all_tenants:
                st.warning("No tenants found. Please add tenants first.")
            else:
                # Create tenant selection dropdown
                tenant_options = {}
                for t in all_tenants:
                    building_name = building_names.get(t.get('building_id'), 'N/A')
                    display = f"{t['name']} | {building_name} - {t.get('portion_number', 'N/A')}"
                    tenant_options[display] = t

                selected_tenant_display = st.selectbox(
                    "Select Tenant",
                    options=list(tenant_options.keys()),
                    key="agreement_tenant_select"
                )

                if selected_tenant_display:
                    selected_tenant = tenant_options[selected_tenant_display]
                    tenant_id = selected_tenant.get('tenant_id')

                    # Fetch preview data
                    try:
                        preview_response = requests.get(
                            f"{API_BASE_URL}/api/files/agreement-preview/{tenant_id}",
                            headers=headers,
                            timeout=10
                        )

                        if preview_response.status_code == 200:
                            preview_data = preview_response.json()

                            # Display preview in columns
                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown("**Owner Details**")
                                owner_data = preview_data.get('owner', {})
                                stored_owner_aadhar = owner_data.get('aadhar_number', '') or ''
                                st.markdown(f"""
                                - **Name:** {owner_data.get('name', 'N/A')}
                                - **Phone:** {owner_data.get('phone', 'N/A')}
                                - **Aadhar:** {stored_owner_aadhar or 'Not provided'}
                                - **Address:** {owner_data.get('address', 'N/A') or 'Not provided'}
                                """)

                                st.markdown("**Rent Details**")
                                rent_data = preview_data.get('rent', {})
                                st.markdown(f"""
                                - **Base Rent:** Rs. {rent_data.get('base_rent', 0):,.0f}
                                - **Water Charge:** Rs. {rent_data.get('water_charge', 0):,.0f}
                                - **Maintenance:** Rs. {rent_data.get('maintenance_charge', 0):,.0f}
                                - **Total Rent:** Rs. {rent_data.get('total_rent', 0):,.0f}
                                - **Advance:** Rs. {rent_data.get('advance_amount', 0):,.0f}
                                - **Due Date:** {rent_data.get('rent_due_date', 1)}th of each month
                                """)

                            with col2:
                                st.markdown("**Tenant Details**")
                                tenant_data = preview_data.get('tenant', {})
                                stored_tenant_address = tenant_data.get('address', '') or ''
                                st.markdown(f"""
                                - **Name:** {tenant_data.get('name', 'N/A')}
                                - **Phone:** {tenant_data.get('phone', 'N/A')}
                                - **Aadhar:** {tenant_data.get('aadhar_number', 'N/A') or 'Not provided'}
                                - **Address:** {stored_tenant_address or 'Not provided'}
                                - **Portion:** {tenant_data.get('portion_number', 'N/A')}
                                """)

                                st.markdown("**Agreement Details**")
                                agreement_data = preview_data.get('agreement', {})
                                building_data = preview_data.get('building', {})
                                st.markdown(f"""
                                - **Building:** {building_data.get('name', 'N/A')}
                                - **Type:** {building_data.get('type', 'N/A')}
                                - **Start Date:** {agreement_data.get('start_date', 'N/A')}
                                - **End Date:** {agreement_data.get('end_date', 'N/A')}
                                - **Duration:** {agreement_data.get('duration', 'N/A')}
                                """)

                            st.divider()

                            # Check if additional info is needed
                            needs_owner_aadhar = not stored_owner_aadhar
                            needs_tenant_address = not stored_tenant_address
                            needs_additional_info = needs_owner_aadhar or needs_tenant_address

                            # Only show form if missing required fields
                            if needs_additional_info:
                                st.markdown("**Additional Information Required**")

                                with st.form("generate_agreement_form"):
                                    owner_aadhar = ""
                                    tenant_address = ""

                                    if needs_owner_aadhar:
                                        owner_aadhar = st.text_input(
                                            "Owner's Aadhar Number *",
                                            placeholder="Enter 12-digit Aadhar number",
                                            max_chars=12
                                        )

                                    if needs_tenant_address:
                                        tenant_address = st.text_area(
                                            "Tenant's Permanent Address *",
                                            placeholder="Enter tenant's permanent/native address"
                                        )

                                    generate_btn = st.form_submit_button("Generate Agreement", use_container_width=True, type="primary")

                                    if generate_btn:
                                        # Validate only the missing fields
                                        if needs_owner_aadhar and (not owner_aadhar or len(owner_aadhar) != 12):
                                            st.error("Please enter a valid 12-digit Aadhar number for the owner")
                                        elif needs_tenant_address and (not tenant_address or len(tenant_address.strip()) < 10):
                                            st.error("Please enter a valid address for the tenant (at least 10 characters)")
                                        else:
                                            try:
                                                params = {}
                                                if owner_aadhar:
                                                    params["owner_aadhar"] = owner_aadhar
                                                if tenant_address:
                                                    params["tenant_address"] = tenant_address.strip()

                                                response = requests.post(
                                                    f"{API_BASE_URL}/api/files/generate-agreement/{tenant_id}",
                                                    params=params,
                                                    headers=headers,
                                                    timeout=30
                                                )

                                                if response.status_code == 200:
                                                    content_disposition = response.headers.get('content-disposition', '')
                                                    if 'filename=' in content_disposition:
                                                        filename = content_disposition.split('filename=')[1].strip('"')
                                                    else:
                                                        filename = f"agreement_{tenant_id}.docx"

                                                    st.session_state['generated_agreement'] = {
                                                        'content': response.content,
                                                        'filename': filename,
                                                        'tenant_id': tenant_id
                                                    }
                                                    st.success("Agreement generated successfully! Click the download button below.")
                                                else:
                                                    error_msg = response.json().get('detail', 'Failed to generate agreement')
                                                    st.error(f"Error: {error_msg}")

                                            except requests.exceptions.ConnectionError:
                                                st.error("Cannot connect to backend API.")
                                            except Exception as e:
                                                st.error(f"An error occurred: {str(e)}")
                            else:
                                # All required fields are present - just show generate button
                                if st.button("Generate Agreement", use_container_width=True, type="primary", key="generate_btn_direct"):
                                    try:
                                        response = requests.post(
                                            f"{API_BASE_URL}/api/files/generate-agreement/{tenant_id}",
                                            params={},
                                            headers=headers,
                                            timeout=30
                                        )

                                        if response.status_code == 200:
                                            content_disposition = response.headers.get('content-disposition', '')
                                            if 'filename=' in content_disposition:
                                                filename = content_disposition.split('filename=')[1].strip('"')
                                            else:
                                                filename = f"agreement_{tenant_id}.docx"

                                            st.session_state['generated_agreement'] = {
                                                'content': response.content,
                                                'filename': filename,
                                                'tenant_id': tenant_id
                                            }
                                            st.success("Agreement generated successfully! Click the download button below.")
                                        else:
                                            error_msg = response.json().get('detail', 'Failed to generate agreement')
                                            st.error(f"Error: {error_msg}")

                                    except requests.exceptions.ConnectionError:
                                        st.error("Cannot connect to backend API.")
                                    except Exception as e:
                                        st.error(f"An error occurred: {str(e)}")

                            # Download button outside the form
                            if 'generated_agreement' in st.session_state and st.session_state['generated_agreement'].get('tenant_id') == tenant_id:
                                agreement_data = st.session_state['generated_agreement']
                                st.download_button(
                                    label="Download Agreement (.docx)",
                                    data=agreement_data['content'],
                                    file_name=agreement_data['filename'],
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    use_container_width=True
                                )

                        else:
                            st.error("Failed to load tenant preview data")

                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to backend API.")
                    except Exception as e:
                        st.error(f"Error loading preview: {str(e)}")

        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend API. Please ensure the server is running.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
