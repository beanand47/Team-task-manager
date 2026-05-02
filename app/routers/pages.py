import uuid
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])
BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/")
def home() -> RedirectResponse:
    return RedirectResponse(url="/dashboard")


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.get("/signup")
def signup_page(request: Request):
    return templates.TemplateResponse("auth/signup.html", {"request": request})


@router.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/projects")
def projects_page(request: Request):
    return templates.TemplateResponse("projects/list.html", {"request": request})


@router.get("/projects/new")
def new_project_page(request: Request):
    return templates.TemplateResponse("projects/new.html", {"request": request})


@router.get("/projects/{project_id}")
def project_detail_page(request: Request, project_id: uuid.UUID):
    return templates.TemplateResponse("projects/detail.html", {"request": request, "project_id": project_id})


@router.get("/projects/{project_id}/members")
def project_members_page(request: Request, project_id: uuid.UUID):
    return templates.TemplateResponse("members/list.html", {"request": request, "project_id": project_id})


@router.get("/tasks/{task_id}")
def task_detail_page(request: Request, task_id: uuid.UUID):
    return templates.TemplateResponse("tasks/detail.html", {"request": request, "task_id": task_id})
