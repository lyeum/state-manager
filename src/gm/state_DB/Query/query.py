# query.py - TRPG 상태 DB 쿼리 관리

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg

# ====================================================================
# 설정 및 초기화
# ====================================================================

# data 폴더 경로 (Query 폴더의 상위인 state_DB/data)
BASE_DIR = Path(__file__).parent.parent / "data"

# PostgreSQL 연결 설정 (환경변수에서 로드)
DB_CONFIG = {
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "database": os.getenv("POSTGRES_DB", "state_db"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
}

# Apache AGE 그래프 이름
GRAPH_NAME = os.getenv("AGE_GRAPH_NAME", "state_db_item_logic")


# ====================================================================
# Connection Pool 관리 클래스
# ====================================================================


class DatabaseManager:
    """
    DB 연결 풀을 관리하는 싱글톤 클래스
    - 매번 연결/종료하지 않고 풀에서 재사용
    - 비동기 컨텍스트 매니저로 안전한 연결 관리
    """

    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """Connection Pool 생성 또는 기존 풀 반환"""
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                **DB_CONFIG,
                min_size=2,  # 최소 연결 수
                max_size=10,  # 최대 연결 수
                command_timeout=60,  # 쿼리 타임아웃 (초)
            )
        return cls._pool

    @classmethod
    async def close_pool(cls):
        """애플리케이션 종료 시 풀 정리"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        """
        안전한 연결 획득/반환을 위한 컨텍스트 매니저
        사용 예: async with DatabaseManager.get_connection() as conn:
        """
        pool = await cls.get_pool()
        async with pool.acquire() as connection:
            yield connection


# ====================================================================
# Apache AGE 그래프 초기화
# ====================================================================


async def init_age_graph():
    """
    Apache AGE 확장 로드 및 그래프 생성
    - ag_catalog 스키마의 함수 사용을 위해 search_path 설정
    - 그래프가 없으면 생성
    """
    async with DatabaseManager.get_connection() as conn:
        # AGE 확장 로드
        await conn.execute("CREATE EXTENSION IF NOT EXISTS age;")

        # search_path 설정 (ag_catalog 포함)
        await conn.execute("SET search_path = ag_catalog, '$user', public;")

        # 그래프 존재 여부 확인
        graph_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM ag_catalog.ag_graph WHERE name = $1)",
            GRAPH_NAME,
        )

        if not graph_exists:
            # 그래프 생성
            await conn.execute(f"SELECT create_graph('{GRAPH_NAME}');")
            print(f"✅ Graph '{GRAPH_NAME}' created")
        else:
            print(f"✅ Graph '{GRAPH_NAME}' already exists")


async def set_age_path(conn):
    """개별 연결에서 AGE search_path 설정"""
    await conn.execute("LOAD 'age';")
    await conn.execute("SET search_path = ag_catalog, '$user', public;")


# ====================================================================
# SQL/Cypher 실행 유틸리티 함수
# ====================================================================


async def run_sql_query(
    sql_path: str | Path, params: Optional[Dict] = None
) -> List[Dict[str, Any]]:
    """
    SELECT 쿼리 실행 (결과 반환)

    Args:
        sql_path: SQL 파일 경로
        params: 쿼리 파라미터 (예: {"player_id": 1})

    Returns:
        쿼리 결과 리스트 (각 행은 dict)
    """
    sql_path = Path(sql_path)

    # SQL 파일 읽기
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    with open(sql_path, "r", encoding="utf-8") as f:
        query = f.read()

    # 연결 풀에서 연결 획득 후 쿼리 실행
    async with DatabaseManager.get_connection() as conn:
        await set_age_path(conn)  # AGE 사용을 위한 설정
        if params:
            # 파라미터가 있는 경우 (예: WHERE player_id = $1)
            rows = await conn.fetch(query, *params.values())
        else:
            rows = await conn.fetch(query)

    # asyncpg Record를 dict로 변환
    return [dict(row) for row in rows]


async def run_sql_command(sql_path: str | Path, params: Optional[Dict] = None) -> str:
    """
    INSERT/UPDATE/DELETE 쿼리 실행 (결과 없음)

    Args:
        sql_path: SQL 파일 경로
        params: 쿼리 파라미터

    Returns:
        실행 결과 상태 문자열 (예: "INSERT 0 3")
    """
    sql_path = Path(sql_path)

    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    with open(sql_path, "r", encoding="utf-8") as f:
        query = f.read()

    async with DatabaseManager.get_connection() as conn:
        await set_age_path(conn)  # AGE 사용을 위한 설정
        if params:
            result = await conn.execute(query, *params.values())
        else:
            result = await conn.execute(query)

    return result  # "INSERT 0 5" 같은 문자열 반환


async def run_cypher_query(
    cypher: str, params: Optional[Dict] = None
) -> List[Dict[str, Any]]:
    """
    Apache AGE Cypher 쿼리 직접 실행

    Args:
        cypher: Cypher 쿼리 문자열
        params: 쿼리 파라미터

    Returns:
        쿼리 결과 리스트
    """
    async with DatabaseManager.get_connection() as conn:
        await set_age_path(conn)

        # Cypher 쿼리를 SQL로 래핑
        wrapped_query = f"""
            SELECT * FROM cypher('{GRAPH_NAME}', $$
                {cypher}
            $$) AS (result agtype);
        """

        if params:
            rows = await conn.fetch(wrapped_query, *params.values())
        else:
            rows = await conn.fetch(wrapped_query)

    return [dict(row) for row in rows]


# ====================================================================
# 세션 관리 함수들 (TODO: 구현 예정)
# ====================================================================

# async def session_start() -> Dict[str, Any]:
#     """
#     게임 세션 시작
#     - 세션 정보 활성화
#     - 엔티티(player, npc, enemy) 생성
#     - 기본 edge(inventory, relation) 설정
#
#     Returns:
#         {"session": {...}, "entities": [...], "edges": [...]}
#     """
#     # TODO: SQL 파일 분리 및 파라미터 형식 통일 필요
#     pass


# async def session_end(session_id: Optional[int] = None) -> Dict[str, str]:
#     """게임 세션 종료"""
#     # TODO: session_end.sql 파일 필요
#     pass


# ====================================================================
# 아이템 로직 (state_db_item_logic) - 구현됨
# ====================================================================


async def get_item_info(item_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    아이템 정보 조회

    Args:
        item_id: 특정 아이템 ID (None이면 전체 조회)

    Returns:
        아이템 정보 리스트
    """
    item_sql = BASE_DIR / "node/asset/item/item_Querry.sql"

    params = {"item_id": item_id} if item_id else None
    items = await run_sql_query(item_sql, params)

    return items


async def inventory_update(
    player_id: int, item_id: int, quantity: int
) -> Dict[str, Any]:
    """
    플레이어 인벤토리 업데이트

    Args:
        player_id: 플레이어 ID
        item_id: 아이템 ID
        quantity: 수량 변화 (양수: 추가, 음수: 제거)

    Returns:
        업데이트된 인벤토리 정보
    """
    # UPDATE 쿼리 실행
    update_sql = BASE_DIR / "edge/ASSET/inventory/inventory_update.sql"
    params = {"player_id": player_id, "item_id": item_id, "quantity": quantity}

    await run_sql_command(update_sql, params)

    # 업데이트 후 현재 인벤토리 조회
    query_sql = BASE_DIR / "edge/ASSET/inventory/player_inventory.sql"
    query_params = {"player_id": player_id}

    inventory = await run_sql_query(query_sql, query_params)

    return {"player_id": player_id, "inventory": inventory}


# ====================================================================
# 플레이어 상태 조회 (TODO: 구현 예정 - SQL 파일 분리 필요)
# ====================================================================

# async def get_player_state(player_id: str) -> Dict[str, Any]:
#     """
#     플레이어 전체 상태 조회 (요구사항 스펙)
#     """
#     # TODO: player_Query.sql이 여러 쿼리를 포함하므로 분리 필요
#     pass


# ====================================================================
# 그래프 조회 (서브그래프 시각화용)
# ====================================================================


async def get_graph_nodes(label: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    그래프의 노드 조회

    Args:
        label: 노드 라벨 (예: 'player', 'item'). None이면 전체 조회

    Returns:
        노드 정보 리스트
    """
    if label:
        cypher = f"MATCH (n:{label}) RETURN n"
    else:
        cypher = "MATCH (n) RETURN n"

    return await run_cypher_query(cypher)


async def get_graph_edges(edge_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    그래프의 엣지 조회

    Args:
        edge_type: 엣지 타입 (예: 'EARN_ITEM', 'PLAYER_INVENTORY'). None이면 전체 조회

    Returns:
        엣지 정보 리스트
    """
    if edge_type:
        cypher = f"MATCH ()-[r:{edge_type}]->() RETURN r"
    else:
        cypher = "MATCH ()-[r]->() RETURN r"

    return await run_cypher_query(cypher)


async def get_subgraph(
    center_id: str, depth: int = 1
) -> Dict[str, List[Dict[str, Any]]]:
    """
    특정 노드를 중심으로 서브그래프 조회

    Args:
        center_id: 중심 노드 ID
        depth: 탐색 깊이

    Returns:
        {"nodes": [...], "edges": [...]}
    """
    # 노드와 연결된 엣지 조회
    cypher = f"""
        MATCH path = (center {{id: '{center_id}'}})-[*1..{depth}]-(connected)
        RETURN path
    """
    paths = await run_cypher_query(cypher)

    return {"paths": paths}


# ====================================================================
# 앱 생명주기 관리용
# ====================================================================


async def startup():
    """FastAPI 시작 시 호출 - Connection Pool 및 AGE 그래프 초기화"""
    await DatabaseManager.get_pool()
    print("✅ Database connection pool initialized")

    # Apache AGE 그래프 초기화
    await init_age_graph()
    print(f"✅ Apache AGE graph '{GRAPH_NAME}' ready")


async def shutdown():
    """FastAPI 종료 시 호출 - Connection Pool 정리"""
    await DatabaseManager.close_pool()
    print("🔒 Database connection pool closed")
