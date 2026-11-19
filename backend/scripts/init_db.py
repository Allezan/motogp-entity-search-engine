import argparse
from pathlib import Path
from app.core import db
from app.core.config import BASE_DIR
from scripts._common import open_db

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--schema",
        type=Path,
        default=BASE_DIR.parent / "database" / "schema.sql"
    )
    args = parser.parse_args()

    try:
        open_db()
        db.wait_pool(timeout=20)

        with db.get_conn() as conn:
            conn.execute(args.schema.read_text(encoding="utf-8"))

    finally:
        db.close_pool(timeout=20)

    print(f"Schema applied: {args.schema}")

if __name__ == "__main__":
    main()