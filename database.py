import contextlib
import sqlite3
import time
from typing import Any, Generator, Iterable, Type
from models import *
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SQLITE_DATABASE = "database.db"

SQLITE_PRAGMA = """
-- Permit SQLite to be concurrently safe.
PRAGMA journal_mode = WAL;

-- Enable foreign key constraints.
PRAGMA foreign_keys = ON;

-- Enforce column types.
PRAGMA strict = ON;

-- Force queries to prefix column names with table names.
-- See https://www2.sqlite.org/cvstrac/wiki?p=ColumnNames.
PRAGMA full_column_names = ON;
PRAGMA short_column_names = OFF;
"""


def get_db() -> Generator[sqlite3.Connection, None, None]:
    read_only = False  # TODO: split to a different function
    with sqlite3.connect(SQLITE_DATABASE) as db:
        db.row_factory = sqlite3.Row

        # These pragmas are only relevant for write operations.
        cur = db.executescript(SQLITE_PRAGMA)
        cur.close()

        try:
            yield db
        finally:
            if read_only:
                db.rollback()
            else:
                db.commit()


def fetch_rows(
    db: sqlite3.Connection,
    sql: str,
    params: Any = None,
) -> list[sqlite3.Row]:
    cursor = db.execute(sql, params if params is not None else ())
    rows = cursor.fetchall()
    cursor.close()
    return [row for row in rows]


def fetch_row(
    db: sqlite3.Connection,
    sql: str,
    params: Any = None,
) -> sqlite3.Row | None:
    cursor = db.execute(sql, params if params is not None else ())
    row = cursor.fetchone()
    cursor.close()
    return row


def extract_dict(d: dict, prefix: str) -> dict:
    """
    Extracts all keys from a dictionary that start with a given prefix.
    This is useful for extracting all keys from a dictionary that start with
    a given prefix, such as "user_" or "course_".
    """
    return {k[len(prefix) :]: v for k, v in d.items() if k.startswith(prefix)}


def extract_row(row: sqlite3.Row, table: str) -> dict:
    """
    Extracts all keys from a row that originate from a given table.
    """
    return extract_dict(dict(row), table + ".")


def exclude_dict(d: dict, keys: Iterable[str]) -> dict:
    """
    Returns a copy of a dictionary without the given keys.
    """
    return {k: v for k, v in d.items() if k not in keys}


def authorize(
    db: sqlite3.Connection = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> Session:
    cursor = db.execute(
        """
        SELECT
            users.*,
            sessions.*
        FROM sessions
        INNER JOIN users ON sessions.user_id = users.id
        WHERE token = ? AND expiry > ?
        """,
        (credentials.credentials, int(time.time())),
    )
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    return Session(
        **extract_row(row, "sessions"),
        user=User(**extract_row(row, "users")),
    )


def list_courses(
    db: sqlite3.Connection,
    course_ids: list[int] | None = None,
) -> list[Course]:
    courses_rows = fetch_rows(
        db,
        """
        SELECT
            courses.*,
            departments.*
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
            **extract_row(row, "courses"),
            department=Department(**extract_row(row, "departments")),
        )
        for row in courses_rows
    ]


def list_sections(
    db: sqlite3.Connection,
    section_ids: list[int] | None = None,
) -> list[Section]:
    rows = fetch_rows(
        db,
        """
        SELECT
            sections.*,
            courses.*,
            departments.*,
            instructors.*
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
    return [
        Section(
            **extract_row(row, "sections"),
            course=Course(
                **extract_row(row, "courses"),
                department=Department(
                    **extract_row(row, "departments"),
                ),
            ),
            instructor=User(**extract_row(row, "instructors")),
        )
        for row in rows
    ]


def list_enrollments(
    db: sqlite3.Connection,
    user_section_ids: list[tuple[int, int]] | None = None,
) -> list[Enrollment]:
    q = """
        SELECT
            courses.*,
            sections.*,
            enrollments.*,
            departments.*,
            users.*,
            instructors.*
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

    rows = fetch_rows(db, q, p)
    return [
        Enrollment(
            **extract_row(row, "enrollments"),
            user=User(**extract_row(row, "users")),
            section=Section(
                **extract_row(row, "sections"),
                course=Course(
                    **extract_row(row, "courses"),
                    department=Department(
                        **extract_row(row, "departments"),
                    ),
                ),
                instructor=User(**extract_row(row, "instructors")),
            ),
        )
        for row in rows
    ]


def list_waitlist(
    db: sqlite3.Connection,
    user_section_ids: list[tuple[int, int]] | None = None,
) -> list[Waitlist]:
    q = """
        SELECT
            waitlist.*,
            sections.*,
            courses.*,
            departments.*,
            users.*,
            instructors.*
        FROM waitlist
        INNER JOIN users ON users.id = waitlist.user_id
        INNER JOIN sections ON sections.id = waitlist.section_id
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

    rows = fetch_rows(db, q, p)
    return [
        Waitlist(
            **extract_row(row, "waitlist"),
            user=User(**extract_row(row, "users")),
            section=Section(
                **extract_row(row, "sections"),
                course=Course(
                    **extract_row(row, "courses"),
                    department=Department(
                        **extract_row(row, "departments"),
                    ),
                ),
                instructor=User(**extract_row(row, "instructors")),
            ),
        )
        for row in rows
    ]
