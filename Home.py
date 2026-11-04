import streamlit as st

import db

st.set_page_config(page_title="MFBC Outreach Assistant", page_icon="📬", layout="wide")
db.init_db()

st.title("📬 MFBC Outreach Assistant")
st.write(
    "A tool for the Madison Fashion Business Collective to draft outreach, "
    "estimate reply likelihood, and track follow-ups — built on the club's "
    "own outreach history."
)

st.info(
    "**Start with Outreach History** (left sidebar) — enter or import past and "
    "ongoing outreach there. Drafting and the reply-likelihood model are built "
    "on top of that data and aren't available yet."
)

df = db.fetch_all()
summary = db.compute_summary(df)
cols = st.columns(4)
cols[0].metric("Total emails logged", summary["total"])
cols[1].metric("Replied", summary["replied"])
cols[2].metric("No reply", summary["no_reply"])
rate = summary["reply_rate"]
cols[3].metric("Reply rate", f"{rate:.0%}" if rate is not None else "—")
