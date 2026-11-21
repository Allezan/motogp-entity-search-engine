import argparse
from app.core import db
from app.core.config import get_settings
from app.services.indexer import rebuild_from_database, rebuild_from_local_exports
from app.services.preprocessing import TextPreprocessor
from scripts._common import open_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the v5 From-Scratch TF-IDF & Entity Index artifact.")
    parser.add_argument(
        "--from-local",
        action="store_true",
        help="Build index from verified local SQL/CSV exports instead of Neon PostgreSQL.",
    )
    args = parser.parse_args()
    settings = get_settings()

    if args.from_local:
        artifact = rebuild_from_local_exports(settings, TextPreprocessor())
        print("Index built (local verified exports):", artifact.summary(), "->", settings.artifact_path)
        return

    open_db()
    try:
        artifact = rebuild_from_database(settings, TextPreprocessor())
        print("Index built (Neon PostgreSQL):", artifact.summary(), "->", settings.artifact_path)
    finally:
        db.close_pool()


if __name__ == "__main__":
    main()
