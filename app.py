import streamlit as st

# Streamlit UI for landing page
st.set_page_config(page_title="Resume & Portfolio Generator", page_icon="🚀", layout="centered")

st.title("Welcome to Resume & Portfolio Generator")
st.markdown("""
Create a professional resume or a stunning portfolio website with ease.  
Choose an option below to get started!
""")

col1, col2 = st.columns(2)
with col1:
    if st.button("Make Resume"):
        st.switch_page("pages/resume.py")
with col2:
    if st.button("Make Portfolio"):
        st.switch_page("pages/portfolio.py")
