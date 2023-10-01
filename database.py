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


async def get_db(read_only=False) -> AsyncGenerator[aiosqlite.Connection, None]:
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
    type: Type,
    sql: str,
    params=(),
) -> list[Type]:
    async with db.execute(sql, params) as cursor:
        rows = await cursor.fetchall()
        return [type(**row) for row in rows]


async def fetch_row(
    db: aiosqlite.Connection,
    type: Type,
    sql: str,
    params=(),
) -> Type:
    async with db.execute(sql, params) as cursor:
        row = await cursor.fetchone()
        return type(**row) if row else None


async def authorize_session(
    db: aiosqlite.Connection = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> Session:
    async with db.execute(
        """
        SELECT sessions.*
        FROM sessions
        WHERE token = ? AND expiry > ?
        """,
        (credentials.credentials, int(time.time())),
    ) as cursor:
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return Session(**dict(row))


async def authorize_user(
    db: aiosqlite.Connection = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> User:
    session = await authorize_session(db, credentials)

    async with db.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (session.user_id,),
    ) as cursor:
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="User not found")

        return User(**dict(row))
