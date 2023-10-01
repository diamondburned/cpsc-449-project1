import collections
import contextlib
import logging.config
import sqlite3
import typing

from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings

def get_db():
    with contextlib.closing(sqlite3.connect("database.db")) as db:
        db.row_factory = sqlite3.Row
        yield db

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def read_root():
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

@app.get("/users/")
def list_users(db: sqlite3.Connection = Depends(get_db)):
    users = db.execute("SELECT * FROM users")
    return {"users": users.fetchall()}

@app.get("/departments/")
def list_departments(db: sqlite3.Connection = Depends(get_db)):
    departments = db.execute("SELECT * FROM departments")
    return {"departments": departments.fetchall()}

@app.get("/courses/")
def list_courses(db: sqlite3.Connection = Depends(get_db)):
    courses = db.execute("SELECT * FROM courses")
    return {"courses": courses.fetchall()}

@app.get("/sections/")
def list_sections(db: sqlite3.Connection = Depends(get_db)):
    sections = db.execute("SELECT * FROM sections")
    return {"sections": sections.fetchall()}

@app.get("/enrollments/")
def list_enrollments(db: sqlite3.Connection = Depends(get_db)):
    enrollments = db.execute("SELECT * FROM enrollments")
    return {"enrollments": enrollments.fetchall()}

@app.get("/waitlist/")
def list_waitlist(db: sqlite3.Connection = Depends(get_db)):
    waitlist = db.execute("SELECT * FROM waitlist")
    return {"waitlist": waitlist.fetchall()}