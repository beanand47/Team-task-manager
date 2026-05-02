import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.middleware.auth import get_current_user, get_project_member, require_admin
from app.models import Project, ProjectMember, ProjectMemberRole, Task, TaskStatus, User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
def list_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ProjectResponse]:
    projects = db.scalars(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == current_user.id)
        .order_by(Project.created_at.desc())
    ).all()
    return [ProjectResponse.model_validate(project) for project in projects]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProjectResponse)
def create_project(
    payload: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Project:
    project = Project(
        name=payload.name.strip(),
        description=payload.description,
        owner_id=current_user.id,
    )
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=current_user.id, role=ProjectMemberRole.admin))
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}")
def get_project_details(
    membership: Annotated[ProjectMember, Depends(get_project_member)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    project = db.scalar(
        select(Project)
        .options(selectinload(Project.members).selectinload(ProjectMember.user))
        .where(Project.id == membership.project_id)
    )
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    counts = dict.fromkeys([status.value for status in TaskStatus], 0)
    rows = db.execute(
        select(Task.status, func.count(Task.id))
        .where(Task.project_id == project.id)
        .group_by(Task.status)
    ).all()
    for task_status, count in rows:
        counts[task_status.value] = count

    return {
        "project": ProjectResponse.model_validate(project),
        "members": [
            {
                "id": member.id,
                "user_id": member.user_id,
                "name": member.user.name,
                "email": member.user.email,
                "role": member.role,
                "joined_at": member.joined_at,
            }
            for member in project.members
        ],
        "task_counts": {
            "total": sum(counts.values()),
            "todo": counts["todo"],
            "in_progress": counts["in_progress"],
            "done": counts["done"],
        },
    }


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    payload: ProjectUpdate,
    membership: Annotated[ProjectMember, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> Project:
    project = db.get(Project, membership.project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates and updates["name"] is not None:
        project.name = updates["name"].strip()
    if "description" in updates:
        project.description = updates["description"]

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    membership: Annotated[ProjectMember, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    result = db.execute(delete(Project).where(Project.id == membership.project_id))
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    db.commit()
