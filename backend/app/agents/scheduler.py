"""Execution Scheduler for traversing and executing DAG goals."""

import asyncio

from app.core.logging import get_logger
from app.db.database import database
from app.schemas.planning import Status
from app.services.planning_service import planning_service
from app.agents.agent_manager import AgentManager
from app.tools.executor import PermissionRequiredError

logger = get_logger(__name__)

class ExecutionScheduler:
    """Traverses Goal DAGs and orchestrates automated task execution."""

    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
        self._running = False
        self._task_queue = asyncio.Queue()

    async def start(self):
        """Starts the background scheduler loop."""
        if self._running:
            return
        self._running = True
        asyncio.create_task(self._loop())
        logger.info("ExecutionScheduler started.")

    def stop(self):
        """Stops the scheduler loop."""
        self._running = False
        logger.info("ExecutionScheduler stopped.")

    async def trigger_evaluation(self, goal_id: str):
        """Triggers a re-evaluation of a specific goal's DAG."""
        await self._task_queue.put(goal_id)

    async def _loop(self):
        while self._running:
            try:
                # Wait for a goal to evaluate, or evaluate all periodically
                # For now, we wait on explicit triggers
                goal_id = await self._task_queue.get()
                await self._evaluate_goal(goal_id)
                self._task_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                await asyncio.sleep(5) # Backoff on error

    async def _evaluate_goal(self, goal_id: str):
        """Evaluates a goal's DAG and executes unblocked tasks."""
        logger.info(f"Evaluating DAG for Goal {goal_id}")
        
        # 1. Find all PENDING tasks for this goal
        pending_tasks = await database.fetch_all(
            """
            SELECT t.id, t.title, t.requires_approval, t.assigned_agent
            FROM planning_tasks t
            JOIN milestones m ON t.milestone_id = m.id
            WHERE m.goal_id = ? AND t.status = ?
            """,
            (goal_id, Status.PENDING.value)
        )
        
        for task_row in pending_tasks:
            task_id = task_row["id"]
            
            # 2. Check dependencies
            deps = await database.fetch_all(
                """
                SELECT d.depends_on_task_id, pt.status
                FROM task_dependencies d
                JOIN planning_tasks pt ON d.depends_on_task_id = pt.id
                WHERE d.task_id = ?
                """,
                (task_id,)
            )
            
            is_unblocked = True
            for dep in deps:
                if dep["status"] != Status.COMPLETED.value:
                    is_unblocked = False
                    break
                    
            if not is_unblocked:
                continue # Still blocked
                
            # 3. Handle unblocked task
            requires_approval = bool(task_row["requires_approval"])
            assigned_agent = task_row["assigned_agent"]
            
            if requires_approval:
                # Can't auto-execute. Just leave as pending, UI will show it as executable (unblocked)
                # Alternatively, we could set status to 'READY' if we had such a state
                pass
            elif assigned_agent:
                # Safe to execute in background
                logger.info(f"Auto-executing task {task_row['title']} via agent {assigned_agent}")
                await planning_service.update_task_status(task_id, Status.IN_PROGRESS)
                asyncio.create_task(self._execute_task_with_agent(task_id, assigned_agent, task_row["title"]))
            else:
                # Unblocked, no approval, but no agent assigned. It's a manual task for the user.
                pass
                
    async def _execute_task_with_agent(self, task_id: str, agent_name: str, task_title: str):
        try:
            agent = self.agent_manager.spawn_agent(agent_name)
            
            # Retrieve full task details for context
            # In a real system we'd pass the goal context, memory, etc.
            
            # Simple execution (simulating non-streaming here)
            final_content = ""
            async for chunk in agent.execute(task_title, [], approved_permissions=[]):
                final_content += chunk + "\\n"
                
            # Complete task
            await database.execute(
                "UPDATE planning_tasks SET status = ?, expected_output = ? WHERE id = ?",
                (Status.COMPLETED.value, final_content, task_id)
            )
            
            # Re-evaluate goal to unblock downstream tasks
            row = await database.fetch_one(
                "SELECT m.goal_id FROM planning_tasks t JOIN milestones m ON t.milestone_id = m.id WHERE t.id = ?",
                (task_id,)
            )
            if row:
                await planning_service.update_task_status(task_id, Status.COMPLETED)
                await self.trigger_evaluation(row["goal_id"])
                
        except PermissionRequiredError:
            # We hit a permissions barrier. We must pause.
            await planning_service.update_task_status(task_id, Status.BLOCKED)
            logger.warning(f"Task {task_id} blocked due to missing permissions.")
            
        except Exception as e:
            logger.error(f"Agent failed to execute task {task_id}: {e}")
            await planning_service.update_task_status(task_id, Status.FAILED)
