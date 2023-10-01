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
    return await fetch_rows(db, User, "SELECT * FROM users")


@app.get("/departments")
async def list_departments(db=Depends(get_db)) -> list[Department]:
    return await fetch_rows(db, Department, "SELECT * FROM departments")


@app.get("/courses")
async def list_courses(db=Depends(get_db)) -> list[Course]:
    return await fetch_rows(db, Course, "SELECT * FROM courses")


@app.get("/sections")
async def list_sections(db=Depends(get_db)) -> list[Section]:
    return await fetch_rows(db, Section, "SELECT * FROM sections")


@app.get("/enrollments")
async def list_enrollments(db=Depends(get_db)) -> list[Enrollment]:
    return await fetch_rows(db, Enrollment, "SELECT * FROM enrollments")


@app.get("/waitlist")
async def list_waitlist(db=Depends(get_db)) -> list[Waitlist]:
    return await fetch_rows(db, Waitlist, "SELECT * FROM waitlist")
