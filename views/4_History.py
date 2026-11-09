import streamlit as st

import db
from styling import inject_global_css, page_header

db.init_db()
inject_global_css()

page_header("History", "Full details on any brand — research, messages, and notes, in one place.")

df = db.fetch_all()

if df.empty:
    st.info("Nothing logged yet — start on Outreach History.")
else:
    target_id = st.session_state.pop("history_target_id", None)

    sorted_df = df.sort_values("updated_at", ascending=False)
    st.caption(f"{len(sorted_df)} brand(s)/people total, most recently updated first.")

    def _label(row):
        when = row.date_sent or "not sent"
        return f"{row.company} — {db.STAGE_LABELS.get(row.stage, row.stage)} — {when} (id {row.id})"

    options = {_label(row): row.id for row in sorted_df.itertuples()}
    labels = list(options.keys())

    default_idx = 0
    if target_id is not None:
        for i, rid in enumerate(options.values()):
            if rid == target_id:
                default_idx = i
                break

    choice = st.selectbox("Pick a brand to view", labels, index=default_idx)
    row = sorted_df[sorted_df["id"] == options[choice]].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stage", db.STAGE_LABELS.get(row["stage"], row["stage"]))
    c2.metric("Date sent", row["date_sent"] or "—")
    c3.metric("Outcome", db.OUTCOME_LABELS.get(row["outcome"], row["outcome"] or "—"))
    c4.metric("Sender", row["sender"] or "—")

    if row["contact_name"] or row["contact_role"]:
        st.caption(f"Contact: {row['contact_name'] or '—'} ({row['contact_role'] or 'role unknown'})")
    st.caption(f"Type of ask: {db.ASK_TYPE_LABELS.get(row['ask_type'], row['ask_type'] or '—')}")

    st.subheader("Saved message")
    if row["email_text"]:
        st.text_area(
            "Saved message", value=row["email_text"], height=280,
            key=f"history_email_{row['id']}", label_visibility="collapsed",
        )
    else:
        st.caption("No message drafted or sent for this one yet.")

    st.subheader("AI research behind it")
    if row.get("ai_chance_label") or row.get("ai_chance_reasoning"):
        if row.get("ai_chance_label"):
            c1, c2 = st.columns([1, 3])
            c1.metric("Researched reply chance", row["ai_chance_label"])
            c2.caption(row.get("ai_chance_reasoning") or "")
        elif row.get("ai_chance_reasoning"):
            st.caption(row["ai_chance_reasoning"])
        if row.get("ai_relied_on"):
            with st.expander("What this draft relied on", expanded=True):
                st.write(row["ai_relied_on"])
    else:
        st.caption(
            "No AI research saved for this one — it was drafted with the free template, "
            "hasn't been drafted yet, or was saved before this history feature existed."
        )

    if row["notes"]:
        st.subheader("Notes on this brand")
        st.write(row["notes"])
