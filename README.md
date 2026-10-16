# AI API Dashboard

An interactive AI API Dashboard with Authentication. Built with a FastAPI backend and a Streamlit frontend, featuring JWT login, a task dashboard with Plotly charts, task management, and an AI-generated task summary.

## Features

- **Authentication:** Login form with JWT tokens stored in session state, logged-in user shown in the sidebar, and a logout button that clears the session
- **Dashboard:** Metric cards, Plotly charts (tasks by status and by priority), and a table of tasks from the API
- **Task management:** Add new tasks, mark tasks complete, and delete tasks
- **AI summary:** Sends the current task list to OpenAI for a summary and suggested next step (falls back to a mock summary if no API key is set)
- **Error handling:** Clear messages for connection errors and expired sessions (401s), with sample data shown when the API is offline
- **Layout:** Sidebar controls with a priority filter, three tabs, and loading spinners

## Tech Stack

- **Backend:** FastAPI, PyJWT, Uvicorn
- **Frontend:** Streamlit, Plotly, pandas
- **API calls:** requests (centralized in `api_client.py`)
- **AI:** OpenAI API (optional)

## Project Structure

```
Module_6_Project/
├── backend.py           # FastAPI backend with JWT auth and task endpoints
├── app.py               # Streamlit frontend
├── api_client.py        # Centralized API call functions
├── mock_data.py         # Sample data for offline development
├── requirements.txt     # Dependencies
└── .streamlit/
    └── secrets.toml     # API URL and keys (not committed to Git)
```

## Setup

1. Create and activate a virtual environment, then install dependencies:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Create `.streamlit/secrets.toml`:

```toml
API_URL = "http://127.0.0.1:8000"
OPENAI_API_KEY = ""   # optional; a mock summary is used if left blank
```

## Running the App

Open two terminals, each with the virtual environment activated.

**Terminal 1 (backend):**
```
uvicorn backend:app --reload
```

**Terminal 2 (frontend):**
```
streamlit run app.py
```

The dashboard opens at http://localhost:8501. API docs are available at http://127.0.0.1:8000/docs.

**Demo login:** `lena` / `password123`

## API Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/health` | Health check | No |
| POST | `/login` | Log in and receive a JWT | No |
| GET | `/me` | Get the current user | Yes |
| GET | `/tasks` | List all tasks | Yes |
| POST | `/tasks` | Create a task | Yes |
| PATCH | `/tasks/{task_id}/complete` | Mark a task complete | Yes |
| DELETE | `/tasks/{task_id}` | Delete a task | Yes |

## Notes

- Tasks are stored in memory, so they reset to the sample data whenever the backend restarts! 
- Demo users and the JWT secret key are hard-coded for this assignment. 
- In a real-world app, passwords would be hashed and stored in a database, and the secret key would be kept out of the code (for example, in an environment variable) so it isn't exposed on GitHub.
  
## Author

Lena Hersloff, Coding Temple AI Engineering Foundations