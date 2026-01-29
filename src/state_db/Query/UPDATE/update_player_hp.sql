-- 1. 플레이어 HP 업데이트
UPDATE player 
SET state = jsonb_set(state, '{numeric, HP}', :new_hp::text::jsonb)
WHERE session_id = :session_id;

-- 2. 상태 변화 기록 (Turn 진행)
SELECT record_state_change(
    :session_id, 
    'exploration', -- 혹은 현재 phase_type
    jsonb_build_object('entity_type', 'player', 'change', 'hp_update', 'value', :new_hp)
);