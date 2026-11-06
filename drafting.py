"""Email-drafting helper built on the Claude API.

The model is instructed to use only facts it's actually given — club
background plus whatever the member types in — and to mark anything it
doesn't know with a placeholder rather than invent it.
"""

import os
from pathlib import Path

import anthropic

CLUB_INFO_PATH = Path(__file__).parent / "club_info.md"
MODEL = "claude-sonnet-5-5"

SYSTEM_PROMPT = """You draft outreach emails for MFBC (Madison Fashion Business Collective), \
a UW-Madison student organization, to send to brands, companies, or individuals for \
sponsorship, speaking, or partnership opportunities.

Rules you must follow exactly:
- Use ONLY the facts given to you below (club background + brand information). Never invent or \
guess facts about the brand/person, their company, numbers, dates, past interactions, or anything \
else not explicitly provided.
- If a fact would make the email better but you were not given it (e.g. a specific event date, \
the recipient's first name, a specific reason this brand fits), insert a clearly marked \
placeholder like [EVENT DATE] or [RECIPIENT FIRST NAME] instead of guessing.
- Keep the tone professional but warm and genuine — this is a student club reaching out, not a \
corporate sales email.
- Keep it concise (under ~200 words for the email body).
- Do not include a subject line unless asked.
- After the email, on a new line, write exactly "---RELIED ON---" followed by a short bullet \
list of the specific facts you used from what was given to you (so the member can verify \
everything in the draft is grounded in real information before sending).
"""


def read_club_info() -> str:
    if CLUB_INFO_PATH.exists():
        return CLUB_INFO_PATH.read_text()
    return ""


def api_key_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def generate_draft(brand_info: dict, extra_public_info: str) -> dict:
    club_info = read_club_info()

    brand_lines = []
    for label, key in [
        ("Company", "company"),
        ("Contact name", "contact_name"),
        ("Contact role", "contact_role"),
        ("Type of ask", "ask_type"),
        ("This is a follow-up", "is_follow_up"),
        ("UW/MFBC connection", "has_uw_mfbc_connection"),
        ("Prior relationship", "has_prior_relationship"),
        ("Notes from the club", "notes"),
    ]:
        val = brand_info.get(key)
        if val not in (None, "", False):
            brand_lines.append(f"- {label}: {val}")
    brand_block = "\n".join(brand_lines) if brand_lines else "(no brand details provided)"

    extra_block = extra_public_info.strip() or "(none provided)"

    user_message = f"""MFBC CLUB BACKGROUND:
{club_info}

BRAND/CONTACT INFORMATION PROVIDED BY THE MEMBER:
{brand_block}

ADDITIONAL PUBLIC INFORMATION PASTED BY THE MEMBER:
{extra_block}

Draft the outreach email now."""

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")

    if "---RELIED ON---" in text:
        draft, relied_on = text.split("---RELIED ON---", 1)
    else:
        draft, relied_on = text, "(model did not return a relied-on list)"

    return {"draft": draft.strip(), "relied_on": relied_on.strip()}
