from __future__ import annotations
from app.core import db
from app.core.config import get_settings

def open_db() -> None:
    db.init_pool(get_settings())
    if not db.ping():
        raise SystemExit("Cannot connect to the database. Check DATABASE_URL / DB_* settings.")
