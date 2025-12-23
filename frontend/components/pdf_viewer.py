import streamlit as st
import requests
import base64

def get_api_url():
    # Try to get from session state first
    if 'API_BASE_URL' in st.session_state:
        return st.session_state['API_BASE_URL']
    # Try secrets, fallback to default
    try:
        return st.secrets.get("API_BASE_URL", "http://localhost:8000")
    except (FileNotFoundError, AttributeError):
        return "http://localhost:8000"


def render_pdf_viewer(tenant_id: int, file_type: str = "agreement"):
    """Render PDF viewer for tenant documents"""
    title = "Agreement" if file_type == "agreement" else "Aadhar Card"
    st.title(f"PDF Viewer - {title}")

    # Back button
    if st.button("Back to Tenants"):
        st.session_state.pop('view_pdf_tenant_id', None)
        st.session_state.pop('view_pdf_type', None)
        st.rerun()

    try:
        # Get PDF file for tenant
        API_BASE_URL = get_api_url()
        response = requests.get(
            f"{API_BASE_URL}/api/files/tenant/{tenant_id}",
            params={"file_type": file_type}
        )

        if response.status_code == 200:
            # Save PDF temporarily and display
            pdf_content = response.content

            # Display PDF using base64 embedding
            base64_pdf = base64.b64encode(pdf_content).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)

            # Download button
            st.download_button(
                label=f"Download {title} PDF",
                data=pdf_content,
                file_name=f"tenant_{tenant_id}_{file_type}.pdf",
                mime="application/pdf"
            )
        else:
            error_detail = response.json().get('detail', 'Unknown error') if response.headers.get('content-type', '').startswith('application/json') else response.text
            st.error(f"{title} PDF not found: {error_detail}")

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend API. Please ensure the server is running.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
