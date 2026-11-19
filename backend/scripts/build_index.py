from app.core import db
from app.core.config import get_settings
from app.services.indexer import rebuild_from_database
from app.services.preprocessing import TextPreprocessor
from scripts._common import open_db

def main() -> None:
    settings = get_settings()
    open_db()
    artifact = rebuild_from_database(settings, TextPreprocessor())
    print("Index built:", artifact.summary(), "->", settings.artifact_path)
    db.close_pool()

if __name__ == "__main__":
    main()
