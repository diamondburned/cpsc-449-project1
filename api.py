import collections
import contextlib
import logging.config
import typing
import aiosqlite

from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from database import get_db, fetch_rows
from models import *


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


@app.get("/users")
async def list_users(db=Depends(get_db)) -> list[User]:
    users = await fetch_rows(db, "SELECT * FROM users")
    return [User(**user) for user in users]


@app.get("/departments")
async def list_departments(
    db=Depends(get_db),
) -> list[Department]:
    departments = await fetch_rows(db, "SELECT * FROM departments")
    return [Department(**department) for department in departments]


@app.get("/courses")
async def list_courses(db=Depends(get_db)) -> list[Course]:
    courses = await fetch_rows(db, "SELECT * FROM courses")
    return [Course(**course) for course in courses]


@app.get("/sections")
async def list_sections(db=Depends(get_db)) -> list[Section]:
    sections = await fetch_rows(db, "SELECT * FROM sections")
    return [Section(**section) for section in sections]


@app.get("/enrollments")
async def list_enrollments(db=Depends(get_db)) -> list[Enrollment]:
    enrollments = await fetch_rows(db, "SELECT * FROM enrollments")
    return [Enrollment(**enrollment) for enrollment in enrollments]


@app.get("/waitlist")
async def list_waitlist(db=Depends(get_db)) -> list[Waitlist]:
    waitlist = await fetch_rows(db, "SELECT * FROM waitlist")
    return [Waitlist(**waitlist) for waitlist in waitlist]
