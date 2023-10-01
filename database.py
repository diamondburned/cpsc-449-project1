import contextlib
import aiosqlite
from typing import AsyncGenerator, Iterable, Type

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
