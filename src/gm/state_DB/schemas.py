# src/gm/state_DB/schemas.py
# API 요청/응답 스키마 정의

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ====================================================================
# 세션 관련 스키마
# ====================================================================


class SessionStartResponse(BaseModel):
    """세션 시작 응답"""

    session: List[Dict[str, Any]] = Field(description="생성된 세션 정보")
    entities: List[Dict[str, Any]] = Field(
        description="초기화된 엔티티 목록 (player, npc, enemy)"
    )
    edges: List[Dict[str, Any]] = Field(
        description="설정된 관계 및 속성 정보 (inventory, ability, relation)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session": [{"session_id": 1, "status": "active"}],
                "entities": [
                    {"entity_id": 1, "type": "player", "name": "Hero"},
                    {"entity_id": 2, "type": "npc", "name": "Merchant"},
                ],
                "edges": [{"player_id": 1, "item_id": 1, "quantity": 5}],
            }
        }


class SessionEndResponse(BaseModel):
    """세션 종료 응답"""

    status: str = Field(description="처리 상태")
    message: str = Field(description="결과 메시지")

    class Config:
        json_schema_extra = {
            "example": {"status": "success", "message": "Session 1 ended"}
        }


class SessionPauseResponse(BaseModel):
    """세션 일시정지 응답"""

    snapshot_id: Optional[int] = Field(description="생성된 스냅샷 ID")
    timestamp: Optional[datetime] = Field(description="스냅샷 생성 시각")

    class Config:
        json_schema_extra = {
            "example": {"snapshot_id": 123, "timestamp": "2026-01-23T10:30:00"}
        }


# ====================================================================
# 인벤토리 관련 스키마
# ====================================================================


class InventoryUpdateRequest(BaseModel):
    """인벤토리 업데이트 요청"""

    player_id: int = Field(..., description="플레이어 ID", gt=0, example=1)
    item_id: int = Field(..., description="아이템 ID", gt=0, example=5)
    quantity: int = Field(
        ..., description="수량 변화 (양수: 추가, 음수: 제거)", example=3
    )

    class Config:
        json_schema_extra = {"example": {"player_id": 1, "item_id": 5, "quantity": 3}}


class InventoryItem(BaseModel):
    """인벤토리 아이템 정보"""

    item_id: int = Field(description="아이템 ID")
    item_name: str = Field(description="아이템 이름")
    quantity: int = Field(description="보유 수량")
    category: Optional[str] = Field(None, description="아이템 카테고리")


class InventoryUpdateResponse(BaseModel):
    """인벤토리 업데이트 응답"""

    player_id: int = Field(description="플레이어 ID")
    inventory: List[Dict[str, Any]] = Field(description="업데이트된 인벤토리 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "player_id": 1,
                "inventory": [
                    {"item_id": 1, "item_name": "Potion", "quantity": 5},
                    {"item_id": 5, "item_name": "Sword", "quantity": 3},
                ],
            }
        }


# ====================================================================
# 아이템 관련 스키마
# ====================================================================


class ItemInfoResponse(BaseModel):
    """아이템 정보 응답"""

    item_id: int = Field(description="아이템 ID")
    item_name: str = Field(description="아이템 이름")
    description: Optional[str] = Field(None, description="아이템 설명")
    category: Optional[str] = Field(None, description="아이템 카테고리")
    rarity: Optional[str] = Field(None, description="희귀도")

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": 1,
                "item_name": "Health Potion",
                "description": "Restores 50 HP",
                "category": "consumable",
                "rarity": "common",
            }
        }


# ====================================================================
# 플레이어 상태 관련 스키마 (요구사항 스펙 기준)
# ====================================================================


class PlayerStateRequest(BaseModel):
    """플레이어 상태 조회 요청 (POST 방식 사용 시)"""

    player_id: str = Field(..., description="플레이어 ID", example="1")

    class Config:
        json_schema_extra = {"example": {"player_id": "1"}}


class PlayerData(BaseModel):
    """플레이어 기본 데이터"""

    hp: int = Field(description="현재 HP", example=7)
    gold: int = Field(description="보유 골드", example=339)
    items: List[int] = Field(description="보유 아이템 ID 목록", example=[1, 3, 5, 7])

    class Config:
        json_schema_extra = {"example": {"hp": 7, "gold": 339, "items": [1, 3, 5, 7]}}


class NPCRelation(BaseModel):
    """NPC 관계 정보"""

    npc_id: int = Field(description="NPC ID", example=7)
    affinity_score: int = Field(description="호감도 점수", example=75)

    class Config:
        json_schema_extra = {"example": {"npc_id": 7, "affinity_score": 75}}


class PlayerStateResponse(BaseModel):
    """플레이어 전체 상태 응답 (요구사항 스펙)"""

    player: PlayerData = Field(description="플레이어 기본 데이터")
    player_npc_relations: List[NPCRelation] = Field(
        description="플레이어-NPC 관계 목록"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "player": {"hp": 7, "gold": 339, "items": [1, 3, 5, 7]},
                "player_npc_relations": [{"npc_id": 7, "affinity_score": 75}],
            }
        }
