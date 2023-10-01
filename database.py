import contextlib
import aiosqlite
from typing import AsyncGenerator, Iterable

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
    db: aiosqlite.Connection, sql: str, params=()
) -> Iterable[aiosqlite.Row]:
    async with db.execute(sql, params) as cursor:
        return await cursor.fetchall()
