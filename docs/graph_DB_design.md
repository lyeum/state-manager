
1. State_DB 구조적인 조건
: RDB = node(entity) | GDB = edge

질의) 
: Apache AGE(cypher + SQL엔진)
* pydantic을 사용해서 안정성을 보장할 예정 
-------------------------------

2. 저장할 데이터 요소
: 일단 관계의 정의가 어떻게 되는가..

# 저장형태?
- 불변 state(Rule Graph)) 시스템 설계 단계에서 미리 정의된 (state)-[:CAN_TRANSITOIN]->(STATE) 
- 가변 state) instance= Entity-[:IN_STATE{session_id}]->(STATE) # 큰 분류

# 데이터 구분
- Node 
: 미리 DB에 등록한 객체(명사) 집합
내부구성) entity_id/name/type/description
 * location
 * condition
 * safe_level

- edge : 
1) trigger 속성 
: 사용자가 하는 행위, 특정 event 발동 요소
ex)
 * condition_ref 
 * required_item
 

2) instance 속성
: session_id를 기준으로 edge를 교체하거나 중첩해서 저장하는 형태.
시작 시에만 처음 생성되고, 끝나기 전까지 교체/중첩과정을 통해 user하나에 대한 
state를 유지한다.

내부구성) session_id/created_at/is_active/duration
* session_id= 사용자 상태에 대한 정보
* created_at= 현재 상태 발생 시점
* is_active= 활성화된 edge의 유효성을 따진다
* duration= edge의 활성화 지속시간 

- Query
: DB에 등재된 단어와 동사만으로 재구성. DB를 기준으로 모르는 요소는 무시로 처리한다. 
[Entity] + [Triger] + [Target Node]로 재구성됨 


--------------------------------
3. pipeline 

# Default로 parsing하는 과정
: 전달받은 데이터에서 인지할 수 있는 요소들만을 뽑아서 
 (Entities)-[Triger] + [Target]형태로 재구성한다. 



# 전달받은 Query에 대한 처리과정
## [1]. query 발동시, session_id를 기준으로 instance를 조회한다. == 사용자 상태 식별

-- 1. 현재 세션의 위치(좌표)를 특정하고
-- 2. 해당 위치에서 실행 가능한 트리거(설계도)와 목적지를 탐색
MATCH (e:Entity {entity_id: "ent_01"})-[instance:IN_STATE {session_id: "A1"}]->(current_loc:location),
      (current_loc)-[rule:CAN_TRANSITION {trigger: "CRAFT"}]->(target)
RETURN current_loc.name AS current_pos, 
       rule.required_item AS requirements, 
       target.name AS potential_result;

## [2]. 식별된 사용자의 instance를 특정한뒤, 변환 받은 query를 기준으로 graph를 조회한다. 


## [3]. 고정된 좌표 상에서 query의 허용여부 판정을 위한 정보들을 탐색한다(pattern_matching/sub_extraction)

## [4]. 탐색된 정보들과 query를 rule-Engine에 전달해 판정 결과를 받는다.
      --> 판정결과는 rule-engine이 LLM_GateWay에 전달하는 영역. 

## [5]. 판정결과를 토대로, Entity의 기존 상태를 갱신한다. == edge의 활성화/비활성화
      -->edge를 끊어서 새 node에 연결하거나, 변화가 없거나(관계를 대체하는 식으로 갱신)

## [6]. 갱신한 결과를 LLM_GateWay에 전달해서 실시간으로 갱신 및 유지.

# 내부 정보 순회 -> state 항상성 유지과정 : edge를 기준으로 가변 instance 유지 
: query 없이 시스템 스스로가 시간의 흐름/ 지속효과에 대해 계산 --> state에 대한 실시간성 유지
[1]. 주기적으로 활성화된 edge를 순회
[2]. 수치조정 혹은 시간이 지난 엣지를 자동으로 분리 == edge 비활성화 
[3]. LLM_GateWay에게만 계속해서 정보를 보낸다. 

# 예시)
: 천과 나무 막대로 횃불 만들기 
-> 


