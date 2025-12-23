import streamlit as st
import requests
from datetime import datetime, date
import plotly.graph_objects as go
from frontend.components.auth import get_api_url, get_auth_headers, get_current_client_id


def get_token():
    """Get just the token for cache key"""
    return st.session_state.get('access_token', '')


@st.cache_data(ttl=300, show_spinner=False)
def fetch_dashboard_stats(token, api_url, client_id=None):
    """Fetch dashboard stats with caching"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    params = {}
    if client_id:
        params["client_id"] = client_id
    response = requests.get(f"{api_url}/api/dashboard/stats", params=params, headers=headers, timeout=10)
    return response.json() if response.status_code == 200 else None


def render_dashboard():
    """Render the main dashboard with statistics, metrics, and graphs"""
    st.title("Dashboard")

    try:
        API_BASE_URL = get_api_url()
        token = get_token()
        client_id = get_current_client_id()
        stats = fetch_dashboard_stats(token, API_BASE_URL, client_id)

        if stats:
            # Modern metric cards with icons
            total_owners = stats.get("total_owners", 0)
            total_buildings = stats.get("total_buildings", 0)
            total_tenants = stats.get("total_tenants", 0)
            expiring = stats.get("expiring_agreements", 0)

            st.markdown(f"""
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;">
                <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                            border-radius: 16px; padding: 24px; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <p style="color: rgba(255,255,255,0.8); font-size: 13px; margin: 0; font-weight: 500;">Total Owners</p>
                            <p style="color: white; font-size: 32px; margin: 8px 0 0; font-weight: 700;">{total_owners}</p>
                        </div>
                        <div style="background: rgba(255,255,255,0.2); border-radius: 12px; width: 48px; height: 48px;
                                    display: flex; align-items: center; justify-content: center; font-size: 24px;">👤</div>
                    </div>
                </div>
                <div style="background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%);
                            border-radius: 16px; padding: 24px; box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <p style="color: rgba(255,255,255,0.8); font-size: 13px; margin: 0; font-weight: 500;">Total Buildings</p>
                            <p style="color: white; font-size: 32px; margin: 8px 0 0; font-weight: 700;">{total_buildings}</p>
                        </div>
                        <div style="background: rgba(255,255,255,0.2); border-radius: 12px; width: 48px; height: 48px;
                                    display: flex; align-items: center; justify-content: center; font-size: 24px;">🏢</div>
                    </div>
                </div>
                <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                            border-radius: 16px; padding: 24px; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <p style="color: rgba(255,255,255,0.8); font-size: 13px; margin: 0; font-weight: 500;">Total Tenants</p>
                            <p style="color: white; font-size: 32px; margin: 8px 0 0; font-weight: 700;">{total_tenants}</p>
                        </div>
                        <div style="background: rgba(255,255,255,0.2); border-radius: 12px; width: 48px; height: 48px;
                                    display: flex; align-items: center; justify-content: center; font-size: 24px;">🏠</div>
                    </div>
                </div>
                <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                            border-radius: 16px; padding: 24px; box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <p style="color: rgba(255,255,255,0.8); font-size: 13px; margin: 0; font-weight: 500;">Expiring Soon</p>
                            <p style="color: white; font-size: 32px; margin: 8px 0 0; font-weight: 700;">{expiring}</p>
                        </div>
                        <div style="background: rgba(255,255,255,0.2); border-radius: 12px; width: 48px; height: 48px;
                                    display: flex; align-items: center; justify-content: center; font-size: 24px;">⏰</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Charts Section
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.subheader("Overall Occupancy")
                occupied = stats.get("occupied_portions", 0)
                vacant = stats.get("vacant_portions", 0)
                total_portions = stats.get("total_portions", 0)

                if total_portions > 0:
                    occupancy_pct = (occupied / total_portions * 100) if total_portions > 0 else 0

                    # Pie chart with transparent background
                    fig = go.Figure(data=[go.Pie(
                        labels=['Occupied', 'Vacant'],
                        values=[occupied, vacant],
                        hole=0.5,
                        marker_colors=['#22c55e', '#ef4444'],
                        textinfo='value',
                        textfont_size=14,
                        hovertemplate='%{label}: %{value} portions<extra></extra>'
                    )])

                    fig.update_layout(
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                        height=250,
                        margin=dict(l=0, r=0, t=0, b=40),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        annotations=[dict(
                            text=f'{occupancy_pct:.0f}%<br>Occupied',
                            x=0.5, y=0.5,
                            font_size=16,
                            showarrow=False
                        )]
                    )

                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                    # Summary below chart
                    st.caption(f"Total: {total_portions} portions")
                else:
                    st.info("No buildings found")

            with col_chart2:
                st.subheader("Per Building")
                occupancy_data = stats.get("building_occupancy", [])

                if occupancy_data:
                    # Add some top padding to align with pie chart
                    st.write("")
                    # Use Streamlit native progress bars
                    for building in occupancy_data:
                        bname = building.get('building_name', 'N/A')
                        occ = building.get('occupied_portions', 0)
                        total = building.get('total_portions', 1)
                        pct = (occ / total) if total > 0 else 0

                        # Building name and stats on same line
                        st.markdown(f"**{bname}** — {occ}/{total} occupied")
                        st.progress(min(pct, 1.0))
                else:
                    st.info("No buildings found")

            st.divider()

            # Expiring Agreements Section
            expiring_tenants = stats.get("expiring_tenants", [])
            st.subheader("Expiring Agreements (Next 30 Days)")

            if expiring_tenants:
                for tenant in expiring_tenants:
                    days = tenant.get("days_remaining", 0)
                    if days <= 7:
                        status_color = "🔴"
                        bg_color = "#fef2f2"
                        border_color = "#ef4444"
                    elif days <= 15:
                        status_color = "🟡"
                        bg_color = "#fffbeb"
                        border_color = "#f59e0b"
                    else:
                        status_color = "🟢"
                        bg_color = "#f0fdf4"
                        border_color = "#22c55e"

                    st.markdown(f"""
                    <div style="background: {bg_color}; border-left: 4px solid {border_color};
                                border-radius: 8px; padding: 12px 16px; margin: 8px 0;
                                display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #1e293b;">{status_color} {tenant.get('tenant_name', 'N/A')}</strong><br>
                            <span style="color: #64748b; font-size: 0.9rem;">{tenant.get('building_name', 'N/A')}</span>
                        </div>
                        <div style="text-align: right;">
                            <strong style="color: #1e293b;">{days} days</strong><br>
                            <span style="color: #64748b; font-size: 0.9rem;">{tenant.get('agreement_end_date', 'N/A')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("No agreements expiring in the next 30 days")

            st.divider()

            # Upcoming Rent Dues Section
            rent_dues = stats.get("upcoming_rent_dues", [])
            st.subheader("Upcoming Rent Dues (Next 7 Days)")

            if rent_dues:
                for tenant in rent_dues:
                    days = tenant.get("days_until_due", 0)
                    if days <= 2:
                        status_color = "🔴"
                        bg_color = "#fef2f2"
                        border_color = "#ef4444"
                    elif days <= 4:
                        status_color = "🟡"
                        bg_color = "#fffbeb"
                        border_color = "#f59e0b"
                    else:
                        status_color = "🟢"
                        bg_color = "#f0fdf4"
                        border_color = "#22c55e"

                    due_date = tenant.get("rent_due_date", 1)
                    total_rent = tenant.get("total_rent", 0)
                    portion = tenant.get("portion_number", "N/A")

                    st.markdown(f"""
                    <div style="background: {bg_color}; border-left: 4px solid {border_color};
                                border-radius: 8px; padding: 12px 16px; margin: 8px 0;
                                display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #1e293b;">{status_color} {tenant.get('tenant_name', 'N/A')}</strong><br>
                            <span style="color: #64748b; font-size: 0.9rem;">{tenant.get('building_name', 'N/A')} - Portion {portion}</span>
                        </div>
                        <div style="text-align: right;">
                            <strong style="color: #1e293b;">Due in {days} days</strong><br>
                            <span style="color: #64748b; font-size: 0.9rem;">Rs. {total_rent:,.0f} (Due: {due_date}th)</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("No rent dues in the next 7 days")

        else:
            st.error("Failed to load dashboard statistics.")

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the backend API. Please ensure the server is running.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
