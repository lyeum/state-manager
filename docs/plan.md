📜 TRPG 시스템 데이터베이스 구축 및 운영 계획
이 계획은 **"설계도(Master)는 보존하고, 진행 상황(State)은 세션별로 격리한다"**는 원칙을 단 하나의 통합 DDL 파일로 구현하는 것을 목표로 합니다.

1. 데이터베이스 아키텍처: "One-Time DDL" 구조
서버 시작 시 실행되는 단일 SQL 파일에는 다음 두 그룹의 테이블이 포함됩니다.

Group A: Master Tables (정적 설계도)
목적: 시나리오 작가와 룰 엔진이 정의한 원본 데이터를 영구 보관.

특징: session_id가 없음. 시나리오 고유 ID(scenario_id)로 관리됨.

대상: scenario, npc_master, enemy_master, item_master, player_template.

Group B: State/Instance Tables (동적 실행기)
목적: 특정 플레이 세션의 실시간 데이터(HP 감소, 아이템 획득 등)를 기록.

특징: 모든 테이블이 session_id를 가짐. 세션 종료 시 CASCADE 삭제됨.

대상: session, npc, enemy, item, player, inventory, phase, turn.

2. 데이터 흐름 및 생애주기 (Life-Cycle)
Step 1: 마스터 데이터 로드 (최초 1회)
시나리오 작성 도구(Writer)나 룰 엔진이 _master 테이블들에 데이터를 채워넣습니다.

예: npc_master에 "이순신 NPC (HP: 100, 태그: ['장군'])" 데이터 저장.

Step 2: 세션 인스턴스화 (Instantiation)
유저가 게임을 시작하여 session 테이블에 새 행을 추가(INSERT)합니다.

핵심 로직: DB 내부의 initialize_session_data() 함수(Trigger)가 자동으로 다음을 수행합니다.

npc_master에서 해당 시나리오의 NPC들을 읽어와 npc 테이블로 복사.

player_template을 읽어와 player 테이블에 생성.

이때 생성되는 모든 복사본에 현재의 session_id를 할당.

Step 3: 런타임 플레이 (Runtime)
게임 중 발생하는 모든 변화는 오직 **Group B(State Tables)**에만 반영됩니다.

플레이어가 NPC에게 데미지를 주면 npc.state의 HP가 100에서 80으로 업데이트됩니다.

결과: 원본인 npc_master는 여전히 HP 100을 유지하므로, 다른 유저가 세션을 시작해도 아무런 영향이 없습니다.

Step 4: 세션 종료 및 정리 (Cleanup)
게임이 끝나고 session 로우를 삭제하면, ON DELETE CASCADE 설정에 의해 해당 세션의 모든 npc, player, inventory 기록이 자동으로 삭제됩니다.

3. 단계별 구축 상세 로드맵
Phase 1: 통합 DDL 작성 (현재 단계)
사용자님이 주신 DDL들을 기반으로 master와 state 테이블이 서로 외래키(template_id)로 맞물리는 하나의 .sql 파일 완성.

session_id가 포함된 테이블과 포함되지 않은 테이블을 명확히 구분하여 선언.

Phase 2: 자동 복사 트리거 구현
session 테이블에 AFTER INSERT 트리거 작성.

시나리오의 Act/Sequence 진행에 따라 NPC를 순차적으로 활성화(is_active)하는 로직 포함.

Phase 3: 애플리케이션 연동 (FastAPI/Python)
schemas.py: Master와 State 각각에 대응하는 Pydantic 모델 정의.

repository.py: SQLAlchemy 또는 SQL을 사용하여 Master를 읽고 State를 수정하는 CRUD 로직 구현.

Phase 4: 데이터 정합성 검증
entity_schema.json 규격이 Master에 저장될 때와 State로 복사될 때 일관성을 유지하는지 테스트.

4. 이 방식의 기대 효과
관리의 단순화: 서버 초기화 시 SQL 파일 하나만 돌리면 모든 DB 준비가 끝납니다.

무한 확장성: 동일한 시나리오(master)를 기반으로 수만 개의 독립적인 세션(state)을 동시에 운영할 수 있습니다.

성능 최적화: 실시간 전투 중에는 가벼운 state 테이블만 건드리므로 DB 부하가 적습니다.