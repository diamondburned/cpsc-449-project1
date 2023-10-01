import collections
import contextlib
import logging.config
import secrets
import base64
import time
import aiosqlite

from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from database import get_db, fetch_rows, authorize_user

from models import *
from model_requests import *


app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def index():
    html_content = """
    <html>
        <head>
            <title>FastAPI</title>
        </head>
        <body>
            <h1>Homepage:</h1>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/login")
async def login(
    request: LoginRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> LoginResponse:
    # Have the token live for 7 days
    TOKEN_AGE = 7 * 24 * 60 * 60

    async with db.execute(
        """
        SELECT *
        FROM users
        WHERE first_name = ? AND last_name = ?
        """,
        (request.first_name, request.last_name),
    ) as cursor:
        user = await cursor.fetchone()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        user = User(**dict(user))
        token = secrets.token_urlsafe(32)
        expiry = int(time.time()) + TOKEN_AGE

        return LoginResponse(user=user, token=token, expiry=expiry)


def assert_role(user: User, role: Role):
    if user.role != role:
        raise HTTPException(status_code=403, detail="Forbidden")


@app.get("/users")
async def list_users(
    db: aiosqlite.Connection = Depends(get_db),
    user: User = Depends(authorize_user),
) -> list[User]:
    return await fetch_rows(db, User, "SELECT * FROM users")


@app.get("/departments")
async def list_departments(
    db: aiosqlite.Connection = Depends(get_db),
    user: User = Depends(authorize_user),
) -> list[Department]:
    return await fetch_rows(db, Department, "SELECT * FROM departments")


@app.get("/courses")
async def list_courses(
    db: aiosqlite.Connection = Depends(get_db),
    user: User = Depends(authorize_user),
) -> list[Course]:
    return await fetch_rows(db, Course, "SELECT * FROM courses")


@app.get("/sections")
async def list_sections(
    db: aiosqlite.Connection = Depends(get_db),
    user: User = Depends(authorize_user),
) -> list[Section]:
    return await fetch_rows(db, Section, "SELECT * FROM sections")


@app.get("/enrollments")
async def list_enrollments(
    db: aiosqlite.Connection = Depends(get_db),
    user: User = Depends(authorize_user),
) -> list[Enrollment]:
    return await fetch_rows(db, Enrollment, "SELECT * FROM enrollments")


@app.get("/waitlist")
async def list_waitlist(
    db: aiosqlite.Connection = Depends(get_db),
    user: User = Depends(authorize_user),
) -> list[Waitlist]:
    return await fetch_rows(db, Waitlist, "SELECT * FROM waitlist")
