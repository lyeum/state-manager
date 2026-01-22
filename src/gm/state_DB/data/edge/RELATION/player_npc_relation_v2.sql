-- player_npc_relation.sql
-- Player와 NPC 간의 관계 생성/업데이트
-- Apache AGE Cypher 쿼리 사용
--
-- Parameters:
--   :player_id       - 플레이어 UUID (player.id)
--   :npc_id          - NPC UUID (npc.npc_id)
--   :session_id      - 세션 UUID
--   :relation_type   - 관계 유형 (선택, 기본값: 'neutral')
--   :affinity        - 호감도 (선택, 기본값: 0)
--   :current_turn    - 현재 턴 번호
--   :meta            - 추가 메타데이터 JSONB (선택)
--
-- 반환값:
--   relation_id, relation_type, affinity, meta

SELECT *
FROM cypher('state_db_actor_logic', $$
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
$$) AS (
  relation_id agtype,
  relation_type agtype,
  affinity agtype,
  meta agtype
);
