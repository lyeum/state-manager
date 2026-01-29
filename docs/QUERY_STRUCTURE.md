# src/state_db/Query 디렉토리 구조 보고서

본 보고서는 `src/state_db/Query` 내의 SQL 및 Cypher 쿼리 파일들의 구조와 역할을 정리한 문서입니다. 시스템은 크게 스키마 정의, 초기화, 조회, 업데이트, 추적, 관리 및 디버깅의 8개 카테고리로 나뉩니다.

## 1. 디렉토리별 역할 상세 정의

| 디렉토리 | 구분 | 역할 및 상세 설명 |
| :--- | :--- | :--- |
| **BASE** | **시스템 뼈대** | **B_ (Base)** 파일은 테이블, 인덱스 등 정적 스키마를 정의하며, **L_ (Logic)** 파일은 세션 복제 트리거, 턴 전진 함수(`record_state_change`) 등 핵심 비즈니스 로직을 포함합니다. |
| **FIRST** | **초기 데이터** | 시스템 가동 및 테스트를 위한 마스터 시나리오, 기본 아이템, NPC 등 `Session 0`용 초기 레코드를 삽입하는 DML 집합입니다. |
| **INQUIRY** | **다차원 조회** | 게임 엔진과 UI에 필요한 정보를 제공합니다. `inventory`, `npc`, `phase`, `relations`, `scenario`, `session` 하위 폴더로 나뉘어 각 도메인별 상세/목록 조회를 수행합니다. |
| **UPDATE** | **실시간 변경** | 플레이어 행동 및 시스템 이벤트에 따른 상태 변화를 처리합니다. 수치 변경 시 자동으로 턴 이력이 생성되도록 로직이 연동되어 있으며, 엔티티별(NPC, Enemy, Player 등) 하위 폴더를 가집니다. |
| **START_by_session** | **세션 인스턴스화** | 신규 세션 시작 시 호출됩니다. SQL을 통한 엔티티 복제뿐만 아니라 Cypher(`*.cypher`)를 이용해 그래프 DB의 관계 데이터(인벤토리 소유권, NPC 관계 등)를 초기화합니다. |
| **TRACE** | **이력 추적** | `turn`, `phase`, `entity` 단위의 타임라인을 제공합니다. 특정 시점의 상태를 복구하거나 플레이어의 행동 궤적을 분석하여 리플레이 및 통계 데이터의 기반이 됩니다. |
| **MANAGE** | **운영 및 제어** | 시나리오의 흐름(Act, Sequence 전환)과 세션의 생명주기(Pause, Resume, End)를 관리합니다. GM 명령이나 시스템 강제 전환 로직이 포함됩니다. |
| **DEBUG** | **진단 및 검증** | `Analyze`(분석), `History`(로그), `Debuggig`(무결성) 폴더를 통해 데이터 불일치를 탐지하고 세션 전체 상태를 덤프하여 문제 해결을 돕습니다. |

---

## 2. 디렉토리 및 파일별 상세 명세

### 📂 BASE (기반 구조 및 로직)
시스템의 핵심 스키마와 자동화 로직을 담당합니다.
- **B_*.sql (Base Schema)**: 테이블 정의 (enemy, inventory, item, npc, phase, player, scenario, session, turn 등)
- **L_*.sql (Logic & Trigger)**: 
    - `L_session.sql`: 세션 생성 로직 및 시나리오 메타데이터 연결.
    - `L_turn.sql`: `record_state_change` 함수를 통한 턴 자동 관리.
    - `L_phase.sql`: 페이즈 전환 감지 및 규칙 검증 로직.
    - `L_enemy.sql`, `L_npc.sql` 등: Session 0 마스터 데이터를 신규 세션으로 복제하는 트리거.

### 📂 FIRST (초기/참조용 스키마)
시스템 초기 설계 버전 또는 수동 데이터 삽입을 위한 참조 파일들입니다. 현재는 `BASE`가 주력으로 사용됩니다.

### 📂 INQUIRY (상태 조회)
엔진 및 프론트엔드 요청에 응답하기 위한 조회 전용 쿼리입니다.
- **inventory/**: `Check_item.sql`(아이템 소유 여부), `List_inventory.sql`(인벤토리 전체 조회)
- **npc/**: `Detail_npc.sql`(스탯 및 배경 조회), `List_npc.sql`(세션 내 NPC 목록)
- **relations/**: `Check_affinity.sql`(호감도 확인)
- **session/**: `Session_active.sql`(현재 활성화된 세션 조회), `Session_phase.sql`(현재 페이즈 정보)

### 📂 UPDATE (상태 변경)
게임 내 동적 변화를 반영하는 쿼리입니다.
- **damaged-r.sql**: 플레이어와 적의 HP 감소 및 MP 소모 통합 처리.
- **earn_item-r.sql / use_item-r.sql**: 아이템 획득 및 사용에 따른 인벤토리 수량 업데이트.
- **update_location-r.sql**: 현재 위치 정보(`session.location`) 갱신.
- **record_action_turn-r.sql**: 행동 완료 후 턴 데이터를 확정하고 기록.

### 📂 START_by_session (세션 초기화 실행)
세션 시작 시점에 필요한 데이터 인스턴스화 명령입니다.
- **C_session.sql**: 신규 세션 레코드 삽입 명령.
- **E_player_inventory.sql**: 플레이어 초기 아이템 지급.
- **relation.cypher / used_item.cypher**: 그래프 DB(Neo4j 등)를 위한 관계 데이터 초기화.

### 📂 TRACE (이력 및 통계)
진행 데이터를 분석하거나 특정 시점으로 되돌리기 위한 쿼리입니다.
- **phase/**: `get_summary.sql`(페이즈별 소요 시간 통계), `get_pattern.sql`(페이즈 전환 패턴 분석)
- **turn/**: `get_details.sql`(특정 턴의 상태 변화 상세), `rollback_turn.sql`(턴 되돌리기 참조)
- **entity/**: `TRACE_npc.sql`(특정 NPC와의 상호작용 이력)

### 📂 MANAGE (운영 관리)
시나리오 주입 및 세션 제어 관리를 담당합니다.
- **scenario/**: `inject_scenario.sql`(시나리오 메타데이터 등록), `inject_edge_relation.sql`(그래프 관계 주입)
- **session/**: `pause_session.sql`, `resume_session.sql`, `end_session.sql` (세션 상태 제어)
- **act / sequence/**: 시나리오 진행 단계(`current_act`, `current_sequence`) 수동 조정.

### 📂 DEBUG (진단 도구)
- **Analyze/**: `A_phase.sql` (페이즈 데이터 무결성 분석)
- **History/**: `H_turn.sql`, `H_phase.sql` (로우 레벨 히스토리 덤프)
- **session_dump-r.sql**: 오류 추적을 위한 특정 세션 전체 데이터 스냅샷.

---

## 3. Review (-r) 파일군 정리

파일명 끝에 `-r`이 붙은 파일들은 검토(Review)가 필요하거나, 특정 기능을 수행하기 위해 임시/참조용으로 작성된 쿼리 집합입니다. 주요 파일별 코멘트는 다음과 같습니다.

### DEBUG 카테고리
- **concept-r.sql**: 시스템 설계 단계의 개념 증명용 쿼리.
- **session_dump-r.sql**: 특정 세션의 모든 연관 테이블 데이터를 한 번에 추출하는 진단용 쿼리.

### INQUIRY 카테고리
- **Current_act-r.sql / Current_sequence-r.sql**: 현재 진행 중인 시나리오의 단계(Act, Sequence) 정보를 확인.
- **Location_now-r.sql**: 플레이어의 현재 위치 정보를 조회.
- **Npc_relations-r.sql**: 플레이어와 모든 NPC 간의 관계도를 일괄 확인.
- **Progress_get-r.sql**: 전반적인 시나리오 진행률 데이터를 수집.
- **session/Session_*-r.sql**: 특정 세션에 종속된 인벤토리, 플레이어, 페이즈, 턴 등의 정보를 세부적으로 필터링하여 조회.

### UPDATE 카테고리
- **damaged-r.sql / defeated_enemy-r.sql**: 전투 결과에 따른 수치 변화 기록.
- **update_location-r.sql / update_npc_affinity-r.sql**: 위치 및 호감도 변화 기록.
- **earn_item-r.sql / use_item-r.sql**: 아이템 라이프사이클(획득/사용) 처리.
- **record_action_turn-r.sql / record_system_event-r.sql**: 턴 기반 시스템에서 행동 및 시스템 이벤트를 로그에 기록.

### MANAGE & TRACE 카테고리
- **act/select_act-r.sql / sequence/select_sequence-r.sql**: 시나리오 단계 강제 전환 및 선택.
- **phase/phase_check-r.sql / session/paused_check-r.sql**: 현재 페이즈 상태 및 세션 정지 여부 검증.
- **phase_tracing-r.sql**: 페이즈 전환 흐름을 분석하기 위한 통합 조회 쿼리.

---
*참고: -r 파일 중 BASE DDL과 충돌하거나 중복되는 파일은 지속적으로 정리 및 통합되고 있습니다.*
