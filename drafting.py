"""Email-drafting helper built on the Claude API.

The model is instructed to use only facts it's actually given — club
background plus whatever the member types in — and to mark anything it
doesn't know with a placeholder rather than invent it.
"""

import os
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

CLUB_INFO_PATH = Path(__file__).parent / "club_info.md"
MODEL = "claude-sonnet-5-5"
RESEARCH_TIMEOUT_SECONDS = 15

SYSTEM_PROMPT_RESEARCH = """You help MFBC (Madison Fashion Business Collective), a UW-Madison \
student organization, prepare outreach to brands, companies, or individuals for sponsorship, \
speaking, or partnership opportunities at their events.

You have a web search tool. Use it to look up real, current public information about the \
company or person MFBC wants to reach out to — their brand, size, audience, recent news, and \
social presence — specifically to judge whether a student fashion-business event at UW-Madison \
would plausibly appeal to them.

You are given:
1. MFBC's own background (club history, past events, audience).
2. MFBC's actual outreach history — brands reached out to before, the type of ask, and the \
outcome where known (replied, no reply, declined, attending, etc.).
3. Details on the NEW brand/contact MFBC wants to reach out to now.

Using real information only — your web search results and what MFBC gave you below, never \
invented facts — produce exactly three sections in this format:

---CHANCE---
<One word: Low, Medium, or High> — <2-4 sentences of reasoning, grounded in (a) how similar this \
company is, in industry/scale/audience, to companies in MFBC's history that did or didn't reply, \
and (b) what your research found about why this company might or might not want to engage with a \
student organization like MFBC. Do not state a numeric percent — there isn't enough historical \
data (only a handful of logged outcomes) to justify one; a plain Low/Medium/High judgment call is \
more honest than a fake-precise number.>

---DRAFT---
<The outreach email body. Explain briefly and specifically why THIS company might want to \
participate in MFBC, using real facts from your research and from MFBC's own background — not \
generic flattery. Professional but warm tone, a student club reaching out, not a sales email. \
Under ~200 words. No subject line unless asked. Use a clearly marked placeholder like \
[SPECIFIC DETAIL] for anything that would improve the email but wasn't available from research or \
the facts given.>

---RELIED ON---
<Bullet list of the specific facts you used — both what you found via web search (with a brief \
source, e.g. "company website," "a 2025 press article") and what was given to you directly — so \
a club member can verify everything in the draft and chance assessment before sending.>

Rules:
- Never invent facts about the company, numbers, dates, or past interactions. If your search \
doesn't turn up something relevant, say so rather than guessing.
- Keep the tone professional but warm and genuine.
- You're working under a tight time budget. Do one or two well-chosen searches, not an \
exhaustive research chain, and move on to writing the three sections as soon as you have \
enough to work with. Getting to a complete, well-formatted answer matters more than finding \
every possible fact.
"""


def read_club_info() -> str:
    if CLUB_INFO_PATH.exists():
        return CLUB_INFO_PATH.read_text()
    return ""


def api_key_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _brand_block(brand_info: dict) -> str:
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
    return "\n".join(brand_lines) if brand_lines else "(no brand details provided)"


def _history_summary(history_df) -> str:
    if history_df is None or history_df.empty:
        return "(no outreach history logged yet)"
    lines = []
    for row in history_df.itertuples():
        bits = [str(row.company)]
        if getattr(row, "ask_type", None):
            bits.append(f"ask: {row.ask_type}")
        if getattr(row, "outcome", None):
            bits.append(f"outcome: {row.outcome}")
        if getattr(row, "stage", None):
            bits.append(f"stage: {row.stage}")
        lines.append("- " + ", ".join(bits))
    return "\n".join(lines) if lines else "(no outreach history logged yet)"


def research_and_draft(brand_info: dict, history_df, extra_public_info: str = "") -> dict:
    """AI mode: Claude researches the company via web search, then returns a chance assessment and a draft grounded in that research plus MFBC's own history.

    Capped at RESEARCH_TIMEOUT_SECONDS of wall-clock time — whatever text has
    streamed back by then is what gets parsed, rather than waiting out a long
    multi-search research chain.
    """
    club_info = read_club_info()
    brand_block = _brand_block(brand_info)
    history_block = _history_summary(history_df)
    extra_block = extra_public_info.strip() or "(none provided)"

    user_message = f"""MFBC CLUB BACKGROUND:
{club_info}

MFBC'S OUTREACH HISTORY (company, ask type, outcome where known):
{history_block}

NEW BRAND/CONTACT MFBC WANTS TO REACH OUT TO:
{brand_block}

ADDITIONAL INFO THE MEMBER ALREADY KNOWS (optional, may be empty):
{extra_block}

Research this company with web search, then produce the three sections exactly as instructed."""

    client = anthropic.Anthropic()
    deadline = time.monotonic() + RESEARCH_TIMEOUT_SECONDS
    text = ""
    timed_out = False
    with client.messages.stream(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT_RESEARCH,
        tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 4}],
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for event in stream:
            if event.type == "content_block_delta" and event.delta.type == "text_delta":
                text += event.delta.text
            if time.monotonic() >= deadline:
                timed_out = True
                break

    chance_label = None
    chance_reasoning = ""
    draft = None
    relied_on = "(model did not return a relied-on list)"

    if "---CHANCE---" in text and "---DRAFT---" in text:
        chance_part, rest = text.split("---DRAFT---", 1)
        chance_reasoning = chance_part.split("---CHANCE---", 1)[1].strip()
        for candidate in ("High", "Medium", "Low"):
            if chance_reasoning.lower().startswith(candidate.lower()):
                chance_label = candidate
                break
        if chance_label is None:
            for candidate in ("High", "Medium", "Low"):
                if candidate.lower() in chance_reasoning.lower():
                    chance_label = candidate
                    break
        if "---RELIED ON---" in rest:
            draft, relied_on = rest.split("---RELIED ON---", 1)
        else:
            draft = rest
            if timed_out:
                relied_on = "(research hit the 15-second limit before it listed sources)"
    elif "---RELIED ON---" in text:
        draft, relied_on = text.split("---RELIED ON---", 1)
    elif not timed_out:
        draft = text

    if draft is None:
        draft = (
            "Research hit the 15-second limit before it got to writing the draft. Try again "
            "(it may get further with a cached search), or use the free template for an "
            "instant draft instead."
        )
        relied_on = chance_reasoning or "(research cut short by the 15-second limit)"

    return {
        "chance_label": chance_label,
        "chance_reasoning": chance_reasoning,
        "draft": draft.strip(),
        "relied_on": relied_on.strip(),
        "timed_out": timed_out,
    }
