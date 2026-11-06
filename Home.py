import streamlit as st

import db
from styling import inject_global_css, page_header

st.set_page_config(page_title="MFBC Outreach Assistant", page_icon="📬", layout="wide")
db.init_db()
inject_global_css()

page_header("MFBC Outreach Assistant", "Draft outreach, estimate reply chances, track the pipeline.")

st.info(
    "**Start with Outreach History** (left sidebar) to enter or import past and ongoing "
    "outreach — drafting and the reply-chance estimate are built on top of that data."
)

df = db.fetch_all()
summary = db.compute_summary(df)
cols = st.columns(4)
cols[0].metric("Total emails logged", summary["total"])
cols[1].metric("Replied", summary["replied"])
cols[2].metric("No reply", summary["no_reply"])
rate = summary["reply_rate"]
cols[3].metric("Reply rate", f"{rate:.0%}" if rate is not None else "—")
