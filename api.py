import collections
import contextlib
import logging.config
import secrets
import base64
import time
import sqlite3
import database

from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from database import extract_row, get_db, fetch_rows, fetch_row

from models import *
from model_requests import *


app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def index():
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
# X /users/{user_id}/{section_id}/enrollments (enroll)
# X /courses (add course)
# X /courses/1/sections (add section)
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
def list_courses(
    db: sqlite3.Connection = Depends(get_db),
) -> list[Course]:
    return database.list_courses(db)


@app.get("/courses/{course_id}")
def get_course(
    course_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> Course:
    courses = database.list_courses(db, [course_id])
    if len(courses) == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return courses[0]


@app.get("/courses/{course_id}/sections")
def list_course_sections(
    course_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> list[Section]:
    section_ids = fetch_rows(
        db,
        """
        SELECT id
        FROM sections
        WHERE course_id = ?
        """,
        (course_id,),
    )
    return database.list_sections(db, [row["sections.id"] for row in section_ids])


@app.get("/users")
def list_users(
    db: sqlite3.Connection = Depends(get_db),
) -> list[User]:
    users_rows = fetch_rows(db, "SELECT * FROM users")
    return [User(**dict(row)) for row in users_rows]


@app.get("/users/{user_id}")
def get_user(
    user_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> User:
    user = fetch_row(db, "SELECT * FROM users WHERE id = ?", (user_id,))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**extract_row(user, "users"))


@app.get("/users/{user_id}/enrollments")
def list_user_enrollments(
    user_id: int,
    status=EnrollmentStatus.ENROLLED,
    db: sqlite3.Connection = Depends(get_db),
) -> list[Enrollment]:
    print(user_id, status)
    rows = fetch_rows(
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
    return database.list_enrollments(
        db,
        [(row["user_id"], row["section_id"]) for row in rows],
    )


@app.post("/users/{user_id}/enrollments")  # student attempt to enroll in class
def create_enrollment(
    user_id: int,
    enrollment: CreateEnrollmentRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> Enrollment:
    d = {
        "user": user_id,
        "section": enrollment.section,
    }

    # Verify that the class still has space.
    cur = db.execute(
        """
        SELECT id
        FROM sections as s
        WHERE s.id = :section
        AND s.capacity > (SELECT COUNT(*) FROM enrollments WHERE section_id = :section)
        AND s.freeze = FALSE 
        """,
        d,
    )
    if cur:
        # If there is space, enroll the student.
        db.execute(
            """
            INSERT INTO enrollments (user_id, section_id, status, grade, date)
            VALUES(:user, :section, 'Enrolled', NULL, CURRENT_TIMESTAMP)
            """,
            d,
        )
    else:
        # Otherwise, try to add them to the waitlist.
        cur = db.execute(
            """
            SELECT id
            FROM sections as s
            WHERE s.id = :section
            AND s.waitlist_capacity > (SELECT COUNT(*) FROM waitlist WHERE section_id = :section)
            AND s.freeze = FALSE
            """,
            d,
        )
        if cur:
            db.execute(
                """
                INSERT INTO waitlist (user_id, section_id, position, date)
                VALUES(:user, :section, (SELECT COUNT(*) FROM waitlist WHERE section_id = :section)+1, CURRENT_TIMESTAMP)
                """,
                d,
            )
            db.execute(
                """
                INSERT INTO enrollments (user_id, section_id, status, grade, date)
                VALUES(:user, :section, 'Waitlisted', NULL, CURRENT_TIMESTAMP)
                """,
                d,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Section is full and waitlist is full.",
            )

    enrollments = database.list_enrollments(db, [(d["user"], d["section"])])
    return enrollments[0]


@app.post("/courses")
def add_course(course: CoursePost, db: sqlite3.Connection = Depends(get_db)):
    c = dict(course)

    try:
        cur = db.execute(
            """
                INSERT INTO courses(code, name, department_id)
                VALUES(:code, :name, :department_id)
            """,
            c,
        )
    except Exception:
        raise HTTPException(status_code=409, detail=f"Failed to add course:")
    return c


@app.post("/courses/{course_id}/sections")
def add_section(
    course_id: int, section: SectionPost, db: sqlite3.Connection = Depends(get_db)
):
    section.course_id = course_id

    s = dict(section)

    try:
        cur = db.execute(
            """
                INSERT INTO sections(course_id, classroom, capacity, waitlist_capacity, day, begin_time, end_time, freeze, instructor_id)
                VALUES(:course_id, :classroom, :capacity, :waitlist_capacity, :day, :begin_time, :end_time, :freeze, :instructor_id)
            """,
            s,
        )
    except Exception as e:
        raise HTTPException(status_code=409, detail=f"Failed to add course:{e}")
    return s


#
# @app.get("/waitlist")
# async def list_waitlist(
#     db: sqlite3.Connection = Depends(get_db),
#     user: User = Depends(authorize_user),
# ) -> list[Waitlist]:
#     return await fetch_rows(db, Waitlist, "SELECT * FROM waitlist")

# @app.post("/login")
# async def login(
#     request: LoginRequest,
#     db: sqlite3.Connection = Depends(get_db),
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
