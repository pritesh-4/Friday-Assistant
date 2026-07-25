"""Service for handling goals, milestones, and planning tasks."""


from app.core.logging import get_logger
from app.db.database import database
from app.schemas.planning import Goal, GoalBase, Status
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger(__name__)

class PlanningService:
    async def create_goal(self, goal_data: GoalBase) -> Goal:
        """Create a full goal hierarchy (Goal -> Milestones -> Tasks -> Dependencies)."""
        goal_id = generate_uuid()
        now = get_utc_now().isoformat()
        
        await database.execute(
            """
            INSERT INTO goals (id, title, description, category, status, progress_percent, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (goal_id, goal_data.title, goal_data.description, goal_data.category.value, Status.PENDING.value, 0, now, now)
        )
        
        # We need to map client-provided task dependencies (which might use temporary IDs or titles) 
        # to actual database IDs. For simplicity in the API, we assume the GoalBase already has dependencies mapped
        # or we generate UUIDs up front.
        
        # Let's pre-generate UUIDs for all tasks to handle dependencies
        task_id_map = {} # client temporary id or title -> real uuid
        
        # Pass 1: generate UUIDs
        for m_idx, milestone in enumerate(goal_data.milestones):
            for t_idx, task in enumerate(milestone.tasks):
                real_id = generate_uuid()
                task_id_map[task.title] = real_id # Using title as mapping key for simplicity in LLM generation
                
        # Pass 2: insert everything
        for m_idx, milestone in enumerate(goal_data.milestones):
            milestone_id = generate_uuid()
            await database.execute(
                """
                INSERT INTO milestones (id, goal_id, title, status, order_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (milestone_id, goal_id, milestone.title, Status.PENDING.value, m_idx, now, now)
            )
            
            for task in milestone.tasks:
                task_id = task_id_map[task.title]
                await database.execute(
                    """
                    INSERT INTO planning_tasks (id, milestone_id, title, description, status, priority, 
                        estimated_duration, requires_approval, assigned_agent, expected_output, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_id, milestone_id, task.title, task.description, Status.PENDING.value, 
                        task.priority.value, task.estimated_duration, 1 if task.requires_approval else 0,
                        task.assigned_agent, task.expected_output, now, now
                    )
                )
                
                # Insert dependencies
                for dep_title in task.depends_on:
                    if dep_title in task_id_map:
                        dep_id = task_id_map[dep_title]
                        await database.execute(
                            """
                            INSERT INTO task_dependencies (task_id, depends_on_task_id)
                            VALUES (?, ?)
                            """,
                            (task_id, dep_id)
                        )
                        
        return await self.get_goal(goal_id)

    async def get_goal(self, goal_id: str) -> Goal | None:
        """Fetch a goal and its full hierarchy."""
        row = await database.fetch_one("SELECT * FROM goals WHERE id = ?", (goal_id,))
        if not row:
            return None
            
        goal = dict(row)
        
        milestone_rows = await database.fetch_all("SELECT * FROM milestones WHERE goal_id = ? ORDER BY order_index ASC", (goal_id,))
        milestones = []
        
        for m_row in milestone_rows:
            m = dict(m_row)
            task_rows = await database.fetch_all("SELECT * FROM planning_tasks WHERE milestone_id = ?", (m["id"],))
            tasks = []
            for t_row in task_rows:
                t = dict(t_row)
                t["requires_approval"] = bool(t["requires_approval"])
                # Fetch dependencies
                dep_rows = await database.fetch_all("SELECT depends_on_task_id FROM task_dependencies WHERE task_id = ?", (t["id"],))
                t["depends_on"] = [r["depends_on_task_id"] for r in dep_rows]
                tasks.append(t)
            
            m["tasks"] = tasks
            milestones.append(m)
            
        goal["milestones"] = milestones
        return Goal.model_validate(goal)

    async def list_goals(self) -> list[Goal]:
        """Fetch all goals without their full hierarchy (for overview)."""
        rows = await database.fetch_all("SELECT * FROM goals ORDER BY created_at DESC")
        return [Goal.model_validate(dict(row)) for row in rows]

    async def update_task_status(self, task_id: str, new_status: Status) -> None:
        """Update a task's status and trigger progress recalculation."""
        now = get_utc_now().isoformat()
        await database.execute(
            "UPDATE planning_tasks SET status = ?, updated_at = ? WHERE id = ?",
            (new_status.value, now, task_id)
        )
        # Recalculate goal progress
        await self._recalculate_progress_from_task(task_id)

    async def _recalculate_progress_from_task(self, task_id: str):
        row = await database.fetch_one(
            """
            SELECT g.id as goal_id 
            FROM planning_tasks t
            JOIN milestones m ON t.milestone_id = m.id
            JOIN goals g ON m.goal_id = g.id
            WHERE t.id = ?
            """,
            (task_id,)
        )
        if row:
            await self._recalculate_goal_progress(row["goal_id"])

    async def _recalculate_goal_progress(self, goal_id: str):
        # Very simple recalculation: completed tasks / total tasks
        rows = await database.fetch_all(
            """
            SELECT t.status
            FROM planning_tasks t
            JOIN milestones m ON t.milestone_id = m.id
            WHERE m.goal_id = ?
            """,
            (goal_id,)
        )
        if not rows:
            return
            
        total = len(rows)
        completed = sum(1 for r in rows if r["status"] == Status.COMPLETED.value)
        progress = int((completed / total) * 100)
        
        now = get_utc_now().isoformat()
        await database.execute(
            "UPDATE goals SET progress_percent = ?, updated_at = ? WHERE id = ?",
            (progress, now, goal_id)
        )

# Global singleton
planning_service = PlanningService()
