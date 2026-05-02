import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.middleware.auth import get_current_user, get_project_member, require_admin
from app.models import ProjectMember, ProjectMemberRole, User
from app.schemas.project import MemberInvite

router = APIRouter(prefix="/api/projects/{project_id}/members", tags=["members"])


class MemberRoleUpdate(BaseModel):
    role: ProjectMemberRole


@router.get("")
def list_members(
    membership: Annotated[ProjectMember, Depends(get_project_member)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    members = db.scalars(
        select(ProjectMember)
        .options(selectinload(ProjectMember.user))
        .where(ProjectMember.project_id == membership.project_id)
        .order_by(ProjectMember.joined_at.asc())
    ).all()
    return [
        {
            "id": member.id,
            "project_id": member.project_id,
            "user_id": member.user_id,
            "role": member.role,
            "joined_at": member.joined_at,
            "user": {
                "id": member.user.id,
                "name": member.user.name,
                "email": member.user.email,
                "created_at": member.user.created_at,
            },
        }
        for member in members
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def invite_member(
    payload: MemberInvite,
    admin_membership: Annotated[ProjectMember, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing_member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == admin_membership.project_id,
            ProjectMember.user_id == user.id,
        )
    )
    if existing_member is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a project member")

    member = ProjectMember(project_id=admin_membership.project_id, user_id=user.id, role=payload.role)
    db.add(member)
    db.commit()
    db.refresh(member)

    return {
        "id": member.id,
        "project_id": member.project_id,
        "user_id": member.user_id,
        "role": member.role,
        "joined_at": member.joined_at,
        "user": {"id": user.id, "name": user.name, "email": user.email, "created_at": user.created_at},
    }


@router.put("/{user_id}")
def change_member_role(
    user_id: Annotated[uuid.UUID, Path()],
    payload: MemberRoleUpdate,
    admin_membership: Annotated[ProjectMember, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    member = db.scalar(
        select(ProjectMember)
        .options(selectinload(ProjectMember.user))
        .where(
            ProjectMember.project_id == admin_membership.project_id,
            ProjectMember.user_id == user_id,
        )
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    member.role = payload.role
    db.commit()
    db.refresh(member)

    return {
        "id": member.id,
        "project_id": member.project_id,
        "user_id": member.user_id,
        "role": member.role,
        "joined_at": member.joined_at,
        "user": {
            "id": member.user.id,
            "name": member.user.name,
            "email": member.user.email,
            "created_at": member.user.created_at,
        },
    }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    user_id: Annotated[uuid.UUID, Path()],
    current_user: Annotated[User, Depends(get_current_user)],
    admin_membership: Annotated[ProjectMember, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot remove yourself")

    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == admin_membership.project_id,
            ProjectMember.user_id == user_id,
        )
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    db.delete(member)
    db.commit()
