-- 1. 적의 HP 차감 (JSONB 수치 수정)
UPDATE enemy 
SET state = jsonb_set(state, '{numeric, HP}', 
    (COALESCE((state->'numeric'->>'HP')::int, 0) - {damage_value})::text::jsonb)
WHERE enemy_id = '{enemy_uuid}' AND session_id = '{session_uuid}';

-- 2. 상태 변화에 따른 턴 증가 및 로그 기록 (record_state_change 함수 호출)
SELECT record_state_change(
    '{session_uuid}', 
    'combat_action', 
    jsonb_build_object('target_id', '{enemy_uuid}', 'action', 'damage', 'value', {damage_value})
);