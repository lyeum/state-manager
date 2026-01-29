-- 시스템 세션(Master)과 현재 세션의 Enemy 숫자 비교 검증
SELECT 
    (SELECT count(*) FROM enemy WHERE session_id = '00000000-0000-0000-0000-000000000000') AS master_count,
    (SELECT count(*) FROM enemy WHERE session_id = '{session_uuid}') AS session_count;