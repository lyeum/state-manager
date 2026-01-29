SELECT player_id, name, state->'numeric' AS stats, tags 
FROM player 
WHERE session_id = :session_id;