
import streamlit as st
import pandas as pd
from datetime import datetime
from io import StringIO

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

@st.cache_data(ttl=60)
def load_csv(path):
    return pd.read_csv(path)

def csv_download(df):
    return df.to_csv(index=False).encode("utf-8")

def save_note_to_session(key, value):
    st.session_state[key] = value

outreach_path = "data/outreach_tracker.csv"
issues_path = "data/issue_tracker.csv"
ground_truth_path = "data/ground_truth_log.csv"
ux_path = "data/ui_test_script.csv"

st.markdown("""
<div class="main-header">
    <h1 style="margin:0;">IntelliAware Field Validation Kit</h1>
    <p style="margin:0.35rem 0 0 0; font-size:1.05rem;">
    Online MVP for planning trials, tracking manufacturer outreach, collecting ground-truth evidence,
    logging deployment issues, and producing a readiness handoff.
    </p>
</div>
""", unsafe_allow_html=True)

st.info(
    "Submission framing: manufacturer access is still pending, so this MVP demonstrates the online/lab validation workflow. "
    "When a factory site responds, its data plugs into the same workflow."
)

tabs = st.tabs([
    "1. Overview",
    "2. Trial Plan",
    "3. Outreach Tracker",
    "4. Ground Truth Log",
    "5. Issue Tracker",
    "6. UI/UX Test Script",
    "7. Readiness Handoff"
])

with tabs[0]:
    st.subheader("Product one-liner")
    st.markdown(
        "**We are building a field-validation and deployment-readiness kit for IntelliAware researchers and manufacturing site partners "
        "who need to test whether an edge-AI monitoring system works in realistic factory workflows so that the system can move from lab prototype to deployable product.**"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("MVP Status", "Online workflow ready")
    with col2:
        st.metric("Factory Access", "Pending")
    with col3:
        st.metric("Fallback Path", "Lab / remote / simulation")

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
    - Manufacturer outreach tracker
    - Field/lab trial planning workflow
    - Ground-truth logging template
    - Issue severity tracker
    - UI/UX task script
    - Readiness handoff structure
    """)

with tabs[1]:
    st.subheader("Trial Plan")
    st.caption("Use this for either a real factory visit, lab rehearsal, remote walkthrough, or Isaac Sim run.")

    col1, col2 = st.columns(2)
    with col1:
        trial_type = st.selectbox("Trial type", ["Factory site visit", "University lab rehearsal", "Remote operator walkthrough", "Isaac Sim / simulated scene"])
        site_name = st.text_input("Site / environment name", value="Wayne State lab fallback")
        process_type = st.text_input("Process type", value="Cyclic robotic or machine process")
        owner = st.text_input("Trial owner", value="Team member name")
    with col2:
        data_source = st.multiselect(
            "Evidence expected",
            ["Wide-angle video", "Jetson/camera feed", "Raw model output JSON/CSV", "Manual ground truth", "Field notes", "Operator feedback"],
            default=["Wide-angle video", "Raw model output JSON/CSV", "Manual ground truth", "Field notes"]
        )
        known_constraints = st.text_area("Known constraints", value="Factory access pending; lab/online fallback prepared.")
        success_criteria = st.text_area("Success criteria", value="Complete a 15-minute run or walkthrough and produce cross-referenceable evidence.")

    st.subheader("Setup checklist")
    checklist = {
        "Confirm permission / scope": False,
        "Confirm safety constraints": False,
        "Mount camera / define camera angle": False,
        "Power on Jetson / edge device": False,
        "Run calibration": False,
        "Start shared clock or sync cue": False,
        "Start video capture": False,
        "Start model output capture": False,
        "Assign manual ground-truth logger": False,
        "Record environmental notes": False,
    }
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

with tabs[2]:
    st.subheader("Manufacturer Outreach Tracker")
    df = load_csv(outreach_path)
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    st.caption("For persistent shared updates, keep the source data in a shared Google Sheet or GitHub CSV and redeploy/sync this app.")
    st.download_button("Download outreach tracker CSV", csv_download(edited), "outreach_tracker.csv", "text/csv")

with tabs[3]:
    st.subheader("Ground Truth Log")
    st.markdown("Record what actually happened in the process so model outputs can be checked against human-observed cycle events.")
    df = load_csv(ground_truth_path)
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    st.download_button("Download ground-truth log CSV", csv_download(edited), "ground_truth_log.csv", "text/csv")

with tabs[4]:
    st.subheader("Issue Tracker")
    st.markdown("Every issue should be actionable for developers: what happened, where, severity, reproduction steps, and suggested fix.")
    df = load_csv(issues_path)
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    st.subheader("Issue summary")
    if "Severity" in edited.columns and not edited.empty:
        st.bar_chart(edited["Severity"].value_counts())
    st.download_button("Download issue tracker CSV", csv_download(edited), "issue_tracker.csv", "text/csv")

with tabs[5]:
    st.subheader("UI/UX Test Script")
    st.markdown("Use this script for in-person operator sessions or remote walkthroughs.")
    df = load_csv(ux_path)
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    st.download_button("Download UI test script CSV", csv_download(edited), "ui_test_script.csv", "text/csv")

with tabs[6]:
    st.subheader("Readiness Handoff")
    st.markdown("This is the final output reviewers should expect from each completed trial or walkthrough.")

    c1, c2 = st.columns(2)
    with c1:
        readiness = st.selectbox("Readiness assessment", ["Not ready", "Ready for lab demo", "Ready for limited field pilot", "Ready for broader pilot"])
        top_issues = st.text_area("Top issues", value="1. Factory access pending\n2. Need real operator feedback\n3. Need synchronized model output + ground truth")
    with c2:
        evidence_level = st.selectbox("Evidence level", ["Remote/mock only", "Lab validated", "Single field trial", "Multiple field trials"])
        next_action = st.text_area("Recommended next action", value="Run lab rehearsal and remote operator walkthrough while continuing manufacturer outreach.")

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
    st.download_button("Download readiness handoff", handoff, "readiness_handoff.md", "text/markdown")

st.divider()
st.caption("IntelliAware Field Validation Kit MVP — built for product design review submission.")
