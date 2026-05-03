# Team Task Manager

Team Task Manager is a full-stack Python web application for managing projects, members, and team tasks through a FastAPI backend and a Jinja2-powered frontend. It includes JWT authentication, PostgreSQL persistence, project membership roles, Kanban task updates, dashboard stats, and deployment-ready Railway configuration.

## Tech Stack

- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Alembic
- Pydantic v2
- pydantic-settings
- python-jose JWT authentication
- passlib bcrypt password hashing
- Jinja2 templates
- Vanilla JavaScript
- Uvicorn
- Railway

## Local Setup

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd team-task-manager
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create your environment file and fill in values:
   ```bash
   cp .env.example .env
   ```

4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Seed sample data:
   ```bash
   python seed.py
   ```

6. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

7. Open the app:
   ```text
   http://localhost:8000
   ```

## Test Login Credentials

- admin@test.com / Test1234
- member1@test.com / Test1234
- member2@test.com / Test1234

## API Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Railway Deployment

1. Push this project to a Git repository.
2. Create a new Railway project from the repository.
3. Add a PostgreSQL database service.
4. Set environment variables:
   ```text
   DATABASE_URL=<Railway PostgreSQL connection URL>
   SECRET_KEY=<a secure random string at least 32 characters long>
   ```
5. Deploy the service. Railway will use `railway.toml` to run:
   ```bash
   alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
6. After deployment, optionally run the seeder from a Railway shell:
   ```bash
   python seed.py
   ```

## Live URL
https://team-task-manager-production-324a.up.railway.app/
