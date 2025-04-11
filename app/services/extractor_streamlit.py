import os
import tempfile
import base64
import sys
import streamlit as st


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))) #needed for streamlit to identify relative system paths
from app.services.form_extraction import W9FormExtraction    #add any module imports after  the above line

w9_form_extractor = W9FormExtraction()

st.set_page_config(page_title="📄 AI W9-Form Extractor", layout="wide")
st.image("https://www.intimetec.com/hubfs/ITT-footer-logo.svg")


USERNAME = "admin"
PASSWORD = "P@ssword123"




st.markdown(
    """
    <style>
        .header { text-align: center; font-size: 150px; font-weight: bold; color: #f8f9fa; margin-bottom: 10px; }
        .st-emotion-cache-7czcpc > img { border-radius : 0rem; }
        .stFileUploader { border: 2px dashed #0000FF !important; background-color: #f8f9fa; padding: 15px; border-radius: 10px; }
        .stButton>button { background: linear-gradient(90deg, #0000FF, #ff6a6a); color: white; font-size: 18px; font-weight: bold; border-radius: 8px; padding: 12px 30px; transition: all 0.3s ease-in-out; box-shadow: 0px 4px 10px rgba(255, 75, 75, 0.3); }
        .stButton>button:hover { background: linear-gradient(90deg, #e63939, #0000FF); transform: scale(1.05); }
        .stJson { max-height: 850px; overflow-y: auto; border: 2px solid #0000FF; padding: 20px; border-radius: 10px; background: #ffffff; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1); font-size: 16px; }
        iframe { border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.15); }
    </style>
""",
    unsafe_allow_html=True,
)


def login():
    """Handles user authentication."""
    st.title("🔐 Login to AI W9 Form Extractor")
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
        help="Your credentials are case-sensitive.",
    )

    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state["authenticated"] = True
            st.success("✅ Login successful! Redirecting...")
            st.rerun()  
        else:
            st.error("❌ Incorrect username or password. Please try again.")



if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop() 




def display_pdf_viewer(pdf_path):
        with open(pdf_path, "rb") as pdf_file:
            base64_pdf = base64.b64encode(pdf_file.read()).decode("utf-8")
        pdf_viewer = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="850px"></iframe>'
        st.markdown(pdf_viewer, unsafe_allow_html=True)




if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.warning("⚠️ You must log in to access the AI W9 Form Extractor.")
    login()
    st.stop() 


def main():
    st.markdown(
        '<h1 class="header">📄 AI W9 Form Extractor</h1>', unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        "📤 Upload W9 Form PDF", type="pdf", accept_multiple_files=False
    )

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_path = tmp_file.name  



        with st.spinner("⏳ Extracting data... Please wait!"):
            extracted_data = w9_form_extractor.extract_form_data(temp_path)

        
        col1, col2 = st.columns([0.5, 0.5])

        with col1:
            st.subheader("📑 PDF Viewer")
            display_pdf_viewer(temp_path)

        with col2:
            st.subheader("📜 Extracted W9 Data")
            st.json(extracted_data, expanded=True) 


        os.remove(temp_path)


if __name__ == "__main__":
    main()