-- 특정 적과 관련된 상태 변화 이력 조회 (turn_id 기반)
SELECT turn_number, turn_type, state_changes, created_at
FROM turn
WHERE session_id = '{session_uuid}' 
  AND state_changes @> jsonb_build_object('target_id', '{enemy_uuid}')
ORDER BY turn_number ASC;