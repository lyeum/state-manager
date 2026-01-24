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
# Node/Edge 테이블 생성
# ====================================================================


# ====================================================================
# 세션 관리 함수들
# ====================================================================


async def session_start() -> Dict[str, Any]:
    """
    게임 세션 시작
    - 세션 정보 활성화
    - 엔티티(player, npc, enemy) 생성
    - 기본 edge(inventory, relation) 설정

    Returns:
        {
            "session": [...],
            "entities": [...],
            "edges": [...]
        }
    """
    # 세션 생성 쿼리
    session_sql = BASE_DIR / "session/session_start.sql"
    session_result = await run_sql_query(session_sql)

    # 엔티티 생성 쿼리
    entities_sql = BASE_DIR / "session/entities_init.sql"
    entities_result = await run_sql_query(entities_sql)

    # Edge 생성 쿼리
    edges_sql = BASE_DIR / "session/edges_init.sql"
    edges_result = await run_sql_query(edges_sql)

    return {
        "session": session_result,
        "entities": entities_result,
        "edges": edges_result,
    }


async def session_end(session_id: Optional[int] = None) -> Dict[str, str]:
    """
    게임 세션 종료

    Args:
        session_id: 종료할 세션 ID (None이면 현재 활성 세션)

    Returns:
        {"status": "success", "message": "Session ended"}
    """
    session_end_sql = BASE_DIR / "session/session_end.sql"

    params = {"session_id": session_id} if session_id else None
    await run_sql_command(session_end_sql, params)

    message = f"Session {session_id} ended" if session_id else "Active session ended"

    return {"status": "success", "message": message}


# TODO: 구현 예정
# async def session_pause(session_id: Optional[int] = None) -> Dict[str, Any]:
#     """
#     게임 세션 일시정지 (스냅샷 저장)
#
#     Args:
#         session_id: 일시정지할 세션 ID
#
#     Returns:
#         {"snapshot_id": ..., "timestamp": ...}
#     """
#     pass


# ====================================================================
# 인벤토리 조회
# ====================================================================


async def get_session_inventory(session_id: str) -> List[Dict[str, Any]]:
    """
    세션의 플레이어 인벤토리 조회

    Args:
        session_id: 세션 ID

    Returns:
        [
            {
                "player_id": "uuid",
                "item_id": 1,
                "quantity": 3,
                "acquired_at": "2026-01-23 10:00:00"
            },
            ...
        ]
    """
    sql_path = Path(__file__).parent / "Query/INQUIRY/Session_inventory.sql"
    return await run_sql_query(sql_path, {"session_id": session_id})


# ====================================================================
# NPC 조회
# ====================================================================


async def get_session_npcs(session_id: str) -> List[Dict[str, Any]]:
    """
    세션의 NPC 목록 조회

    Args:
        session_id: 세션 ID

    Returns:
        NPC 정보 리스트
    """
    sql_path = Path(__file__).parent / "Query/INQUIRY/Session_npc.sql"
    return await run_sql_query(sql_path, {"session_id": session_id})


async def get_npc_relations(player_id: str) -> List[Dict[str, Any]]:
    """
    특정 플레이어의 NPC 호감도 조회

    Args:
        player_id: 플레이어 ID

    Returns:
        [
            {
                "npc_id": "uuid",
                "npc_name": "Merchant Tom",
                "affinity_score": 75
            },
            ...
        ]
    """
    sql_path = Path(__file__).parent / "Query/INQUIRY/Npc_relations.sql"
    return await run_sql_query(sql_path, {"player_id": player_id})


# ====================================================================
# Enemy 조회
# ====================================================================


async def get_session_enemies(
    session_id: str, active_only: bool = True
) -> List[Dict[str, Any]]:
    """
    세션의 Enemy 목록 조회

    Args:
        session_id: 세션 ID
        active_only: True면 생존한 적만, False면 전체

    Returns:
        Enemy 정보 리스트
    """
    sql_path = Path(__file__).parent / "Query/INQUIRY/Session_enemy.sql"
    return await run_sql_query(
        sql_path, {"session_id": session_id, "active_only": active_only}
    )


async def get_player_stats(player_id: str) -> Dict[str, Any]:
    """
    플레이어 상세 스탯 조회

    Args:
        player_id: 플레이어 ID

    Returns:
        {
            "player_id": "uuid",
            "name": "Hero",
            "state": {
                "numeric": {"HP": 85, "MP": 50, ...},
                "boolean": {}
            }
        }
    """
    sql_path = Path(__file__).parent / "Query/INQUIRY/Player_stats.sql"
    result = await run_sql_query(sql_path, {"player_id": player_id})
    return result[0] if result else {}


# ====================================================================
# 플레이어 상태 조회
# ====================================================================


async def get_player_state(player_id: str) -> Dict[str, Any]:
    """
    플레이어 전체 상태 조회 (요구사항 스펙)

    Args:
        player_id: 조회할 플레이어 ID

    Returns:
        {
            "player": {
                "hp": 7,
                "gold": 339,
                "items": [1, 3, 5, 7]
            },
            "player_npc_relations": [
                {"npc_id": 7, "affinity_score": 75}
            ]
        }
    """
    # 플레이어 기본 정보 조회
    player_sql = BASE_DIR / "node/entity/player/player_state.sql"
    player_result = await run_sql_query(player_sql, {"player_id": player_id})

    # NPC 관계 조회
    npc_relation_sql = BASE_DIR / "edge/RELATION/player_npc/player_npc_relations.sql"
    npc_relations = await run_sql_query(npc_relation_sql, {"player_id": player_id})

    # 결과가 없으면 기본값 반환 (router에서 404 처리)
    if not player_result:
        return {
            "player": {"hp": 0, "gold": 0, "items": []},
            "player_npc_relations": [],
        }

    # 플레이어 데이터 가공
    player_data = player_result[0]

    return {
        "player": {
            "hp": player_data.get("hp", 0),
            "gold": player_data.get("gold", 0),
            "items": player_data.get("items", []),  # 배열로 반환되어야 함
        },
        "player_npc_relations": [
            {
                "npc_id": relation["npc_id"],
                "affinity_score": relation["affinity_score"],
            }
            for relation in npc_relations
        ],
    }


# ====================================================================
# 아이템 로직 (state_db_item_logic)
# ====================================================================


async def get_item_info(item_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    아이템 정보 조회

    Args:
        item_id: 특정 아이템 ID (None이면 전체 조회)

    Returns:
        아이템 정보 리스트
    """
    item_sql = BASE_DIR / "node/asset/item/item_Query.sql"

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
# 플레이어 상태 업데이트
# ====================================================================


async def update_player_hp(
    player_id: str, session_id: str, hp_change: int, reason: str = "unknown"
) -> Dict[str, Any]:
    """
    플레이어 HP 변경

    Args:
        player_id: 플레이어 ID
        session_id: 세션 ID
        hp_change: HP 변화량 (양수: 회복, 음수: 피해)
        reason: 변경 사유 (combat, item, rest 등)

    Returns:
        {
            "player_id": "uuid",
            "current_hp": 75,
            "max_hp": 100,
            "changed_by": -25
        }
    """
    sql_path = Path(__file__).parent / "Query/UPDATE/update_player_hp.sql"
    params = {"player_id": player_id, "session_id": session_id, "hp_change": hp_change}
    result = await run_sql_query(sql_path, params)

    if result:
        return result[0]
    else:
        # 변경 후 현재 HP 조회
        player_result = await get_player_stats(player_id)
        return {
            "player_id": player_id,
            "current_hp": player_result.get("state", {})
            .get("numeric", {})
            .get("HP", 0),
            "max_hp": player_result.get("state", {})
            .get("numeric", {})
            .get("max_hp", 100),
            "changed_by": hp_change,
        }


async def update_player_stats(
    player_id: str, session_id: str, stat_changes: Dict[str, int]
) -> Dict[str, Any]:
    """
    플레이어 스탯 변경 (범용)

    Args:
        player_id: 플레이어 ID
        session_id: 세션 ID
        stat_changes: 변경할 스탯들 {"HP": -10, "MP": 5, "STR": 1}

    Returns:
        업데이트된 플레이어 상태
    """
    sql_path = Path(__file__).parent / "Query/UPDATE/update_player_stats.sql"
    params = {
        "player_id": player_id,
        "session_id": session_id,
        "stat_changes": stat_changes,
    }
    await run_sql_command(sql_path, params)
    return await get_player_stats(player_id)


# ====================================================================
# NPC 상태 업데이트
# ====================================================================


async def update_npc_affinity(
    player_id: str, npc_id: str, affinity_change: int
) -> Dict[str, Any]:
    """
    NPC 호감도 변경

    Args:
        player_id: 플레이어 ID
        npc_id: NPC ID
        affinity_change: 호감도 변화량 (양수/음수)

    Returns:
        {
            "player_id": "uuid",
            "npc_id": "uuid",
            "new_affinity": 80
        }
    """
    sql_path = Path(__file__).parent / "Query/UPDATE/update_npc_affinity.sql"
    params = {
        "player_id": player_id,
        "npc_id": npc_id,
        "affinity_change": affinity_change,
    }
    result = await run_sql_query(sql_path, params)

    if result:
        return {
            "player_id": player_id,
            "npc_id": npc_id,
            "new_affinity": result[0].get("new_affinity", 0),
        }
    else:
        return {"player_id": player_id, "npc_id": npc_id, "new_affinity": 0}


# ====================================================================
# Enemy 상태 업데이트
# ====================================================================


async def update_enemy_hp(
    enemy_instance_id: str, session_id: str, hp_change: int
) -> Dict[str, Any]:
    """
    적 HP 변경

    Args:
        enemy_instance_id: 적 인스턴스 ID
        session_id: 세션 ID
        hp_change: HP 변화량 (보통 음수)

    Returns:
        {
            "enemy_instance_id": "uuid",
            "current_hp": 15,
            "is_defeated": false
        }
    """
    sql_path = Path(__file__).parent / "Query/UPDATE/update_enemy_hp.sql"
    params = {
        "enemy_instance_id": enemy_instance_id,
        "session_id": session_id,
        "hp_change": hp_change,
    }
    result = await run_sql_query(sql_path, params)
    return result[0] if result else {}


async def defeat_enemy(enemy_instance_id: str, session_id: str) -> Dict[str, str]:
    """
    적 처치 처리

    Args:
        enemy_instance_id: 적 인스턴스 ID
        session_id: 세션 ID

    Returns:
        {"status": "defeated", "enemy_id": "uuid"}
    """
    sql_path = Path(__file__).parent / "Query/UPDATE/defeated_enemy.sql"
    params = {"enemy_instance_id": enemy_instance_id, "session_id": session_id}
    await run_sql_command(sql_path, params)

    return {"status": "defeated", "enemy_id": enemy_instance_id}


# ====================================================================
# 위치 업데이트
# ====================================================================


async def update_location(session_id: str, new_location: str) -> Dict[str, str]:
    """
    세션 위치 변경

    Args:
        session_id: 세션 ID
        new_location: 새 위치 이름

    Returns:
        {"session_id": "uuid", "location": "Dark Forest"}
    """
    sql_path = Path(__file__).parent / "Query/UPDATE/update_location.sql"
    params = {"session_id": session_id, "new_location": new_location}
    await run_sql_command(sql_path, params)

    return {"session_id": session_id, "location": new_location}


# ====================================================================
# Enemy 관리
# ====================================================================


async def spawn_enemy(session_id: str, enemy_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    적 동적 생성

    Args:
        session_id: 세션 ID
        enemy_data: {
            "enemy_id": 1,
            "name": "Goblin Warrior",
            "hp": 30,
            "attack": 10,
            "defense": 5
        }

    Returns:
        생성된 적 정보 (enemy_instance_id 포함)
    """
    sql_path = Path(__file__).parent / "Query/MANAGE/enemy/spawn_enemy.sql"
    params = {
        "session_id": session_id,
        "enemy_id": enemy_data.get("enemy_id"),
        "name": enemy_data.get("name"),
        "description": enemy_data.get("description", ""),
        "hp": enemy_data.get("hp", 30),
        "attack": enemy_data.get("attack", 10),
        "defense": enemy_data.get("defense", 5),
        "tags": enemy_data.get("tags", ["enemy"]),
    }
    result = await run_sql_query(sql_path, params)
    return result[0] if result else {}


async def remove_enemy(enemy_instance_id: str, session_id: str) -> Dict[str, str]:
    """
    적 제거 (물리적 삭제)

    Args:
        enemy_instance_id: 적 인스턴스 ID
        session_id: 세션 ID

    Returns:
        {"status": "removed"}
    """
    sql_path = Path(__file__).parent / "Query/MANAGE/enemy/remove_enemy.sql"
    params = {"enemy_instance_id": enemy_instance_id, "session_id": session_id}
    await run_sql_command(sql_path, params)

    return {"status": "removed"}


# ====================================================================
# NPC 관리
# ====================================================================


async def spawn_npc(session_id: str, npc_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    NPC 동적 생성

    Args:
        session_id: 세션 ID
        npc_data: {
            "npc_id": 1,
            "name": "Merchant Tom",
            "description": "A friendly merchant"
        }

    Returns:
        생성된 NPC 정보
    """
    sql_path = Path(__file__).parent / "Query/MANAGE/npc/spawn_npc.sql"
    params = {
        "session_id": session_id,
        "npc_id": npc_data.get("npc_id"),
        "name": npc_data.get("name"),
        "description": npc_data.get("description", ""),
        "hp": npc_data.get("hp", 100),
        "tags": npc_data.get("tags", ["npc"]),
    }
    result = await run_sql_query(sql_path, params)
    return result[0] if result else {}


async def remove_npc(npc_instance_id: str, session_id: str) -> Dict[str, str]:
    """
    NPC 제거

    Args:
        npc_instance_id: NPC 인스턴스 ID
        session_id: 세션 ID

    Returns:
        {"status": "removed"}
    """
    sql_path = Path(__file__).parent / "Query/MANAGE/npc/remove_npc.sql"
    params = {"npc_instance_id": npc_instance_id, "session_id": session_id}
    await run_sql_command(sql_path, params)

    return {"status": "removed"}


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
        {"paths": [...]}
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
