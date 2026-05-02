import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user, get_project_member, require_admin
from app.models import ProjectMember, ProjectMemberRole, Task, TaskPriority, TaskStatus, User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(tags=["tasks"])


def get_task_or_404(task_id: uuid.UUID, db: Session) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def get_membership_for_project(project_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> ProjectMember | None:
    return db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )


def ensure_project_member(project_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> ProjectMember:
    membership = get_membership_for_project(project_id, user_id, db)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this project")
    return membership


@router.get("/api/projects/{project_id}/tasks", response_model=list[TaskResponse])
def list_tasks(
    membership: Annotated[ProjectMember, Depends(get_project_member)],
    db: Annotated[Session, Depends(get_db)],
    task_status: Annotated[TaskStatus | None, Query(alias="status")] = None,
    priority: TaskPriority | None = None,
    assigned_to: uuid.UUID | None = None,
) -> list[Task]:
    query = select(Task).where(Task.project_id == membership.project_id)
    if task_status is not None:
        query = query.where(Task.status == task_status)
    if priority is not None:
        query = query.where(Task.priority == priority)
    if assigned_to is not None:
        query = query.where(Task.assigned_to == assigned_to)

    return list(db.scalars(query.order_by(Task.created_at.desc())).all())


@router.post("/api/projects/{project_id}/tasks", status_code=status.HTTP_201_CREATED, response_model=TaskResponse)
def create_task(
    payload: TaskCreate,
    admin_membership: Annotated[ProjectMember, Depends(require_admin)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Task:
    if payload.assigned_to is not None:
        ensure_project_member(admin_membership.project_id, payload.assigned_to, db)

    task = Task(
        project_id=admin_membership.project_id,
        title=payload.title.strip(),
        description=payload.description,
        priority=payload.priority,
        assigned_to=payload.assigned_to,
        created_by=current_user.id,
        due_date=payload.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/api/tasks/{task_id}", response_model=TaskResponse)
def get_task_detail(
    task_id: Annotated[uuid.UUID, Path()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Task:
    task = get_task_or_404(task_id, db)
    ensure_project_member(task.project_id, current_user.id, db)
    return task


@router.put("/api/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: Annotated[uuid.UUID, Path()],
    payload: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Task:
    task = get_task_or_404(task_id, db)
    membership = ensure_project_member(task.project_id, current_user.id, db)
    updates = payload.model_dump(exclude_unset=True)

    if membership.role != ProjectMemberRole.admin:
        allowed_keys = {"status"}
        if set(updates) - allowed_keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Project members can only update task status",
            )

    if "assigned_to" in updates and updates["assigned_to"] is not None:
        ensure_project_member(task.project_id, updates["assigned_to"], db)

    for field, value in updates.items():
        if field == "title" and value is not None:
            value = value.strip()
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: Annotated[uuid.UUID, Path()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    task = get_task_or_404(task_id, db)
    membership = ensure_project_member(task.project_id, current_user.id, db)
    if membership.role != ProjectMemberRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project admin access is required")

    db.delete(task)
    db.commit()
