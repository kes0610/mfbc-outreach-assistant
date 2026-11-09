import streamlit as st

import db
from styling import inject_global_css, page_header

db.init_db()
inject_global_css()

page_header("History", "Every saved draft and the AI research behind it, in one place.")

df = db.fetch_all()
sent_df = df[df["email_text"].notna() & (df["email_text"].str.strip() != "")].copy()
sent_df = sent_df.sort_values("updated_at", ascending=False)

if sent_df.empty:
    st.info("Nothing saved yet — drafts you save or mark as sent on the Draft Email page show up here.")
else:
    st.caption(f"{len(sent_df)} saved draft(s), most recently updated first.")

    def _label(row):
        when = row.date_sent or "not sent"
        return f"{row.company} — {db.STAGE_LABELS.get(row.stage, row.stage)} — {when} (id {row.id})"

    options = {_label(row): row.id for row in sent_df.itertuples()}
    choice = st.selectbox("Pick a brand to view", list(options.keys()))
    row = sent_df[sent_df["id"] == options[choice]].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stage", db.STAGE_LABELS.get(row["stage"], row["stage"]))
    c2.metric("Date sent", row["date_sent"] or "—")
    c3.metric("Outcome", db.OUTCOME_LABELS.get(row["outcome"], row["outcome"] or "—"))
    c4.metric("Sender", row["sender"] or "—")

    if row["contact_name"] or row["contact_role"]:
        st.caption(f"Contact: {row['contact_name'] or '—'} ({row['contact_role'] or 'role unknown'})")

    st.subheader("Saved message")
    st.text_area(
        "Saved message", value=row["email_text"], height=280,
        key=f"history_email_{row['id']}", label_visibility="collapsed",
    )

    st.subheader("AI research behind it")
    if row.get("ai_chance_label") or row.get("ai_chance_reasoning"):
        if row.get("ai_chance_label"):
            c1, c2 = st.columns([1, 3])
            c1.metric("Researched reply chance", row["ai_chance_label"])
            c2.caption(row.get("ai_chance_reasoning") or "")
        elif row.get("ai_chance_reasoning"):
            st.caption(row["ai_chance_reasoning"])
        if row.get("ai_relied_on"):
            with st.expander("What this draft relied on"):
                st.write(row["ai_relied_on"])
    else:
        st.caption(
            "No AI research saved for this one — it was drafted with the free template, or "
            "saved before this history feature existed."
        )

    if row["notes"]:
        with st.expander("Notes on this brand"):
            st.write(row["notes"])
