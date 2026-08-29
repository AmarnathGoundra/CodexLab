from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .store import load_tasks, next_task_id, save_tasks


def list_tasks(status: str | None = None, q: str | None = None) -> list[dict[str, Any]]:
    """Return task records, optionally filtered by status and search text."""
    tasks = load_tasks()
    filtered: list[dict[str, Any]] = []

    # Normalize the status parameter to a string value. FastAPI may pass an
    # Enum (TaskStatus) or a plain string, so handle both cases.
    status_str: str | None = None
    if status is not None:
        status_str = getattr(status, "value", str(status))

    for task in tasks:
        if status_str and task["status"] != status_str:
            continue

        # If a search query was provided, do a case-insensitive check across
        # title and description and skip non-matching tasks.
        if q:
            q_lower = q.lower()
            title = task.get("title", "") or ""
            desc = task.get("description", "") or ""
            if q_lower not in title.lower() and q_lower not in desc.lower():
                continue

        filtered.append(task)

    return filtered


def get_task(task_id: int) -> dict[str, Any] | None:
    """Find a single task by ID."""
    tasks = load_tasks()
    return next((task for task in tasks if task["id"] == task_id), None)


def create_task(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new task and persist it."""
    tasks = load_tasks()
    task = {
        "id": next_task_id(tasks),
        "title": payload["title"],
        "description": payload["description"],
        "status": "open",
        "priority": payload["priority"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }
    tasks.append(task)
    save_tasks(tasks)
    return task


def complete_task(task_id: int) -> dict[str, Any] | None:
    """Mark a task as completed."""
    tasks = load_tasks()

    for task in tasks:
        if task["id"] == task_id:
            # Update the task in-place and persist the change.
            task["status"] = "done"
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            save_tasks(tasks)
            return task

    return None
