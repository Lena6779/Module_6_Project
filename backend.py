"""FastAPI backend with JWT authentication for the AI Dashboard."""
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

SECRET_KEY = "change-me-in-a-real-app"  # a real app loads this from an environment variable
ALGORITHM = "HS256"
TOKEN_MINUTES = 30

app = FastAPI(title="AI Dashboard API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Demo users. A real app stores hashed passwords in a database.
USERS = {"lena": "password123", "demo": "demo123"}


# ---------- Models ----------
class TaskCreate(BaseModel):
    title: str
    priority: Literal["high", "medium", "low"] = "medium"
    status: Literal["todo", "in_progress", "done"] = "todo"


class Task(TaskCreate):
    id: int


tasks: list[Task] = [
    Task(id=1, title="Set up project structure", priority="high", status="done"),
    Task(id=2, title="Build API client", priority="high", status="in_progress"),
    Task(id=3, title="Add Plotly charts", priority="medium", status="todo"),
    Task(id=4, title="Write README", priority="low", status="todo"),
]


# ---------- Auth helpers ----------
def create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_error = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:  # also catches expired tokens
        raise credentials_error
    username = payload.get("sub")
    if username not in USERS:
        raise credentials_error
    return username


def find_task(task_id: int) -> Task:
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")


# ---------- Routes ----------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    if USERS.get(form.username) != form.password:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return {"access_token": create_token(form.username), "token_type": "bearer"}


@app.get("/me")
def me(user: str = Depends(get_current_user)):
    return {"username": user}


@app.get("/tasks", response_model=list[Task])
def list_tasks(user: str = Depends(get_current_user)):
    return tasks


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate, user: str = Depends(get_current_user)):
    new_id = max((t.id for t in tasks), default=0) + 1
    new_task = Task(id=new_id, **task.model_dump())
    tasks.append(new_task)
    return new_task


@app.patch("/tasks/{task_id}/complete", response_model=Task)
def complete_task(task_id: int, user: str = Depends(get_current_user)):
    task = find_task(task_id)
    task.status = "done"
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, user: str = Depends(get_current_user)):
    tasks.remove(find_task(task_id))