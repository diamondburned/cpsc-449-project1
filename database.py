import contextlib
import aiosqlite
import time
from typing import AsyncGenerator, Iterable, Type
from models import *
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SQLITE_DATABASE = "database.db"

SQLITE_PRAGMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA strict = ON;
"""


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    read_only = False  # TODO: split to a different function
    async with aiosqlite.connect(SQLITE_DATABASE) as db:
        db.row_factory = aiosqlite.Row

        if not read_only:
            # These pragmas are only relevant for write operations.
            await db.executescript(SQLITE_PRAGMA)

        try:
            yield db
        finally:
            if read_only:
                await db.rollback()
            else:
                await db.commit()


async def fetch_rows(
    db: aiosqlite.Connection,
    sql: str,
    params=(),
) -> list[aiosqlite.Row]:
    async with db.execute(sql, params) as cursor:
        rows = await cursor.fetchall()
        return [row for row in rows]


async def fetch_row(
    db: aiosqlite.Connection,
    sql: str,
    params=(),
) -> aiosqlite.Row | None:
    async with db.execute(sql, params) as cursor:
        row = await cursor.fetchone()
        return row


def extract_dict(d: dict, prefix: str) -> dict:
    """
    Extracts all keys from a dictionary that start with a given prefix.
    This is useful for extracting all keys from a dictionary that start with
    a given prefix, such as "user_" or "course_".
    """
    return {k[len(prefix) :]: v for k, v in d.items() if k.startswith(prefix)}


def exclude_dict(d: dict, keys: Iterable[str]) -> dict:
    """
    Returns a copy of a dictionary without the given keys.
    """
    return {k: v for k, v in d.items() if k not in keys}


async def authorize(
    db: aiosqlite.Connection = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> Session:
    async with db.execute(
        """
        SELECT
            users.*,
            sessions.id AS sessions_id,
            sessions.token AS sessions_token,
            sessions.expiry AS sessions_expiry
        FROM sessions
        INNER JOIN users ON sessions.user_id = users.id
        WHERE token = ? AND expiry > ?
        """,
        (credentials.credentials, int(time.time())),
    ) as cursor:
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = User(**dict(row))
        session = Session(
            id=row["sessions_id"],
            user=user,
            token=row["sessions_token"],
            expiry=row["sessions_expiry"],
        )
        return session


async def list_courses(
    db: aiosqlite.Connection,
    course_ids: list[int] | None = None,
) -> list[Course]:
    courses_rows = await fetch_rows(
        db,
        """
        SELECT
            courses.*,
            departments.id AS departments_id,
            departments.name AS departments_name
        FROM courses
        INNER JOIN departments ON departments.id = courses.department_id
        """
        + (
            "WHERE courses.id IN (%s)" % ",".join(["?"] * len(course_ids))
            if course_ids is not None
            else ""
        ),
        course_ids,
    )
    return [
        Course(
            **dict(row),
            department=Department(**extract_dict(dict(row), "departments_")),
        )
        for row in courses_rows
    ]


async def list_enrollments(
    db: aiosqlite.Connection,
    user_section_ids: list[tuple[int, int]] | None = None,
) -> list[Enrollment]:
    q = """
        SELECT
            courses.*,
            courses.id AS courses_id,
            sections.*,
            sections.id AS sections_id,
            enrollments.*,
            users.id AS users_id,
            users.first_name AS users_first_name,
            users.last_name AS users_last_name,
            users.role AS users_role,
            instructors.id AS instructors_id,
            instructors.first_name AS instructors_first_name,
            instructors.last_name AS instructors_last_name,
            instructors.role AS instructors_role
        FROM enrollments
        INNER JOIN users ON users.id = enrollments.user_id
        INNER JOIN sections ON sections.id = enrollments.section_id
        INNER JOIN courses ON courses.id = sections.course_id
        INNER JOIN departments ON departments.id = courses.department_id
        INNER JOIN users AS instructors ON instructors.id = sections.instructor_id
    """
    p = []
    if user_section_ids is not None:
        q += "WHERE (users.id, sections.id) IN (%s)" % ",".join(
            ["(?, ?)"] * len(user_section_ids)
        )
        p = [item for sublist in user_section_ids for item in sublist]  # flatten list

    print(q, p)

    rows = await fetch_rows(db, q, p)
    # Remove conflicting ID columns
    rows = [exclude_dict(dict(row), "id") for row in rows]
    return [
        Enrollment(
            **dict(row),
            user=User(**extract_dict(dict(row), "users_")),
            section=Section(
                **dict(row),
                id=row["sections_id"],
                course=Course(
                    **dict(row),
                    id=row["courses_id"],
                    department=Department(**dict(row)),
                ),
                instructor=User(**extract_dict(dict(row), "instructors_")),
            ),
        )
        for row in rows
    ]


async def list_sections(
    db: aiosqlite.Connection,
    section_ids: list[int] | None = None,
) -> list[Section]:
    rows = await fetch_rows(
        db,
        """
        SELECT
            sections.*,
            sections.id AS sections_id,
            courses.*,
            courses.id AS courses_id,
            departments.id AS departments_id,
            departments.name AS departments_name,
            instructors.id AS instructors_id,
            instructors.first_name AS instructors_first_name,
            instructors.last_name AS instructors_last_name,
            instructors.role AS instructors_role
        FROM sections
        INNER JOIN courses ON courses.id = sections.course_id
        INNER JOIN departments ON departments.id = courses.department_id
        INNER JOIN users AS instructors ON instructors.id = sections.instructor_id
        """
        + (
            "WHERE sections.id IN (%s)" % ",".join(["?"] * len(section_ids))
            if section_ids is not None
            else ""
        ),
        section_ids,
    )
    # Remove conflicting ID columns
    rows = [exclude_dict(dict(row), "id") for row in rows]
    return [
        Section(
            **dict(row),
            id=row["sections_id"],
            course=Course(
                **dict(row),
                id=row["courses_id"],
                department=Department(**extract_dict(dict(row), "departments_")),
            ),
            instructor=User(**extract_dict(dict(row), "instructors_")),
        )
        for row in rows
    ]
