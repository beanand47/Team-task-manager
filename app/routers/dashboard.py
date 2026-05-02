from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import Project, ProjectMember, Task, TaskStatus, User
from app.schemas.project import ProjectResponse
from app.schemas.task import TaskResponse

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    member_project_ids = select(ProjectMember.project_id).where(ProjectMember.user_id == current_user.id)

    my_tasks = db.scalars(
        select(Task)
        .where(
            Task.assigned_to == current_user.id,
            Task.status != TaskStatus.done,
            Task.project_id.in_(member_project_ids),
        )
        .order_by(Task.due_date.asc().nulls_last(), Task.created_at.desc())
    ).all()

    overdue_tasks = db.scalars(
        select(Task)
        .where(
            Task.assigned_to == current_user.id,
            Task.status != TaskStatus.done,
            Task.due_date < date.today(),
            Task.project_id.in_(member_project_ids),
        )
        .order_by(Task.due_date.asc())
    ).all()

    projects = db.scalars(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == current_user.id)
        .order_by(Project.created_at.desc())
    ).all()

    count_rows = db.execute(
        select(Task.project_id, Task.status, func.count(Task.id))
        .where(Task.project_id.in_(member_project_ids))
        .group_by(Task.project_id, Task.status)
    ).all()

    counts_by_project = {
        project.id: {"total": 0, "todo": 0, "in_progress": 0, "done": 0}
        for project in projects
    }
    for project_id, task_status, count in count_rows:
        bucket = counts_by_project[project_id]
        bucket[task_status.value] = count
        bucket["total"] += count

    project_stats = [
        {
            "project": ProjectResponse.model_validate(project),
            "total": counts_by_project[project.id]["total"],
            "todo": counts_by_project[project.id]["todo"],
            "in_progress": counts_by_project[project.id]["in_progress"],
            "done": counts_by_project[project.id]["done"],
        }
        for project in projects
    ]

    return {
        "my_tasks": [TaskResponse.model_validate(task) for task in my_tasks],
        "overdue_tasks": [TaskResponse.model_validate(task) for task in overdue_tasks],
        "project_stats": project_stats,
        "total_projects": len(projects),
        "total_my_tasks": len(my_tasks),
        "total_overdue": len(overdue_tasks),
    }
