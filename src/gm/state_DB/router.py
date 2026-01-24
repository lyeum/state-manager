# src/gm/state_DB/routers.py
# 상태 관리 관련 API 엔드포인트 정의

from typing import List, Optional

from fastapi import APIRouter, HTTPException

# 공통 응답 래퍼 import
from .custom import WrappedResponse

# Query 함수 import
from .Query.query import (
    get_item_info,
    get_player_state,
    inventory_update,
    session_end,
    session_start,
)

# Pydantic 스키마 import
from .schemas import (
    InventoryUpdateRequest,
    InventoryUpdateResponse,
    ItemInfoResponse,
    PlayerStateResponse,
    SessionEndResponse,
    SessionStartResponse,
)

# ====================================================================
# 라우터 생성
# ====================================================================

state_router = APIRouter()


# ====================================================================
# 세션 관리 엔드포인트
# ====================================================================


@state_router.post(
    "/session/start",
    response_model=WrappedResponse[SessionStartResponse],
    summary="게임 세션 시작",
    description="새 게임 세션을 시작하고 초기 상태를 설정합니다.",
)
async def start_session():
    """
    새 게임 세션 시작

    - 세션 정보 생성
    - 플레이어/NPC/Enemy 엔티티 초기화
    - 인벤토리 및 관계 설정

    Returns:
        세션 정보, 엔티티 목록, Edge 목록
    """
    try:
        result = await session_start()
        # CustomJSONResponse가 자동으로 래핑하므로 데이터만 반환
        return result
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"SQL 파일을 찾을 수 없습니다: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"세션 시작 중 오류 발생: {str(e)}"
        ) from e


@state_router.post(
    "/session/end",
    response_model=WrappedResponse[SessionEndResponse],
    summary="게임 세션 종료",
    description="진행 중인 게임 세션을 종료합니다.",
)
async def end_session(session_id: Optional[int] = None):
    """
    게임 세션 종료

    Args:
        session_id: 종료할 세션 ID (생략 시 현재 활성 세션)

    Returns:
        종료 결과
    """
    try:
        result = await session_end(session_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"세션 종료 중 오류 발생: {str(e)}"
        ) from e


# TODO: 구현 예정 - session_pause
# @state_router.post(
#     "/session/pause",
#     response_model=WrappedResponse[SessionPauseResponse],
#     summary="게임 세션 일시정지",
#     description="현재 게임 상태를 스냅샷으로 저장하고 세션을 일시정지합니다.",
# )
# async def pause_session(session_id: Optional[int] = None):
#     """
#     게임 세션 일시정지 (스냅샷 저장)
#
#     Args:
#         session_id: 일시정지할 세션 ID
#
#     Returns:
#         스냅샷 정보
#     """
#     try:
#         result = await session_pause(session_id)
#         return result
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, detail=f"세션 일시정지 중 오류 발생: {str(e)}"
#         ) from e


# ====================================================================
# 상태 조회 엔드포인트
# ====================================================================


@state_router.get(
    "/player/{player_id}",
    response_model=WrappedResponse[PlayerStateResponse],
    summary="플레이어 현재 상태 조회",
    description="플레이어의 현재 상태(HP, 골드, 아이템, NPC 관계)를 조회합니다.",
)
async def get_player(player_id: str):
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
    try:
        result = await get_player_state(player_id)

        # 플레이어가 존재하지 않는 경우 (hp와 gold가 모두 0이고 items가 비어있으면)
        if (
            result["player"]["hp"] == 0
            and result["player"]["gold"] == 0
            and not result["player"]["items"]
        ):
            raise HTTPException(
                status_code=404, detail=f"Player ID {player_id}를 찾을 수 없습니다."
            )

        return result
    except HTTPException:
        raise  # 이미 처리된 HTTPException은 그대로 전달
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"플레이어 상태 조회 중 오류 발생: {str(e)}"
        ) from e


@state_router.get(
    "/items",
    response_model=WrappedResponse[List[ItemInfoResponse]],
    summary="아이템 정보 조회",
    description="아이템 정보를 조회합니다."
    " item_id를 지정하면 특정 아이템만 조회합니다.",
)
async def get_items(item_id: Optional[int] = None):
    """
    아이템 정보 조회

    Args:
        item_id: 특정 아이템 ID (생략 시 전체 조회)

    Returns:
        아이템 정보 리스트
    """
    try:
        result = await get_item_info(item_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"아이템 조회 중 오류 발생: {str(e)}"
        ) from e


# ====================================================================
# 상태 업데이트 엔드포인트
# ====================================================================


@state_router.put(
    "/inventory/update",
    response_model=WrappedResponse[InventoryUpdateResponse],
    summary="인벤토리 업데이트",
    description="플레이어의 인벤토리에 아이템을 추가하거나 제거합니다.",
)
async def update_inventory(request: InventoryUpdateRequest):
    """
    플레이어 인벤토리 업데이트

    Request Body:
        {
            "player_id": 1,
            "item_id": 5,
            "quantity": 3  // 양수: 추가, 음수: 제거
        }

    Returns:
        업데이트된 인벤토리 정보
    """
    try:
        result = await inventory_update(
            player_id=request.player_id,
            item_id=request.item_id,
            quantity=request.quantity,
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"인벤토리 업데이트 중 오류 발생: {str(e)}"
        ) from e
