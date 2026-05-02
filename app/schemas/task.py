import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import TaskPriority, TaskStatus


def validate_due_date_not_past(value: date | None) -> date | None:
    if value is not None and value < date.today():
        raise ValueError("Due date cannot be in the past")
    return value


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    priority: TaskPriority = TaskPriority.medium
    assigned_to: uuid.UUID | None = None
    due_date: date | None = None

    @field_validator("due_date")
    @classmethod
    def due_date_cannot_be_past(cls, value: date | None) -> date | None:
        return validate_due_date_not_past(value)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assigned_to: uuid.UUID | None = None
    due_date: date | None = None

    @field_validator("due_date")
    @classmethod
    def due_date_cannot_be_past(cls, value: date | None) -> date | None:
        return validate_due_date_not_past(value)


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    assigned_to: uuid.UUID | None
    created_by: uuid.UUID
    due_date: date | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
