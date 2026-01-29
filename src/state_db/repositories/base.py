from pathlib import Path

# Query 폴더 경로 설정 (src/state_db/Query)
QUERY_DIR = Path(__file__).parent.parent / "Query"


class BaseRepository:
    def __init__(self) -> None:
        self.query_dir = QUERY_DIR
