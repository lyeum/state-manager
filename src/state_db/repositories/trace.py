from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from state_db.infrastructure import run_sql_query
from state_db.repositories.base import BaseRepository


class TraceRepository(BaseRepository):
    """TRACE 관련 히스토리 조회를 담당하는 Repository"""

    # ====================================================================
    # Turn History
    # ====================================================================

    async def get_turn_history(self, session_id: str) -> List[Dict[str, Any]]:
        """특정 세션의 Turn 이력 조회 (전체)"""
        sql_path = self.query_dir / "TRACE" / "turn" / "get_history.sql"
        results = await run_sql_query(sql_path, [session_id])
        return list(results) if results else []

    async def get_recent_turns(
        self, session_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """최근 N개의 Turn 조회"""
        sql_path = self.query_dir / "TRACE" / "turn" / "get_recent.sql"
        results = await run_sql_query(sql_path, [session_id, limit])
        return list(results) if results else []

    async def get_turn_details(
        self, session_id: str, turn_number: int
    ) -> Dict[str, Any]:
        """특정 Turn의 상세 정보 조회"""
        sql_path = self.query_dir / "TRACE" / "turn" / "get_details.sql"
        result = await run_sql_query(sql_path, [session_id, turn_number])
        if result:
            return result[0]
        raise HTTPException(status_code=404, detail="Turn not found")

    async def get_turn_range(
        self, session_id: str, start_turn: int, end_turn: int
    ) -> List[Dict[str, Any]]:
        """Turn 범위 조회 (리플레이용)"""
        sql_path = self.query_dir / "TRACE" / "turn" / "get_range.sql"
        results = await run_sql_query(sql_path, [session_id, start_turn, end_turn])
        return list(results) if results else []

    async def get_latest_turn(self, session_id: str) -> Optional[Dict[str, Any]]:
        """가장 최근 Turn 조회"""
        sql_path = self.query_dir / "TRACE" / "turn" / "get_latest.sql"
        result = await run_sql_query(sql_path, [session_id])
        return result[0] if result else None

    async def get_turn_statistics_by_phase(
        self, session_id: str
    ) -> List[Dict[str, Any]]:
        """Phase별 Turn 수 집계 및 상세 통계"""
        sql_path = self.query_dir / "TRACE" / "turn" / "get_statistics_by_phase.sql"
        results = await run_sql_query(sql_path, [session_id])
        return list(results) if results else []

    async def get_turn_statistics_by_type(
        self, session_id: str
    ) -> List[Dict[str, Any]]:
        """Turn Type별 집계"""
        sql_path = self.query_dir / "TRACE" / "turn" / "get_statistics_by_type.sql"
        results = await run_sql_query(sql_path, [session_id])
        return list(results) if results else []

    async def get_turn_duration_analysis(
        self, session_id: str
    ) -> List[Dict[str, Any]]:
        """각 Turn의 소요 시간 계산 및 분석"""
        sql_path = self.query_dir / "TRACE" / "turn" / "get_duration_analysis.sql"
        results = await run_sql_query(sql_path, [session_id])
        return list(results) if results else []

    async def get_turn_summary(self, session_id: str) -> Dict[str, Any]:
        """Turn 요약 리포트"""
        sql_path = self.query_dir / "TRACE" / "turn" / "get_summary.sql"
        result = await run_sql_query(sql_path, [session_id])
        if result:
            return result[0]
        return {}

    # ====================================================================
    # Phase History
    # ====================================================================

    async def get_phase_history(self, session_id: str) -> List[Dict[str, Any]]:
        """특정 세션의 Phase 전환 이력 조회 (전체)"""
        sql_path = self.query_dir / "TRACE" / "phase" / "get_history.sql"
        results = await run_sql_query(sql_path, [session_id])
        return list(results) if results else []

    async def get_recent_phases(
        self, session_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """최근 N개의 Phase 전환 조회"""
        sql_path = self.query_dir / "TRACE" / "phase" / "get_recent.sql"
        results = await run_sql_query(sql_path, [session_id, limit])
        return list(results) if results else []

    async def get_phase_by_phase(
        self, session_id: str, phase: str
    ) -> List[Dict[str, Any]]:
        """특정 Phase로의 전환 이력만 조회"""
        sql_path = self.query_dir / "TRACE" / "phase" / "get_by_phase.sql"
        results = await run_sql_query(sql_path, [session_id, phase])
        return list(results) if results else []

    async def get_phase_range(
        self, session_id: str, start_turn: int, end_turn: int
    ) -> List[Dict[str, Any]]:
        """특정 Turn 범위의 Phase 전환 조회"""
        sql_path = self.query_dir / "TRACE" / "phase" / "get_range.sql"
        results = await run_sql_query(sql_path, [session_id, start_turn, end_turn])
        return list(results) if results else []

    async def get_latest_phase(self, session_id: str) -> Optional[Dict[str, Any]]:
        """가장 최근 Phase 전환 조회"""
        sql_path = self.query_dir / "TRACE" / "phase" / "get_latest.sql"
        result = await run_sql_query(sql_path, [session_id])
        return result[0] if result else None

    async def get_phase_statistics(self, session_id: str) -> List[Dict[str, Any]]:
        """Phase별 총 소요 시간 및 전환 횟수"""
        sql_path = self.query_dir / "TRACE" / "phase" / "get_statistics.sql"
        results = await run_sql_query(sql_path, [session_id])
        return list(results) if results else []

    async def get_phase_pattern(self, session_id: str) -> List[Dict[str, Any]]:
        """Phase 전환 패턴 조회"""
        sql_path = self.query_dir / "TRACE" / "phase" / "get_pattern.sql"
        results = await run_sql_query(sql_path, [session_id])
        return list(results) if results else []

    async def get_phase_summary(self, session_id: str) -> List[Dict[str, Any]]:
        """Phase 전환 요약 리포트"""
        sql_path = self.query_dir / "TRACE" / "phase" / "get_summary.sql"
        results = await run_sql_query(sql_path, [session_id])
        return list(results) if results else []
