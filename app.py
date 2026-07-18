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
    """
    execute(alter_sql)


def table_exists(name: str) -> bool:
    row = fetch_one("SELECT to_regclass(:name) AS t", {"name": f"public.{name}"})
    return bool(row and row["t"])


# -----------------------------
# Utilities
# -----------------------------
def normalize_evidence_url(value: str | None) -> str | None:
    """Return a safe HTTP(S) evidence URL, or None when the value is unusable."""
    if value is None:
        return None

    url = str(value).strip()
    if not url:
        return None

    # Local file paths cannot be opened by users from Streamlit Cloud.
    lowered = url.lower()
    if lowered.startswith(("file://", "localhost", "127.0.0.1")) or \
       (len(url) >= 3 and url[1:3] in {":\\", ":/"}):
        return None

    if not lowered.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    return url


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
                insert_record("comments", {"entity_type": entity_type, "entity_id": entity_id, "body": body, "author": actor, "author_user_id": (st.session_state.get("current_user") or {}).get("id")}, actor, "Comment added")
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
    project_map=project_options(); teams=team_options()
    st.markdown("### Workstreams and teams")
    top1,top2=st.tabs(["Workstreams","Teams"])
    with top1:
        if not project_map: st.info("Create a project first.")
        else:
            selected_project=st.selectbox("Project", list(project_map)); pid=project_map[selected_project]
            if can_edit:
                with st.expander("Add workstream"):
                    with st.form("add_workstream"):
                        c1,c2=st.columns(2); name=c1.text_input("Name"); work_users=user_options(); owner_label=c2.selectbox("Owner", list(work_users)) if work_users else None; owner_user_id=work_users.get(owner_label) if owner_label else None; owner=(user_by_id(owner_user_id) or {}).get("display_name", "")
                        team_name=c1.selectbox("Team", ["Unassigned"]+list(teams)); priority=c2.selectbox("Priority",["Low","Medium","High","Critical"],index=1)
                        due=c1.date_input("Due date",value=None); description=st.text_area("Description"); deps=st.text_area("Dependencies / blockers")
                        if st.form_submit_button("Create workstream") and name:
                            insert_record("workstreams",{"project_id":pid,"name":name,"owner":owner,"owner_user_id":owner_user_id,"team_id":teams.get(team_name),"priority":priority,"due_date":due,"description":description,"dependency_notes":deps},actor,f"Workstream '{name}' created")
                            st.rerun()
            ws=query_df("SELECT w.*, t.name AS team_name FROM workstreams w LEFT JOIN teams t ON t.id=w.team_id WHERE w.project_id=:p ORDER BY w.id DESC",{"p":pid})
            for _,r in ws.iterrows():
                render_card(r["name"],f"Owner: {r.get('owner') or 'Unassigned'} · Team: {r.get('team_name') or 'Unassigned'}",[r.get("status"),r.get("priority"),f"{r.get('progress') or 0}%"],r.get("dependency_notes") or "")
                if can_edit:
                    with st.expander(f"Update {r['name']}"):
                        with st.form(f"ws_{r['id']}"):
                            status=st.selectbox("Status",["Backlog","Ready","In progress","Blocked","Under review","Completed"],key=f"wss{r['id']}")
                            progress=st.slider("Progress",0,100,int(r.get("progress") or 0),key=f"wsp{r['id']}")
                            owner=st.text_input("Owner",r.get("owner") or "",key=f"wso{r['id']}")
                            if st.form_submit_button("Save"):
                                update_record("workstreams",int(r["id"]),{"status":status,"progress":progress,"owner":owner,"updated_at":datetime.utcnow()},actor,f"Workstream '{r['name']}' updated")
                                st.rerun()
    with top2:
        if can_edit:
            with st.expander("Create team"):
                with st.form("create_team"):
                    name=st.text_input("Team name"); lead=st.text_input("Team lead"); purpose=st.text_area("Purpose")
                    if st.form_submit_button("Create team") and name:
                        insert_record("teams",{"name":name,"lead_name":lead,"purpose":purpose},actor,f"Team '{name}' created"); st.rerun()
        team_df=query_df("SELECT * FROM teams ORDER BY name")
        for _,r in team_df.iterrows(): render_card(r["name"],f"Lead: {r.get('lead_name') or 'Unassigned'}",[r.get("status")],r.get("purpose") or "")

# -----------------------------
# My Work / tasks
# -----------------------------
elif page == "My Work":
    project_map = project_options()
    users = user_options()
    st.markdown("### My Work")
    st.caption("Tasks are loaded automatically from your authenticated account. No name matching is used.")

    if has_permission("task.write") and project_map:
        with st.expander("Create task"):
            with st.form("create_task"):
                p_name = st.selectbox("Project", list(project_map)); pid = project_map[p_name]
                ws_df = query_df("SELECT id,name FROM workstreams WHERE project_id=:p ORDER BY name", {"p": pid})
                ws_map = {r['name']: int(r['id']) for _, r in ws_df.iterrows()}
                c1, c2 = st.columns(2)
                title = c1.text_input("Task title")
                assignee_label = c2.selectbox("Assignee", list(users), index=list(users.values()).index(actor_id) if actor_id in users.values() else 0) if users else None
                ws_name = c1.selectbox("Workstream", ["None"] + list(ws_map))
                priority = c2.selectbox("Priority", ["Low", "Medium", "High", "Critical"], index=1)
                due = c1.date_input("Due date", value=None)
                description = st.text_area("Description")
                criteria = st.text_area("Completion criteria")
                if st.form_submit_button("Create task") and title and assignee_label:
                    assignee_user_id = users[assignee_label]
                    assignee_user = user_by_id(assignee_user_id)
                    insert_record("tasks", {
                        "project_id": pid,
                        "workstream_id": ws_map.get(ws_name),
                        "title": title,
                        "assignee": assignee_user["display_name"],
                        "assignee_user_id": assignee_user_id,
                        "priority": priority,
                        "due_date": due,
                        "description": description,
                        "completion_criteria": criteria,
                    }, actor, f"Task '{title}' created and assigned to {assignee_user['display_name']}")
                    st.rerun()

    tasks = query_df("""
        SELECT tk.*, p.name project_name, w.name workstream_name
        FROM tasks tk
        LEFT JOIN projects p ON p.id=tk.project_id
        LEFT JOIN workstreams w ON w.id=tk.workstream_id
        WHERE tk.assignee_user_id=:uid
        ORDER BY tk.due_date NULLS LAST, tk.id DESC
    """, {"uid": actor_id})

    if tasks.empty:
        st.info("No tasks are currently assigned to your account.")
    for _, r in tasks.iterrows():
        due_text = str(r.get("due_date") or "No due date")
        render_card(r["title"], f"{r.get('project_name') or 'No project'} · {r.get('workstream_name') or 'No workstream'}", [r.get("status"), r.get("priority"), due_text], r.get("description") or "")
        if has_permission("task.write"):
            with st.expander("Update task", expanded=False):
                with st.form(f"task_{r['id']}"):
                    status = st.selectbox("Status", ["Backlog", "Ready", "In progress", "Blocked", "Under review", "Completed"], index=["Backlog", "Ready", "In progress", "Blocked", "Under review", "Completed"].index(r.get("status")) if r.get("status") in ["Backlog", "Ready", "In progress", "Blocked", "Under review", "Completed"] else 0)
                    note = st.text_area("Update note", key=f"tn{r['id']}")
                    if st.form_submit_button("Save update"):
                        vals = {"status": status, "updated_at": datetime.utcnow()}
                        if status == "Completed":
                            vals["completed_at"] = datetime.utcnow()
                        update_record("tasks", int(r["id"]), vals, actor, note or f"Task '{r['title']}' updated")
                        st.rerun()

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
    project_map=project_options()
    if has_permission("trial.write"):
        with st.expander("Plan trial"):
            with st.form("create_trial"):
                p_name=st.selectbox("Project",["Unassigned"]+list(project_map)); pid=project_map.get(p_name)
                c1,c2=st.columns(2); name=c1.text_input("Trial name"); trial_users=user_options(); owner_label=c2.selectbox("Owner", list(trial_users), index=list(trial_users.values()).index(actor_id) if actor_id in trial_users.values() else 0) if trial_users else None; trial_owner_user_id=trial_users.get(owner_label) if owner_label else None; owner=(user_by_id(trial_owner_user_id) or {}).get("display_name", actor)
                environment=c1.text_input("Environment / site"); process=c2.text_input("Process type")
                planned=c1.date_input("Planned date",value=None); model=c2.text_input("Model/software version")
                level=c1.selectbox("Validation level",["Simulated","Controlled lab","Shadow factory","Operational pilot","Production readiness"])
                criteria=st.text_area("Success criteria"); notes=st.text_area("Notes")
                if st.form_submit_button("Create trial") and name:
                    insert_record("trials",{"trial_name":name,"project_id":pid,"environment":environment,"process_type":process,"trial_owner":owner,"trial_owner_user_id":trial_owner_user_id,"planned_date":planned,"status":"Draft","success_criteria":criteria,"notes":notes,"model_version":model,"validation_level":level},actor,f"Trial '{name}' created")
                    st.rerun()
    trials=query_df("SELECT tr.*,p.name project_name FROM trials tr LEFT JOIN projects p ON p.id=tr.project_id ORDER BY tr.id DESC")
    for _,r in trials.iterrows():
        render_card(r.get("trial_name") or f"Trial {r['id']}",f"{r.get('project_name') or 'Legacy/unassigned'} · Owner: {r.get('trial_owner') or 'Unassigned'}",[r.get("status"),r.get("validation_level") or "Legacy",r.get("model_version") or "Version not set"],r.get("success_criteria") or "")
        with st.expander("Open trial"):
            c1,c2=st.columns([1,1])
            with c1:
                st.write(f"**Environment:** {r.get('environment') or '—'}")
                st.write(f"**Process:** {r.get('process_type') or '—'}")
                st.write(f"**Planned:** {r.get('planned_date') or '—'}")
                st.write(f"**Notes:** {r.get('notes') or '—'}")
            with c2:
                gt=query_df("SELECT * FROM ground_truth_logs WHERE trial_id=:id OR (trial_id IS NULL AND run_id=:run)",{"id":int(r['id']),"run":r.get('trial_name')})
                if not gt.empty:
                    row=gt.iloc[-1]; obs=float(row.get("observed_cycle_count") or 0); fp=float(row.get("false_positives") or 0); fn=float(row.get("false_negatives") or 0); tp=max(obs-fn,0)
                    precision=tp/(tp+fp) if tp+fp else 0; recall=tp/obs if obs else 0
                    m=st.columns(3);m[0].metric("Precision",f"{precision:.1%}");m[1].metric("Recall",f"{recall:.1%}");m[2].metric("Mismatches",int(row.get("mismatch_count") or 0))
                else: st.caption("No linked validation-run results yet.")
            if has_permission("trial.write"):
                with st.form(f"trial_update_{r['id']}"):
                    status=st.selectbox("Status",["Draft","Planned","Approved","Setup in progress","Ready to run","Running","Evidence review","Analysis","Completed","Archived"],key=f"trs{r['id']}")
                    note=st.text_area("Update note",key=f"trn{r['id']}")
                    if st.form_submit_button("Update trial"):
                        update_record("trials",int(r["id"]),{"status":status,"updated_at":datetime.utcnow()},actor,note or f"Trial status changed to {status}");st.rerun()
            record_timeline("trials",int(r["id"]))

# -----------------------------
# Evidence
# -----------------------------
elif page == "Evidence":
    st.markdown("### Evidence registry")
    pmap=project_options()
    if has_permission("evidence.write"):
        with st.expander("Register evidence"):
            with st.form("evidence_create"):
                p_name=st.selectbox("Project",["Unassigned"]+list(pmap));pid=pmap.get(p_name)
                c1,c2=st.columns(2); title=c1.text_input("Evidence title"); etype=c2.selectbox("Type",["Video","Image","Model output","Sensor log","Ground truth","Calibration","Operator feedback","Report","Other"])
                source=c1.text_input("Source / system"); uri=c2.text_input("File or repository link")
                version=c1.text_input("Model/software version"); status=c2.selectbox("Verification status",["Expected","Submitted","Under review","Verified","Rejected","Superseded"])
                desc=st.text_area("Description")
                if st.form_submit_button("Register evidence", type="primary"):
                    normalized_uri = normalize_evidence_url(uri)
                    if not title.strip():
                        st.error("Evidence title is required.")
                    elif uri.strip() and not normalized_uri:
                        st.error("Enter a valid public HTTP(S) link, or leave the link field blank. Local computer paths cannot be opened from Streamlit Cloud.")
                    else:
                        insert_record(
                            "evidence_items",
                            {
                                "project_id": pid,
                                "title": title.strip(),
                                "evidence_type": etype,
                                "source": source.strip(),
                                "uri": normalized_uri,
                                "model_version": version.strip(),
                                "verification_status": status,
                                "description": desc.strip(),
                                "uploaded_by": actor,
                                "uploaded_by_user_id": actor_id,
                            },
                            actor,
                            f"Evidence '{title.strip()}' registered",
                        )
                        st.success("Evidence registered.")
                        st.rerun()
    f1,f2=st.columns(2); project_filter=f1.selectbox("Project filter",["All"]+list(pmap)); status_filter=f2.selectbox("Verification",["All","Expected","Submitted","Under review","Verified","Rejected","Superseded"])
    sql="SELECT e.*,p.name project_name FROM evidence_items e LEFT JOIN projects p ON p.id=e.project_id WHERE 1=1";params={}
    if project_filter!="All":sql+=" AND e.project_id=:p";params['p']=pmap[project_filter]
    if status_filter!="All":sql+=" AND e.verification_status=:s";params['s']=status_filter
    sql+=" ORDER BY e.id DESC"
    edf=query_df(sql,params)
    if edf.empty: st.markdown('<div class="empty-state">No evidence records match this view.</div>',unsafe_allow_html=True)
    for _, r in edf.iterrows():
        evidence_url = normalize_evidence_url(r.get("uri"))
        if evidence_url:
            safe_url = html.escape(evidence_url, quote=True)
            link = f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">Open evidence</a>'
        elif str(r.get("uri") or "").strip():
            link = "Invalid or inaccessible evidence link"
        else:
            link = "No external file linked"

        render_card(
            r["title"],
            f"{r.get('project_name') or 'Unassigned'} · Uploaded by {r.get('uploaded_by') or 'Unknown'}",
            [r.get("evidence_type"), r.get("verification_status"), r.get("model_version") or "No version"],
            f"{r.get('description') or ''}<br>{link}",
        )
        if has_permission("evidence.write"):
            with st.expander("Review evidence"):
                with st.form(f"ev_{r['id']}"):
                    status=st.selectbox("Verification status",["Expected","Submitted","Under review","Verified","Rejected","Superseded"],key=f"evs{r['id']}")
                    verify_users=user_options(); verifier_label=st.selectbox("Verified/reviewed by", list(verify_users), index=list(verify_users.values()).index(actor_id) if actor_id in verify_users.values() else 0, key=f"evv{r['id']}") if verify_users else None; verified_by_user_id=verify_users.get(verifier_label) if verifier_label else None; verifier=(user_by_id(verified_by_user_id) or {}).get("display_name", actor)
                    note=st.text_area("Review note",key=f"evn{r['id']}")
                    if st.form_submit_button("Save review"):
                        update_record("evidence_items",int(r['id']),{"verification_status":status,"verified_by":verifier,"verified_by_user_id":verified_by_user_id},actor,note or f"Evidence moved to {status}");st.rerun()

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
    project_map=project_options()
    if can_edit:
        with st.expander("Add outreach thread"):
            with st.form("outreach_new"):
                p_name=st.selectbox("Project",["Unassigned"]+list(project_map)); pid=project_map.get(p_name)
                c1,c2=st.columns(2); company=c1.text_input("Company"); contact=c2.text_input("Contact name")
                outreach_users=user_options(); owner_label=c1.selectbox("Owner", list(outreach_users), index=list(outreach_users.values()).index(actor_id) if actor_id in outreach_users.values() else 0) if outreach_users else None; contact_owner_user_id=outreach_users.get(owner_label) if owner_label else None; owner=(user_by_id(contact_owner_user_id) or {}).get("display_name", actor); process=c2.text_input("Process / topic")
                next_action=st.text_input("Next action"); notes=st.text_area("Notes")
                if st.form_submit_button("Create outreach thread") and company:
                    insert_record("outreach_contacts",{"project_id":pid,"company":company,"contact_name":contact,"contact_owner":owner,"contact_owner_user_id":contact_owner_user_id,"process_type":process,"status":"Identified","next_action":next_action,"notes":notes,"last_touchpoint":"Thread created"},actor,f"Outreach thread for {company} created");st.rerun()
    rows=query_df("SELECT o.*,p.name project_name FROM outreach_contacts o LEFT JOIN projects p ON p.id=o.project_id ORDER BY o.id DESC")
    for _,r in rows.iterrows():
        render_card(r.get("company") or "Unnamed organization",f"{r.get('contact_name') or 'No contact'} · Owner: {r.get('contact_owner') or 'Unassigned'}",[r.get("status"),r.get("project_name") or "Legacy/unassigned"],f"<strong>Next:</strong> {r.get('next_action') or 'Not defined'}")
        with st.expander("Open thread"):
            st.write(f"**Last touchpoint:** {r.get('last_touchpoint') or '—'}")
            st.write(f"**Follow-up:** {r.get('follow_up_date') or '—'}")
            st.write(f"**Notes:** {r.get('notes') or '—'}")
            if can_edit:
                with st.form(f"outreach_{r['id']}"):
                    status=st.selectbox("Status",["Identified","Contact pending","Contacted","Follow-up due","Response received","Meeting scheduled","Access confirmed","Closed"],key=f"os{r['id']}")
                    touch=st.text_input("Latest touchpoint",key=f"ot{r['id']}")
                    next_action=st.text_input("Next action",r.get("next_action") or "",key=f"on{r['id']}")
                    note=st.text_area("Update note",key=f"ou{r['id']}")
                    if st.form_submit_button("Add update"):
                        update_record("outreach_contacts",int(r["id"]),{"status":status,"last_touchpoint":touch or r.get("last_touchpoint"),"next_action":next_action,"updated_at":datetime.utcnow()},actor,note or f"Outreach status moved to {status}");st.rerun()
            comments_panel("outreach_contacts",int(r["id"]),actor,can_edit)
            record_timeline("outreach_contacts",int(r["id"]))

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
    st.warning("This page never drops or clears populated legacy tables. Use a Neon branch or export before any schema change.")

    st.markdown("#### User accounts and access")
    admin_count = active_administrator_count()
    st.info(f"Active administrators: {admin_count} of 2. Public registration creates User accounts with Read access only.")

    if admin_count < 2:
        with st.expander("Create second administrator", expanded=True):
            st.caption("Only an existing administrator can create the second administrator. This section disappears after two administrators exist.")
            with st.form("create_second_admin"):
                second_name = st.text_input("Full name")
                second_email = st.text_input("Email")
                second_password = st.text_input("Temporary password", type="password")
                second_confirm = st.text_input("Confirm temporary password", type="password")
                second_code = st.text_input("Bootstrap code", type="password")
                create_second = st.form_submit_button("Create second administrator", type="primary")
            if create_second:
                normalized = second_email.strip().lower()
                if active_administrator_count() >= 2:
                    st.error("Two active administrators already exist.")
                elif not bootstrap_secret() or not hmac.compare_digest(second_code, bootstrap_secret()):
                    st.error("Invalid bootstrap code.")
                elif not second_name.strip() or "@" not in normalized:
                    st.error("Enter a valid name and email address.")
                elif len(second_password) < 12:
                    st.error("Use a password with at least 12 characters.")
                elif second_password != second_confirm:
                    st.error("Passwords do not match.")
                elif fetch_one("SELECT id FROM users WHERE LOWER(email)=LOWER(:email)", {"email": normalized}):
                    st.error("An account already exists with that email.")
                else:
                    insert_record("users", {"email": normalized, "display_name": second_name.strip(), "password_hash": ph.hash(second_password), "role": "Administrator", "access_level": "Write", "active": True}, actor, f"Second administrator created: {normalized}")
                    st.success("Second administrator created.")
                    st.rerun()

    user_df = query_df("""
        SELECT id, display_name, email, role, access_level, active, last_login_at, created_at
        FROM users ORDER BY CASE WHEN role='Administrator' THEN 0 ELSE 1 END, display_name
    """)
    st.dataframe(user_df, use_container_width=True, hide_index=True)

    normal_users = user_df[user_df["role"] == "User"] if not user_df.empty else pd.DataFrame()
    if not normal_users.empty:
        with st.expander("Approve user access", expanded=True):
            user_map = {f"{r['display_name']} · {r['email']}": int(r['id']) for _, r in normal_users.iterrows()}
            selected_user = st.selectbox("User", list(user_map))
            selected_record = fetch_one("SELECT * FROM users WHERE id=:id", {"id": user_map[selected_user]})
            access_options = ["Read", "Write"]
            current_access = selected_record.get("access_level") if selected_record.get("access_level") in access_options else "Read"
            new_access = st.selectbox("Access level", access_options, index=access_options.index(current_access))
            active_user = st.checkbox("Account active", value=bool(selected_record.get("active")))
            if st.button("Save user access", type="primary"):
                selected_id = int(selected_record["id"])
                update_record("users", selected_id, {"role": "User", "access_level": new_access, "active": active_user, "updated_at": datetime.utcnow()}, actor, f"User access updated for {selected_record['email']}")
                if not active_user:
                    execute("UPDATE app_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE user_id=:uid AND revoked_at IS NULL", {"uid": selected_id})
                st.success("User access updated.")
                st.rerun()
    else:
        st.caption("No normal user accounts are available for access approval yet.")

    tables=["project_status","outreach_contacts","trials","ground_truth_logs","issue_logs","ux_test_logs","readiness_handoffs","projects","teams","workstreams","tasks","activity_log","users","app_sessions","project_memberships"]
    counts=[]
    for table in tables:
        if table_exists(table):
            row=fetch_one(f"SELECT COUNT(*) AS n FROM {table}"); counts.append({"Table":table,"Rows":row["n"]})
    st.dataframe(pd.DataFrame(counts),use_container_width=True,hide_index=True)

    if can_edit:
        st.markdown("#### Link existing legacy records to a project")
        pmap=project_options()
        if pmap:
            p_name=st.selectbox("Target project",list(pmap));pid=pmap[p_name]
            c1,c2,c3=st.columns(3)
            if c1.button("Link unassigned trials"):
                result=execute("UPDATE trials SET project_id=:p WHERE project_id IS NULL",{"p":pid});st.success(f"Linked {result.rowcount} trials.")
            if c2.button("Link unassigned issues"):
                result=execute("UPDATE issue_logs SET project_id=:p WHERE project_id IS NULL",{"p":pid});st.success(f"Linked {result.rowcount} issues.")
            if c3.button("Link unassigned outreach"):
                result=execute("UPDATE outreach_contacts SET project_id=:p WHERE project_id IS NULL",{"p":pid});st.success(f"Linked {result.rowcount} outreach records.")
        st.markdown("#### Register existing rows in audit history")
        if st.button("Backfill baseline history"):
            tracked=["project_status","outreach_contacts","trials","ground_truth_logs","issue_logs","ux_test_logs","readiness_handoffs"]
            inserted=0
            with get_engine().begin() as conn:
                for table in tracked:
                    if not table_exists(table): continue
                    rows=conn.execute(text(f"SELECT * FROM {table}")).mappings().all()
                    for row in rows:
                        exists=conn.execute(text("SELECT 1 FROM record_revisions WHERE entity_type=:e AND entity_id=:i LIMIT 1"),{"e":table,"i":row["id"]}).scalar()
                        if exists: continue
                        changes={k:{"old":None,"new":clean(v)} for k,v in dict(row).items() if k!="id"}
                        log_activity(conn,table,int(row["id"]),"baseline","Existing record registered during safe migration.",actor,changes);inserted+=1
            st.success(f"Registered {inserted} existing records without modifying them.")
    st.markdown("#### Legacy data view")
    selected=st.selectbox("Table",[t for t in tables if table_exists(t)])
    st.dataframe(query_df(f"SELECT * FROM {selected} ORDER BY id"),use_container_width=True,hide_index=True)

st.divider()
st.caption("IntelliAware ValidationOps v6.1 — two-administrator self-registration, administrator-managed read/write access and user-linked workflows.")