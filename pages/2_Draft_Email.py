from datetime import date, datetime

import streamlit as st

import db
import drafting

st.set_page_config(page_title="Draft Email", page_icon="✉️", layout="wide")
db.init_db()

st.title("✉️ Draft Outreach Email")
st.caption(
    "Drafts only — nothing is ever sent from here. A member reviews, edits, and sends it "
    "themselves from their own email."
)

if not drafting.api_key_available():
    st.error(
        "ANTHROPIC_API_KEY isn't set, so drafting can't call the Claude API. "
        "Set it as an environment variable (never hard-coded) before using this page:\n\n"
        "`export ANTHROPIC_API_KEY=sk-ant-...`"
    )
    st.stop()

df = db.fetch_all()
new_df = df[df["stage"] == "new"].copy()

target_id = st.session_state.get("draft_target_id")
target = None
if target_id is not None:
    match = df[df["id"] == target_id]
    if not match.empty:
        target = match.iloc[0].to_dict()

st.subheader("1. Who is this for?")
mode = st.radio(
    "Brand source",
    ["Pick from New brand", "Enter a brand not logged yet"],
    horizontal=True,
    index=0 if target is not None else (0 if not new_df.empty else 1),
)

if mode == "Pick from New brand":
    if new_df.empty:
        st.info("Nothing in New brand to pick from — switch to entering one manually.")
        brand_info = None
    else:
        default_idx = 0
        options = {f"{row.company} (id {row.id})": row.id for row in new_df.itertuples()}
        if target is not None:
            for i, (label, rid) in enumerate(options.items()):
                if rid == target_id:
                    default_idx = i
        choice = st.selectbox("Brand", list(options.keys()), index=default_idx)
        row_id = options[choice]
        brand_info = df[df["id"] == row_id].iloc[0].to_dict()
else:
    c1, c2 = st.columns(2)
    with c1:
        company = st.text_input("Company *")
        contact_name = st.text_input("Contact name")
        contact_role = st.text_input("Contact role")
    with c2:
        ask_type = st.selectbox("Type of ask", db.ASK_TYPES, format_func=lambda k: db.ASK_TYPE_LABELS[k])
        has_uw_mfbc_connection = st.checkbox("UW or MFBC connection")
        has_prior_relationship = st.checkbox("Prior relationship")
    notes = st.text_area("Notes about this brand")
    brand_info = {
        "id": None,
        "company": company.strip(),
        "contact_name": contact_name.strip() or None,
        "contact_role": contact_role.strip() or None,
        "ask_type": ask_type,
        "has_uw_mfbc_connection": has_uw_mfbc_connection,
        "has_prior_relationship": has_prior_relationship,
        "is_follow_up": False,
        "notes": notes.strip() or None,
    } if company.strip() else None

if brand_info:
    chance = db.estimate_reply_chance(brand_info, df)
    c1, c2 = st.columns([1, 3])
    c1.metric("Rough reply chance", chance["label"])
    c2.caption(
        f"Rule of thumb, not a trained model ({chance['base_n']} labeled outcome(s) so far, "
        f"need {db.MODEL_MIN_N}+). " + " · ".join(chance["reasons"])
    )

    st.subheader("2. Anything else true about this brand?")
    extra_info = st.text_area(
        "Paste any public information you know about them (website copy, recent news, "
        "their Instagram bio, etc.) — the draft will only use what's here plus the fields above.",
        key="extra_public_info",
    )

    if st.button("Generate draft", type="primary"):
        with st.spinner("Drafting..."):
            try:
                result = drafting.generate_draft(brand_info, extra_info)
                st.session_state["draft_result"] = result
            except Exception as exc:
                st.error(f"Couldn't generate a draft: {exc}")

    result = st.session_state.get("draft_result")
    if result:
        st.subheader("3. Review and edit")
        edited_draft = st.text_area("Draft email", value=result["draft"], height=280)
        with st.expander("What this draft relied on"):
            st.write(result["relied_on"])
        st.caption(
            "Check every placeholder in brackets and every claim before sending — this tool "
            "never sends email on its own."
        )

        st.subheader("4. Save it")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Save draft to this brand's record"):
                record = {c: brand_info.get(c) for c in db.EDITABLE_COLUMNS}
                record["email_text"] = edited_draft
                if brand_info.get("id") is not None:
                    db.update_record(int(brand_info["id"]), record)
                else:
                    record.setdefault("outcome", None)
                    db.insert_record(record)
                st.success("Draft saved.")
                st.rerun()
        with c2:
            sent_date = st.date_input("Date actually sent", value=date.today())
            if st.button("Mark as sent"):
                record = {c: brand_info.get(c) for c in db.EDITABLE_COLUMNS}
                record["email_text"] = edited_draft
                record["date_sent"] = sent_date.isoformat()
                record["stage"] = "in_communication"
                if brand_info.get("id") is not None:
                    db.update_record(int(brand_info["id"]), record)
                else:
                    db.insert_record(record)
                st.session_state.pop("draft_result", None)
                st.session_state.pop("draft_target_id", None)
                st.success(f"Marked as sent on {sent_date.isoformat()} and moved to In communication.")
                st.switch_page("pages/1_Outreach_History.py")
