from __future__ import annotations

import json
import platform
import shutil
from pathlib import Path

import streamlit as st

from ctfhive.agents.classifier import classify
from ctfhive.agents.coordinator import Coordinator
from ctfhive.config import Config
from ctfhive.doctor import run_checks
from ctfhive.evidence.store import EvidenceStore
from ctfhive.intake import ingest
from ctfhive.models.claude import ClaudeCodeModel
from ctfhive.models.ollama import OllamaModel
from ctfhive.knowledge.research import format_items
from ctfhive.knowledge.store import KnowledgeStore
from ctfhive.tools.registry import ToolRegistry


st.set_page_config(page_title="CTFHive", page_icon="🐝", layout="wide")
st.markdown("""
<style>
:root { --ink: #e7edf2; --muted: #91a0ad; --panel: #14202a; --accent: #f4b942; --line: #2b3b47; }
.stApp { background: radial-gradient(circle at 15% 0%, #203645 0, #0b1116 42%, #070a0d 100%); color: var(--ink); }
[data-testid="stMetricValue"] { color: var(--accent); }
[data-testid="stSidebar"] { background: #0d151c; border-right: 1px solid var(--line); }
.ctf-kicker { color: var(--accent); letter-spacing: .18em; font-size: .72rem; text-transform: uppercase; }
.ctf-panel { border: 1px solid var(--line); background: rgba(20,32,42,.82); padding: 1rem; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


def config() -> Config:
    value = Config.from_env()
    value.ensure_dirs()
    return value


def status_icon(status: str) -> str:
    return "🟢" if status in {"AVAILABLE", "REQUIRED"} else "🟡" if status == "OPTIONAL" else "🔴"


def dashboard(value: Config) -> None:
    st.markdown('<div class="ctf-kicker">authorized operations console</div>', unsafe_allow_html=True)
    st.title("🐝 CTFHive")
    st.caption("AI-Assisted Autonomous CTF Solver · local-first, evidence-backed")
    checks = run_checks(value)
    by_name = {check.name: check for check in checks}
    cols = st.columns(5)
    for column, name in zip(cols, ["Ollama connectivity", "Configured model", "Claude Code", "Docker", "WSL/Linux runtime"]):
        check = by_name[name]
        column.metric(name, f"{status_icon(check.status)} {check.detail[:24]}")
    st.divider()
    tools = [check for check in checks if check.name.startswith("tool:") and check.status == "AVAILABLE"]
    knowledge = KnowledgeStore(value.knowledge_path)
    a, b, c = st.columns(3)
    a.metric("Available tools", len(tools))
    b.metric("Knowledge records", knowledge.count())
    c.metric("Python", platform.python_version())


def analysis(value: Config) -> None:
    st.subheader("Challenge intake and analysis")
    source = st.text_input("Local challenge file or directory", placeholder="./fixtures/hello.txt")
    uploaded = st.file_uploader("Or upload a challenge artifact", accept_multiple_files=True)
    mock = st.toggle("Mock mode", value=True)
    no_submit = st.toggle("No CTFd submission", value=True)
    category = st.selectbox("Category override", ["auto", "web", "pwn", "rev", "crypto", "forensics", "stego", "osint", "misc"])
    if st.button("🚀 Start analysis", type="primary", disabled=not source and not uploaded):
        try:
            if uploaded:
                upload_root = value.workspace_root / "uploads"
                upload_root.mkdir(parents=True, exist_ok=True)
                for item in uploaded:
                    (upload_root / Path(item.name).name).write_bytes(item.getbuffer())
                source = str(upload_root)
            with st.status("Running CTFHive coordinator", expanded=True) as progress:
                st.write("Inspecting challenge and enumerating files")
                challenge = ingest(source, value.workspace_root)
                st.write(f"Classified as {category if category != 'auto' else classify(challenge).value}")
                st.write("Selecting specialist and available tools")
                result = Coordinator(value, EvidenceStore(value.evidence_root), model=None if mock else OllamaModel(value.ollama_base_url, value.model)).solve(challenge, None if category == "auto" else category, mock)
                st.write("Collecting evidence, retrieving knowledge, and verifying candidates")
                progress.update(label="Analysis complete", state="complete")
            st.session_state["last_challenge"] = challenge.name
            st.session_state["last_result"] = result
            st.session_state["last_records"] = EvidenceStore(value.evidence_root).read(challenge.name)
        except (OSError, ValueError, ConnectionError) as error:
            st.error(f"Analysis failed safely: {error}")
    result = st.session_state.get("last_result")
    if result:
        st.divider()
        st.subheader("Result")
        left, mid, right = st.columns(3)
        left.metric("Category", result.category.value.upper())
        mid.metric("Status", "SOLVED" if result.solved else "NOT SOLVED")
        right.metric("Flag", result.flag or "No verified flag")
        st.caption("A candidate is displayed only when it matches configured patterns and appears in stored evidence.")


def evidence_view(value: Config) -> None:
    st.subheader("Evidence")
    challenge = st.text_input("Challenge name", value=st.session_state.get("last_challenge", ""))
    records = EvidenceStore(value.evidence_root).read(challenge) if challenge else list(EvidenceStore(value.evidence_root).all())
    for record in records:
        with st.expander(f"{record.tool} · {record.agent} · exit {record.exit_code}"):
            st.caption(f"{record.timestamp} · {record.duration_ms} ms · confidence {record.confidence:.2f}")
            st.code(" ".join(record.arguments), language="text")
            if record.stdout:
                st.code(record.stdout, language="text")
            if record.stderr:
                st.error(record.stderr)
            st.write(record.observations)


def tools_view() -> None:
    st.subheader("Registered capabilities")
    for category in sorted({tool.category for tool in ToolRegistry().all()}):
        st.markdown(f"**{category.upper()}**")
        for tool in [item for item in ToolRegistry().all() if item.category == category]:
            st.write(f"{status_icon('AVAILABLE' if tool.availability() else 'OPTIONAL')} `{tool.name}` · {tool.description}")


def knowledge_view(value: Config) -> None:
    st.subheader("🧠 Knowledge Center")
    store = KnowledgeStore(value.knowledge_path)
    query = st.text_input("Search local strategies", placeholder="PIE ROP")
    for item in store.search(query, limit=12, include_unapproved=True):
        with st.expander(f"{item.title} · {item.category} · {item.confidence:.2f}"):
            st.write(item.summary)
            st.caption(f"Source: {item.source} · {item.source_quality.value} · successes {item.success_count} · failures {item.failure_count}")
            st.write(item.content)


def diagnostics(value: Config) -> None:
    st.subheader("System diagnostics")
    for check in run_checks(value):
        st.write(f"{status_icon(check.status)} **{check.name}** · {check.detail}")


def main() -> None:
    value = config()
    page = st.sidebar.radio("CTFHive", ["Dashboard", "Analysis", "Evidence", "Knowledge Center", "Tools", "Diagnostics"])
    if page == "Dashboard":
        dashboard(value)
    elif page == "Analysis":
        analysis(value)
    elif page == "Evidence":
        evidence_view(value)
    elif page == "Knowledge Center":
        knowledge_view(value)
    elif page == "Tools":
        tools_view()
    else:
        diagnostics(value)


if __name__ == "__main__":
    main()
