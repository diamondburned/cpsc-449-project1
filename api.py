import collections
import contextlib
import logging.config
import secrets
import base64
import time
import database
import aiosqlite

from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from database import extract_row, get_db, fetch_rows, fetch_row

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


# @app.post("/login")
# async def login(
#     request: LoginRequest,
#     db: aiosqlite.Connection = Depends(get_db),
# ) -> LoginResponse:
#     # Have the token live for 7 days
#     TOKEN_AGE = 7 * 24 * 60 * 60
#
#     async with db.execute(
#         """
#         SELECT *
#         FROM users
#         WHERE first_name = ? AND last_name = ?
#         """,
#         (request.first_name, request.last_name),
#     ) as cursor:
#         user = await cursor.fetchone()
#         if user is None:
#             raise HTTPException(status_code=404, detail="User not found")
#
#         user = User(**dict(user))
#         token = secrets.token_urlsafe(32)
#         expiry = int(time.time()) + TOKEN_AGE
#
#         await db.execute(
#             """
#             INSERT INTO sessions (user_id, token, expiry)
#             VALUES (?, ?, ?)
#             """,
#             (user.id, token, expiry),
#         )
#
#         return LoginResponse(user=user, token=token, expiry=expiry)


# The API should allow students to:
#  - List available classes (/courses)
#  - Attempt to enroll in a class
#  - Drop a class
#
# Instructors should be able to:
#  - View current enrollment for their classes (/users/1/enrollments)
#  - View students who have dropped the class (/users/1/enrollments?status=Dropped)
#  - Drop students administratively (e.g. if they do not show up to class)
#
# The registrar should be able to:
#  - Add new classes and sections
#  - Remove existing sections
#  - Change the instructor for a section

# API draft:
#
# GET
#
# X /courses
# X /courses/1
# X /courses/1/sections
# X /users
# X /users/1/enrollments (all enrolled or instructing courses)
# X /users/1/enrollments?status=Dropped (all dropped classes)
#
# POST
#
#   /users/1/enrollments (enroll)
#   /courses (add course)
#   /courses/1/sections (add section)
#
# PATCH
#
#   /courses/1/sections/2 (change section, registrar only)
#
# DELETE
#
#   /courses/1
#   /courses/1/sections/1


@app.get("/courses")
async def list_courses(
    db: aiosqlite.Connection = Depends(get_db),
) -> list[Course]:
    return await database.list_courses(db)


@app.get("/courses/{course_id}")
async def get_course(
    course_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> Course:
    courses = await database.list_courses(db, [course_id])
    if len(courses) == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return courses[0]


@app.get("/courses/{course_id}/sections")
async def list_course_sections(
    course_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> list[Section]:
    section_ids = await fetch_rows(
        db,
        """
        SELECT id
        FROM sections
        WHERE course_id = ?
        """,
        (course_id,),
    )
    return await database.list_sections(db, [row["sections.id"] for row in section_ids])


@app.get("/users")
async def list_users(
    db: aiosqlite.Connection = Depends(get_db),
) -> list[User]:
    users_rows = await fetch_rows(db, "SELECT * FROM users")
    return [User(**dict(row)) for row in users_rows]


@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> User:
    user = await fetch_row(db, "SELECT * FROM users WHERE id = ?", (user_id,))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**extract_row(user, "users"))


@app.get("/users/{user_id}/enrollments")
async def list_user_enrollments(
    user_id: int,
    status=EnrollmentStatus.ENROLLED,
    db: aiosqlite.Connection = Depends(get_db),
) -> list[Enrollment]:
    print(user_id, status)
    rows = await fetch_rows(
        db,
        """
        SELECT enrollments.user_id, enrollments.section_id
        FROM enrollments
        INNER JOIN sections ON sections.id = enrollments.section_id
        WHERE
            enrollments.status = ?
            AND (enrollments.user_id = ? OR sections.instructor_id = ?)
        """,
        ("Dropped", user_id, user_id),
    )
    rows = [extract_row(row, "enrollments") for row in rows]
    return await database.list_enrollments(
        db,
        [(row["user_id"], row["section_id"]) for row in rows],
    )


#
# @app.get("/waitlist")
# async def list_waitlist(
#     db: aiosqlite.Connection = Depends(get_db),
#     user: User = Depends(authorize_user),
# ) -> list[Waitlist]:
#     return await fetch_rows(db, Waitlist, "SELECT * FROM waitlist")
