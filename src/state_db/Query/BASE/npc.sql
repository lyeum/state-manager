-- ====================================================================
-- 2. npc.sql (Master)
-- NPC 원형 및 등장 조건
-- ====================================================================

CREATE TABLE IF NOT EXISTS npc_master (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Writer 제공 ID
    scenario_id UUID NOT NULL REFERENCES scenario(scenario_id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- [Lifecycle] 등장 및 퇴장 조건 (세션 트리거용)
    spawn_act INTEGER NOT NULL DEFAULT 1,
    spawn_seq INTEGER NOT NULL DEFAULT 1,
    despawn_act INTEGER, 
    despawn_seq INTEGER,

    -- [Entity Schema] entity_schema.json 및 기존 npc.sql의 state 구조 반영
    meta JSONB NOT NULL DEFAULT '{"tags": []}'::jsonb,
    
    state JSONB NOT NULL DEFAULT '{
        "numeric": {
            "HP": 100, "MP": 50, "SAN": 10,
            "STR": null, "DEX": null, "INT": null, "LUX": null
        },
        "boolean": {}
    }'::jsonb,
    
    -- [Relations] player_npc_relations.sql의 초기 호감도 정보 통합
    -- 예: [{"target": "player", "affinity": 50, "type": "neutral"}]
    relations JSONB DEFAULT '[]'::jsonb,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);