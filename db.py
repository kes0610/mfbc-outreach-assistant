"""SQLite data layer for the MFBC Outreach Assistant.

Every write (add / edit / delete / import) commits immediately — there is no
manual save step. Backups and import-undo exist as a safety net around that.
"""

from __future__ import annotations

import shutil
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
DB_PATH = DATA_DIR / "outreach.db"

ASK_TYPES = ["sponsorship", "speaker", "partnership", "other"]
ASK_TYPE_LABELS = {
    "sponsorship": "Sponsorship",
    "speaker": "Speaker",
    "partnership": "Partnership",
    "other": "Other",
}

OUTCOMES = ["no_reply", "replied", "declined", "meeting_booked"]
OUTCOME_LABELS = {
    "no_reply": "No reply",
    "replied": "Replied",
    "declined": "Declined",
    "meeting_booked": "Meeting booked",
}
REPLIED_OUTCOMES = {"replied", "declined", "meeting_booked"}

STAGES = ["new", "in_communication", "archived", "attending"]
STAGE_LABELS = {
    "new": "New brand",
    "in_communication": "In communication",
    "archived": "Archived",
    "attending": "Attending",
}

COLUMNS = [
    "id",
    "company",
    "contact_name",
    "contact_role",
    "ask_type",
    "date_sent",
    "sender",
    "is_follow_up",
    "has_uw_mfbc_connection",
    "has_prior_relationship",
    "email_text",
    "notes",
    "outcome",
    "reply_date",
    "stage",
    "created_at",
    "updated_at",
]

EDITABLE_COLUMNS = [c for c in COLUMNS if c not in ("id", "created_at", "updated_at")]


def init_db() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS outreach (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                contact_name TEXT,
                contact_role TEXT,
                ask_type TEXT,
                date_sent TEXT,
                sender TEXT,
                is_follow_up INTEGER NOT NULL DEFAULT 0,
                has_uw_mfbc_connection INTEGER NOT NULL DEFAULT 0,
                has_prior_relationship INTEGER NOT NULL DEFAULT 0,
                email_text TEXT,
                notes TEXT,
                outcome TEXT,
                reply_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS import_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                outreach_id INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(outreach)").fetchall()}
        if "stage" not in existing_cols:
            conn.execute("ALTER TABLE outreach ADD COLUMN stage TEXT")
            conn.execute(
                """
                UPDATE outreach SET stage = CASE
                    WHEN outcome = 'declined' THEN 'archived'
                    WHEN outcome IN ('replied', 'meeting_booked') THEN 'in_communication'
                    WHEN outcome = 'no_reply' THEN 'in_communication'
                    WHEN date_sent IS NOT NULL AND date_sent != '' THEN 'in_communication'
                    ELSE 'new'
                END
                WHERE stage IS NULL
                """
            )
    maybe_daily_backup()


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Backups
# ---------------------------------------------------------------------------

def backup_now(reason: str) -> Path | None:
    """Copy the db file to backups/ with a timestamp. No-op if db doesn't exist yet."""
    if not DB_PATH.exists():
        return None
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"outreach_{stamp}_{reason}.db"
    shutil.copy2(DB_PATH, dest)
    return dest


def maybe_daily_backup() -> None:
    """Back up once per calendar day, on first use of the app that day."""
    today = date.today().isoformat()
    marker = BACKUP_DIR / f".last_daily_backup_{today}"
    if marker.exists():
        return
    backup_now("daily")
    for old in BACKUP_DIR.glob(".last_daily_backup_*"):
        old.unlink(missing_ok=True)
    marker.touch()


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------

def fetch_all() -> pd.DataFrame:
    with _connect() as conn:
        df = pd.read_sql_query(f"SELECT {', '.join(COLUMNS)} FROM outreach ORDER BY date_sent DESC, id DESC", conn)
    for col in ("is_follow_up", "has_uw_mfbc_connection", "has_prior_relationship"):
        df[col] = df[col].astype(bool)
    return df


def latest_active_batch_id() -> str | None:
    """Most recent import batch that still has rows present (so undo makes sense)."""
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT il.batch_id
            FROM import_log il
            JOIN outreach o ON o.id = il.outreach_id
            ORDER BY il.id DESC
            LIMIT 1
            """
        ).fetchone()
    return row[0] if row else None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_record(record: dict) -> list[str]:
    issues = []
    if not record.get("date_sent"):
        issues.append("missing date sent")
    if record.get("outcome") not in OUTCOMES:
        issues.append(f"unrecognized outcome: {record.get('outcome')!r}")
    if not record.get("company"):
        issues.append("missing company")
    outcome = record.get("outcome")
    reply_date = record.get("reply_date")
    if outcome in REPLIED_OUTCOMES and not reply_date:
        issues.append("outcome implies a reply but reply date is missing")
    if outcome == "no_reply" and reply_date:
        issues.append("marked no reply but has a reply date")
    return issues


def default_stage(record: dict) -> str:
    """Best starting stage for a record that doesn't specify one."""
    outcome = record.get("outcome")
    if outcome == "declined":
        return "archived"
    if outcome in ("replied", "meeting_booked", "no_reply"):
        return "in_communication"
    if record.get("date_sent"):
        return "in_communication"
    return "new"


def dup_key(record: dict) -> tuple:
    return (
        str(record.get("company") or "").strip().lower(),
        str(record.get("contact_name") or "").strip().lower(),
        str(record.get("date_sent") or "").strip(),
        str(record.get("ask_type") or "").strip().lower(),
    )


def find_duplicate_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Rows in the existing table that share the same dedup key as another row."""
    if df.empty:
        return df.iloc[0:0]
    keys = df.apply(lambda r: dup_key(r.to_dict()), axis=1)
    dup_mask = keys.duplicated(keep=False)
    return df[dup_mask]


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------

def insert_record(record: dict) -> int:
    now = _now()
    record = dict(record)
    if not record.get("stage"):
        record["stage"] = default_stage(record)
    with _connect() as conn:
        cur = conn.execute(
            f"""
            INSERT INTO outreach ({', '.join(EDITABLE_COLUMNS)}, created_at, updated_at)
            VALUES ({', '.join('?' for _ in EDITABLE_COLUMNS)}, ?, ?)
            """,
            [record.get(c) for c in EDITABLE_COLUMNS] + [now, now],
        )
        return cur.lastrowid


def update_record(record_id: int, record: dict) -> None:
    now = _now()
    with _connect() as conn:
        conn.execute(
            f"""
            UPDATE outreach
            SET {', '.join(f'{c} = ?' for c in EDITABLE_COLUMNS)}, updated_at = ?
            WHERE id = ?
            """,
            [record.get(c) for c in EDITABLE_COLUMNS] + [now, record_id],
        )


def delete_records(ids: list[int]) -> None:
    if not ids:
        return
    with _connect() as conn:
        conn.executemany("DELETE FROM outreach WHERE id = ?", [(i,) for i in ids])


def bulk_import(records: list[dict]) -> dict:
    """Insert records, skipping exact duplicates against existing data and within the batch.

    Returns a summary dict: inserted, skipped_duplicate, issues (per-row validation warnings), batch_id.
    """
    backup_now("pre_import")
    existing = fetch_all()
    existing_keys = {dup_key(r) for r in existing.to_dict("records")}
    seen_keys = set()
    batch_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    now = _now()

    inserted = 0
    skipped_duplicate = 0
    row_issues = []

    with _connect() as conn:
        for record in records:
            key = dup_key(record)
            issues = validate_record(record)
            if key in existing_keys or key in seen_keys:
                skipped_duplicate += 1
                row_issues.append({"company": record.get("company"), "issues": issues + ["duplicate — skipped"]})
                continue
            seen_keys.add(key)
            cur = conn.execute(
                f"""
                INSERT INTO outreach ({', '.join(EDITABLE_COLUMNS)}, created_at, updated_at)
                VALUES ({', '.join('?' for _ in EDITABLE_COLUMNS)}, ?, ?)
                """,
                [record.get(c) for c in EDITABLE_COLUMNS] + [now, now],
            )
            conn.execute(
                "INSERT INTO import_log (batch_id, outreach_id, created_at) VALUES (?, ?, ?)",
                (batch_id, cur.lastrowid, now),
            )
            inserted += 1
            if issues:
                row_issues.append({"company": record.get("company"), "issues": issues})

    return {
        "batch_id": batch_id,
        "inserted": inserted,
        "skipped_duplicate": skipped_duplicate,
        "row_issues": row_issues,
    }


def undo_import(batch_id: str) -> int:
    with _connect() as conn:
        ids = [r[0] for r in conn.execute("SELECT outreach_id FROM import_log WHERE batch_id = ?", (batch_id,)).fetchall()]
        if ids:
            conn.executemany("DELETE FROM outreach WHERE id = ?", [(i,) for i in ids])
        conn.execute("DELETE FROM import_log WHERE batch_id = ?", (batch_id,))
    return len(ids)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def compute_summary(df: pd.DataFrame) -> dict:
    total = len(df)
    replied = int((df["outcome"].isin(REPLIED_OUTCOMES)).sum()) if total else 0
    no_reply = int((df["outcome"] == "no_reply").sum()) if total else 0
    reply_rate = (replied / total) if total else None
    date_min = date_max = None
    if total:
        dates = pd.to_datetime(df["date_sent"], errors="coerce").dropna()
        if not dates.empty:
            date_min, date_max = dates.min().date(), dates.max().date()

    warnings = []
    if total == 0:
        warnings.append("No outreach records yet — add or import data to get started.")
    else:
        if no_reply == 0:
            warnings.append(
                "No 'no reply' outcomes are recorded. If non-replies aren't being logged, "
                "any reply-likelihood model built on this data will be biased toward predicting replies."
            )
        if total < 30:
            warnings.append(
                f"Only {total} record(s) so far — too small for a reliable statistical model. "
                "The app will fall back to a High / Medium / Low rating until there's more data."
            )
        missing_dates = int(df["date_sent"].isna().sum() or (df["date_sent"] == "").sum())
        if missing_dates:
            warnings.append(f"{missing_dates} record(s) are missing a date sent.")
        bad_outcomes = int((~df["outcome"].isin(OUTCOMES)).sum())
        if bad_outcomes:
            warnings.append(f"{bad_outcomes} record(s) have an outcome value the model can't use.")
        dup_count = len(find_duplicate_groups(df))
        if dup_count:
            warnings.append(f"{dup_count} record(s) look like duplicates of each other.")

    return {
        "total": total,
        "replied": replied,
        "no_reply": no_reply,
        "reply_rate": reply_rate,
        "date_min": date_min,
        "date_max": date_max,
        "warnings": warnings,
    }


def export_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


MODEL_MIN_N = 30


def estimate_reply_chance(record: dict, df: pd.DataFrame) -> dict:
    """Rough, transparent reply-chance estimate.

    With this little labeled history, a trained model would just memorize
    noise, so this is a simple, documented rule of thumb against the club's
    own historical reply rate — not a calibrated probability. Once there are
    MODEL_MIN_N+ labeled outcomes, this should be replaced by an actual
    trained/evaluated model (logistic regression per the project plan).
    """
    labeled = df[df["outcome"].isin(OUTCOMES)] if len(df) else df
    base_n = len(labeled)
    base_replied = int(labeled["outcome"].isin(REPLIED_OUTCOMES).sum()) if base_n else 0
    base_rate = (base_replied / base_n) if base_n else None

    score = 0
    reasons = []
    if record.get("has_uw_mfbc_connection"):
        score += 1
        reasons.append("higher: UW/MFBC connection")
    if record.get("has_prior_relationship"):
        score += 1
        reasons.append("higher: prior relationship with this company/contact")
    if record.get("is_follow_up"):
        score += 1
        reasons.append("higher: this is a follow-up, not cold outreach")
    if not reasons:
        reasons.append("lower: no known UW/MFBC connection or prior relationship on file")

    label = "Low"
    if score >= 2:
        label = "High"
    elif score == 1:
        label = "Medium"

    return {
        "label": label,
        "reasons": reasons,
        "base_n": base_n,
        "base_replied": base_replied,
        "base_rate": base_rate,
        "enough_for_model": base_n >= MODEL_MIN_N,
    }
