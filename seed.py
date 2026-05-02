from datetime import date, timedelta

from passlib.context import CryptContext
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Project, ProjectMember, ProjectMemberRole, Task, TaskPriority, TaskStatus, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

USERS = [
    {"name": "Alex Admin", "email": "admin@test.com", "password": "Test1234"},
    {"name": "Sam Member", "email": "member1@test.com", "password": "Test1234"},
    {"name": "Jordan Dev", "email": "member2@test.com", "password": "Test1234"},
]

PROJECTS = [
    {
        "name": "Website Redesign",
        "description": "Refresh the public marketing site, improve conversion paths, and clean up the content structure.",
    },
    {
        "name": "Mobile App",
        "description": "Build the first mobile experience for task updates, notifications, and lightweight project tracking.",
    },
]

TASK_BLUEPRINTS = [
    ("Audit current UX", "Review existing flows and capture friction points.", TaskStatus.todo, TaskPriority.medium, -3, 1),
    ("Create visual direction", "Prepare updated typography, colors, and component examples.", TaskStatus.in_progress, TaskPriority.high, 4, 0),
    ("Implement dashboard", "Build the main dashboard experience and connect it to live API data.", TaskStatus.todo, TaskPriority.high, 7, 2),
    ("Write acceptance tests", "Cover the most important task and project workflows.", TaskStatus.in_progress, TaskPriority.medium, 2, 1),
    ("Polish empty states", "Improve first-run and no-data experiences across the app.", TaskStatus.done, TaskPriority.low, -1, 2),
    ("Prepare launch notes", "Summarize shipped changes and rollout steps for the team.", TaskStatus.done, TaskPriority.medium, 10, 0),
]


def password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_or_create_user(db, user_data: dict[str, str]) -> User:
    user = db.scalar(select(User).where(User.email == user_data["email"]))
    if user is not None:
        user.name = user_data["name"]
        user.password_hash = password_hash(user_data["password"])
        return user

    user = User(
        name=user_data["name"],
        email=user_data["email"],
        password_hash=password_hash(user_data["password"]),
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_project(db, project_data: dict[str, str], owner: User) -> Project:
    project = db.scalar(select(Project).where(Project.name == project_data["name"]))
    if project is not None:
        project.description = project_data["description"]
        project.owner_id = owner.id
        return project

    project = Project(
        name=project_data["name"],
        description=project_data["description"],
        owner_id=owner.id,
    )
    db.add(project)
    db.flush()
    return project


def ensure_membership(db, project: Project, user: User, role: ProjectMemberRole) -> None:
    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id,
        )
    )
    if membership is None:
        db.add(ProjectMember(project_id=project.id, user_id=user.id, role=role))
    else:
        membership.role = role


def reset_project_tasks(db, project: Project, users: list[User]) -> None:
    for task in db.scalars(select(Task).where(Task.project_id == project.id)).all():
        db.delete(task)
    db.flush()

    today = date.today()
    for index, (title, description, status, priority, due_offset, assignee_index) in enumerate(TASK_BLUEPRINTS, start=1):
        db.add(
            Task(
                project_id=project.id,
                title=f"{title} ({project.name})",
                description=description,
                status=status,
                priority=priority,
                assigned_to=users[assignee_index].id,
                created_by=users[0].id,
                due_date=today + timedelta(days=due_offset),
            )
        )


def main() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        users = [get_or_create_user(db, user_data) for user_data in USERS]
        projects = [get_or_create_project(db, project_data, users[0]) for project_data in PROJECTS]

        for project in projects:
            for index, user in enumerate(users):
                role = ProjectMemberRole.admin if index == 0 else ProjectMemberRole.member
                ensure_membership(db, project, user, role)
            reset_project_tasks(db, project, users)

        db.commit()

    print("Seed complete.")
    print("Login credentials:")
    for user in USERS:
        print(f"- {user['email']} / {user['password']} ({user['name']})")


if __name__ == "__main__":
    main()
