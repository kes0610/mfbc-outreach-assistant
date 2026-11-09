import streamlit as st

st.set_page_config(page_title="MFBC Outreach Assistant", layout="wide")

pages = [
    st.Page("views/0_Home.py", title="Home", url_path="home", default=True),
    st.Page("views/1_Outreach_History.py", title="Outreach History", url_path="outreach-history"),
    st.Page("views/2_Draft_Email.py", title="Draft Email", url_path="draft-email"),
    st.Page("views/3_Templates.py", title="Templates", url_path="templates"),
    st.Page("views/4_History.py", title="History", url_path="history"),
]

nav = st.navigation(pages, position="top")
nav.run()
