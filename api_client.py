"""Centralized API call functions. app.py never calls requests directly."""
import requests
import streamlit as st

from mock_data import mock_ai_summary

TIMEOUT = 10


class APIError(Exception):
    """Any problem talking to the backend."""


class AuthError(APIError):
    """The token is missing, invalid, or expired (HTTP 401)."""


def _secret(key, default=""):
    """Read from secrets.toml without crashing if the file is missing."""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


BASE_URL = _secret("API_URL", "http://127.0.0.1:8000")


def _detail(response, default="Unknown error"):
    try:
        return response.json().get("detail", default)
    except ValueError:
        return default


def _request(method, path, token=None, **kwargs):
    """Single place where every backend request is sent and errors are handled."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = requests.request(
            method, f"{BASE_URL}{path}", headers=headers, timeout=TIMEOUT, **kwargs
        )
    except requests.ConnectionError:
        raise APIError(f"Can't connect to the API at {BASE_URL}. Is the backend running?") from None
    except requests.Timeout:
        raise APIError("The API took too long to respond.") from None

    if response.status_code == 401:
        raise AuthError(_detail(response, "Your session has expired. Please log in again."))
    if not response.ok:
        raise APIError(f"API error {response.status_code}: {_detail(response)}")
    if response.status_code == 204:  # No Content (e.g. after delete)
        return None
    return response.json()


# ---------- Auth ----------
def login(username, password):
    data = _request("POST", "/login", data={"username": username, "password": password})
    return data["access_token"]


# ---------- Tasks ----------
def get_tasks(token):
    return _request("GET", "/tasks", token=token)


def create_task(token, title, priority, status):
    payload = {"title": title, "priority": priority, "status": status}
    return _request("POST", "/tasks", token=token, json=payload)


def complete_task(token, task_id):
    return _request("PATCH", f"/tasks/{task_id}/complete", token=token)


def delete_task(token, task_id):
    return _request("DELETE", f"/tasks/{task_id}", token=token)


# ---------- AI ----------
def get_ai_summary(tasks):
    """Send tasks to OpenAI for a summary; fall back to the mock if there's no key or it fails."""
    api_key = _secret("OPENAI_API_KEY")
    if not api_key:
        return mock_ai_summary(tasks)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        task_text = "\n".join(
            f"- {t['title']} ({t['status']}, {t['priority']} priority)" for t in tasks
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # use whichever model your course uses
            messages=[
                {"role": "system", "content": "You are a productivity assistant. Summarize this "
                 "task list in 3 short bullet points and suggest what to work on next."},
                {"role": "user", "content": task_text},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI request failed ({e}). Showing a mock summary instead.\n\n" + mock_ai_summary(tasks)