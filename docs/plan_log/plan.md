# Refactoring Plan

## 목적

500줄 이상의 대형 파일들을 기능별로 분할하여 유지보수성을 높이고 가독성을 개선함.

## 대상 파일

1. `src/state_db/schemas.py` (788 lines)
2. `src/state_db/data/node/core/session_Query.sql` (766 lines)
3. `src/state_db/Query/TRACE/phase_tracing-r.sql` (701 lines)
4. `src/state_db/data/node/core/m_act_seq.sql` (692 lines)
5. `src/state_db/Query/DEBUG/concept-r.sql` (647 lines)

## 진행 현황

- [x] `src/state_db/schemas.py` 분할 (cop 브랜치 스키마 변경점 통합 완료)
- [x] `src/state_db/data/node/core/session_Query.sql` 분할 및 삭제 (중복 제거)
- [x] `src/state_db/Query/TRACE/phase_tracing-r.sql` 분할
- [x] `src/state_db/data/node/core/m_act_seq.sql` 분할 및 삭제 (중복 제거)
- [x] `src/state_db/Query/DEBUG/concept-r.sql` 분할 및 삭제 (중복 제거)

## 2차 리팩터링 (Python 파일 200줄 이하 목표)

- [x] `src/state_db/infrastructure/database.py`: 스키마 초기화 로직 분리
- [x] `src/state_db/repositories/session.py`: 월드 상태 관리 로직 분리
- [x] `src/state_db/routers/router_TRACE.py`: Turn/Phase 라우터 분리
- [x] `src/state_db/models/__init__.py`: 모델 정의 파일 분산

## 상세 계획

### 1. `src/state_db/schemas.py` 분할

- `src/state_db/schemas/` 패키지화
- `cop` 브랜치의 새로운 Base 모델(SessionBase, EntityBase, StateBase 등) 및 APIKey 모델 통합 반영

### 2. SQL 파일 분할 및 로직 동기화

- `cop` 브랜치의 `is_defeated` 컬럼 및 관련 처치(Defeat) 로직 반영
- 파라미터 바인딩 방식($1, $2) 표준화 및 리포지토리 필드명 매핑 최적화
