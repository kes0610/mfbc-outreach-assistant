import streamlit as st

st.set_page_config(page_title="MFBC Outreach Assistant", page_icon="📬", layout="wide")

pages = [
    st.Page("views/0_Home.py", title="Home", icon="🏠", url_path="home", default=True),
    st.Page("views/1_Outreach_History.py", title="Outreach History", icon="📋", url_path="outreach-history"),
    st.Page("views/2_Draft_Email.py", title="Draft Email", icon="✉️", url_path="draft-email"),
    st.Page("views/3_Templates.py", title="Templates", icon="📝", url_path="templates"),
]

nav = st.navigation(pages, position="top")
nav.run()
