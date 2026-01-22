-- player_npc_relation.cypher
-- Player와 NPC 간의 관계 정의
--
-- 관계 타입: PLAYER_NPC_RELATION
-- 방향: player ↔ npc (양방향)
--
-- 속성:
--   - relation_id: UUID (고유 식별자)
--   - session_id: UUID (세션 격리)
--   - relation_type: TEXT (관계 유형: 'friendly', 'hostile', 'neutral', 'quest_giver' 등)
--   - affinity: INTEGER (호감도: -100 ~ 100)
--   - meta: JSONB (추가 메타데이터)
--     * first_met_turn: INTEGER (최초 만남 턴)
--     * last_interaction_turn: INTEGER (마지막 상호작용 턴)
--     * dialogue_count: INTEGER (대화 횟수)
--   - created_at: TIMESTAMP
--   - updated_at: TIMESTAMP
--
-- 참고:
--   - player.id 사용
--   - npc.npc_id 사용
--   - 둘 다 session_id로 격리됨

MATCH
  (p:player {id: $player_id, session_id: $session_id}),
  (n:npc {npc_id: $npc_id, session_id: $session_id})
MERGE
  (p)-[r:PLAYER_NPC_RELATION]-(n)
ON CREATE SET
  r.relation_id = gen_random_uuid(),
  r.session_id = $session_id,
  r.relation_type = coalesce($relation_type, 'neutral'),
  r.affinity = coalesce($affinity, 0),
  r.meta = coalesce($meta, jsonb_build_object(
    'first_met_turn', $current_turn,
    'last_interaction_turn', $current_turn,
    'dialogue_count', 0
  )),
  r.created_at = now()
ON MATCH SET
  r.affinity = coalesce($affinity, r.affinity),
  r.relation_type = coalesce($relation_type, r.relation_type),
  r.meta = jsonb_set(
    r.meta,
    '{last_interaction_turn}',
    to_jsonb($current_turn)
  ),
  r.meta = jsonb_set(
    r.meta,
    '{dialogue_count}',
    to_jsonb((r.meta->'dialogue_count')::int + 1)
  ),
  r.updated_at = now()
RETURN
  r.relation_id AS relation_id,
  r.relation_type AS relation_type,
  r.affinity AS affinity,
  r.meta AS meta
