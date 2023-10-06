import collections
import contextlib
import logging.config
import secrets
import base64
import time
import sqlite3
from typing import Optional
import database

from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from database import extract_row, get_db, fetch_rows, fetch_row

from models import *
from model_requests import *


app = FastAPI()


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
# X /sections
# X /sections/1
# X /sections/1/enrollments
# X /sections/1/waitlist
# X /courses/1/waitlist
# X /users
# X /users/1/enrollments
# X /users/1/sections
# X /users/1/waitlist
#
# POST
#
# X /users/{user_id}/enrollments (enroll)
# X /courses (add course)
# X /sections (add section)
#
# PATCH
#
#   /sections/2 (change section, registrar only)
#
# DELETE
#
#   X /users/{user_id}/enrollments/{section_id} (drop enrollment)
#   X /users/{user_id}/waitlist/{section_id} (drop waitlist)
#   X /sections/{section_id}/enrollments/{user_id}
#     (drop enrollment,
#      instructor only,
#      just call /users' method though)
#   X /sections/{section_id} (remove section, registrar only)


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


@app.get("/courses/{course_id}/waitlist")
def get_course_waitlist(
    course_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> list[Waitlist]:
    rows = fetch_rows(
        db,
        """
        SELECT waitlist.user_id, sections.id
        FROM waitlist
        INNER JOIN sections ON waitlist.section_id = sections.id
        WHERE sections.course_id = ? AND sections.deleted = FALSE
        """,
        (course_id,),
    )
    return database.list_waitlist(
        db,
        [(row["waitlist.user_id"], row["sections.id"]) for row in rows],
    )


@app.get("/sections")
def list_sections(
    course_id: Optional[int] = None,
    db: sqlite3.Connection = Depends(get_db),
) -> list[Section]:
    section_ids = fetch_rows(
        db,
        """
        SELECT id
        FROM sections
        WHERE deleted = FALSE
        """
        + ("" if course_id is None else "AND course_id = :course_id"),
        {"course_id": course_id},
    )
    return database.list_sections(db, [row["sections.id"] for row in section_ids])


@app.get("/sections/{section_id}")
def get_section(
    section_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> Section:
    sections = database.list_sections(db, [section_id])
    if len(sections) == 0:
        raise HTTPException(status_code=404, detail="Section not found")
    return sections[0]


@app.get("/sections/{section_id}/enrollments")
def list_section_enrollments(
    section_id: int,
    status=EnrollmentStatus.ENROLLED,
    db: sqlite3.Connection = Depends(get_db),
) -> list[Enrollment]:
    rows = fetch_rows(
        db,
        """
        SELECT enrollments.user_id, enrollments.section_id
        FROM enrollments
        INNER JOIN sections ON sections.id = enrollments.section_id
        WHERE
            enrollments.status = ?
            AND sections.deleted = FALSE
            AND sections.id = ?
        """,
        (status, section_id),
    )
    rows = [extract_row(row, "enrollments") for row in rows]
    return database.list_enrollments(
        db,
        [(row["user_id"], row["section_id"]) for row in rows],
    )


@app.get("/sections/{section_id}/waitlist")
def list_section_waitlist(
    section_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> list[Waitlist]:
    rows = fetch_rows(
        db,
        """
        SELECT waitlist.user_id, waitlist.section_id
        FROM waitlist
        INNER JOIN sections ON sections.id = waitlist.section_id
        WHERE waitlist.section_id = ? AND sections.deleted = FALSE
        """,
        (section_id,),
    )
    rows = [extract_row(row, "waitlist") for row in rows]
    return database.list_waitlist(
        db,
        [(row["user_id"], row["section_id"]) for row in rows],
    )


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
    rows = fetch_rows(
        db,
        """
        SELECT enrollments.user_id, enrollments.section_id
        FROM enrollments
        INNER JOIN sections ON sections.id = enrollments.section_id
        WHERE
            enrollments.status = ?
            AND sections.deleted = FALSE
            AND enrollments.user_id = ?
        """,
        (status, user_id),
    )
    rows = [extract_row(row, "enrollments") for row in rows]
    return database.list_enrollments(
        db,
        [(row["user_id"], row["section_id"]) for row in rows],
    )


@app.get("/users/{user_id}/sections")
def list_user_sections(
    user_id: int,
    type: ListUserSectionsType = ListUserSectionsType.ALL,
    db: sqlite3.Connection = Depends(get_db),
) -> list[Section]:
    q = """
        SELECT sections.id
        FROM sections
        INNER JOIN enrollments ON enrollments.section_id = sections.id
        WHERE sections.deleted = FALSE AND
    """

    wheres = []
    q += "("
    if type == ListUserSectionsType.ALL or type == ListUserSectionsType.ENROLLED:
        wheres.append("enrollments.user_id = :user_id")
    if type == ListUserSectionsType.ALL or type == ListUserSectionsType.INSTRUCTING:
        wheres.append("sections.instructor_id = :user_id")
    q += " OR ".join(wheres)
    q += ")"

    rows = fetch_rows(db, q, {"user_id": user_id})
    return database.list_sections(db, [row["sections.id"] for row in rows])


@app.get("/users/{user_id}/waitlist")
def list_user_waitlist(
    user_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> list[Waitlist]:
    section_ids = fetch_rows(
        db,
        """
        SELECT waitlist.user_id, waitlist.section_id
        FROM waitlist
        INNER JOIN sections ON sections.id = waitlist.section_id
        WHERE
            sections.deleted = FALSE
            AND (user_id = :user_id OR instructor_id = :user_id)
        """,
        {"user_id": user_id},
    )
    rows = [extract_row(row, "waitlist") for row in section_ids]
    return database.list_waitlist(
        db,
        [(row["user_id"], row["section_id"]) for row in rows],
    )


@app.post("/users/{user_id}/enrollments")  # student attempt to enroll in class
def create_enrollment(
    user_id: int,
    enrollment: CreateEnrollmentRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> CreateEnrollmentResponse:
    d = {
        "user": user_id,
        "section": enrollment.section,
    }

    waitlist_position = None

    # Verify that the class still has space.
    id = fetch_row(
        db,
        """
        SELECT id
        FROM sections as s
        WHERE s.id = :section
        AND s.capacity > (SELECT COUNT(*) FROM enrollments WHERE section_id = :section)
        AND s.freeze = FALSE
        AND s.deleted = FALSE
        """,
        d,
    )
    if id:
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
        id = fetch_row(
            db,
            """
            SELECT id
            FROM sections as s
            WHERE s.id = :section
            AND s.waitlist_capacity > (SELECT COUNT(*) FROM waitlist WHERE section_id = :section)
            AND (SELECT COUNT(*) FROM waitlist WHERE user_id = :user) < 3
            AND s.freeze = FALSE
            AND s.deleted = FALSE
            """,
            d,
        )
        if id:
            row = fetch_row(
                db,
                """
                INSERT INTO waitlist (user_id, section_id, position, date)
                VALUES(:user, :section, (SELECT COUNT(*) FROM waitlist WHERE section_id = :section), CURRENT_TIMESTAMP)
                RETURNING position
                """,
                d,
            )

            # Read back the waitlist position.
            assert row
            waitlist_position = row["waitlist.position"]

            # Ensure that there's also a waitlist enrollment.
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
    return CreateEnrollmentResponse(
        **dict(enrollments[0]),
        waitlist_position=waitlist_position,
    )


@app.post("/courses")
def add_course(course: AddCourseRequest, db: sqlite3.Connection = Depends(get_db)):
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


@app.post("/sections")
def add_section(
    section: AddSectionRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> Section:
    try:
        cur = db.execute(
            """
                INSERT INTO sections(course_id, classroom, capacity, waitlist_capacity, day, begin_time, end_time, freeze, instructor_id)
                VALUES(:course_id, :classroom, :capacity, :waitlist_capacity, :day, :begin_time, :end_time, :freeze, :instructor_id)
            """,
            dict(section),
        )
    except Exception as e:
        raise HTTPException(status_code=409, detail=f"Failed to add course: {e}")

    sections = database.list_sections(db, [section.course_id])
    return sections[0]


@app.patch("/sections/{section_id}")
def update_section(
    section_id: int,
    section: UpdateSectionRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> Section:
    q = """
    UPDATE sections
    SET
    """
    v = {}
    for key, value in section.dict().items():
        if value is not None:
            q += f"{key} = :{key}, "
            v[key] = value

    if len(v) == 0:
        raise HTTPException(
            status_code=400,
            detail="No fields provided to update.",
        )

    q = q[:-2]  # remove trailing comma

    q += """
    WHERE id = :section_id
    """
    v["section_id"] = section_id

    try:
        db.execute(q, v)
    except Exception as e:
        raise HTTPException(status_code=409, detail=f"Failed to update section:{e}")

    sections = database.list_sections(db, [section_id])
    return sections[0]


@app.delete("/users/{user_id}/enrollments/{section_id}")
def drop_user_enrollment(
    user_id: int,
    section_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> Enrollment:
    db.execute(
        """
        UPDATE enrollments
        SET status = 'Dropped'
        WHERE
            user_id = :user_id
            AND section_id = :section_id
            AND status = 'Enrolled'
        """,
        {"user_id": user_id, "section_id": section_id}
    )

    enrollments = database.list_enrollments(db, [(user_id, section_id)])
    return enrollments[0]


@app.delete("/users/{user_id}/waitlist/{section_id}")
def drop_user_waitlist(
    user_id: int,
    section_id: int,
    db: sqlite3.Connection = Depends(get_db),
):
    # Delete the entry from the waitlist, storing the position.
    row = fetch_row(
        db,
        """
        DELETE FROM waitlist
        WHERE
            user_id = :user_id
            AND section_id = :section_id
        RETURNING position
        """,
        {"user_id": user_id, "section_id": section_id},
    )
    if row is None:
        raise HTTPException(
            status_code=400,
            detail="User is not on the waitlist.",
        )

    position = row["waitlist.position"]

    # Ensure that every waitlist entry after this one has its position decremented.
    db.execute(
        """
        UPDATE waitlist
        SET position = position - 1
        WHERE
            section_id = :section_id
            AND position > :position
        """,
        {"section_id": section_id, "position": position},
    )

    # Delete the waitlist enrollment.
    db.execute(
        """
        DELETE FROM enrollments
        WHERE
            user_id = :user_id
            AND section_id = :section_id
            AND status = 'Waitlisted'
        """,
        {"user_id": user_id, "section_id": section_id},
    )


@app.delete("/sections/{section_id}/enrollments/{user_id}")
def drop_section_enrollment(
    section_id: int,
    user_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> Enrollment:
    # No auth so these two methods behave virtually identically.
    return drop_user_enrollment(user_id, section_id, db)

@app.delete("/sections/{section_id}")
def delete_section(
    section_id: int,
    db: sqlite3.Connection = Depends(get_db)
):
    # check validity of section_id
    get_section(section_id, db)
    
    # mark section as deleted
    db.execute(
        """
        UPDATE sections
        SET deleted = TRUE
        WHERE id = :section_id
        """,
        {"section_id": section_id}
    )
    
    # drop enrolled users
    ue = fetch_rows(
        db,
        f"""
        SELECT user_id FROM enrollments
        WHERE 
            section_id = :section_id
        """,
        { "section_id": section_id }
    )
    for u in ue:
        print(u)
        drop_user_enrollment(u[0], section_id, db)
    
    # drop waitlisted users
    uw = fetch_rows(
        db,
        f"""
        SELECT user_id FROM waitlist
        WHERE 
            section_id = :section_id
        """,
        { "section_id": section_id }
    )
    for u in uw:
        drop_user_waitlist(u[0], section_id, db)
