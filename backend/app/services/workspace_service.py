"""Persistence services for the assistant's notes and task workspace."""

from fastapi import HTTPException, status

from app.db.database import database
from app.schemas.common import Note, NoteCreate, Task, TaskCreate, TaskUpdate
from app.utils.helpers import generate_uuid, get_utc_now


class WorkspaceService:
    async def list_notes(self) -> list[Note]:
        rows = await database.fetch_all("SELECT * FROM notes ORDER BY updated_at DESC")
        return [Note.model_validate(row) for row in rows]

    async def create_note(self, note: NoteCreate) -> Note:
        note_id = generate_uuid()
        now = get_utc_now().isoformat()
        await database.execute(
            """
            INSERT INTO notes (id, title, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (note_id, note.title, note.content, now, now),
        )
        return Note(id=note_id, created_at=now, updated_at=now, **note.model_dump())

    async def delete_note(self, note_id: str) -> bool:
        return bool(await database.execute("DELETE FROM notes WHERE id = ?", (note_id,)))

    async def list_tasks(self) -> list[Task]:
        rows = await database.fetch_all(
            "SELECT * FROM tasks ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END, due_date"
        )
        return [Task.model_validate(row) for row in rows]

    async def create_task(self, task: TaskCreate) -> Task:
        task_id = generate_uuid()
        await database.execute(
            """
            INSERT INTO tasks (id, title, status, priority, due_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, task.title, task.status, task.priority, task.due_date),
        )
        return Task(id=task_id, **task.model_dump())

    async def update_task(self, task_id: str, update: TaskUpdate) -> Task:
        values = update.model_dump(exclude_unset=True)
        if not values:
            row = await database.fetch_one("SELECT * FROM tasks WHERE id = ?", (task_id,))
            if row is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
            return Task.model_validate(row)

        columns = {
            "title": "title",
            "status": "status",
            "priority": "priority",
            "due_date": "due_date",
        }
        assignments = ", ".join(f"{columns[key]} = ?" for key in values)
        updated = await database.execute(
            f"UPDATE tasks SET {assignments} WHERE id = ?", (*values.values(), task_id)  # nosec B608
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        row = await database.fetch_one("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return Task.model_validate(row)

    async def delete_task(self, task_id: str) -> bool:
        return bool(await database.execute("DELETE FROM tasks WHERE id = ?", (task_id,)))
