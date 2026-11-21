from __future__ import annotations
import logging
import os
from contextlib import contextmanager
from typing import Iterator, Optional
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from app.core.config import Settings

logger = logging.getLogger(__name__)

_pool: Optional[ConnectionPool] = None

def init_pool(settings: Settings) -> None:
    # Create the pool without blocking: Neon may need a moment to wake from idle
    global _pool
    if _pool is not None:
        return
    is_serverless = bool(os.environ.get("VERCEL"))
    min_size = 0 if is_serverless else settings.db_pool_min_size
    max_size = min(settings.db_pool_max_size, 3) if is_serverless else settings.db_pool_max_size
    _pool = ConnectionPool(
        conninfo=settings.conninfo,
        min_size=min_size,
        max_size=max_size,
        kwargs={
            "row_factory": dict_row,
            # Safe with Neon's PgBouncer pooler endpoint (-pooler)
            "prepare_threshold": None,
        },
        # Neon suspends idle computes, so validate connections before handing them out.
        check=ConnectionPool.check_connection,
        max_idle=120,
        max_lifetime=900,
        timeout=settings.db_connect_timeout,
        open=False,
    )
    _pool.open(wait=False)
    logger.info("Database pool opened (lazy connect).")

def wait_pool(timeout: float = 20.0) -> None:
    if _pool is None:
        raise RuntimeError("Database pool is not initialised.")
    _pool.wait(timeout=timeout)

def close_pool(timeout: float = 20.0) -> None:
    global _pool
    if _pool is not None:
        pool = _pool
        _pool = None
        pool.close(timeout=timeout)

@contextmanager
def get_conn() -> Iterator[psycopg.Connection]:
    # Borrow a connection; commits on success, rolls back on exception
    if _pool is None:
        raise RuntimeError("Database pool is not initialised.")
    with _pool.connection() as conn:
        yield conn

def ping() -> bool:
    try:
        if _pool is None:
            return False
        with _pool.connection(timeout=3) as conn:  # short timeout so /health stays responsive
            conn.execute("SELECT 1")
        return True
    except Exception:  # noqa: BLE001
        return False
