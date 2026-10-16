"""Streamlit frontend for the AI Task Dashboard."""
import pandas as pd
import plotly.express as px
import streamlit as st

import api_client
from api_client import APIError, AuthError
from mock_data import MOCK_TASKS

st.set_page_config(page_title="AI Task Dashboard", page_icon="📊", layout="wide")

STATUSES = ["todo", "in_progress", "done"]
PRIORITIES = ["high", "medium", "low"]
STATUS_COLORS = {"todo": "#EF553B", "in_progress": "#FFA15A", "done": "#00CC96"}

def init_session_state():
    """Create every session key once, using the 'if key not in' pattern."""
    defaults = {
        "token": None,       # JWT from /login
        "username": None,    # shown in the sidebar
        "ai_summary": None,  # last AI result, so it survives reruns
        "flash": None,       # message for the login page (e.g. "session expired")
        "notice": None,      # success message after an add/complete/delete
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def logout(message=None):
    """Clear the whole session and go back to the login page."""
    st.session_state.clear()
    init_session_state()
    st.session_state.flash = message
    st.rerun()
    
# Login Page
def render_login():
    st.title("📊 AI Task Dashboard")
    st.subheader("Please log in")

    if st.session_state.flash:
        st.info(st.session_state.flash)
        st.session_state.flash = None

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")

    if submitted:
        if not username or not password:
            st.error("Please enter both a username and password.")
            return
        try:
            with st.spinner("Logging in..."):
                token = api_client.login(username, password)
        except APIError as e:  # also catches AuthError (wrong password)
            st.error(str(e))
            return
        st.session_state.token = token
        st.session_state.username = username
        st.rerun()

    st.caption("Demo login: lena / password123")
    
# Sidebar 
def render_sidebar():
    with st.sidebar:
        st.header("👤 Account")
        st.write(f"Logged in as **{st.session_state.username}**")
        if st.button("Log out"):
            logout("You've been logged out.")

        st.divider()
        st.header("⚙️ Settings")
        priority_filter = st.multiselect("Filter by priority", PRIORITIES, default=PRIORITIES)
        if st.button("🔄 Refresh data"):
            st.rerun()
    return priority_filter

# Loading and Running Actions
def load_tasks():
    """Returns (tasks, read_only). read_only is True when we fell back to mock data."""
    try:
        with st.spinner("Loading tasks..."):
            return api_client.get_tasks(st.session_state.token), False
    except AuthError:
        logout("Your session expired. Please log in again.")
    except APIError as e:
        st.error(f"{e} Showing sample data instead.")
        return MOCK_TASKS, True


def run_action(func, *args, success_message):
    """Call an API action (create/complete/delete) with consistent error handling."""
    try:
        with st.spinner("Saving..."):
            func(st.session_state.token, *args)
    except AuthError:
        logout("Your session expired. Please log in again.")
    except APIError as e:
        st.error(str(e))
        return
    st.session_state.notice = success_message
    st.rerun()
    
# Dashboard Metrics 
def render_metrics(df):
    total = len(df)
    done = int((df["status"] == "done").sum())
    open_tasks = total - done
    high_open = int(((df["priority"] == "high") & (df["status"] != "done")).sum())
    completion = f"{done / total:.0%}" if total else "0%"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tasks", total)
    col2.metric("Completed", done, f"{completion} done")
    col3.metric("Open", open_tasks)
    col4.metric("High Priority Open", high_open)


def render_dashboard_tab(df):
    if df.empty:
        st.info("No tasks match your filters yet.")
        return

    render_metrics(df)

    left, right = st.columns(2)
    with left:
        fig = px.pie(
            df, names="status", title="Tasks by Status", hole=0.4,
            color="status", color_discrete_map=STATUS_COLORS,
        )
        st.plotly_chart(fig)
    with right:
        fig = px.histogram(
            df, x="priority", color="status", barmode="group",
            title="Tasks by Priority", category_orders={"priority": PRIORITIES},
            color_discrete_map=STATUS_COLORS,
        )
        st.plotly_chart(fig)

    st.subheader("All Tasks")
    st.dataframe(df, hide_index=True)

# Manage Tasks Tab (Add form and Complete/Delete Actions)
def render_add_form(read_only):
    st.subheader("➕ Add a Task")
    with st.form("add_task", clear_on_submit=True):
        title = st.text_input("Title")
        col1, col2 = st.columns(2)
        priority = col1.selectbox("Priority", PRIORITIES, index=1)
        status = col2.selectbox("Status", STATUSES)
        submitted = st.form_submit_button("Add Task", disabled=read_only)

    if submitted:
        if not title.strip():
            st.warning("Please enter a title.")
            return
        run_action(api_client.create_task, title.strip(), priority, status,
                   success_message=f"Added '{title.strip()}'")


def render_task_actions(tasks, read_only):
    st.subheader("✏️ Update a Task")
    if not tasks:
        st.info("No tasks to update.")
        return

    options = {f"#{t['id']} – {t['title']} ({t['status']})": t for t in tasks}
    choice = st.selectbox("Choose a task", list(options))
    task = options[choice]

    col1, col2 = st.columns(2)
    if col1.button("✅ Mark Complete", disabled=read_only or task["status"] == "done"):
        run_action(api_client.complete_task, task["id"],
                   success_message=f"Completed '{task['title']}'")
    if col2.button("🗑️ Delete", disabled=read_only):
        run_action(api_client.delete_task, task["id"],
                   success_message=f"Deleted '{task['title']}'")
        
# AI Insights Tab
def render_ai_tab(tasks):
    st.subheader("🤖 AI Task Summary")
    st.write("Send your current tasks to the AI for a quick summary and a suggested next step.")

    if st.button("Generate Summary", type="primary"):
        with st.spinner("Asking the AI..."):
            st.session_state.ai_summary = api_client.get_ai_summary(tasks)

    if st.session_state.ai_summary:
        st.markdown(st.session_state.ai_summary)

# Main Application aka Traffic Control
def main():
    init_session_state()

    if not st.session_state.token:
        render_login()
        return

    priority_filter = render_sidebar()
    st.title("📊 AI Task Dashboard")

    if st.session_state.notice:
        st.success(st.session_state.notice)
        st.session_state.notice = None

    tasks, read_only = load_tasks()
    df = pd.DataFrame(tasks, columns=["id", "title", "priority", "status"])
    df = df[df["priority"].isin(priority_filter)]

    tab_dashboard, tab_manage, tab_ai = st.tabs(["📊 Dashboard", "✏️ Manage Tasks", "🤖 AI Insights"])
    with tab_dashboard:
        render_dashboard_tab(df)
    with tab_manage:
        render_add_form(read_only)
        st.divider()
        render_task_actions(tasks, read_only)
    with tab_ai:
        render_ai_tab(tasks)


main()