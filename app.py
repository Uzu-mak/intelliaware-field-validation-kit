import json
import math
import hashlib
import hmac
import html
import time
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

try:
    from streamlit_cookies_controller import CookieController
except ImportError:
    CookieController = None

st.set_page_config(page_title="IntelliAware ValidationOps", page_icon="🏭", layout="wide")

# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
      .block-container {padding-top: 3.75rem !important; padding-bottom: 2.5rem; max-width: 1480px;}
      [data-testid="stSidebar"] {
        background:linear-gradient(180deg,#081A30 0%,#102A46 100%);
        min-width:270px !important;
        max-width:270px !important;
      }
      [data-testid="stSidebar"] > div:first-child {width:270px !important;}
      [data-testid="stSidebar"] h1,
      [data-testid="stSidebar"] h2,
      [data-testid="stSidebar"] h3,
      [data-testid="stSidebar"] h4,
      [data-testid="stSidebar"] label,
      [data-testid="stSidebar"] p,
      [data-testid="stSidebar"] small {color:#F5F8FC !important;}
      [data-testid="stSidebar"] input {color:#172033 !important;}
      [data-testid="stSidebar"] .stButton {margin:0 !important;}
      [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
      [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
        width:100% !important;
        min-height:38px !important;
        height:38px !important;
        text-align:left !important;
        justify-content:flex-start !important;
        border-radius:9px !important;
        padding:.35rem .70rem !important;
        margin:.08rem 0 !important;
        font-weight:650 !important;
        box-shadow:none !important;
      }
      [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] {
        background:rgba(255,255,255,.045) !important;
        color:#E7F0F8 !important;
        border:1px solid rgba(255,255,255,.08) !important;
      }
      [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
        background:linear-gradient(90deg,#00A6D6,#16B6D4) !important;
        color:#FFFFFF !important;
        border:1px solid transparent !important;
      }
      [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] p,
      [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] span,
      [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] p,
      [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] span {
        color:inherit !important;
        font-size:.91rem !important;
        line-height:1.05 !important;
        white-space:nowrap !important;
      }
      [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover {
        background:rgba(255,255,255,.12) !important;
        color:#FFFFFF !important;
        border-color:rgba(255,255,255,.18) !important;
        transform:translateX(2px);
      }
      [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover {
        filter:brightness(1.06);
      }
      [data-testid="stSidebar"] hr {margin:.7rem 0 !important; border-color:rgba(255,255,255,.14) !important;}
      .appbar {display:flex;align-items:center;justify-content:space-between;background:white;border:1px solid #E5EAF1;border-radius:14px;padding:1.15rem 1.25rem;margin:.25rem 0 1rem;min-height:82px;box-shadow:0 2px 8px rgba(16,42,70,.04)}
      .appbar-title{font-size:1.35rem;line-height:1.25;font-weight:780;color:#13243A}.appbar-meta{color:#667085;font-size:.86rem}
      .kpi {background:white;border:1px solid #E5EAF1;border-radius:14px;padding:1rem;box-shadow:0 2px 10px rgba(16,42,70,.04)}
      .kpi-value{font-size:1.65rem;font-weight:760;color:#102A46}.kpi-label{color:#667085;font-size:.84rem}
      .entity-card {border:1px solid #E4EAF1;border-radius:14px;padding:1rem;background:#fff;margin:.55rem 0;box-shadow:0 2px 8px rgba(16,42,70,.04)}
      .entity-title{font-size:1rem;font-weight:720;color:#102A46}.entity-meta{font-size:.84rem;color:#667085;margin-top:.2rem}
      .progress-shell{height:8px;background:#ECF0F4;border-radius:99px;overflow:hidden;margin-top:.55rem}.progress-fill{height:100%;background:linear-gradient(90deg,#15B8A6,#00A6D6)}
      .board-col{background:#F2F5F8;border:1px solid #E4EAF1;border-radius:14px;padding:.65rem;min-height:220px}
      .board-head{font-weight:720;color:#344054;margin-bottom:.5rem}
      .empty-state{text-align:center;padding:2.2rem;border:1px dashed #CAD3DF;border-radius:14px;background:#FBFCFD;color:#667085}
      button[kind="primary"] {border-radius:10px !important;font-weight:700 !important;}
      .hero {background:linear-gradient(105deg,#0B1F3A,#123C69);color:white;padding:1.3rem 1.5rem;border-radius:16px;margin-bottom:1rem;}
      .hero h1 {margin:0;font-size:2rem}.hero p{margin:.35rem 0 0;color:#D8E7F3}
      .card {border:1px solid #E3E8EF;border-radius:14px;padding:1rem;background:#fff;box-shadow:0 1px 5px rgba(0,0,0,.05);margin-bottom:.75rem;}
      .muted {color:#667085;font-size:.9rem}.pill{display:inline-block;padding:.18rem .55rem;border-radius:999px;background:#EFF4F8;font-size:.78rem;margin-right:.3rem}
      .danger {color:#B42318;font-weight:700}.warn{color:#B54708;font-weight:700}.ok{color:#067647;font-weight:700}
      div[data-testid="stMetric"] {border:1px solid #E3E8EF;padding:.8rem;border-radius:12px;background:white;}
      .section-title {font-weight:700;font-size:1.15rem;margin:.4rem 0 .8rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Database
# -----------------------------
@st.cache_resource
def get_engine():
    database_url = st.secrets["DATABASE_URL"]
    if database_url.startswith("postgresql+psycopg2://"):
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    return create_engine(database_url, pool_pre_ping=True, pool_recycle=300, future=True)


def clean(v: Any):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    if isinstance(v, (datetime, date, pd.Timestamp)):
        return v.isoformat()
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def query_df(sql: str, params: dict | None = None) -> pd.DataFrame:
    try:
        return pd.read_sql(text(sql), get_engine(), params=params or {})
    except Exception as exc:
        st.error(f"Database read failed: {exc}")
        return pd.DataFrame()


def execute(sql: str, params: dict | None = None):
    with get_engine().begin() as conn:
        return conn.execute(text(sql), params or {})


def fetch_one(sql: str, params: dict | None = None):
    with get_engine().begin() as conn:
        row = conn.execute(text(sql), params or {}).mappings().first()
        return dict(row) if row else None


def log_activity(conn, entity_type: str, entity_id: int | None, action: str, description: str, actor: str, changes: dict | None = None):
    current_user = st.session_state.get("current_user") or {}
    actor_user_id = current_user.get("id")
    conn.execute(
        text("""
        INSERT INTO activity_log(entity_type, entity_id, action, description, performed_by, performed_by_user_id)
        VALUES (:entity_type, :entity_id, :action, :description, :actor, :actor_user_id)
        """),
        {"entity_type": entity_type, "entity_id": entity_id, "action": action, "description": description, "actor": actor, "actor_user_id": actor_user_id},
    )
    if entity_id is not None:
        conn.execute(
            text("""
            INSERT INTO record_revisions(entity_type, entity_id, action, changed_fields, changed_by, change_reason, changed_by_user_id)
            VALUES (:entity_type, :entity_id, :action, CAST(:changes AS JSONB), :actor, :description, :actor_user_id)
            """),
            {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "changes": json.dumps(changes or {}),
                "actor": actor,
                "description": description,
                "actor_user_id": actor_user_id,
            },
        )


def insert_record(table: str, values: dict, actor: str, description: str) -> int:
    values = {k: clean(v) for k, v in values.items()}
    cols = list(values)
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(':'+c for c in cols)}) RETURNING id"
    with get_engine().begin() as conn:
        new_id = int(conn.execute(text(sql), values).scalar_one())
        log_activity(conn, table, new_id, "create", description, actor, {k: {"old": None, "new": v} for k, v in values.items()})
        return new_id


def update_record(table: str, record_id: int, values: dict, actor: str, description: str):
    values = {k: clean(v) for k, v in values.items()}
    current = fetch_one(f"SELECT * FROM {table} WHERE id=:id", {"id": record_id})
    if not current:
        raise ValueError("Record no longer exists. Refresh the page.")
    changes = {k: {"old": clean(current.get(k)), "new": v} for k, v in values.items() if clean(current.get(k)) != v}
    if not changes:
        return False
    assignments = [f"{k}=:{k}" for k in values]
    params = dict(values, id=record_id)
    with get_engine().begin() as conn:
        conn.execute(text(f"UPDATE {table} SET {', '.join(assignments)} WHERE id=:id"), params)
        log_activity(conn, table, record_id, "update", description, actor, changes)
    return True


def init_schema():
    # Additive only. No DROP, DELETE or table replacement.
    sql = """
    CREATE TABLE IF NOT EXISTS record_revisions (
        id BIGSERIAL PRIMARY KEY, entity_type TEXT NOT NULL, entity_id INTEGER NOT NULL,
        action TEXT NOT NULL, changed_fields JSONB, changed_by TEXT, change_reason TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_revisions_entity ON record_revisions(entity_type, entity_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS activity_log (
        id BIGSERIAL PRIMARY KEY, entity_type TEXT NOT NULL, entity_id INTEGER,
        action TEXT NOT NULL, description TEXT, performed_by TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_log(created_at DESC);

    CREATE TABLE IF NOT EXISTS users (
        id BIGSERIAL PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        display_name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'User',
        access_level TEXT NOT NULL DEFAULT 'Read',
        active BOOLEAN NOT NULL DEFAULT TRUE,
        last_login_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(LOWER(email));

    CREATE TABLE IF NOT EXISTS app_sessions (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token_hash TEXT NOT NULL UNIQUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        last_seen_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        idle_expires_at TIMESTAMPTZ NOT NULL,
        absolute_expires_at TIMESTAMPTZ NOT NULL,
        revoked_at TIMESTAMPTZ,
        user_agent TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_sessions_token ON app_sessions(token_hash);
    CREATE INDEX IF NOT EXISTS idx_sessions_user ON app_sessions(user_id, revoked_at);

    CREATE TABLE IF NOT EXISTS teams (
        id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL UNIQUE, lead_name TEXT,
        purpose TEXT, status TEXT DEFAULT 'Active', created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS team_members (
        id BIGSERIAL PRIMARY KEY, team_id BIGINT REFERENCES teams(id), name TEXT NOT NULL,
        email TEXT, role TEXT, active BOOLEAN DEFAULT TRUE, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS projects (
        id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL, code TEXT UNIQUE, description TEXT,
        owner TEXT, priority TEXT DEFAULT 'Medium', phase TEXT DEFAULT 'Discovery', status TEXT DEFAULT 'Active',
        start_date DATE, target_date DATE, environment TEXT, objectives TEXT, success_criteria TEXT,
        readiness_level TEXT DEFAULT 'Not assessed', created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, archived BOOLEAN DEFAULT FALSE
    );
    CREATE TABLE IF NOT EXISTS project_memberships (
        id BIGSERIAL PRIMARY KEY,
        project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        project_role TEXT NOT NULL DEFAULT 'Contributor',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(project_id, user_id)
    );

    CREATE TABLE IF NOT EXISTS project_teams (
        id BIGSERIAL PRIMARY KEY, project_id BIGINT REFERENCES projects(id), team_id BIGINT REFERENCES teams(id),
        responsibility TEXT, UNIQUE(project_id, team_id)
    );
    CREATE TABLE IF NOT EXISTS workstreams (
        id BIGSERIAL PRIMARY KEY, project_id BIGINT REFERENCES projects(id), name TEXT NOT NULL,
        description TEXT, owner TEXT, team_id BIGINT REFERENCES teams(id), priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Backlog', start_date DATE, due_date DATE, progress INTEGER DEFAULT 0,
        dependency_notes TEXT, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS tasks (
        id BIGSERIAL PRIMARY KEY, project_id BIGINT REFERENCES projects(id), workstream_id BIGINT REFERENCES workstreams(id),
        title TEXT NOT NULL, description TEXT, assignee TEXT, team_id BIGINT REFERENCES teams(id),
        priority TEXT DEFAULT 'Medium', status TEXT DEFAULT 'Backlog', due_date DATE, completion_criteria TEXT,
        related_entity_type TEXT, related_entity_id INTEGER, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, completed_at TIMESTAMPTZ
    );
    CREATE TABLE IF NOT EXISTS comments (
        id BIGSERIAL PRIMARY KEY, entity_type TEXT NOT NULL, entity_id INTEGER NOT NULL,
        body TEXT NOT NULL, author TEXT, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS baseline_metrics (
        id BIGSERIAL PRIMARY KEY, project_id BIGINT REFERENCES projects(id), trial_id INTEGER,
        metric_name TEXT NOT NULL, baseline_value NUMERIC, improved_value NUMERIC, unit TEXT,
        measurement_method TEXT, recorded_by TEXT, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS readiness_criteria (
        id BIGSERIAL PRIMARY KEY, project_id BIGINT REFERENCES projects(id), category TEXT, criterion_name TEXT NOT NULL,
        operator TEXT DEFAULT '>=', target_value NUMERIC, actual_value NUMERIC, unit TEXT,
        mandatory BOOLEAN DEFAULT FALSE, status TEXT DEFAULT 'Not evaluated', notes TEXT,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS milestones (
        id BIGSERIAL PRIMARY KEY, project_id BIGINT REFERENCES projects(id), title TEXT NOT NULL,
        owner TEXT, due_date DATE, status TEXT DEFAULT 'Planned', description TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS evidence_items (
        id BIGSERIAL PRIMARY KEY, project_id BIGINT REFERENCES projects(id), trial_id INTEGER,
        evidence_type TEXT NOT NULL, title TEXT NOT NULL, uri TEXT, source TEXT, captured_at TIMESTAMPTZ,
        model_version TEXT, verification_status TEXT DEFAULT 'Submitted', verified_by TEXT,
        description TEXT, uploaded_by TEXT, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS risks (
        id BIGSERIAL PRIMARY KEY, project_id BIGINT REFERENCES projects(id), title TEXT NOT NULL,
        category TEXT, probability TEXT, impact TEXT, owner TEXT, mitigation TEXT,
        status TEXT DEFAULT 'Open', due_date DATE, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS notifications (
        id BIGSERIAL PRIMARY KEY, recipient TEXT, title TEXT NOT NULL, body TEXT,
        entity_type TEXT, entity_id INTEGER, is_read BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS team_memberships (
        id BIGSERIAL PRIMARY KEY,
        team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
        user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        team_role TEXT NOT NULL DEFAULT 'Member',
        active BOOLEAN NOT NULL DEFAULT TRUE,
        added_by_user_id BIGINT REFERENCES users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(team_id, user_id)
    );
    CREATE INDEX IF NOT EXISTS idx_team_memberships_team ON team_memberships(team_id, active);
    CREATE INDEX IF NOT EXISTS idx_team_memberships_user ON team_memberships(user_id, active);

    CREATE TABLE IF NOT EXISTS direct_messages (
        id BIGSERIAL PRIMARY KEY,
        sender_user_id BIGINT NOT NULL REFERENCES users(id),
        recipient_user_id BIGINT NOT NULL REFERENCES users(id),
        subject TEXT,
        body TEXT NOT NULL,
        parent_message_id BIGINT REFERENCES direct_messages(id),
        related_entity_type TEXT,
        related_entity_id INTEGER,
        is_read BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_messages_recipient ON direct_messages(recipient_user_id, is_read, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_messages_sender ON direct_messages(sender_user_id, created_at DESC);
    """
    execute(sql)

    # Safely extend legacy tables. Existing rows remain untouched.
    alter_sql = """
    ALTER TABLE trials ADD COLUMN IF NOT EXISTS project_id BIGINT REFERENCES projects(id);
    ALTER TABLE trials ADD COLUMN IF NOT EXISTS workstream_id BIGINT REFERENCES workstreams(id);
    ALTER TABLE trials ADD COLUMN IF NOT EXISTS model_version TEXT;
    ALTER TABLE trials ADD COLUMN IF NOT EXISTS validation_level TEXT;
    ALTER TABLE issue_logs ADD COLUMN IF NOT EXISTS project_id BIGINT REFERENCES projects(id);
    ALTER TABLE issue_logs ADD COLUMN IF NOT EXISTS workstream_id BIGINT REFERENCES workstreams(id);
    ALTER TABLE issue_logs ADD COLUMN IF NOT EXISTS trial_id INTEGER;
    ALTER TABLE issue_logs ADD COLUMN IF NOT EXISTS priority TEXT;
    ALTER TABLE issue_logs ADD COLUMN IF NOT EXISTS root_cause TEXT;
    ALTER TABLE issue_logs ADD COLUMN IF NOT EXISTS target_fix_version TEXT;
    ALTER TABLE issue_logs ADD COLUMN IF NOT EXISTS retest_trial_id INTEGER;
    ALTER TABLE outreach_contacts ADD COLUMN IF NOT EXISTS project_id BIGINT REFERENCES projects(id);
    ALTER TABLE ground_truth_logs ADD COLUMN IF NOT EXISTS project_id BIGINT REFERENCES projects(id);
    ALTER TABLE ground_truth_logs ADD COLUMN IF NOT EXISTS trial_id INTEGER;
    ALTER TABLE projects ADD COLUMN IF NOT EXISTS owner_user_id BIGINT REFERENCES users(id);
    ALTER TABLE workstreams ADD COLUMN IF NOT EXISTS owner_user_id BIGINT REFERENCES users(id);
    ALTER TABLE tasks ADD COLUMN IF NOT EXISTS assignee_user_id BIGINT REFERENCES users(id);
    ALTER TABLE trials ADD COLUMN IF NOT EXISTS trial_owner_user_id BIGINT REFERENCES users(id);
    ALTER TABLE issue_logs ADD COLUMN IF NOT EXISTS owner_user_id BIGINT REFERENCES users(id);
    ALTER TABLE evidence_items ADD COLUMN IF NOT EXISTS uploaded_by_user_id BIGINT REFERENCES users(id);
    ALTER TABLE evidence_items ADD COLUMN IF NOT EXISTS verified_by_user_id BIGINT REFERENCES users(id);
    ALTER TABLE milestones ADD COLUMN IF NOT EXISTS owner_user_id BIGINT REFERENCES users(id);
    ALTER TABLE risks ADD COLUMN IF NOT EXISTS owner_user_id BIGINT REFERENCES users(id);
    ALTER TABLE outreach_contacts ADD COLUMN IF NOT EXISTS contact_owner_user_id BIGINT REFERENCES users(id);
    ALTER TABLE comments ADD COLUMN IF NOT EXISTS author_user_id BIGINT REFERENCES users(id);
    ALTER TABLE activity_log ADD COLUMN IF NOT EXISTS performed_by_user_id BIGINT REFERENCES users(id);
    ALTER TABLE record_revisions ADD COLUMN IF NOT EXISTS changed_by_user_id BIGINT REFERENCES users(id);
    ALTER TABLE users ADD COLUMN IF NOT EXISTS access_level TEXT NOT NULL DEFAULT 'Read';
    ALTER TABLE teams ADD COLUMN IF NOT EXISTS lead_user_id BIGINT REFERENCES users(id);
    ALTER TABLE trials ADD COLUMN IF NOT EXISTS team_id BIGINT REFERENCES teams(id);
    ALTER TABLE tasks ADD COLUMN IF NOT EXISTS team_id BIGINT REFERENCES teams(id);
    ALTER TABLE outreach_contacts ADD COLUMN IF NOT EXISTS latest_touchpoint_date DATE;
    ALTER TABLE notifications ADD COLUMN IF NOT EXISTS recipient_user_id BIGINT REFERENCES users(id) ON DELETE CASCADE;
    ALTER TABLE notifications ADD COLUMN IF NOT EXISTS sender_user_id BIGINT REFERENCES users(id);
    ALTER TABLE notifications ADD COLUMN IF NOT EXISTS link_page TEXT;
    """
    execute(alter_sql)


def table_exists(name: str) -> bool:
    row = fetch_one("SELECT to_regclass(:name) AS t", {"name": f"public.{name}"})
    return bool(row and row["t"])


# -----------------------------
# Utilities
# -----------------------------
def normalize_evidence_url(value: str | None) -> str | None:
    """Return a usable public HTTP(S) evidence URL, or None."""
    if value is None:
        return None

    url = str(value).strip()
    if not url:
        return None

    lowered = url.lower().strip()
    placeholder_values = {
        "n/a", "na", "none", "null", "nil", "not applicable",
        "not available", "unknown", "tbd", "-", "--"
    }
    if lowered in placeholder_values:
        return None

    # Local paths and local-only hosts cannot be opened by Streamlit Cloud users.
    if lowered.startswith(("file://", "localhost", "127.0.0.1", "0.0.0.0")) or \
       (len(url) >= 3 and url[1:3] in {":\\", ":/"}):
        return None

    if not lowered.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").strip().lower()

    if parsed.scheme not in {"http", "https"} or not hostname:
        return None

    # Reject single-word hosts such as https://n/a or https://test.
    # Public evidence links should use a real domain or a valid IP address.
    is_ipv4 = False
    try:
        parts = hostname.split(".")
        is_ipv4 = len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        is_ipv4 = False

    if "." not in hostname and not is_ipv4:
        return None

    if hostname.endswith((".local", ".localhost")):
        return None

    return url


def safe_text(value: Any, fallback: str = "—") -> str:
    text_value = str(value or "").strip()
    return html.escape(text_value) if text_value else fallback


def create_notification(recipient_user_id: int | None, title: str, body: str, entity_type: str | None = None, entity_id: int | None = None, sender_user_id: int | None = None, link_page: str | None = None):
    if not recipient_user_id:
        return
    execute("""
        INSERT INTO notifications(recipient_user_id, recipient, title, body, entity_type, entity_id, sender_user_id, link_page)
        SELECT :recipient_user_id, display_name, :title, :body, :entity_type, :entity_id, :sender_user_id, :link_page
        FROM users WHERE id=:recipient_user_id
    """, {
        "recipient_user_id": recipient_user_id, "title": title, "body": body,
        "entity_type": entity_type, "entity_id": entity_id,
        "sender_user_id": sender_user_id, "link_page": link_page,
    })


def notify_active_administrators(title: str, body: str, entity_type: str | None = None, entity_id: int | None = None, sender_user_id: int | None = None):
    admins = query_df("SELECT id FROM users WHERE role='Administrator' AND active=TRUE")
    for _, row in admins.iterrows():
        create_notification(int(row["id"]), title, body, entity_type, entity_id, sender_user_id, "Administration")


def team_member_options(team_id: int | None, active_only: bool = True):
    if not team_id:
        return {}
    active_clause = "AND tm.active=TRUE AND u.active=TRUE" if active_only else ""
    df = query_df(f"""
        SELECT u.id, u.display_name, u.email, tm.team_role, u.access_level
        FROM team_memberships tm
        JOIN users u ON u.id=tm.user_id
        WHERE tm.team_id=:team_id {active_clause}
        ORDER BY CASE WHEN tm.team_role='Team Lead' THEN 0 ELSE 1 END, u.display_name
    """, {"team_id": team_id})
    return {f"{r['display_name']} · {r['team_role']} · {r['email']} ({r['access_level']})": int(r['id']) for _, r in df.iterrows()}


def user_leads_team(user_id: int, team_id: int | None = None) -> bool:
    if not user_id:
        return False
    sql = "SELECT 1 FROM team_memberships WHERE user_id=:uid AND team_role='Team Lead' AND active=TRUE"
    params = {"uid": user_id}
    if team_id:
        sql += " AND team_id=:tid"
        params["tid"] = team_id
    return bool(fetch_one(sql + " LIMIT 1", params))


def can_manage_team(team_id: int | None) -> bool:
    current = st.session_state.get("current_user") or {}
    return current.get("role") == "Administrator" or (team_id is not None and user_leads_team(int(current.get("id") or 0), team_id))


def notify_team_leads(team_id: int | None, title: str, body: str, entity_type: str | None = None, entity_id: int | None = None, sender_user_id: int | None = None):
    if not team_id:
        return
    leads = query_df("""
        SELECT DISTINCT u.id FROM team_memberships tm JOIN users u ON u.id=tm.user_id
        WHERE tm.team_id=:tid AND tm.team_role='Team Lead' AND tm.active=TRUE AND u.active=TRUE
    """, {"tid": team_id})
    for _, row in leads.iterrows():
        if sender_user_id and int(row["id"]) == int(sender_user_id):
            continue
        create_notification(int(row["id"]), title, body, entity_type, entity_id, sender_user_id, "My Work")


def parse_optional_date(value):
    if value is None or value == "":
        return None
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def status_class(value: str) -> str:
    v = str(value or "").lower()
    if any(x in v for x in ["critical", "blocked", "overdue", "not ready"]): return "danger"
    if any(x in v for x in ["high", "risk", "conditional", "pending"]): return "warn"
    if any(x in v for x in ["complete", "ready", "closed", "verified", "active"]): return "ok"
    return ""


def render_card(title: str, subtitle: str = "", badges: list[str] | None = None, body: str = ""):
    pills = "".join(f'<span class="pill">{b}</span>' for b in (badges or []))
    st.markdown(f'<div class="card"><strong>{title}</strong><div class="muted">{subtitle}</div><div style="margin:.45rem 0">{pills}</div><div>{body}</div></div>', unsafe_allow_html=True)


def record_timeline(entity_type: str, entity_id: int):
    history = query_df("""
        SELECT created_at, action, description, performed_by
        FROM activity_log WHERE entity_type=:e AND entity_id=:i ORDER BY created_at DESC
    """, {"e": entity_type, "i": entity_id})
    if history.empty:
        st.caption("No recorded history yet.")
        return
    for _, row in history.iterrows():
        st.markdown(f"**{row['action'].title()}** · {row['created_at']}  \n{row['description']}  \n*{row.get('performed_by') or 'System'}*")
        st.divider()


def comments_panel(entity_type: str, entity_id: int, actor: str, can_edit: bool):
    st.markdown("#### Discussion")
    comments = query_df("SELECT * FROM comments WHERE entity_type=:e AND entity_id=:i ORDER BY created_at", {"e": entity_type, "i": entity_id})
    for _, row in comments.iterrows():
        st.markdown(f"**{row.get('author') or 'Team member'}** · {row['created_at']}  \n{row['body']}")
    if can_edit:
        with st.form(f"comment_{entity_type}_{entity_id}", clear_on_submit=True):
            body = st.text_area("Add a comment", label_visibility="collapsed", placeholder="Add context, a decision, or a handoff note…")
            if st.form_submit_button("Post comment") and body.strip():
                current = st.session_state.get("current_user") or {}
                comment_id = insert_record("comments", {"entity_type": entity_type, "entity_id": entity_id, "body": body, "author": actor, "author_user_id": current.get("id")}, actor, "Comment added")
                if entity_type == "tasks":
                    task = fetch_one("SELECT id,title,assignee_user_id,team_id FROM tasks WHERE id=:id", {"id": entity_id})
                    if task:
                        assignee_id = task.get("assignee_user_id")
                        if assignee_id and int(assignee_id) != int(current.get("id") or 0):
                            create_notification(int(assignee_id), "New task comment", f"{actor} commented on '{task.get('title') or 'Task'}': {body.strip()[:180]}", "tasks", entity_id, current.get("id"), "My Work")
                        notify_team_leads(int(task["team_id"]) if task.get("team_id") else None, "New task comment", f"{actor} commented on '{task.get('title') or 'Task'}': {body.strip()[:180]}", "tasks", entity_id, current.get("id"))
                st.rerun()


def project_options():
    df = query_df("SELECT id, name, code FROM projects WHERE archived=FALSE ORDER BY name")
    return {f"{r['name']} ({r['code'] or r['id']})": int(r['id']) for _, r in df.iterrows()}


def team_options():
    df = query_df("SELECT id, name FROM teams WHERE status='Active' ORDER BY name")
    return {r['name']: int(r['id']) for _, r in df.iterrows()}


def user_options(active_only: bool = True):
    where = "WHERE active=TRUE" if active_only else ""
    df = query_df(f"SELECT id, display_name, email, role FROM users {where} ORDER BY display_name, email")
    return {f"{r['display_name']} · {r['email']} ({r['role']})": int(r['id']) for _, r in df.iterrows()}


def user_by_id(user_id: int | None):
    if not user_id:
        return None
    return fetch_one("SELECT id, email, display_name, role, active FROM users WHERE id=:id", {"id": user_id})


# -----------------------------
# Startup + access
# -----------------------------
if "DATABASE_URL" not in st.secrets:
    st.error("DATABASE_URL is missing from .streamlit/secrets.toml")
    st.stop()

try:
    init_schema()
except Exception as exc:
    st.error(f"Safe schema initialization failed: {exc}")
    st.stop()

# Individual authentication, RBAC and server-managed sessions.
NAV_ITEMS = {
    "Dashboard": ("⌂", "Portfolio overview, priorities, blockers and recent activity."),
    "Portfolio Search": ("⌕", "Search projects, tasks, trials, issues, evidence and outreach."),
    "Projects": ("▣", "Create projects and manage objectives, teams, status and readiness."),
    "Workstreams": ("↳", "Split projects into owned workstreams and monitor progress."),
    "My Work": ("✓", "View tasks assigned to your authenticated user account."),
    "Milestones & Risks": ("◆", "Track delivery milestones, risks, mitigations and review dates."),
    "Trials": ("◉", "Plan, execute and follow validation trials through their lifecycle."),
    "Evidence": ("▤", "Register, review and verify trial evidence and technical artifacts."),
    "Issues": ("!", "Triage failures, assign developers, document fixes and manage retests."),
    "Outreach": ("◌", "Manage manufacturer and stakeholder engagement threads and follow-ups."),
    "Analytics & Readiness": ("⌁", "Compare baselines, validation results and readiness gates."),
    "Reports": ("▧", "Generate project, trial, issue and readiness summaries."),
    "Activity": ("◷", "Review the cross-system audit trail and record revisions."),
    "Notifications": ("●", "Review account, task, team and workflow alerts."),
    "Messages": ("✉", "Send and receive direct messages with registered users."),
    "Administration": ("⚙", "Manage users, roles, migrations and administrative data views."),
}

ROLE_PERMISSIONS = {
    "Administrator": {"*"},
    "User": set(),
}

WRITE_PERMISSIONS = {
    "project.write", "team.assign", "task.write", "trial.write",
    "evidence.write", "issue.write", "readiness.write"
}


SESSION_IDLE_MINUTES = 30
SESSION_ABSOLUTE_HOURS = 8
SESSION_COOKIE = "validationops_session"
ph = PasswordHasher()


def _safe_cookie_get(controller, key):
    try:
        return controller.get(key) if controller else None
    except Exception:
        return None


def _safe_cookie_set(controller, key, value, max_age=1800):
    try:
        if controller:
            controller.set(key, value, max_age=max_age)
    except Exception:
        pass


def _safe_cookie_remove(controller, key):
    try:
        if controller:
            controller.remove(key)
    except Exception:
        pass


def _token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_login_session(user_id: int) -> str:
    raw_token = secrets.token_urlsafe(48)
    now = datetime.now(timezone.utc)
    idle_expiry = now + timedelta(minutes=SESSION_IDLE_MINUTES)
    absolute_expiry = now + timedelta(hours=SESSION_ABSOLUTE_HOURS)
    execute("""
        INSERT INTO app_sessions(user_id, token_hash, last_seen_at, idle_expires_at, absolute_expires_at)
        VALUES (:uid, :token_hash, :now, :idle_expiry, :absolute_expiry)
    """, {"uid": user_id, "token_hash": _token_hash(raw_token), "now": now, "idle_expiry": idle_expiry, "absolute_expiry": absolute_expiry})
    execute("UPDATE users SET last_login_at=:now, updated_at=:now WHERE id=:uid", {"now": now, "uid": user_id})
    return raw_token


def resolve_login_session(raw_token: str | None):
    if not raw_token:
        return None
    now = datetime.now(timezone.utc)
    row = fetch_one("""
        SELECT s.id AS session_id, s.user_id, s.idle_expires_at, s.absolute_expires_at,
               u.email, u.display_name, u.role, u.access_level, u.active
        FROM app_sessions s
        JOIN users u ON u.id=s.user_id
        WHERE s.token_hash=:token_hash AND s.revoked_at IS NULL
    """, {"token_hash": _token_hash(raw_token)})
    if not row or not row.get("active"):
        return None
    idle_expiry = row["idle_expires_at"]
    absolute_expiry = row["absolute_expires_at"]
    if idle_expiry.tzinfo is None:
        idle_expiry = idle_expiry.replace(tzinfo=timezone.utc)
    if absolute_expiry.tzinfo is None:
        absolute_expiry = absolute_expiry.replace(tzinfo=timezone.utc)
    if now >= idle_expiry or now >= absolute_expiry:
        execute("UPDATE app_sessions SET revoked_at=:now WHERE id=:id", {"now": now, "id": row["session_id"]})
        return None
    renewed_idle = min(now + timedelta(minutes=SESSION_IDLE_MINUTES), absolute_expiry)
    execute("UPDATE app_sessions SET last_seen_at=:now, idle_expires_at=:idle WHERE id=:id", {"now": now, "idle": renewed_idle, "id": row["session_id"]})
    return {
        "id": int(row["user_id"]),
        "email": row["email"],
        "display_name": row["display_name"],
        "role": row["role"],
        "access_level": row.get("access_level") or "Read",
        "session_id": int(row["session_id"]),
    }


def revoke_login_session(raw_token: str | None):
    if raw_token:
        execute("UPDATE app_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE token_hash=:token_hash", {"token_hash": _token_hash(raw_token)})


def has_permission(permission: str) -> bool:
    current = st.session_state.get("current_user") or {}
    if current.get("role") == "Administrator":
        return True
    if permission.endswith(".read") or permission == "report.read":
        return True
    return current.get("access_level") == "Write" and permission in WRITE_PERMISSIONS


def users_count() -> int:
    row = fetch_one("SELECT COUNT(*) AS n FROM users")
    return int(row["n"] if row else 0)


def active_administrator_count() -> int:
    row = fetch_one("SELECT COUNT(*) AS n FROM users WHERE role='Administrator' AND active=TRUE")
    return int(row["n"] if row else 0)


def bootstrap_secret() -> str:
    # TEAM_EDIT_CODE remains only as a temporary migration fallback.
    return str(st.secrets.get("ADMIN_BOOTSTRAP_CODE", st.secrets.get("TEAM_EDIT_CODE", "")))


cookies = CookieController() if CookieController else None
raw_session_token = (
    st.session_state.get("pending_session_token")
    or _safe_cookie_get(cookies, SESSION_COOKIE)
)
current_user = resolve_login_session(raw_session_token)
if current_user:
    st.session_state.pop("pending_session_token", None)

# One-time initialization creates both administrator accounts together.
# Public registration never creates administrators.
if active_administrator_count() == 0:
    st.markdown('<div class="appbar"><div><div class="appbar-title">Initialize ValidationOps</div><div class="appbar-meta">Create the two administrator accounts</div></div></div>', unsafe_allow_html=True)
    st.info("Create both administrator accounts during the one-time setup. All later self-registered accounts are normal users with Read access.")
    with st.form("bootstrap_admins"):
        st.markdown("#### Administrator 1")
        a1, a2 = st.columns(2)
        admin1_name = a1.text_input("Full name", key="admin1_name")
        admin1_email = a2.text_input("Email", key="admin1_email")
        admin1_password = a1.text_input("Create password", type="password", key="admin1_password")
        admin1_confirm = a2.text_input("Confirm password", type="password", key="admin1_confirm")
        st.markdown("#### Administrator 2")
        b1, b2 = st.columns(2)
        admin2_name = b1.text_input("Full name", key="admin2_name")
        admin2_email = b2.text_input("Email", key="admin2_email")
        admin2_password = b1.text_input("Create password", type="password", key="admin2_password")
        admin2_confirm = b2.text_input("Confirm password", type="password", key="admin2_confirm")
        bootstrap_code = st.text_input("Bootstrap code", type="password")
        submitted = st.form_submit_button("Create both administrators and continue", type="primary", use_container_width=True)
    if submitted:
        expected = bootstrap_secret()
        email1, email2 = admin1_email.strip().lower(), admin2_email.strip().lower()
        if not expected or not hmac.compare_digest(bootstrap_code, expected):
            st.error("Invalid bootstrap code.")
        elif not admin1_name.strip() or "@" not in email1 or not admin2_name.strip() or "@" not in email2:
            st.error("Enter valid names and email addresses for both administrators.")
        elif email1 == email2:
            st.error("The two administrators must use different email addresses.")
        elif len(admin1_password) < 12 or len(admin2_password) < 12:
            st.error("Each administrator password must contain at least 12 characters.")
        elif admin1_password != admin1_confirm or admin2_password != admin2_confirm:
            st.error("One or both password confirmations do not match.")
        else:
            with get_engine().begin() as conn:
                admin1 = conn.execute(text("""
                    INSERT INTO users(email, display_name, password_hash, role, access_level, active, updated_at)
                    VALUES (:email, :name, :password_hash, 'Administrator', 'Write', TRUE, CURRENT_TIMESTAMP)
                    ON CONFLICT (email) DO UPDATE SET display_name=EXCLUDED.display_name, password_hash=EXCLUDED.password_hash, role='Administrator', access_level='Write', active=TRUE, updated_at=CURRENT_TIMESTAMP
                    RETURNING id, email, display_name, role, access_level
                """), {"email": email1, "name": admin1_name.strip(), "password_hash": ph.hash(admin1_password)}).mappings().one()
                conn.execute(text("""
                    INSERT INTO users(email, display_name, password_hash, role, access_level, active, updated_at)
                    VALUES (:email, :name, :password_hash, 'Administrator', 'Write', TRUE, CURRENT_TIMESTAMP)
                    ON CONFLICT (email) DO UPDATE SET display_name=EXCLUDED.display_name, password_hash=EXCLUDED.password_hash, role='Administrator', access_level='Write', active=TRUE, updated_at=CURRENT_TIMESTAMP
                """), {"email": email2, "name": admin2_name.strip(), "password_hash": ph.hash(admin2_password)})
            token = create_login_session(int(admin1["id"]))
            _safe_cookie_set(cookies, SESSION_COOKIE, token, max_age=SESSION_ABSOLUTE_HOURS * 3600)
            st.session_state.pending_session_token = token
            st.session_state.current_user = {"id": int(admin1["id"]), "email": admin1["email"], "display_name": admin1["display_name"], "role": admin1["role"], "access_level": admin1["access_level"]}
            st.session_state.current_page = "Dashboard"
            st.query_params["page"] = "Dashboard"
            st.rerun()
    st.stop()

if not current_user:
    st.markdown('<div class="appbar"><div><div class="appbar-title">IntelliAware ValidationOps</div><div class="appbar-meta">Secure user access</div></div></div>', unsafe_allow_html=True)
    sign_in_tab, register_tab = st.tabs(["Sign in", "Create account"])

    with sign_in_tab:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="name@company.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if submitted:
            user = fetch_one("SELECT * FROM users WHERE LOWER(email)=LOWER(:email) AND active=TRUE", {"email": email.strip()})
            valid = False
            if user:
                try:
                    valid = ph.verify(user["password_hash"], password)
                except (VerifyMismatchError, InvalidHashError):
                    valid = False
            if not valid:
                st.error("Invalid email or password.")
            else:
                token = create_login_session(int(user["id"]))
                _safe_cookie_set(cookies, SESSION_COOKIE, token, max_age=SESSION_ABSOLUTE_HOURS * 3600)
                st.session_state.pending_session_token = token
                st.session_state.current_user = {
                    "id": int(user["id"]),
                    "email": user["email"],
                    "display_name": user["display_name"],
                    "role": user["role"],
                    "access_level": user.get("access_level") or "Read",
                }
                st.rerun()

    with register_tab:
        st.caption("Create a user account. New accounts always start with Read access; an administrator can later approve Write access.")
        with st.form("self_registration_form"):
            new_name = st.text_input("Full name")
            new_email = st.text_input("Email address")
            new_password = st.text_input("Create password", type="password")
            new_confirm = st.text_input("Confirm password", type="password")
            st.text_input("Account type", value="User", disabled=True)
            st.text_input("Initial access", value="Read", disabled=True)
            register = st.form_submit_button("Create account", type="primary", use_container_width=True)
        if register:
            normalized_email = new_email.strip().lower()
            if not new_name.strip() or "@" not in normalized_email:
                st.error("Enter a valid name and email address.")
            elif len(new_password) < 12:
                st.error("Use a password with at least 12 characters.")
            elif new_password != new_confirm:
                st.error("Passwords do not match.")
            elif fetch_one("SELECT id FROM users WHERE LOWER(email)=LOWER(:email)", {"email": normalized_email}):
                st.error("An account already exists with that email.")
            else:
                user = fetch_one("""
                    INSERT INTO users(email, display_name, password_hash, role, access_level, active)
                    VALUES (:email, :display_name, :password_hash, 'User', 'Read', TRUE)
                    RETURNING id, email, display_name, role, access_level
                """, {"email": normalized_email, "display_name": new_name.strip(), "password_hash": ph.hash(new_password)})
                notify_active_administrators(
                    "New user registration",
                    f"{user['display_name']} ({user['email']}) created an account with Read access and is awaiting review.",
                    "users", int(user["id"]), int(user["id"]),
                )
                token = create_login_session(int(user["id"]))
                _safe_cookie_set(cookies, SESSION_COOKIE, token, max_age=SESSION_ABSOLUTE_HOURS * 3600)
                st.session_state.pending_session_token = token
                st.session_state.current_user = {"id": int(user["id"]), "email": user["email"], "display_name": user["display_name"], "role": "User", "access_level": "Read"}
                st.session_state.current_page = "Dashboard"
                st.query_params["page"] = "Dashboard"
                st.rerun()

    st.stop()

st.session_state.current_user = current_user
actor = current_user["display_name"]
actor_id = current_user["id"]
can_edit = current_user["role"] == "Administrator" or current_user.get("access_level") == "Write"

query_page = st.query_params.get("page", "Dashboard")
if isinstance(query_page, list):
    query_page = query_page[0] if query_page else "Dashboard"
saved_page = _safe_cookie_get(cookies, "validationops_page")
initial_page = query_page if query_page in NAV_ITEMS else (saved_page if saved_page in NAV_ITEMS else "Dashboard")
if "current_page" not in st.session_state:
    st.session_state.current_page = initial_page

# Hide Administration from non-admin users.
visible_nav = {k: v for k, v in NAV_ITEMS.items() if k != "Administration" or current_user["role"] == "Administrator"}

with st.sidebar:
    st.markdown("### IntelliAware ValidationOps")
    st.caption(f"{current_user['display_name']} · {current_user['role']} · {current_user.get('access_level', 'Read')}")
    st.markdown("#### Navigation")
    for page_name, (icon, description) in visible_nav.items():
        active = st.session_state.current_page == page_name
        if st.button(f"{icon}  {page_name}", key=f"nav_{page_name}", type="primary" if active else "secondary", help=description, use_container_width=True):
            st.session_state.current_page = page_name
            st.query_params["page"] = page_name
            _safe_cookie_set(cookies, "validationops_page", page_name, max_age=60 * 60 * 24 * 30)
            st.rerun()

    st.divider()
    st.markdown('<div style="padding:.7rem .8rem;border-radius:10px;background:#DCFCE7;color:#166534;font-weight:700;">● Authenticated</div>', unsafe_allow_html=True)
    unread_row = fetch_one("SELECT COUNT(*) AS n FROM notifications WHERE recipient_user_id=:uid AND is_read=FALSE", {"uid": actor_id})
    unread_count = int(unread_row["n"] if unread_row else 0)
    st.caption(f"Unread notifications: {unread_count}")
    st.caption(f"Session expires after {SESSION_IDLE_MINUTES} minutes of inactivity.")
    with st.popover("Account", use_container_width=True):
        st.write(f"**{current_user['display_name']}**")
        st.caption(current_user['email'])
        with st.form("change_password_form"):
            current_password = st.text_input("Current password", type="password")
            new_password = st.text_input("New password", type="password")
            confirm_password = st.text_input("Confirm new password", type="password")
            if st.form_submit_button("Change password"):
                user_row = fetch_one("SELECT password_hash FROM users WHERE id=:id", {"id": actor_id})
                password_valid = False
                try:
                    password_valid = bool(user_row) and ph.verify(user_row["password_hash"], current_password)
                except (VerifyMismatchError, InvalidHashError):
                    password_valid = False
                if not password_valid:
                    st.error("Current password is incorrect.")
                elif len(new_password) < 12:
                    st.error("New password must contain at least 12 characters.")
                elif new_password != confirm_password:
                    st.error("New passwords do not match.")
                else:
                    execute("UPDATE users SET password_hash=:hash, updated_at=CURRENT_TIMESTAMP WHERE id=:id", {"hash": ph.hash(new_password), "id": actor_id})
                    execute("UPDATE app_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE user_id=:uid AND id<>:sid AND revoked_at IS NULL", {"uid": actor_id, "sid": current_user["session_id"]})
                    st.success("Password changed. Other sessions were signed out.")
    if st.button("Sign out", use_container_width=True):
        revoke_login_session(raw_session_token)
        _safe_cookie_remove(cookies, SESSION_COOKIE)
        st.session_state.clear()
        st.rerun()
    if st.button("Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

page = st.session_state.current_page
if page == "Administration" and current_user["role"] != "Administrator":
    page = "Dashboard"
    st.session_state.current_page = page
st.query_params["page"] = page
_safe_cookie_set(cookies, "validationops_page", page, max_age=60 * 60 * 24 * 30)

st.markdown(f'<div class="appbar"><div><div class="appbar-title">IntelliAware ValidationOps</div><div class="appbar-meta">Validation operations, development remediation and deployment readiness</div></div><div class="appbar-meta"><strong>{current_user["display_name"]}</strong><br>{current_user["role"]} · {current_user.get("access_level", "Read")}</div></div>', unsafe_allow_html=True)

# -----------------------------
# Dashboard
# -----------------------------
if page == "Dashboard":
    p = query_df("SELECT * FROM projects WHERE archived=FALSE")
    w = query_df("SELECT * FROM workstreams")
    t = query_df("SELECT * FROM tasks")
    issues = query_df("SELECT * FROM issue_logs") if table_exists("issue_logs") else pd.DataFrame()
    trials = query_df("SELECT * FROM trials") if table_exists("trials") else pd.DataFrame()
    evidence = query_df("SELECT * FROM evidence_items")
    risks = query_df("SELECT * FROM risks")

    overdue = 0
    if not t.empty and "due_date" in t:
        due = pd.to_datetime(t["due_date"], errors="coerce")
        overdue = int(((due < pd.Timestamp.today().normalize()) & ~t["status"].astype(str).str.lower().isin(["completed", "closed"])).sum())
    critical = 0 if issues.empty else int(issues["severity"].astype(str).str.lower().isin(["critical", "high"]).sum())

    cols = st.columns(6)
    metrics = [("Active projects", len(p)), ("Active workstreams", int((~w.get("status", pd.Series(dtype=str)).astype(str).str.lower().isin(["completed", "closed"])).sum()) if not w.empty else 0), ("Open tasks", int((~t.get("status", pd.Series(dtype=str)).astype(str).str.lower().isin(["completed", "closed"])).sum()) if not t.empty else 0), ("Overdue", overdue), ("Open high/critical", critical), ("Trials", len(trials))]
    for c, (label, value) in zip(cols, metrics): c.metric(label, value)

    left, right = st.columns([1.5, 1])
    with left:
        st.markdown("### Project health")
        if p.empty:
            st.info("Create the first project to start organizing workstreams, teams and trials.")
        else:
            for _, r in p.sort_values("updated_at", ascending=False).head(8).iterrows():
                ws_count = len(w[w["project_id"] == r["id"]]) if not w.empty else 0
                task_count = len(t[t["project_id"] == r["id"]]) if not t.empty else 0
                render_card(r["name"], f"Owner: {r.get('owner') or 'Unassigned'}", [r.get("phase") or "", r.get("status") or "", f"{ws_count} workstreams", f"{task_count} tasks"], r.get("description") or "")
    with right:
        st.markdown("### Recent activity")
        activity = query_df("SELECT * FROM activity_log ORDER BY created_at DESC LIMIT 12")
        if activity.empty: st.caption("No activity recorded.")
        for _, r in activity.iterrows():
            st.markdown(f"**{r['action'].title()}** · {r['entity_type']}  \n{r.get('description') or ''}  \n<span class='muted'>{r['created_at']} · {r.get('performed_by') or 'System'}</span>", unsafe_allow_html=True)
            st.divider()

# -----------------------------
# Portfolio Search
# -----------------------------
elif page == "Portfolio Search":
    st.markdown("### Global search")
    q = st.text_input("Search projects, workstreams, tasks, trials, issues, outreach and evidence", placeholder="Type a name, key, owner, company or keyword…")
    if not q.strip():
        st.markdown('<div class="empty-state">Search across the complete validation portfolio.</div>', unsafe_allow_html=True)
    else:
        like = f"%{q.strip()}%"
        searches = [
            ("Projects", "SELECT id, name AS title, status AS state, owner AS owner, description AS detail FROM projects WHERE name ILIKE :q OR description ILIKE :q OR owner ILIKE :q LIMIT 25"),
            ("Workstreams", "SELECT id, name AS title, status AS state, owner AS owner, description AS detail FROM workstreams WHERE name ILIKE :q OR description ILIKE :q OR owner ILIKE :q LIMIT 25"),
            ("Tasks", "SELECT id, title, status AS state, assignee AS owner, description AS detail FROM tasks WHERE title ILIKE :q OR description ILIKE :q OR assignee ILIKE :q LIMIT 25"),
            ("Trials", "SELECT id, trial_name AS title, status AS state, trial_owner AS owner, notes AS detail FROM trials WHERE trial_name ILIKE :q OR notes ILIKE :q OR trial_owner ILIKE :q LIMIT 25"),
            ("Issues", "SELECT id, COALESCE(issue_id,'ISS') || ' — ' || COALESCE(title,'') AS title, status AS state, owner, observed_behavior AS detail FROM issue_logs WHERE title ILIKE :q OR issue_id ILIKE :q OR owner ILIKE :q OR observed_behavior ILIKE :q LIMIT 25"),
            ("Outreach", "SELECT id, company || ' — ' || COALESCE(contact_name,'') AS title, status AS state, contact_owner AS owner, notes AS detail FROM outreach_contacts WHERE company ILIKE :q OR contact_name ILIKE :q OR notes ILIKE :q LIMIT 25"),
            ("Evidence", "SELECT id, title, verification_status AS state, uploaded_by AS owner, description AS detail FROM evidence_items WHERE title ILIKE :q OR description ILIKE :q OR evidence_type ILIKE :q LIMIT 25"),
        ]
        found = 0
        for label, sql in searches:
            df = query_df(sql, {"q": like})
            if not df.empty:
                found += len(df); st.markdown(f"#### {label}")
                for _, r in df.iterrows():
                    render_card(str(r.get("title") or "Untitled"), f"Owner: {r.get('owner') or 'Unassigned'}", [str(r.get("state") or "")], str(r.get("detail") or ""))
        if found == 0: st.info("No matching records.")

# -----------------------------
# Projects
# -----------------------------
elif page == "Projects":
    st.markdown("### Projects")
    if can_edit:
        with st.expander("Create project", expanded=False):
            with st.form("create_project"):
                c1, c2 = st.columns(2)
                name = c1.text_input("Project name")
                code = c2.text_input("Project code")
                project_users = user_options(); owner_label = c1.selectbox("Project owner", list(project_users)) if project_users else None; owner_user_id = project_users.get(owner_label) if owner_label else None; owner = (user_by_id(owner_user_id) or {}).get("display_name", "")
                priority = c2.selectbox("Priority", ["Low", "Medium", "High", "Critical"], index=1)
                phase = c1.selectbox("Phase", ["Discovery", "Planning", "Validation", "Remediation", "Readiness review", "Completed"])
                environment = c2.text_input("Environment / site")
                dates = st.columns(2)
                start_date = dates[0].date_input("Start date", value=None)
                target_date = dates[1].date_input("Target date", value=None)
                description = st.text_area("Description")
                objectives = st.text_area("Objectives")
                success = st.text_area("Success criteria")
                if st.form_submit_button("Create project", type="primary"):
                    if not name.strip(): st.error("Project name is required.")
                    else:
                        insert_record("projects", {"name": name, "code": code or None, "owner": owner, "owner_user_id": owner_user_id, "priority": priority, "phase": phase, "environment": environment, "start_date": start_date, "target_date": target_date, "description": description, "objectives": objectives, "success_criteria": success}, actor, f"Project '{name}' created")
                        st.success("Project created."); st.rerun()

    projects = query_df("SELECT * FROM projects WHERE archived=FALSE ORDER BY updated_at DESC")
    if projects.empty: st.info("No projects yet.")
    else:
        selection = st.selectbox("Open project", {f"{r['name']} — {r.get('status')}": int(r['id']) for _, r in projects.iterrows()})
        project_id = {f"{r['name']} — {r.get('status')}": int(r['id']) for _, r in projects.iterrows()}[selection]
        project = fetch_one("SELECT * FROM projects WHERE id=:id", {"id": project_id})
        tabs = st.tabs(["Overview", "Edit", "Teams", "Timeline"])
        with tabs[0]:
            c = st.columns(4)
            c[0].metric("Phase", project.get("phase") or "—"); c[1].metric("Status", project.get("status") or "—"); c[2].metric("Priority", project.get("priority") or "—"); c[3].metric("Readiness", project.get("readiness_level") or "—")
            st.markdown(project.get("description") or "No description")
            st.markdown("#### Objectives"); st.write(project.get("objectives") or "Not defined")
            st.markdown("#### Success criteria"); st.write(project.get("success_criteria") or "Not defined")
            comments_panel("projects", project_id, actor, can_edit)
        with tabs[1]:
            if not can_edit: st.info("Enable edit access to modify this project.")
            else:
                with st.form(f"edit_project_{project_id}"):
                    c1,c2=st.columns(2)
                    name=c1.text_input("Name", project.get("name") or ""); project_users=user_options(); current_owner_id=project.get("owner_user_id"); owner_labels=list(project_users); default_owner_idx=list(project_users.values()).index(current_owner_id) if current_owner_id in project_users.values() else 0; owner_label=c2.selectbox("Owner", owner_labels, index=default_owner_idx) if owner_labels else None; owner_user_id=project_users.get(owner_label) if owner_label else None; owner=(user_by_id(owner_user_id) or {}).get("display_name", project.get("owner") or "")
                    priority=c1.selectbox("Priority", ["Low","Medium","High","Critical"], index=["Low","Medium","High","Critical"].index(project.get("priority") or "Medium"))
                    phase_opts=["Discovery","Planning","Validation","Remediation","Readiness review","Completed"]
                    phase=c2.selectbox("Phase", phase_opts, index=phase_opts.index(project.get("phase")) if project.get("phase") in phase_opts else 0)
                    status=c1.selectbox("Status", ["Active","At risk","Blocked","On hold","Completed"])
                    readiness=c2.selectbox("Readiness", ["Not assessed","Not ready","More validation required","Conditionally ready","Ready"])
                    description=st.text_area("Description", project.get("description") or "")
                    if st.form_submit_button("Save changes", type="primary"):
                        update_record("projects", project_id, {"name":name,"owner":owner,"owner_user_id":owner_user_id,"priority":priority,"phase":phase,"status":status,"readiness_level":readiness,"description":description,"updated_at":datetime.utcnow()}, actor, f"Project '{name}' updated")
                        st.success("Saved."); st.rerun()
        with tabs[2]:
            teams=team_options(); linked=query_df("SELECT pt.id, t.name, pt.responsibility FROM project_teams pt JOIN teams t ON t.id=pt.team_id WHERE pt.project_id=:p", {"p":project_id})
            st.dataframe(linked, use_container_width=True, hide_index=True)
            if can_edit and teams:
                with st.form(f"link_team_{project_id}"):
                    team_name=st.selectbox("Team", list(teams)); responsibility=st.text_input("Responsibility")
                    if st.form_submit_button("Assign team"):
                        execute("INSERT INTO project_teams(project_id,team_id,responsibility) VALUES(:p,:t,:r) ON CONFLICT(project_id,team_id) DO UPDATE SET responsibility=EXCLUDED.responsibility", {"p":project_id,"t":teams[team_name],"r":responsibility})
                        with get_engine().begin() as conn: log_activity(conn,"projects",project_id,"team_assignment",f"Assigned {team_name}: {responsibility}",actor)
                        st.rerun()
        with tabs[3]: record_timeline("projects", project_id)

# -----------------------------
# Workstreams + teams
# -----------------------------
elif page == "Workstreams":
    project_map = project_options()
    active_teams = team_options()
    st.markdown("### Workstreams and teams")
    work_tab, team_tab = st.tabs(["Workstreams", "Teams"])

    with work_tab:
        if not project_map:
            st.info("Create a project first.")
        else:
            selected_project = st.selectbox("Project", list(project_map), key="ws_project")
            pid = project_map[selected_project]
            if can_edit:
                with st.expander("Add workstream"):
                    with st.form("add_workstream"):
                        c1, c2 = st.columns(2)
                        name = c1.text_input("Name")
                        work_users = user_options()
                        owner_label = c2.selectbox("Owner", ["Unassigned"] + list(work_users)) if work_users else None
                        owner_user_id = work_users.get(owner_label) if owner_label else None
                        owner = (user_by_id(owner_user_id) or {}).get("display_name", "")
                        team_name = c1.selectbox("Team", ["Unassigned"] + list(active_teams))
                        priority = c2.selectbox("Priority", ["Low", "Medium", "High", "Critical"], index=1)
                        d1, d2 = st.columns(2)
                        start_date = d1.date_input("Start date", value=None)
                        due = d2.date_input("Due date", value=None)
                        description = st.text_area("Description")
                        deps = st.text_area("Dependencies / blockers")
                        if st.form_submit_button("Create workstream", type="primary"):
                            if not name.strip():
                                st.error("Workstream name is required.")
                            else:
                                insert_record("workstreams", {"project_id": pid, "name": name.strip(), "owner": owner, "owner_user_id": owner_user_id, "team_id": active_teams.get(team_name), "priority": priority, "start_date": start_date, "due_date": due, "description": description, "dependency_notes": deps}, actor, f"Workstream '{name.strip()}' created")
                                st.rerun()

            ws = query_df("SELECT w.*, t.name AS team_name FROM workstreams w LEFT JOIN teams t ON t.id=w.team_id WHERE w.project_id=:p ORDER BY w.id DESC", {"p": pid})
            for _, r in ws.iterrows():
                render_card(safe_text(r.get("name"), "Unnamed workstream"), f"Owner: {safe_text(r.get('owner'), 'Unassigned')} · Team: {safe_text(r.get('team_name'), 'Unassigned')}", [r.get("status"), r.get("priority"), f"{r.get('progress') or 0}%"], safe_text(r.get("dependency_notes"), ""))
                if can_edit:
                    with st.expander(f"Edit {r['name']}"):
                        with st.form(f"ws_{r['id']}"):
                            c1, c2 = st.columns(2)
                            edit_name = c1.text_input("Name", r.get("name") or "", key=f"wsn{r['id']}")
                            work_users = user_options()
                            owner_labels = ["Unassigned"] + list(work_users)
                            current_owner_id = r.get("owner_user_id")
                            current_owner_label = next((label for label, uid in work_users.items() if uid == current_owner_id), "Unassigned")
                            owner_label = c2.selectbox("Owner", owner_labels, index=owner_labels.index(current_owner_label), key=f"wso{r['id']}")
                            owner_user_id = work_users.get(owner_label)
                            owner_name = (user_by_id(owner_user_id) or {}).get("display_name", "")
                            all_team_df = query_df("SELECT id,name,status FROM teams ORDER BY name")
                            team_map = {f"{row['name']} ({row['status']})": int(row['id']) for _, row in all_team_df.iterrows()}
                            team_labels = ["Unassigned"] + list(team_map)
                            current_team_label = next((label for label, tid in team_map.items() if tid == r.get("team_id")), "Unassigned")
                            team_label = c1.selectbox("Team", team_labels, index=team_labels.index(current_team_label), key=f"wst{r['id']}")
                            priority_opts = ["Low", "Medium", "High", "Critical"]
                            priority = c2.selectbox("Priority", priority_opts, index=priority_opts.index(r.get("priority")) if r.get("priority") in priority_opts else 1, key=f"wsp{r['id']}")
                            d1, d2 = st.columns(2)
                            start_date = d1.date_input("Start date", value=parse_optional_date(r.get("start_date")), key=f"wssd{r['id']}")
                            due_date = d2.date_input("Due date", value=parse_optional_date(r.get("due_date")), key=f"wsdd{r['id']}")
                            status_opts = ["Backlog", "Ready", "In progress", "Blocked", "Under review", "Completed"]
                            status = c1.selectbox("Status", status_opts, index=status_opts.index(r.get("status")) if r.get("status") in status_opts else 0, key=f"wss{r['id']}")
                            progress = c2.slider("Progress", 0, 100, int(r.get("progress") or 0), key=f"wspr{r['id']}")
                            description = st.text_area("Description", r.get("description") or "", key=f"wsdesc{r['id']}")
                            deps = st.text_area("Dependencies / blockers", r.get("dependency_notes") or "", key=f"wsdep{r['id']}")
                            if st.form_submit_button("Save workstream", type="primary"):
                                if not edit_name.strip():
                                    st.error("Workstream name is required.")
                                else:
                                    update_record("workstreams", int(r["id"]), {"name": edit_name.strip(), "owner": owner_name, "owner_user_id": owner_user_id, "team_id": team_map.get(team_label), "priority": priority, "start_date": start_date, "due_date": due_date, "status": status, "progress": progress, "description": description, "dependency_notes": deps, "updated_at": datetime.utcnow()}, actor, f"Workstream '{edit_name.strip()}' updated")
                                    st.rerun()

    with team_tab:
        can_create_team = current_user["role"] == "Administrator" or user_leads_team(actor_id)
        if can_create_team:
            with st.expander("Create team"):
                with st.form("create_team"):
                    name = st.text_input("Team name")
                    purpose = st.text_area("Purpose")
                    registered = user_options()
                    lead_label = st.selectbox("Team lead", ["Unassigned"] + list(registered)) if registered else None
                    lead_user_id = registered.get(lead_label) if lead_label else None
                    if st.form_submit_button("Create team", type="primary"):
                        if not name.strip():
                            st.error("Team name is required.")
                        else:
                            lead_user = user_by_id(lead_user_id) or {}
                            team_id = insert_record("teams", {"name": name.strip(), "lead_name": lead_user.get("display_name"), "lead_user_id": lead_user_id, "purpose": purpose, "status": "Active"}, actor, f"Team '{name.strip()}' created")
                            if lead_user_id:
                                execute("INSERT INTO team_memberships(team_id,user_id,team_role,active,added_by_user_id) VALUES(:t,:u,'Team Lead',TRUE,:a) ON CONFLICT(team_id,user_id) DO UPDATE SET team_role='Team Lead',active=TRUE,updated_at=CURRENT_TIMESTAMP", {"t": team_id, "u": lead_user_id, "a": actor_id})
                                create_notification(lead_user_id, "Team lead assignment", f"You were assigned as Team Lead for {name.strip()}.", "teams", team_id, actor_id, "Workstreams")
                            st.rerun()

        team_df = query_df("SELECT t.*,u.display_name AS lead_display_name FROM teams t LEFT JOIN users u ON u.id=t.lead_user_id ORDER BY t.name")
        for _, team in team_df.iterrows():
            team_id = int(team["id"])
            lead_name = team.get("lead_display_name") or team.get("lead_name") or "Unassigned"
            member_count = fetch_one("SELECT COUNT(*) AS n FROM team_memberships WHERE team_id=:t AND active=TRUE", {"t": team_id})
            render_card(safe_text(team.get("name")), f"Lead: {safe_text(lead_name)}", [team.get("status"), f"{int(member_count['n'] if member_count else 0)} active members"], safe_text(team.get("purpose"), ""))
            with st.expander(f"Manage {team['name']}"):
                members = query_df("""
                    SELECT tm.id membership_id,tm.user_id,tm.team_role,tm.active,u.display_name,u.email,u.access_level
                    FROM team_memberships tm JOIN users u ON u.id=tm.user_id
                    WHERE tm.team_id=:t ORDER BY tm.active DESC, CASE WHEN tm.team_role='Team Lead' THEN 0 ELSE 1 END,u.display_name
                """, {"t": team_id})
                if members.empty:
                    st.caption("No registered users have been added to this team.")
                else:
                    st.dataframe(members[["display_name", "email", "team_role", "access_level", "active"]], use_container_width=True, hide_index=True)

                if can_manage_team(team_id):
                    st.markdown("#### Add registered user")
                    search = st.text_input("Search users by name or email", key=f"team_search_{team_id}")
                    params = {"team": team_id}
                    sql = """SELECT id,display_name,email,access_level FROM users WHERE active=TRUE AND id NOT IN (SELECT user_id FROM team_memberships WHERE team_id=:team AND active=TRUE)"""
                    if search.strip():
                        sql += " AND (display_name ILIKE :q OR email ILIKE :q)"
                        params["q"] = f"%{search.strip()}%"
                    sql += " ORDER BY display_name LIMIT 50"
                    candidates = query_df(sql, params)
                    candidate_map = {f"{r['display_name']} · {r['email']} ({r['access_level']})": int(r['id']) for _, r in candidates.iterrows()}
                    with st.form(f"add_member_{team_id}"):
                        member_label = st.selectbox("User", list(candidate_map) if candidate_map else ["No matching users"], key=f"member_select_{team_id}")
                        member_role = st.selectbox("Team role", ["Member", "Developer", "Validation Engineer", "Reviewer", "Team Lead"], key=f"member_role_{team_id}")
                        add_member = st.form_submit_button("Add to team")
                    if add_member and candidate_map and member_label in candidate_map:
                        uid = candidate_map[member_label]
                        execute("INSERT INTO team_memberships(team_id,user_id,team_role,active,added_by_user_id) VALUES(:t,:u,:r,TRUE,:a) ON CONFLICT(team_id,user_id) DO UPDATE SET team_role=:r,active=TRUE,updated_at=CURRENT_TIMESTAMP", {"t": team_id, "u": uid, "r": member_role, "a": actor_id})
                        if member_role == "Team Lead":
                            lead_user = user_by_id(uid) or {}
                            execute("UPDATE teams SET lead_user_id=:u,lead_name=:n WHERE id=:t", {"u": uid, "n": lead_user.get("display_name"), "t": team_id})
                        create_notification(uid, "Team membership updated", f"You were added to {team['name']} as {member_role}.", "teams", team_id, actor_id, "Workstreams")
                        st.rerun()

                    if not members.empty:
                        st.markdown("#### Update or remove member")
                        member_map = {f"{r['display_name']} · {r['email']} ({r['team_role']})": int(r['membership_id']) for _, r in members.iterrows()}
                        selected_member = st.selectbox("Team member", list(member_map), key=f"remove_member_{team_id}")
                        membership = fetch_one("SELECT tm.*,u.display_name,u.id AS uid FROM team_memberships tm JOIN users u ON u.id=tm.user_id WHERE tm.id=:id", {"id": member_map[selected_member]})
                        mc1, mc2 = st.columns(2)
                        role_opts = ["Member", "Developer", "Validation Engineer", "Reviewer", "Team Lead"]
                        new_role = mc1.selectbox("Member role", role_opts, index=role_opts.index(membership.get("team_role")) if membership.get("team_role") in role_opts else 0, key=f"change_role_{team_id}")
                        active_member = mc2.checkbox("Membership active", value=bool(membership.get("active")), key=f"member_active_{team_id}")
                        if st.button("Save membership", key=f"save_membership_{team_id}"):
                            execute("UPDATE team_memberships SET team_role=:r,active=:active,updated_at=CURRENT_TIMESTAMP WHERE id=:id", {"r": new_role, "active": active_member, "id": membership["id"]})
                            create_notification(int(membership["uid"]), "Team membership updated", f"Your membership in {team['name']} is now {new_role} ({'active' if active_member else 'inactive'}).", "teams", team_id, actor_id, "Workstreams")
                            st.rerun()

                    status_options = ["Active", "Inactive"]
                    new_status = st.selectbox("Team status", status_options, index=status_options.index(team.get("status")) if team.get("status") in status_options else 0, key=f"team_status_{team_id}")
                    if st.button("Save team status", key=f"save_team_status_{team_id}"):
                        update_record("teams", team_id, {"status": new_status}, actor, f"Team '{team['name']}' changed to {new_status}")
                        st.rerun()

# -----------------------------
# My Work / tasks
# -----------------------------
elif page == "My Work":
    project_map = project_options()
    st.markdown("### My Work")
    st.caption("Tasks are linked to your authenticated account. Team-aware assignment limits assignees to active members of the selected workstream team.")

    can_create_task = has_permission("task.write")
    if can_create_task and project_map:
        with st.expander("Create task"):
            p_name = st.selectbox("Project", list(project_map), key="task_project")
            pid = project_map[p_name]
            ws_df = query_df("SELECT w.id,w.name,w.team_id,t.name team_name FROM workstreams w LEFT JOIN teams t ON t.id=w.team_id WHERE w.project_id=:p ORDER BY w.name", {"p": pid})
            ws_map = {f"{r['name']} · {r.get('team_name') or 'No team'}": int(r['id']) for _, r in ws_df.iterrows()}
            ws_label = st.selectbox("Workstream", list(ws_map) if ws_map else ["No workstreams available"], key="task_workstream")
            selected_ws = fetch_one("SELECT * FROM workstreams WHERE id=:id", {"id": ws_map.get(ws_label)}) if ws_map and ws_label in ws_map else None
            team_id = int(selected_ws["team_id"]) if selected_ws and selected_ws.get("team_id") else None
            members = team_member_options(team_id)
            if not team_id:
                st.warning("Assign an active team to this workstream before creating a task.")
            elif not members:
                st.warning("The assigned team has no active registered members. Add users to the team first.")
            else:
                with st.form("create_task"):
                    c1, c2 = st.columns(2)
                    title = c1.text_input("Task title")
                    assignee_label = c2.selectbox("Assignee", list(members))
                    priority = c1.selectbox("Priority", ["Low", "Medium", "High", "Critical"], index=1)
                    due = c2.date_input("Due date", value=None)
                    description = st.text_area("Description")
                    criteria = st.text_area("Completion criteria")
                    if st.form_submit_button("Create task", type="primary"):
                        if not title.strip():
                            st.error("Task title is required.")
                        else:
                            assignee_user_id = members[assignee_label]
                            assignee_user = user_by_id(assignee_user_id)
                            task_id = insert_record("tasks", {"project_id": pid, "workstream_id": int(selected_ws["id"]), "team_id": team_id, "title": title.strip(), "assignee": assignee_user["display_name"], "assignee_user_id": assignee_user_id, "priority": priority, "due_date": due, "description": description, "completion_criteria": criteria}, actor, f"Task '{title.strip()}' created and assigned to {assignee_user['display_name']}")
                            create_notification(assignee_user_id, "New task assigned", f"{actor} assigned you '{title.strip()}'.", "tasks", task_id, actor_id, "My Work")
                            notify_team_leads(team_id, "Task assigned", f"{actor} assigned '{title.strip()}' to {assignee_user['display_name']}.", "tasks", task_id, actor_id)
                            st.rerun()

    mine_tab, team_tab = st.tabs(["My assigned tasks", "Team tasks"])
    with mine_tab:
        tasks = query_df("""
            SELECT tk.*, p.name project_name, w.name workstream_name,te.name team_name
            FROM tasks tk LEFT JOIN projects p ON p.id=tk.project_id
            LEFT JOIN workstreams w ON w.id=tk.workstream_id LEFT JOIN teams te ON te.id=tk.team_id
            WHERE tk.assignee_user_id=:uid ORDER BY tk.due_date NULLS LAST, tk.id DESC
        """, {"uid": actor_id})
        if tasks.empty:
            st.info("No tasks are currently assigned to your account.")
        for _, r in tasks.iterrows():
            render_card(safe_text(r.get("title")), f"{safe_text(r.get('project_name'), 'No project')} · {safe_text(r.get('workstream_name'), 'No workstream')} · {safe_text(r.get('team_name'), 'No team')}", [r.get("status"), r.get("priority"), str(r.get("due_date") or "No due date")], safe_text(r.get("description"), ""))
            with st.expander("Open task"):
                st.write(f"**Completion criteria:** {r.get('completion_criteria') or 'Not defined'}")
                if has_permission("task.write"):
                    with st.form(f"task_{r['id']}"):
                        status_opts = ["Backlog", "Ready", "In progress", "Blocked", "Under review", "Completed"]
                        status = st.selectbox("Status", status_opts, index=status_opts.index(r.get("status")) if r.get("status") in status_opts else 0)
                        note = st.text_area("Update note")
                        if st.form_submit_button("Save update"):
                            old_status = r.get("status")
                            vals = {"status": status, "updated_at": datetime.utcnow()}
                            if status == "Completed": vals["completed_at"] = datetime.utcnow()
                            update_record("tasks", int(r["id"]), vals, actor, note or f"Task '{r['title']}' moved from {old_status} to {status}")
                            notify_team_leads(int(r["team_id"]) if r.get("team_id") else None, "Task status changed", f"{actor} changed '{r['title']}' from {old_status} to {status}. {note}".strip(), "tasks", int(r["id"]), actor_id)
                            st.rerun()
                comments_panel("tasks", int(r["id"]), actor, True)
                record_timeline("tasks", int(r["id"]))

    with team_tab:
        led = query_df("""SELECT t.id,t.name FROM teams t JOIN team_memberships tm ON tm.team_id=t.id WHERE tm.user_id=:uid AND tm.team_role='Team Lead' AND tm.active=TRUE ORDER BY t.name""", {"uid": actor_id})
        if current_user["role"] == "Administrator":
            led = query_df("SELECT id,name FROM teams ORDER BY name")
        if led.empty:
            st.caption("Team-task oversight is available to administrators and designated team leads.")
        else:
            led_map = {r["name"]: int(r["id"]) for _, r in led.iterrows()}
            team_name = st.selectbox("Team", list(led_map), key="team_task_team")
            team_tasks = query_df("""SELECT tk.*,u.display_name assignee_name,w.name workstream_name FROM tasks tk LEFT JOIN users u ON u.id=tk.assignee_user_id LEFT JOIN workstreams w ON w.id=tk.workstream_id WHERE tk.team_id=:t ORDER BY tk.updated_at DESC""", {"t": led_map[team_name]})
            st.dataframe(team_tasks[[c for c in ["title","assignee_name","workstream_name","priority","status","due_date","updated_at"] if c in team_tasks]], use_container_width=True, hide_index=True)

# -----------------------------
# Milestones and risks
# -----------------------------
elif page == "Milestones & Risks":
    st.markdown("### Milestones and risk register")
    pmap = project_options()
    if not pmap: st.info("Create a project first.")
    else:
        pname = st.selectbox("Project", list(pmap)); pid = pmap[pname]
        mt, rt = st.tabs(["Milestones", "Risks"])
        with mt:
            if can_edit:
                with st.expander("Add milestone"):
                    with st.form("milestone_create"):
                        c1,c2=st.columns(2); title=c1.text_input("Milestone"); milestone_users=user_options(); owner_label=c2.selectbox("Owner", list(milestone_users), index=list(milestone_users.values()).index(actor_id) if actor_id in milestone_users.values() else 0) if milestone_users else None; owner_user_id=milestone_users.get(owner_label) if owner_label else None; owner=(user_by_id(owner_user_id) or {}).get("display_name", actor)
                        due=c1.date_input("Due date", value=None); status=c2.selectbox("Status",["Planned","In progress","At risk","Completed"])
                        desc=st.text_area("Description")
                        if st.form_submit_button("Create milestone", type="primary") and title:
                            insert_record("milestones", {"project_id":pid,"title":title,"owner":owner,"owner_user_id":owner_user_id,"due_date":due,"status":status,"description":desc}, actor, f"Milestone '{title}' created"); st.rerun()
            mdf=query_df("SELECT * FROM milestones WHERE project_id=:p ORDER BY due_date NULLS LAST,id",{"p":pid})
            if mdf.empty: st.markdown('<div class="empty-state">No milestones defined.</div>', unsafe_allow_html=True)
            for _,r in mdf.iterrows():
                render_card(r['title'],f"Owner: {r.get('owner') or 'Unassigned'} · Due: {r.get('due_date') or 'Not set'}",[r.get('status')],r.get('description') or '')
                if can_edit:
                    with st.expander("Update milestone"):
                        with st.form(f"mile_{r['id']}"):
                            s=st.selectbox("Status",["Planned","In progress","At risk","Completed"],index=["Planned","In progress","At risk","Completed"].index(r.get('status')) if r.get('status') in ["Planned","In progress","At risk","Completed"] else 0)
                            note=st.text_input("Change note")
                            if st.form_submit_button("Save"):
                                update_record("milestones",int(r['id']),{"status":s,"updated_at":datetime.utcnow()},actor,note or f"Milestone moved to {s}");st.rerun()
        with rt:
            if can_edit:
                with st.expander("Add risk"):
                    with st.form("risk_create"):
                        c1,c2=st.columns(2); title=c1.text_input("Risk"); risk_users=user_options(); owner_label=c2.selectbox("Owner", list(risk_users), index=list(risk_users.values()).index(actor_id) if actor_id in risk_users.values() else 0) if risk_users else None; owner_user_id=risk_users.get(owner_label) if owner_label else None; owner=(user_by_id(owner_user_id) or {}).get("display_name", actor)
                        category=c1.selectbox("Category",["Technical","Schedule","Access","Data","Safety","Adoption","Integration"])
                        probability=c2.selectbox("Probability",["Low","Medium","High"]); impact=c1.selectbox("Impact",["Low","Medium","High","Critical"])
                        due=c2.date_input("Review date",value=None); mitigation=st.text_area("Mitigation / contingency")
                        if st.form_submit_button("Create risk",type="primary") and title:
                            insert_record("risks",{"project_id":pid,"title":title,"owner":owner,"owner_user_id":owner_user_id,"category":category,"probability":probability,"impact":impact,"due_date":due,"mitigation":mitigation},actor,f"Risk '{title}' created");st.rerun()
            rdf=query_df("SELECT * FROM risks WHERE project_id=:p ORDER BY CASE impact WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,id DESC",{"p":pid})
            for _,r in rdf.iterrows():
                render_card(r['title'],f"{r.get('category') or 'General'} · Owner: {r.get('owner') or 'Unassigned'}",[r.get('probability'),r.get('impact'),r.get('status')],r.get('mitigation') or '')

# -----------------------------
# Trials
# -----------------------------
elif page == "Trials":
    st.markdown("### Trial operations")
    project_map = project_options()
    active_teams = team_options()
    if has_permission("trial.write"):
        with st.expander("Plan trial"):
            with st.form("create_trial"):
                p_name = st.selectbox("Project", ["Unassigned"] + list(project_map)); pid = project_map.get(p_name)
                c1, c2 = st.columns(2)
                name = c1.text_input("Trial name")
                trial_users = user_options()
                owner_label = c2.selectbox("Owner", ["Unassigned"] + list(trial_users)) if trial_users else None
                trial_owner_user_id = trial_users.get(owner_label) if owner_label else None
                owner = (user_by_id(trial_owner_user_id) or {}).get("display_name", "")
                environment = c1.text_input("Environment / site")
                process = c2.text_input("Process type")
                planned = c1.date_input("Planned date", value=None)
                model = c2.text_input("Model/software version")
                team_label = c1.selectbox("Team", ["Unassigned"] + list(active_teams))
                level = c2.selectbox("Validation level", ["Simulated", "Controlled lab", "Shadow factory", "Operational pilot", "Production readiness"])
                ws_df = query_df("SELECT id,name FROM workstreams WHERE project_id=:p ORDER BY name", {"p": pid}) if pid else pd.DataFrame()
                ws_map = {r["name"]: int(r["id"]) for _, r in ws_df.iterrows()}
                ws_label = st.selectbox("Workstream", ["Unassigned"] + list(ws_map))
                criteria = st.text_area("Success criteria")
                notes = st.text_area("Notes")
                if st.form_submit_button("Create trial", type="primary"):
                    if not name.strip():
                        st.error("Trial name is required.")
                    else:
                        insert_record("trials", {"trial_name": name.strip(), "project_id": pid, "workstream_id": ws_map.get(ws_label), "team_id": active_teams.get(team_label), "environment": environment, "process_type": process, "trial_owner": owner, "trial_owner_user_id": trial_owner_user_id, "planned_date": planned, "status": "Draft", "success_criteria": criteria, "notes": notes, "model_version": model, "validation_level": level}, actor, f"Trial '{name.strip()}' created")
                        st.rerun()
    trials = query_df("SELECT tr.*,p.name project_name,w.name workstream_name,t.name team_name FROM trials tr LEFT JOIN projects p ON p.id=tr.project_id LEFT JOIN workstreams w ON w.id=tr.workstream_id LEFT JOIN teams t ON t.id=tr.team_id ORDER BY tr.id DESC")
    for _, r in trials.iterrows():
        render_card(safe_text(r.get("trial_name"), f"Trial {r['id']}"), f"{safe_text(r.get('project_name'), 'Legacy/unassigned')} · {safe_text(r.get('workstream_name'), 'No workstream')} · Team: {safe_text(r.get('team_name'), 'Unassigned')}", [r.get("status"), r.get("validation_level") or "Legacy", r.get("model_version") or "Version not set"], safe_text(r.get("success_criteria"), ""))
        with st.expander("Open trial"):
            st.write(f"**Owner:** {r.get('trial_owner') or 'Unassigned'}")
            st.write(f"**Environment:** {r.get('environment') or '—'}")
            st.write(f"**Process:** {r.get('process_type') or '—'}")
            st.write(f"**Planned:** {r.get('planned_date') or '—'}")
            st.write(f"**Notes:** {r.get('notes') or '—'}")
            if has_permission("trial.write"):
                with st.form(f"trial_update_{r['id']}"):
                    c1, c2 = st.columns(2)
                    edit_name = c1.text_input("Trial name", r.get("trial_name") or "")
                    project_labels = ["Unassigned"] + list(project_map)
                    current_project = next((label for label, val in project_map.items() if val == r.get("project_id")), "Unassigned")
                    project_label = c2.selectbox("Project", project_labels, index=project_labels.index(current_project))
                    edit_pid = project_map.get(project_label)
                    edit_ws_df = query_df("SELECT id,name FROM workstreams WHERE project_id=:p ORDER BY name", {"p": edit_pid}) if edit_pid else pd.DataFrame()
                    edit_ws_map = {row["name"]: int(row["id"]) for _, row in edit_ws_df.iterrows()}
                    ws_labels = ["Unassigned"] + list(edit_ws_map)
                    current_ws = next((label for label, val in edit_ws_map.items() if val == r.get("workstream_id")), "Unassigned")
                    ws_label = c1.selectbox("Workstream", ws_labels, index=ws_labels.index(current_ws))
                    all_team_df = query_df("SELECT id,name,status FROM teams ORDER BY name")
                    team_map = {f"{row['name']} ({row['status']})": int(row['id']) for _, row in all_team_df.iterrows()}
                    team_labels = ["Unassigned"] + list(team_map)
                    current_team = next((label for label, val in team_map.items() if val == r.get("team_id")), "Unassigned")
                    team_label = c2.selectbox("Team", team_labels, index=team_labels.index(current_team))
                    users = user_options(); owner_labels = ["Unassigned"] + list(users)
                    current_owner = next((label for label, val in users.items() if val == r.get("trial_owner_user_id")), "Unassigned")
                    owner_label = c1.selectbox("Owner", owner_labels, index=owner_labels.index(current_owner))
                    owner_uid = users.get(owner_label); owner_name = (user_by_id(owner_uid) or {}).get("display_name", "")
                    environment = c2.text_input("Environment / site", r.get("environment") or "")
                    process = c1.text_input("Process type", r.get("process_type") or "")
                    planned = c2.date_input("Planned date", value=parse_optional_date(r.get("planned_date")))
                    model = c1.text_input("Model/software version", r.get("model_version") or "")
                    level_opts = ["Simulated", "Controlled lab", "Shadow factory", "Operational pilot", "Production readiness"]
                    level = c2.selectbox("Validation level", level_opts, index=level_opts.index(r.get("validation_level")) if r.get("validation_level") in level_opts else 0)
                    status_opts = ["Draft", "Planned", "Approved", "Setup in progress", "Ready to run", "Running", "Evidence review", "Analysis", "Completed", "Archived"]
                    status = c1.selectbox("Status", status_opts, index=status_opts.index(r.get("status")) if r.get("status") in status_opts else 0)
                    criteria = st.text_area("Success criteria", r.get("success_criteria") or "")
                    notes = st.text_area("Notes", r.get("notes") or "")
                    change_note = st.text_area("Change note")
                    if st.form_submit_button("Save trial", type="primary"):
                        update_record("trials", int(r["id"]), {"trial_name": edit_name.strip(), "project_id": edit_pid, "workstream_id": edit_ws_map.get(ws_label), "team_id": team_map.get(team_label), "trial_owner": owner_name, "trial_owner_user_id": owner_uid, "environment": environment, "process_type": process, "planned_date": planned, "model_version": model, "validation_level": level, "status": status, "success_criteria": criteria, "notes": notes, "updated_at": datetime.utcnow()}, actor, change_note or f"Trial '{edit_name.strip()}' updated")
                        st.rerun()
            record_timeline("trials", int(r["id"]))

# -----------------------------
# Evidence
# -----------------------------
elif page == "Evidence":
    st.markdown("### Evidence registry")
    pmap = project_options()
    if has_permission("evidence.write"):
        with st.expander("Register evidence"):
            p_name = st.selectbox("Project", ["Unassigned"] + list(pmap), key="evidence_project")
            pid = pmap.get(p_name)
            trial_df = query_df("SELECT id,trial_name FROM trials WHERE project_id=:p ORDER BY id DESC", {"p": pid}) if pid else pd.DataFrame()
            trial_map = {r["trial_name"]: int(r["id"]) for _, r in trial_df.iterrows()}
            with st.form("evidence_create"):
                c1, c2 = st.columns(2)
                title = c1.text_input("Evidence title")
                etype = c2.selectbox("Type", ["Video", "Image", "Model output", "Sensor log", "Ground truth", "Calibration", "Operator feedback", "Report", "Other"])
                trial_label = c1.selectbox("Related trial", ["Project-level / none"] + list(trial_map))
                source = c2.text_input("Source / system")
                uri = st.text_input("Public file or repository link", help="Use a complete public or organization-accessible HTTPS link. Do not enter N/A or a local computer path.")
                version = c1.text_input("Model/software version")
                status = c2.selectbox("Verification status", ["Expected", "Submitted", "Under review", "Verified", "Rejected", "Superseded"])
                desc = st.text_area("Description")
                if st.form_submit_button("Register evidence", type="primary"):
                    normalized_uri = normalize_evidence_url(uri)
                    if not title.strip():
                        st.error("Evidence title is required.")
                    elif uri.strip() and not normalized_uri:
                        st.error("Enter a valid HTTPS link or leave the field blank. Placeholder values and local paths are not accepted.")
                    else:
                        insert_record("evidence_items", {"project_id": pid, "trial_id": trial_map.get(trial_label), "title": title.strip(), "evidence_type": etype, "source": source.strip(), "uri": normalized_uri, "model_version": version.strip(), "verification_status": status, "description": desc.strip(), "uploaded_by": actor, "uploaded_by_user_id": actor_id}, actor, f"Evidence '{title.strip()}' registered")
                        st.rerun()
    f1, f2 = st.columns(2)
    project_filter = f1.selectbox("Project filter", ["All"] + list(pmap))
    status_filter = f2.selectbox("Verification", ["All", "Expected", "Submitted", "Under review", "Verified", "Rejected", "Superseded"])
    sql = "SELECT e.*,p.name project_name,tr.trial_name FROM evidence_items e LEFT JOIN projects p ON p.id=e.project_id LEFT JOIN trials tr ON tr.id=e.trial_id WHERE 1=1"; params = {}
    if project_filter != "All": sql += " AND e.project_id=:p"; params["p"] = pmap[project_filter]
    if status_filter != "All": sql += " AND e.verification_status=:s"; params["s"] = status_filter
    sql += " ORDER BY e.id DESC"
    edf = query_df(sql, params)
    if edf.empty: st.markdown('<div class="empty-state">No evidence records match this view.</div>', unsafe_allow_html=True)
    for _, r in edf.iterrows():
        evidence_url = normalize_evidence_url(r.get("uri"))
        link = f'<a href="{html.escape(evidence_url, quote=True)}" target="_blank" rel="noopener noreferrer">Open evidence</a>' if evidence_url else ("Invalid or inaccessible evidence link" if str(r.get("uri") or "").strip() else "No external file linked")
        render_card(safe_text(r.get("title")), f"{safe_text(r.get('project_name'), 'Unassigned')} · Trial: {safe_text(r.get('trial_name'), 'Project-level')} · Uploaded by {safe_text(r.get('uploaded_by'), 'Unknown')}", [r.get("evidence_type"), r.get("verification_status"), r.get("model_version") or "No version"], f"{safe_text(r.get('description'), '')}<br>{link}")
        if has_permission("evidence.write"):
            with st.expander("Review or correct evidence"):
                with st.form(f"ev_{r['id']}"):
                    status_opts = ["Expected", "Submitted", "Under review", "Verified", "Rejected", "Superseded"]
                    status = st.selectbox("Verification status", status_opts, index=status_opts.index(r.get("verification_status")) if r.get("verification_status") in status_opts else 0)
                    uri_value = st.text_input("Public evidence link", r.get("uri") or "")
                    source = st.text_input("Source / system", r.get("source") or "")
                    desc = st.text_area("Description", r.get("description") or "")
                    verify_users = user_options(); verifier_label = st.selectbox("Verified/reviewed by", list(verify_users), index=list(verify_users.values()).index(actor_id) if actor_id in verify_users.values() else 0) if verify_users else None
                    verified_by_user_id = verify_users.get(verifier_label) if verifier_label else None
                    verifier = (user_by_id(verified_by_user_id) or {}).get("display_name", actor)
                    note = st.text_area("Review note")
                    if st.form_submit_button("Save evidence"):
                        normalized = normalize_evidence_url(uri_value)
                        if uri_value.strip() and not normalized:
                            st.error("Enter a valid HTTPS link or clear the field.")
                        else:
                            update_record("evidence_items", int(r["id"]), {"verification_status": status, "uri": normalized, "source": source, "description": desc, "verified_by": verifier, "verified_by_user_id": verified_by_user_id}, actor, note or f"Evidence moved to {status}")
                            st.rerun()

# -----------------------------
# Issues
# -----------------------------
elif page == "Issues":
    st.markdown("### Issue and developer workflow")
    project_map=project_options()
    if has_permission("issue.write"):
        with st.expander("Report issue"):
            with st.form("create_issue"):
                p_name=st.selectbox("Project",["Unassigned"]+list(project_map)); pid=project_map.get(p_name)
                c1,c2=st.columns(2); issue_id=c1.text_input("Issue key",value=f"ISS-{datetime.now().strftime('%H%M%S')}"); title=c2.text_input("Title")
                severity=c1.selectbox("Severity",["Low","Medium","High","Critical"]); priority=c2.selectbox("Priority",["Low","Medium","High","Critical"],index=1)
                issue_users=user_options(); owner_label=c1.selectbox("Owner", ["Unassigned"]+list(issue_users)); owner_user_id=issue_users.get(owner_label); owner=(user_by_id(owner_user_id) or {}).get("display_name", "") if owner_user_id else ""; environment=c2.text_input("Environment")
                observed=st.text_area("Observed behavior"); expected=st.text_area("Expected behavior"); fix=st.text_area("Suggested action / fix")
                if st.form_submit_button("Create issue") and title:
                    insert_record("issue_logs",{"issue_id":issue_id,"title":title,"project_id":pid,"severity":severity,"priority":priority,"owner":owner,"owner_user_id":owner_user_id,"environment":environment,"observed_behavior":observed,"expected_behavior":expected,"suggested_fix":fix,"status":"Reported"},actor,f"Issue {issue_id} created")
                    st.rerun()
    issues=query_df("SELECT i.*,p.name project_name FROM issue_logs i LEFT JOIN projects p ON p.id=i.project_id ORDER BY CASE LOWER(i.severity) WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,i.id DESC")
    f1,f2,f3=st.columns(3); sev_filter=f1.selectbox("Severity",["All","Critical","High","Medium","Low"]); status_filter=f2.selectbox("Status",["All","Reported","Triaged","Assigned","Under investigation","Root cause identified","Fix in progress","Ready for retest","Retesting","Verified","Closed","Deferred"]); owner_filter=f3.text_input("Owner contains")
    if sev_filter!="All":issues=issues[issues["severity"].astype(str).str.lower()==sev_filter.lower()]
    if status_filter!="All":issues=issues[issues["status"].astype(str).str.lower()==status_filter.lower()]
    if owner_filter:issues=issues[issues["owner"].astype(str).str.contains(owner_filter,case=False,na=False)]
    for _,r in issues.iterrows():
        render_card(f"{r.get('issue_id') or 'ISS'} — {r.get('title')}",f"{r.get('project_name') or 'Legacy/unassigned'} · Owner: {r.get('owner') or 'Unassigned'}",[r.get("severity"),r.get("priority") or "No priority",r.get("status")],r.get("observed_behavior") or "")
        with st.expander("Open issue"):
            st.write(f"**Expected behavior:** {r.get('expected_behavior') or '—'}")
            st.write(f"**Suggested fix:** {r.get('suggested_fix') or '—'}")
            st.write(f"**Root cause:** {r.get('root_cause') or 'Not recorded'}")
            if has_permission("issue.write"):
                with st.form(f"issue_update_{r['id']}"):
                    status=st.selectbox("Workflow status",["Reported","Triaged","Assigned","Under investigation","Root cause identified","Fix in progress","Ready for retest","Retesting","Verified","Closed","Deferred"],key=f"is{r['id']}")
                    owner=st.text_input("Owner",r.get("owner") or "",key=f"io{r['id']}")
                    root=st.text_area("Root cause",r.get("root_cause") or "",key=f"ir{r['id']}")
                    version=st.text_input("Target fix version",r.get("target_fix_version") or "",key=f"iv{r['id']}")
                    note=st.text_area("Change note",key=f"in{r['id']}")
                    if st.form_submit_button("Save issue update"):
                        update_record("issue_logs",int(r["id"]),{"status":status,"owner":owner,"root_cause":root,"target_fix_version":version,"updated_at":datetime.utcnow()},actor,note or f"Issue moved to {status}")
                        st.rerun()
            comments_panel("issue_logs",int(r["id"]),actor,can_edit)
            record_timeline("issue_logs",int(r["id"]))

# -----------------------------
# Outreach
# -----------------------------
elif page == "Outreach":
    st.markdown("### Manufacturer and stakeholder threads")
    project_map = project_options()
    if can_edit:
        with st.expander("Add outreach thread"):
            with st.form("outreach_new"):
                p_name = st.selectbox("Project", ["Unassigned"] + list(project_map)); pid = project_map.get(p_name)
                c1, c2 = st.columns(2)
                company = c1.text_input("Company")
                contact = c2.text_input("Contact name")
                outreach_users = user_options()
                owner_label = c1.selectbox("Owner", list(outreach_users), index=list(outreach_users.values()).index(actor_id) if actor_id in outreach_users.values() else 0) if outreach_users else None
                contact_owner_user_id = outreach_users.get(owner_label) if owner_label else None
                owner = (user_by_id(contact_owner_user_id) or {}).get("display_name", actor)
                process = c2.text_input("Process / topic")
                latest_touch = c1.date_input("Latest touchpoint", value=None)
                follow_up = c2.date_input("Follow-up date", value=None)
                next_action = st.text_input("Next action")
                notes = st.text_area("Notes")
                if st.form_submit_button("Create outreach thread", type="primary"):
                    if not company.strip():
                        st.error("Company is required.")
                    else:
                        insert_record("outreach_contacts", {"project_id": pid, "company": company.strip(), "contact_name": contact.strip(), "contact_owner": owner, "contact_owner_user_id": contact_owner_user_id, "process_type": process, "status": "Identified", "next_action": next_action, "notes": notes, "latest_touchpoint_date": latest_touch, "last_touchpoint": latest_touch.isoformat() if latest_touch else None, "follow_up_date": follow_up}, actor, f"Outreach thread for {company.strip()} created")
                        st.rerun()

    f1, f2, f3, f4 = st.columns(4)
    search = f1.text_input("Search company or contact")
    project_filter = f2.selectbox("Project", ["All"] + list(project_map))
    status_opts = ["All", "Identified", "Contact pending", "Contacted", "Follow-up due", "Response received", "Meeting scheduled", "Access confirmed", "Closed"]
    status_filter = f3.selectbox("Status", status_opts)
    owner_filter = f4.text_input("Owner contains")
    sql = "SELECT o.*,p.name project_name FROM outreach_contacts o LEFT JOIN projects p ON p.id=o.project_id WHERE 1=1"; params = {}
    if search.strip(): sql += " AND (o.company ILIKE :q OR o.contact_name ILIKE :q OR o.notes ILIKE :q)"; params["q"] = f"%{search.strip()}%"
    if project_filter != "All": sql += " AND o.project_id=:p"; params["p"] = project_map[project_filter]
    if status_filter != "All": sql += " AND o.status=:s"; params["s"] = status_filter
    if owner_filter.strip(): sql += " AND o.contact_owner ILIKE :o"; params["o"] = f"%{owner_filter.strip()}%"
    sql += " ORDER BY o.id DESC"
    rows = query_df(sql, params)
    if rows.empty: st.info("No outreach contacts match the selected filters.")
    for _, r in rows.iterrows():
        render_card(safe_text(r.get("company"), "Unnamed organization"), f"{safe_text(r.get('contact_name'), 'No contact')} · Owner: {safe_text(r.get('contact_owner'), 'Unassigned')}", [r.get("status"), r.get("project_name") or "Legacy/unassigned"], f"<strong>Next:</strong> {safe_text(r.get('next_action'), 'Not defined')}")
        with st.expander("Open thread"):
            st.write(f"**Last touchpoint:** {r.get('latest_touchpoint_date') or r.get('last_touchpoint') or '—'}")
            st.write(f"**Follow-up:** {r.get('follow_up_date') or '—'}")
            st.write(f"**Notes:** {safe_text(r.get('notes'))}")
            if can_edit:
                with st.form(f"outreach_{r['id']}"):
                    status = st.selectbox("Status", status_opts[1:], index=status_opts[1:].index(r.get("status")) if r.get("status") in status_opts[1:] else 0)
                    c1, c2 = st.columns(2)
                    touch = c1.date_input("Latest touchpoint", value=parse_optional_date(r.get("latest_touchpoint_date") or r.get("last_touchpoint")))
                    follow = c2.date_input("Follow-up date", value=parse_optional_date(r.get("follow_up_date")))
                    next_action = st.text_input("Next action", r.get("next_action") or "")
                    notes = st.text_area("Notes", r.get("notes") or "")
                    note = st.text_area("Update note")
                    if st.form_submit_button("Save outreach update"):
                        update_record("outreach_contacts", int(r["id"]), {"status": status, "latest_touchpoint_date": touch, "last_touchpoint": touch.isoformat() if touch else None, "follow_up_date": follow, "next_action": next_action, "notes": notes, "updated_at": datetime.utcnow()}, actor, note or f"Outreach status moved to {status}")
                        st.rerun()
            comments_panel("outreach_contacts", int(r["id"]), actor, can_edit)
            record_timeline("outreach_contacts", int(r["id"]))

# -----------------------------
# Notifications
# -----------------------------
elif page == "Notifications":
    st.markdown("### Notifications")
    notifications = query_df("SELECT * FROM notifications WHERE recipient_user_id=:uid ORDER BY is_read,created_at DESC LIMIT 300", {"uid": actor_id})
    if notifications.empty:
        st.info("You have no notifications.")
    else:
        if st.button("Mark all as read"):
            execute("UPDATE notifications SET is_read=TRUE WHERE recipient_user_id=:uid", {"uid": actor_id})
            st.rerun()
        for _, n in notifications.iterrows():
            badge = "Unread" if not n.get("is_read") else "Read"
            render_card(safe_text(n.get("title")), str(n.get("created_at")), [badge, n.get("entity_type") or "General"], safe_text(n.get("body"), ""))
            if not n.get("is_read") and st.button("Mark read", key=f"notif_{n['id']}"):
                execute("UPDATE notifications SET is_read=TRUE WHERE id=:id AND recipient_user_id=:uid", {"id": int(n["id"]), "uid": actor_id})
                st.rerun()

# -----------------------------
# Messages
# -----------------------------
elif page == "Messages":
    st.markdown("### Direct messages")
    compose, inbox, sent = st.tabs(["Compose", "Inbox", "Sent"])
    with compose:
        users = user_options()
        users = {label: uid for label, uid in users.items() if uid != actor_id}
        with st.form("compose_message"):
            recipient_label = st.selectbox("Recipient", list(users) if users else ["No available users"])
            subject = st.text_input("Subject")
            body = st.text_area("Message")
            if st.form_submit_button("Send message", type="primary"):
                if not users or recipient_label not in users:
                    st.error("Select a recipient.")
                elif not body.strip():
                    st.error("Message cannot be empty.")
                else:
                    recipient_id = users[recipient_label]
                    msg_id = insert_record("direct_messages", {"sender_user_id": actor_id, "recipient_user_id": recipient_id, "subject": subject.strip(), "body": body.strip()}, actor, f"Direct message sent to user {recipient_id}")
                    create_notification(recipient_id, f"New message from {actor}", subject.strip() or body.strip()[:80], "direct_messages", msg_id, actor_id, "Messages")
                    st.success("Message sent.")
                    st.rerun()
    with inbox:
        messages = query_df("""SELECT m.*,u.display_name sender_name,u.email sender_email FROM direct_messages m JOIN users u ON u.id=m.sender_user_id WHERE m.recipient_user_id=:uid ORDER BY m.is_read,m.created_at DESC""", {"uid": actor_id})
        if messages.empty: st.caption("Inbox is empty.")
        for _, m in messages.iterrows():
            render_card(safe_text(m.get("subject"), "No subject"), f"From {safe_text(m.get('sender_name'))} · {m.get('created_at')}", ["Unread" if not m.get("is_read") else "Read"], safe_text(m.get("body"), ""))
            with st.expander("Open and reply"):
                if not m.get("is_read"):
                    execute("UPDATE direct_messages SET is_read=TRUE WHERE id=:id AND recipient_user_id=:uid", {"id": int(m["id"]), "uid": actor_id})
                with st.form(f"reply_{m['id']}"):
                    reply = st.text_area("Reply")
                    if st.form_submit_button("Send reply") and reply.strip():
                        reply_id = insert_record("direct_messages", {"sender_user_id": actor_id, "recipient_user_id": int(m["sender_user_id"]), "subject": f"Re: {m.get('subject') or 'Message'}", "body": reply.strip(), "parent_message_id": int(m["id"])}, actor, f"Reply sent to user {m['sender_user_id']}")
                        create_notification(int(m["sender_user_id"]), f"Reply from {actor}", reply.strip()[:100], "direct_messages", reply_id, actor_id, "Messages")
                        st.rerun()
    with sent:
        messages = query_df("""SELECT m.*,u.display_name recipient_name,u.email recipient_email FROM direct_messages m JOIN users u ON u.id=m.recipient_user_id WHERE m.sender_user_id=:uid ORDER BY m.created_at DESC""", {"uid": actor_id})
        if messages.empty: st.caption("No sent messages.")
        for _, m in messages.iterrows():
            render_card(safe_text(m.get("subject"), "No subject"), f"To {safe_text(m.get('recipient_name'))} · {m.get('created_at')}", ["Read" if m.get("is_read") else "Unread"], safe_text(m.get("body"), ""))

# -----------------------------
# Analytics & readiness
# -----------------------------
elif page == "Analytics & Readiness":
    st.markdown("### Baseline, benefits and readiness")
    project_map=project_options()
    if not project_map: st.info("Create a project first.")
    else:
        p_name=st.selectbox("Project",list(project_map)); pid=project_map[p_name]
        tabs=st.tabs(["Benefits","Readiness criteria","Validation results"])
        with tabs[0]:
            if has_permission("readiness.write"):
                with st.form("metric_new"):
                    c1,c2,c3=st.columns(3); metric=c1.text_input("Metric"); baseline=c2.number_input("Baseline",value=0.0); improved=c3.number_input("Current / improved",value=0.0)
                    unit=c1.text_input("Unit"); method=st.text_input("Measurement method")
                    if st.form_submit_button("Add metric") and metric:
                        insert_record("baseline_metrics",{"project_id":pid,"metric_name":metric,"baseline_value":baseline,"improved_value":improved,"unit":unit,"measurement_method":method,"recorded_by":actor},actor,f"Baseline metric '{metric}' added");st.rerun()
            metrics=query_df("SELECT * FROM baseline_metrics WHERE project_id=:p ORDER BY id",{"p":pid})
            if metrics.empty: st.caption("No baseline metrics yet.")
            else:
                display=metrics[["metric_name","baseline_value","improved_value","unit","measurement_method"]].copy()
                display["improvement_%"] = display.apply(lambda r: ((float(r["baseline_value"])-float(r["improved_value"]))/float(r["baseline_value"])*100) if r["baseline_value"] not in [None,0] else None,axis=1)
                st.dataframe(display,use_container_width=True,hide_index=True)
        with tabs[1]:
            if has_permission("readiness.write"):
                with st.form("criterion_new"):
                    c1,c2,c3=st.columns(3); category=c1.selectbox("Category",["Technical","Operational","Evidence","Issues","Usability","Integration"]); name=c2.text_input("Criterion"); op=c3.selectbox("Operator",[">=","<=","=","boolean"])
                    target=c1.number_input("Target",value=0.0); actual=c2.number_input("Actual",value=0.0); unit=c3.text_input("Unit"); mandatory=st.checkbox("Mandatory gate")
                    if st.form_submit_button("Add criterion") and name:
                        passed=(actual>=target if op==">=" else actual<=target if op=="<=" else actual==target)
                        insert_record("readiness_criteria",{"project_id":pid,"category":category,"criterion_name":name,"operator":op,"target_value":target,"actual_value":actual,"unit":unit,"mandatory":mandatory,"status":"Passed" if passed else "Failed"},actor,f"Readiness criterion '{name}' added");st.rerun()
            crit=query_df("SELECT * FROM readiness_criteria WHERE project_id=:p ORDER BY mandatory DESC,id",{"p":pid})
            if crit.empty: st.caption("No criteria defined.")
            else:
                passed=int((crit["status"]=="Passed").sum()); failed=len(crit)-passed; mandatory_failed=int(((crit["mandatory"]==True)&(crit["status"]!="Passed")).sum())
                c=st.columns(4);c[0].metric("Criteria",len(crit));c[1].metric("Passed",passed);c[2].metric("Failed",failed);c[3].metric("Mandatory failures",mandatory_failed)
                recommendation="Not ready" if mandatory_failed else ("Ready" if failed==0 else "Conditionally ready")
                st.markdown(f"### Recommendation: **{recommendation}**")
                st.dataframe(crit[["category","criterion_name","operator","target_value","actual_value","unit","mandatory","status"]],use_container_width=True,hide_index=True)
        with tabs[2]:
            gt=query_df("SELECT * FROM ground_truth_logs WHERE project_id=:p ORDER BY id DESC",{"p":pid})
            if gt.empty: st.caption("No linked validation results. Legacy records can be linked from Administration.")
            else:
                rows=[]
                for _,r in gt.iterrows():
                    obs=float(r.get("observed_cycle_count") or 0);fp=float(r.get("false_positives") or 0);fn=float(r.get("false_negatives") or 0);tp=max(obs-fn,0)
                    rows.append({"run":r.get("run_id"),"precision":tp/(tp+fp) if tp+fp else None,"recall":tp/obs if obs else None,"false_positives":fp,"false_negatives":fn,"mismatches":r.get("mismatch_count")})
                st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

# -----------------------------
# Reports
# -----------------------------
elif page == "Reports":
    st.markdown("### Operational reports")
    pmap=project_options()
    if not pmap: st.info("Create a project first.")
    else:
        pname=st.selectbox("Project",list(pmap));pid=pmap[pname]
        project=fetch_one("SELECT * FROM projects WHERE id=:p",{"p":pid})
        work=query_df("SELECT * FROM workstreams WHERE project_id=:p",{"p":pid}); tasks=query_df("SELECT * FROM tasks WHERE project_id=:p",{"p":pid})
        trials=query_df("SELECT * FROM trials WHERE project_id=:p",{"p":pid}); issues=query_df("SELECT * FROM issue_logs WHERE project_id=:p",{"p":pid})
        evidence=query_df("SELECT * FROM evidence_items WHERE project_id=:p",{"p":pid}); risks=query_df("SELECT * FROM risks WHERE project_id=:p",{"p":pid})
        open_tasks=0 if tasks.empty else int((~tasks['status'].astype(str).str.lower().isin(['completed','closed'])).sum())
        open_issues=0 if issues.empty else int((~issues['status'].astype(str).str.lower().isin(['verified','closed'])).sum())
        verified_evidence=0 if evidence.empty else int((evidence['verification_status']=='Verified').sum())
        report=f"""# {project.get('name')} — Validation Operations Report

Generated: {datetime.now().isoformat()}

## Executive status
- Phase: {project.get('phase')}
- Status: {project.get('status')}
- Owner: {project.get('owner')}
- Readiness: {project.get('readiness_level')}
- Target date: {project.get('target_date')}

## Delivery portfolio
- Workstreams: {len(work)}
- Open tasks: {open_tasks}
- Trials: {len(trials)}
- Open issues: {open_issues}
- Evidence records: {len(evidence)}
- Verified evidence: {verified_evidence}
- Open risks: {0 if risks.empty else int((risks['status']!='Closed').sum())}

## Objectives
{project.get('objectives') or 'Not defined'}

## Success criteria
{project.get('success_criteria') or 'Not defined'}
"""
        st.download_button("Download management report",report,file_name=f"{project.get('code') or 'project'}_validation_report.md",mime="text/markdown",type="primary")
        st.markdown(report)
        st.markdown("#### Issue register")
        if not issues.empty: st.dataframe(issues[[c for c in ['issue_id','title','severity','priority','status','owner','target_fix_version'] if c in issues]],use_container_width=True,hide_index=True)
        st.markdown("#### Trial register")
        if not trials.empty: st.dataframe(trials[[c for c in ['trial_name','environment','trial_owner','planned_date','status','model_version','validation_level'] if c in trials]],use_container_width=True,hide_index=True)

# -----------------------------
# Activity
# -----------------------------
elif page == "Activity":
    st.markdown("### Audit trail")
    entity=st.text_input("Filter entity type")
    actor_filter=st.text_input("Filter person")
    sql="SELECT * FROM activity_log WHERE 1=1"; params={}
    if entity: sql+=" AND entity_type ILIKE :e"; params["e"]=f"%{entity}%"
    if actor_filter: sql+=" AND performed_by ILIKE :a"; params["a"]=f"%{actor_filter}%"
    sql+=" ORDER BY created_at DESC LIMIT 500"
    st.dataframe(query_df(sql,params),use_container_width=True,hide_index=True)

# -----------------------------
# Administration / migration
# -----------------------------
elif page == "Administration":
    if current_user["role"] != "Administrator":
        st.error("Administrator access is required.")
        st.stop()
    st.markdown("### Administration and migration safety")
    st.warning("All schema changes in this version are additive. Existing populated records are preserved; no table is dropped, truncated, or cleared.")

    users_tab, admins_tab, data_tab = st.tabs(["User approvals", "Administrators", "Data safety"])
    with users_tab:
        user_df = query_df("""SELECT id,display_name,email,role,access_level,active,last_login_at,created_at FROM users WHERE role='User' ORDER BY created_at DESC""")
        if user_df.empty:
            st.info("No normal user accounts exist yet.")
        else:
            s1, s2 = st.columns(2)
            user_search = s1.text_input("Search users", placeholder="Name or email")
            access_filter = s2.selectbox("Access", ["All", "Read", "Write", "Inactive"])
            filtered = user_df.copy()
            if user_search.strip():
                mask = filtered["display_name"].astype(str).str.contains(user_search, case=False, na=False) | filtered["email"].astype(str).str.contains(user_search, case=False, na=False)
                filtered = filtered[mask]
            if access_filter == "Inactive": filtered = filtered[filtered["active"] == False]
            elif access_filter != "All": filtered = filtered[(filtered["access_level"] == access_filter) & (filtered["active"] == True)]
            st.dataframe(filtered, use_container_width=True, hide_index=True)
            if not filtered.empty:
                user_map = {f"{r['display_name']} · {r['email']} · {r['access_level']}": int(r['id']) for _, r in filtered.iterrows()}
                selected_user = st.selectbox("Select user", list(user_map))
                selected_record = fetch_one("SELECT * FROM users WHERE id=:id", {"id": user_map[selected_user]})
                memberships = query_df("""SELECT t.name,tm.team_role,tm.active FROM team_memberships tm JOIN teams t ON t.id=tm.team_id WHERE tm.user_id=:u ORDER BY t.name""", {"u": selected_record["id"]})
                if not memberships.empty:
                    st.markdown("**Team memberships**")
                    st.dataframe(memberships, use_container_width=True, hide_index=True)
                access_options = ["Read", "Write"]
                current_access = selected_record.get("access_level") if selected_record.get("access_level") in access_options else "Read"
                new_access = st.selectbox("Access level", access_options, index=access_options.index(current_access))
                active_user = st.checkbox("Account active", value=bool(selected_record.get("active")))
                if st.button("Save user access", type="primary"):
                    old_access = selected_record.get("access_level") or "Read"
                    old_active = bool(selected_record.get("active"))
                    selected_id = int(selected_record["id"])
                    update_record("users", selected_id, {"role": "User", "access_level": new_access, "active": active_user, "updated_at": datetime.utcnow()}, actor, f"User access updated for {selected_record['email']}")
                    if not active_user:
                        execute("UPDATE app_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE user_id=:uid AND revoked_at IS NULL", {"uid": selected_id})
                    message = f"Your ValidationOps access changed from {old_access} to {new_access}. Account status: {'Active' if active_user else 'Inactive'}."
                    if old_access != new_access or old_active != active_user:
                        create_notification(selected_id, "Account permission updated", message, "users", selected_id, actor_id, "Dashboard")
                    st.success("User access updated and the user was notified.")
                    st.rerun()

    with admins_tab:
        admin_count = active_administrator_count()
        st.info(f"Active administrators: {admin_count} of 2. Public registration creates User accounts with Read access only.")
        admins = query_df("SELECT id,display_name,email,access_level,active,last_login_at,created_at FROM users WHERE role='Administrator' ORDER BY created_at")
        st.dataframe(admins, use_container_width=True, hide_index=True)
        if admin_count < 2:
            with st.expander("Create second administrator", expanded=True):
                with st.form("create_second_admin"):
                    second_name = st.text_input("Full name")
                    second_email = st.text_input("Email")
                    second_password = st.text_input("Temporary password", type="password")
                    second_confirm = st.text_input("Confirm temporary password", type="password")
                    second_code = st.text_input("Bootstrap code", type="password")
                    create_second = st.form_submit_button("Create second administrator", type="primary")
                if create_second:
                    normalized = second_email.strip().lower()
                    if active_administrator_count() >= 2: st.error("Two active administrators already exist.")
                    elif not bootstrap_secret() or not hmac.compare_digest(second_code, bootstrap_secret()): st.error("Invalid bootstrap code.")
                    elif not second_name.strip() or "@" not in normalized: st.error("Enter a valid name and email address.")
                    elif len(second_password) < 12: st.error("Use a password with at least 12 characters.")
                    elif second_password != second_confirm: st.error("Passwords do not match.")
                    elif fetch_one("SELECT id FROM users WHERE LOWER(email)=LOWER(:email)", {"email": normalized}): st.error("An account already exists with that email.")
                    else:
                        insert_record("users", {"email": normalized, "display_name": second_name.strip(), "password_hash": ph.hash(second_password), "role": "Administrator", "access_level": "Write", "active": True}, actor, f"Second administrator created: {normalized}")
                        st.rerun()

    with data_tab:
        tables = ["project_status", "outreach_contacts", "trials", "ground_truth_logs", "issue_logs", "ux_test_logs", "readiness_handoffs", "projects", "teams", "team_memberships", "workstreams", "tasks", "evidence_items", "activity_log", "users", "app_sessions", "project_memberships", "notifications", "direct_messages"]
        counts = []
        for table in tables:
            if table_exists(table):
                row = fetch_one(f"SELECT COUNT(*) AS n FROM {table}")
                counts.append({"Table": table, "Rows": row["n"]})
        st.dataframe(pd.DataFrame(counts), use_container_width=True, hide_index=True)
        st.markdown("#### Link existing legacy records to a project")
        pmap = project_options()
        if pmap:
            p_name = st.selectbox("Target project", list(pmap)); pid = pmap[p_name]
            c1, c2, c3 = st.columns(3)
            if c1.button("Link unassigned trials"):
                result = execute("UPDATE trials SET project_id=:p WHERE project_id IS NULL", {"p": pid}); st.success(f"Linked {result.rowcount} trials.")
            if c2.button("Link unassigned issues"):
                result = execute("UPDATE issue_logs SET project_id=:p WHERE project_id IS NULL", {"p": pid}); st.success(f"Linked {result.rowcount} issues.")
            if c3.button("Link unassigned outreach"):
                result = execute("UPDATE outreach_contacts SET project_id=:p WHERE project_id IS NULL", {"p": pid}); st.success(f"Linked {result.rowcount} outreach records.")
        st.markdown("#### Legacy data view")
        existing_tables = [t for t in tables if table_exists(t)]
        selected = st.selectbox("Table", existing_tables)
        st.dataframe(query_df(f"SELECT * FROM {selected} ORDER BY id"), use_container_width=True, hide_index=True)

st.divider()
st.caption("IntelliAware ValidationOps v7 — additive team membership, full workflow editing, approvals, notifications and messaging.")