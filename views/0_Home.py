import streamlit as st

import db
from styling import inject_global_css, page_header

db.init_db()
inject_global_css()

page_header("MFBC Outreach Assistant", "Draft outreach, estimate reply chances, track the pipeline.")

st.info(
    "**Start with Outreach History** (top menu) to enter or import past and ongoing "
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

st.divider()
st.subheader("Follow-ups")

in_comm = df[df["stage"] == "in_communication"].copy()
needs_follow_up = in_comm[in_comm["outcome"].isin(["replied", "meeting_booked"])]
awaiting_reply = in_comm[in_comm["outcome"].isna() | (in_comm["outcome"] == "no_reply")]

if needs_follow_up.empty and awaiting_reply.empty:
    st.caption("Nothing in In communication right now — no follow-ups today.")
else:
    lines = []
    for row in needs_follow_up.itertuples():
        who = f" — {row.sender}" if row.sender else ""
        lines.append(f"- **Follow up with:** {row.company}{who}")
    for row in awaiting_reply.itertuples():
        who = f" — {row.sender}" if row.sender else ""
        lines.append(f"- **Awaiting response from:** {row.company}{who}")
    st.markdown("\n".join(lines))
