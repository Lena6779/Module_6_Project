"""Sample data for offline development and fallbacks."""

MOCK_TASKS = [
    {"id": 1, "title": "Finish Module 6 project", "priority": "high", "status": "in_progress"},
    {"id": 2, "title": "Review FastAPI routers", "priority": "medium", "status": "done"},
    {"id": 3, "title": "Write pytest tests", "priority": "high", "status": "todo"},
    {"id": 4, "title": "Update portfolio page", "priority": "low", "status": "todo"},
    {"id": 5, "title": "Practice Streamlit layouts", "priority": "medium", "status": "done"},
]


def mock_ai_summary(tasks):
    """Fake AI response used when no OpenAI key is set or the AI call fails."""
    done = sum(1 for t in tasks if t["status"] == "done")
    high_open = [t["title"] for t in tasks if t["priority"] == "high" and t["status"] != "done"]
    next_up = high_open[0] if high_open else "any remaining task"
    return (
        f"- You've completed **{done} of {len(tasks)}** tasks.\n"
        f"- **{len(high_open)}** high-priority task(s) are still open.\n"
        f"- Suggested next step: **{next_up}**.\n\n"
        "_Mock summary. Add an OpenAI key to secrets.toml for real AI output._"
    )