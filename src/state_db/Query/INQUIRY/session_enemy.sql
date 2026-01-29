-- 현재 세션에 복제된 적들의 목록과 실시간 HP 조회
SELECT enemy_id, name, state->'numeric'->>'HP' AS hp, tags
FROM enemy
WHERE session_id = '{session_uuid}';