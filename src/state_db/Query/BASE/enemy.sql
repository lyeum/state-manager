-- ====================================================================
-- 3. enemy.sql (Master)
-- Enemy 원형 및 출현 위치
-- ====================================================================

CREATE TABLE IF NOT EXISTS enemy_master (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID NOT NULL REFERENCES scenario(scenario_id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- [Lifecycle] 적 출현 정보 (다수 등장/재등장 지원을 위해 JSONB 사용)
    -- 예: [{"act": 1, "seq": 2, "location": "ruins"}, {"act": 3, "seq": 1, "location": "boss_room"}]
    appearance_info JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- [Entity Schema] 기존 enemy.sql 구조 반영
    meta JSONB NOT NULL DEFAULT '{"difficulty_rank": 1}'::jsonb,
    
    state JSONB NOT NULL DEFAULT '{
        "numeric": {
            "HP": 100, "MP": 0, "SAN": null,
            "STR": null, "DEX": null, "INT": null, "LUX": null
        },
        "boolean": {}
    }'::jsonb,

    relations JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- [Item] 전리품 (item_master.item_template_id 참조)
    dropped_item_templates UUID[] DEFAULT ARRAY[]::UUID[],
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);