# Bank System FastAPI

Web-based banking system for managing clients, bank accounts and credit services.

## Technologies

- Python
- FastAPI
- SQLAlchemy
- MySQL
- Alembic
- Pydantic
- Jinja2
- Pytest

## Project structure

The project follows a code-first approach.  
SQLAlchemy models are the source of truth and Alembic migrations will generate the database schema.

## Run project

```bash
uvicorn app.main:app --reload

http://127.0.0.1:8000/docs


---

## 13. Install packages and update requirements

Run:

```powershell
pip install fastapi uvicorn sqlalchemy pymysql cryptography alembic pydantic pydantic-settings python-dotenv jinja2 python-multipart pytest
pip freeze > requirements.txt