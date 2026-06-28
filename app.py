import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import math
from io import BytesIO
import zipfile

st.set_page_config(
    page_title="IntelliAware Field Validation Kit",
    page_icon="🏭",
    layout="wide"
)

PRIMARY = "#0B1F3A"
ACCENT = "#00A6D6"

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #0B1F3A 0%, #123C69 100%);
        color: white;
        padding: 1.2rem 1.4rem;
        border-radius: 14px;
        margin-bottom: 1rem;
    }
    .metric-card {
        border: 1px solid #E3E8EF;
        border-radius: 12px;
        padding: 1rem;
        background: #FFFFFF;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .small-label {
        color: #5D6B82;
        font-size: 0.88rem;
        margin-bottom: 0.2rem;
    }
    .risk-high { color: #B42318; font-weight: 700; }
    .risk-medium { color: #B54708; font-weight: 700; }
    .risk-low { color: #067647; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Database helpers
# -----------------------------

@st.cache_resource
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"], pool_pre_ping=True)


def db_is_configured():
    try:
        _ = st.secrets["DATABASE_URL"]
        return True
    except Exception:
        return False


def run_sql(sql, params=None):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})


def read_table(table_name):
    try:
        engine = get_engine()
        return pd.read_sql(f"SELECT * FROM {table_name} ORDER BY id", engine)
    except Exception:
        return pd.DataFrame()


def clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def clear_and_insert(table_name, df, allowed_columns):
    """
    MVP-friendly save behavior:
    - Deletes existing rows in a table
    - Inserts the edited rows from Streamlit
    - Keeps table schema stable
    """
    if df is None:
        return

    working = df.copy()

    working = working[[c for c in allowed_columns if c in working.columns]]

    if not working.empty:
        working = working.dropna(how="all")

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {table_name}"))

        for _, row in working.iterrows():
            row_dict = {col: clean_value(row[col]) for col in working.columns}

            if all(v is None or str(v).strip() == "" for v in row_dict.values()):
                continue

            columns = list(row_dict.keys())
            placeholders = [f":{col}" for col in columns]

            sql = f"""
                INSERT INTO {table_name} ({", ".join(columns)})
                VALUES ({", ".join(placeholders)})
            """

            conn.execute(text(sql), row_dict)


def append_row(table_name, row_dict):
    engine = get_engine()
    cols = list(row_dict.keys())
    placeholders = [f":{c}" for c in cols]

    sql = f"""
        INSERT INTO {table_name} ({", ".join(cols)})
        VALUES ({", ".join(placeholders)})
    """

    with engine.begin() as conn:
        conn.execute(text(sql), row_dict)


def init_db():
    sql = """
    CREATE TABLE IF NOT EXISTS project_status (
        id SERIAL PRIMARY KEY,
        status_label TEXT,
        current_evidence_source TEXT,
        manufacturer_access_status TEXT,
        next_milestone TEXT,
        updated_by TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS outreach_contacts (
        id SERIAL PRIMARY KEY,
        company TEXT,
        contact_name TEXT,
        contact_link TEXT,
        process_type TEXT,
        first_contact_date TEXT,
        follow_up_date TEXT,
        status TEXT,
        contact_owner TEXT,
        last_touchpoint TEXT,
        next_action TEXT,
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS trials (
        id SERIAL PRIMARY KEY,
        trial_name TEXT,
        evidence_source TEXT,
        environment TEXT,
        process_type TEXT,
        trial_owner TEXT,
        planned_date TEXT,
        status TEXT,
        success_criteria TEXT,
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS ground_truth_logs (
        id SERIAL PRIMARY KEY,
        run_id TEXT,
        run_date TEXT,
        evidence_source TEXT,
        environment TEXT,
        start_time TEXT,
        end_time TEXT,
        observed_cycle_count INTEGER,
        model_cycle_count INTEGER,
        mismatch_count INTEGER,
        false_positives INTEGER,
        false_negatives INTEGER,
        sync_method TEXT,
        video_file_link TEXT,
        model_output_link TEXT,
        logger TEXT,
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS issue_logs (
        id SERIAL PRIMARY KEY,
        issue_id TEXT,
        title TEXT,
        environment TEXT,
        workflow_step TEXT,
        category TEXT,
        observed_behavior TEXT,
        expected_behavior TEXT,
        severity TEXT,
        suggested_fix TEXT,
        status TEXT,
        owner TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS ux_test_logs (
        id SERIAL PRIMARY KEY,
        task_id TEXT,
        participant_role TEXT,
        scenario TEXT,
        task TEXT,
        success_criteria TEXT,
        task_success TEXT,
        confusion_point TEXT,
        quote_feedback TEXT,
        recommended_change TEXT,
        time_on_task TEXT,
        result TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS readiness_handoffs (
        id SERIAL PRIMARY KEY,
        readiness_level TEXT,
        evidence_level TEXT,
        top_issues TEXT,
        recommended_next_action TEXT,
        created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    run_sql(sql)


def seed_db_if_empty():
    """
    Adds starter rows so the app does not look empty after first initialization.
    Safe to run multiple times; it only inserts when tables are empty.
    """

    if read_table("project_status").empty:
        append_row(
            "project_status",
            {
                "status_label": "Live workspace",
                "current_evidence_source": "Online / lab workflow",
                "manufacturer_access_status": "Outreach pending",
                "next_milestone": "Continue manufacturer follow-ups and run lab rehearsal.",
                "updated_by": "System seed"
            }
        )

    if read_table("outreach_contacts").empty:
        clear_and_insert(
            "outreach_contacts",
            pd.DataFrame([
                {
                    "company": "Example Manufacturer A",
                    "contact_name": "TBD",
                    "contact_link": "TBD",
                    "process_type": "Cyclic robotic process",
                    "first_contact_date": "2026-06-18",
                    "follow_up_date": "2026-06-21",
                    "status": "Contact pending",
                    "contact_owner": "TBD",
                    "last_touchpoint": "Initial target added",
                    "next_action": "Send outreach message",
                    "notes": "Replace with real contact."
                }
            ]),
            [
                "company", "contact_name", "contact_link", "process_type",
                "first_contact_date", "follow_up_date", "status",
                "contact_owner", "last_touchpoint", "next_action", "notes"
            ]
        )

    if read_table("issue_logs").empty:
        clear_and_insert(
            "issue_logs",
            pd.DataFrame([
                {
                    "issue_id": "ISS-001",
                    "title": "Factory access not yet confirmed",
                    "environment": "Outreach",
                    "workflow_step": "Site recruitment",
                    "category": "Access",
                    "observed_behavior": "No confirmed site visit yet.",
                    "expected_behavior": "At least one site visit or lab fallback should be confirmed.",
                    "severity": "High",
                    "suggested_fix": "Continue outreach while running lab/remote validation workflow.",
                    "status": "Open",
                    "owner": "Team"
                }
            ]),
            [
                "issue_id", "title", "environment", "workflow_step", "category",
                "observed_behavior", "expected_behavior", "severity",
                "suggested_fix", "status", "owner"
            ]
        )


def csv_download(df):
    return df.to_csv(index=False).encode("utf-8")


def build_documentation_summary(export_tables):
    project_status = export_tables.get("project_status", pd.DataFrame())
    outreach = export_tables.get("outreach_contacts", pd.DataFrame())
    ground_truth = export_tables.get("ground_truth_logs", pd.DataFrame())
    issues = export_tables.get("issue_logs", pd.DataFrame())
    ux_tests = export_tables.get("ux_test_logs", pd.DataFrame())
    handoffs = export_tables.get("readiness_handoffs", pd.DataFrame())

    latest_status_text = "No project status has been saved yet."

    if not project_status.empty:
        latest = project_status.iloc[-1]
        latest_status_text = f"""MVP Status: {latest.get("status_label", "")}
Current Evidence Source: {latest.get("current_evidence_source", "")}
Manufacturer Access Status: {latest.get("manufacturer_access_status", "")}
Next Milestone: {latest.get("next_milestone", "")}
Updated By: {latest.get("updated_by", "")}
Last Updated: {latest.get("last_updated", "")}"""

    high_critical_issue_count = 0
    if not issues.empty and "severity" in issues.columns:
        high_critical_issue_count = len(
            issues[
                issues["severity"]
                .astype(str)
                .str.lower()
                .isin(["high", "critical"])
            ]
        )

    documentation = f"""# IntelliAware Field Validation Kit — Project Documentation Export

Generated: {datetime.now().isoformat()}

## Current Project Status

{latest_status_text}

## Record Counts

- Project status records: {len(project_status)}
- Outreach contacts: {len(outreach)}
- Ground-truth logs: {len(ground_truth)}
- Issue logs: {len(issues)}
- High/Critical issue count: {high_critical_issue_count}
- UI/UX test records: {len(ux_tests)}
- Readiness handoffs: {len(handoffs)}

## Product Framing

This MVP is a live field-validation workspace for IntelliAware. The current evidence source may be online, lab-based, remote, simulated, or factory-based depending on access status. As manufacturer responses, lab results, trial data, and issue reports are added, the same workflow updates and produces the current readiness handoff.

## Export Notes

This export summarizes the current state of the live PostgreSQL-backed MVP. The full records are included as CSV files in the export archive or can be downloaded individually from the Export Center.
"""

    return documentation


def build_export_zip(export_tables):
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for table_name, df in export_tables.items():
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            zip_file.writestr(f"{table_name}.csv", csv_bytes)

        documentation = build_documentation_summary(export_tables)
        zip_file.writestr(
            "intelliaware_documentation_summary.md",
            documentation.encode("utf-8")
        )

    buffer.seek(0)
    return buffer.getvalue()


# -----------------------------
# Header
# -----------------------------

st.markdown("""
<div class="main-header">
    <h1 style="margin:0;">IntelliAware Field Validation Kit</h1>
    <p style="margin:0.35rem 0 0 0; font-size:1.05rem;">
    Live MVP for planning validation trials, tracking manufacturer outreach, collecting ground-truth evidence,
    logging deployment issues, and producing readiness handoffs.
    </p>
</div>
""", unsafe_allow_html=True)


# -----------------------------
# Sidebar access control
# -----------------------------

with st.sidebar:
    st.subheader("Team Access")

    if not db_is_configured():
        st.error("DATABASE_URL is not configured in Streamlit secrets.")
        can_edit = False
    else:
        edit_code = st.text_input("Enter team edit code", type="password")
        can_edit = edit_code == st.secrets.get("TEAM_EDIT_CODE", "")

        if can_edit:
            st.success("Edit mode enabled")
        else:
            st.caption("View-only mode")

        st.divider()
        st.subheader("Database Admin")

        if can_edit and st.button("Initialize / repair database tables"):
            try:
                init_db()
                seed_db_if_empty()
                st.success("Database tables initialized and starter data checked.")
                st.rerun()
            except Exception as e:
                st.error(f"Database initialization failed: {e}")

        if st.button("Refresh app data"):
            st.cache_data.clear()
            st.rerun()


# -----------------------------
# Dynamic framing
# -----------------------------

if db_is_configured():
    status_df = read_table("project_status")
else:
    status_df = pd.DataFrame()

if status_df.empty:
    st.info(
        "This MVP is a live field-validation workspace for IntelliAware. "
        "The current evidence source may be online, lab-based, remote, simulated, or factory-based depending on access status. "
        "As manufacturer responses, lab results, trial data, and issue reports are added, the same workflow updates and produces the current readiness handoff."
    )
else:
    latest_status = status_df.iloc[-1]
    st.info(
        f"This MVP is a live field-validation workspace for IntelliAware. "
        f"Current evidence source: {latest_status['current_evidence_source']}. "
        f"Manufacturer access status: {latest_status['manufacturer_access_status']}. "
        f"Next milestone: {latest_status['next_milestone']}"
    )


# -----------------------------
# Tabs
# -----------------------------

tabs = st.tabs([
    "0. Project Status",
    "1. Overview",
    "2. Trial Plan",
    "3. Outreach Tracker",
    "4. Ground Truth Log",
    "5. Issue Tracker",
    "6. UI/UX Test Script",
    "7. Readiness Handoff",
    "8. Export Center"
])


# -----------------------------
# 0. Project Status
# -----------------------------

with tabs[0]:
    st.subheader("Project Status")
    st.markdown(
        "Use this page to update the live framing shown on the homepage. "
        "This prevents the MVP from sounding static as manufacturer access and evidence sources change."
    )

    col1, col2 = st.columns(2)

    with col1:
        status_label = st.selectbox(
            "MVP status",
            [
                "Live workspace",
                "Online/Lab MVP Live",
                "Field trial scheduled",
                "Field trial completed",
                "Ready for review"
            ]
        )

        evidence_source = st.selectbox(
            "Current evidence source",
            [
                "Online workflow",
                "University lab rehearsal",
                "Remote walkthrough",
                "Isaac Sim / simulated footage",
                "Factory field trial"
            ]
        )

    with col2:
        manufacturer_status = st.selectbox(
            "Manufacturer access status",
            [
                "Outreach pending",
                "Follow-up ongoing",
                "One response received",
                "Meeting scheduled",
                "Site visit confirmed",
                "No access yet — using fallback"
            ]
        )

        updated_by = st.text_input("Updated by", value="Team member")

    next_milestone = st.text_area(
        "Next milestone",
        value="Continue manufacturer follow-ups and run lab rehearsal."
    )

    if can_edit:
        if st.button("Save project status"):
            append_row(
                "project_status",
                {
                    "status_label": status_label,
                    "current_evidence_source": evidence_source,
                    "manufacturer_access_status": manufacturer_status,
                    "next_milestone": next_milestone,
                    "updated_by": updated_by
                }
            )
            st.success("Project status saved to PostgreSQL.")
            st.rerun()
    else:
        st.caption("Enter team edit code in the sidebar to save project status updates.")

    st.subheader("Status history")
    st.dataframe(read_table("project_status"), use_container_width=True)


# -----------------------------
# 1. Overview
# -----------------------------

with tabs[1]:
    st.subheader("Product one-liner")
    st.markdown(
        "**We are building a field-validation and deployment-readiness kit for IntelliAware researchers and manufacturing site partners "
        "who need to test whether an edge-AI monitoring system works in realistic factory workflows so that the system can move from lab prototype to deployable product.**"
    )

    latest_status_df = read_table("project_status")

    if latest_status_df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("MVP Status", "Live workspace")
        with col2:
            st.metric("Evidence Source", "Online / lab")
        with col3:
            st.metric("Factory Access", "Pending")
    else:
        latest = latest_status_df.iloc[-1]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("MVP Status", latest["status_label"])
        with col2:
            st.metric("Evidence Source", latest["current_evidence_source"])
        with col3:
            st.metric("Factory Access", latest["manufacturer_access_status"])

    st.subheader("Workflow")
    st.graphviz_chart("""
        digraph {
            rankdir=LR;
            node [shape=box, style="rounded,filled", fillcolor="#EAF6FB", color="#0B1F3A"];
            A [label="Plan Trial"];
            B [label="Run Setup Checklist"];
            C [label="Capture Video + Model Output"];
            D [label="Log Ground Truth"];
            E [label="Record Issues"];
            F [label="Generate Readiness Handoff"];
            A -> B -> C -> D -> E -> F;
        }
    """)

    st.subheader("What reviewers can inspect today")
    st.markdown("""
    - Live project status
    - Manufacturer outreach tracker
    - Field/lab trial planning workflow
    - Ground-truth logging table
    - Issue severity tracker
    - UI/UX task script
    - Readiness handoff structure
    - Export Center for downloading records and documentation
    """)


# -----------------------------
# 2. Trial Plan
# -----------------------------

with tabs[2]:
    st.subheader("Trial Plan")
    st.caption("Use this for either a real factory visit, lab rehearsal, remote walkthrough, or Isaac Sim run.")

    col1, col2 = st.columns(2)

    with col1:
        trial_type = st.selectbox(
            "Trial type",
            [
                "Factory site visit",
                "University lab rehearsal",
                "Remote operator walkthrough",
                "Isaac Sim / simulated scene"
            ]
        )
        site_name = st.text_input("Site / environment name", value="Wayne State lab fallback")
        process_type = st.text_input("Process type", value="Cyclic robotic or machine process")
        owner = st.text_input("Trial owner", value="Team member name")

    with col2:
        data_source = st.multiselect(
            "Evidence expected",
            [
                "Wide-angle video",
                "Jetson/camera feed",
                "Raw model output JSON/CSV",
                "Manual ground truth",
                "Field notes",
                "Operator feedback"
            ],
            default=[
                "Wide-angle video",
                "Raw model output JSON/CSV",
                "Manual ground truth",
                "Field notes"
            ]
        )
        known_constraints = st.text_area(
            "Known constraints",
            value="Factory access pending; lab/online fallback prepared."
        )
        success_criteria = st.text_area(
            "Success criteria",
            value="Complete a 15-minute run or walkthrough and produce cross-referenceable evidence."
        )

    st.subheader("Setup checklist")
    checklist = [
        "Confirm permission / scope",
        "Confirm safety constraints",
        "Mount camera / define camera angle",
        "Power on Jetson / edge device",
        "Run calibration",
        "Start shared clock or sync cue",
        "Start video capture",
        "Start model output capture",
        "Assign manual ground-truth logger",
        "Record environmental notes",
    ]

    cols = st.columns(2)
    for i, item in enumerate(checklist):
        with cols[i % 2]:
            st.checkbox(item, key=f"check_{item}")

    st.download_button(
        "Download trial plan summary",
        data=f"""Trial Type: {trial_type}
Site/Environment: {site_name}
Process Type: {process_type}
Owner: {owner}
Evidence Expected: {', '.join(data_source)}
Known Constraints: {known_constraints}
Success Criteria: {success_criteria}
Generated: {datetime.now().isoformat()}
""",
        file_name="trial_plan_summary.txt"
    )


# -----------------------------
# 3. Outreach Tracker
# -----------------------------

with tabs[3]:
    st.subheader("Manufacturer Outreach Tracker")
    st.caption("This table is stored in PostgreSQL. Team members can update it from the website when edit mode is enabled.")

    outreach_columns = [
        "company", "contact_name", "contact_link", "process_type",
        "first_contact_date", "follow_up_date", "status",
        "contact_owner", "last_touchpoint", "next_action", "notes"
    ]

    df = read_table("outreach_contacts")

    if df.empty:
        df = pd.DataFrame(columns=["id"] + outreach_columns + ["updated_at"])

    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        disabled=["id", "updated_at"]
    )

    if can_edit:
        if st.button("Save outreach tracker"):
            clear_and_insert("outreach_contacts", edited, outreach_columns)
            st.success("Outreach tracker saved to PostgreSQL.")
            st.rerun()
    else:
        st.caption("View-only mode. Enter team edit code in the sidebar to save changes.")

    st.download_button(
        "Download outreach tracker CSV",
        csv_download(edited),
        "outreach_tracker.csv",
        "text/csv"
    )


# -----------------------------
# 4. Ground Truth Log
# -----------------------------

with tabs[4]:
    st.subheader("Ground Truth Log")
    st.markdown("Record what actually happened in the process so model outputs can be checked against human-observed cycle events.")

    gt_columns = [
        "run_id", "run_date", "evidence_source", "environment",
        "start_time", "end_time", "observed_cycle_count", "model_cycle_count",
        "mismatch_count", "false_positives", "false_negatives",
        "sync_method", "video_file_link", "model_output_link", "logger", "notes"
    ]

    df = read_table("ground_truth_logs")

    if df.empty:
        df = pd.DataFrame(columns=["id"] + gt_columns + ["updated_at"])

    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        disabled=["id", "updated_at"]
    )

    if can_edit:
        if st.button("Save ground-truth log"):
            clear_and_insert("ground_truth_logs", edited, gt_columns)
            st.success("Ground-truth log saved to PostgreSQL.")
            st.rerun()
    else:
        st.caption("View-only mode. Enter team edit code in the sidebar to save changes.")

    st.download_button(
        "Download ground-truth log CSV",
        csv_download(edited),
        "ground_truth_log.csv",
        "text/csv"
    )


# -----------------------------
# 5. Issue Tracker
# -----------------------------

with tabs[5]:
    st.subheader("Issue Tracker")
    st.markdown("Every issue should be actionable for developers: what happened, where, severity, reproduction steps, and suggested fix.")

    issue_columns = [
        "issue_id", "title", "environment", "workflow_step", "category",
        "observed_behavior", "expected_behavior", "severity",
        "suggested_fix", "status", "owner"
    ]

    df = read_table("issue_logs")

    if df.empty:
        df = pd.DataFrame(columns=["id"] + issue_columns + ["updated_at"])

    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        disabled=["id", "updated_at"]
    )

    if "severity" in edited.columns and not edited.empty:
        st.subheader("Issue summary")
        st.bar_chart(edited["severity"].value_counts())

    if can_edit:
        if st.button("Save issue tracker"):
            clear_and_insert("issue_logs", edited, issue_columns)
            st.success("Issue tracker saved to PostgreSQL.")
            st.rerun()
    else:
        st.caption("View-only mode. Enter team edit code in the sidebar to save changes.")

    st.download_button(
        "Download issue tracker CSV",
        csv_download(edited),
        "issue_tracker.csv",
        "text/csv"
    )


# -----------------------------
# 6. UI/UX Test Script
# -----------------------------

with tabs[6]:
    st.subheader("UI/UX Test Script")
    st.markdown("Use this script for in-person operator sessions or remote walkthroughs.")

    ux_columns = [
        "task_id", "participant_role", "scenario", "task", "success_criteria",
        "task_success", "confusion_point", "quote_feedback",
        "recommended_change", "time_on_task", "result"
    ]

    df = read_table("ux_test_logs")

    if df.empty:
        df = pd.DataFrame(columns=["id"] + ux_columns + ["updated_at"])

    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        disabled=["id", "updated_at"]
    )

    if can_edit:
        if st.button("Save UI/UX test script"):
            clear_and_insert("ux_test_logs", edited, ux_columns)
            st.success("UI/UX test script saved to PostgreSQL.")
            st.rerun()
    else:
        st.caption("View-only mode. Enter team edit code in the sidebar to save changes.")

    st.download_button(
        "Download UI test script CSV",
        csv_download(edited),
        "ui_test_script.csv",
        "text/csv"
    )


# -----------------------------
# 7. Readiness Handoff
# -----------------------------

with tabs[7]:
    st.subheader("Readiness Handoff")
    st.markdown("This is the final output reviewers should expect from each completed trial or walkthrough.")

    c1, c2 = st.columns(2)

    with c1:
        readiness = st.selectbox(
            "Readiness assessment",
            [
                "Not ready",
                "Ready for lab demo",
                "Ready for limited field pilot",
                "Ready for broader pilot"
            ]
        )

        top_issues = st.text_area(
            "Top issues",
            value=(
                "1. Manufacturer access is still pending; outreach and follow-ups are ongoing.\n"
                "2. Current validation evidence is online/lab-based until a factory site confirms access.\n"
                "3. Need synchronized model output, manual ground truth, and operator feedback for stronger readiness assessment."
            )
        )

    with c2:
        evidence_level = st.selectbox(
            "Evidence level",
            [
                "Remote/mock only",
                "Lab validated",
                "Single field trial",
                "Multiple field trials"
            ]
        )

        next_action = st.text_area(
            "Recommended next action",
            value=(
                "Continue manufacturer follow-ups, run the lab/online validation workflow, "
                "collect sample issue logs and ground-truth records, and plug factory data into the same workflow once access is confirmed."
            )
        )

        created_by = st.text_input("Created by", value="Team member")

    handoff = f"""# IntelliAware Readiness Handoff

Readiness assessment: {readiness}
Evidence level: {evidence_level}

Top issues:
{top_issues}

Recommended next action:
{next_action}

Generated: {datetime.now().isoformat()}
"""

    st.markdown(handoff)

    if can_edit:
        if st.button("Save readiness handoff"):
            append_row(
                "readiness_handoffs",
                {
                    "readiness_level": readiness,
                    "evidence_level": evidence_level,
                    "top_issues": top_issues,
                    "recommended_next_action": next_action,
                    "created_by": created_by
                }
            )
            st.success("Readiness handoff saved to PostgreSQL.")
            st.rerun()
    else:
        st.caption("View-only mode. Enter team edit code in the sidebar to save readiness handoff.")

    st.download_button(
        "Download readiness handoff",
        handoff,
        "readiness_handoff.md",
        "text/markdown"
    )

    st.subheader("Saved readiness handoffs")
    st.dataframe(read_table("readiness_handoffs"), use_container_width=True)


# -----------------------------
# 8. Export Center
# -----------------------------

with tabs[8]:
    st.subheader("Export Center")
    st.markdown(
        "Download the current project records from PostgreSQL for submission, backup, future documentation, or handoff to the IntelliAware research team."
    )

    export_tables = {
        "project_status": read_table("project_status"),
        "outreach_contacts": read_table("outreach_contacts"),
        "ground_truth_logs": read_table("ground_truth_logs"),
        "issue_logs": read_table("issue_logs"),
        "ux_test_logs": read_table("ux_test_logs"),
        "readiness_handoffs": read_table("readiness_handoffs"),
    }

    st.subheader("Database record counts")

    count_df = pd.DataFrame(
        [
            {"Table": table_name, "Records": len(df)}
            for table_name, df in export_tables.items()
        ]
    )

    st.dataframe(count_df, use_container_width=True, hide_index=True)

    st.subheader("Download individual tables")

    for table_name, df in export_tables.items():
        st.download_button(
            label=f"Download {table_name}.csv",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"{table_name}.csv",
            mime="text/csv"
        )

    st.subheader("Download full project archive")

    documentation = build_documentation_summary(export_tables)
    archive = build_export_zip(export_tables)

    st.download_button(
        label="Download documentation summary.md",
        data=documentation,
        file_name="intelliaware_documentation_summary.md",
        mime="text/markdown"
    )

    st.download_button(
        label="Download full PostgreSQL export ZIP",
        data=archive,
        file_name=f"intelliaware_postgres_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
        mime="application/zip"
    )

    st.subheader("Documentation preview")
    st.markdown(documentation)


st.divider()
st.caption("IntelliAware Field Validation Kit MVP — live workspace backed by PostgreSQL.")