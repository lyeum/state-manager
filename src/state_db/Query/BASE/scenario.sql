-- ====================================================================
-- 1. scenario.sql (Master)
-- 시나리오 메타데이터 및 구조 정의
-- ====================================================================

CREATE TABLE IF NOT EXISTS scenario (
    scenario_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- [기존 필드 유지]
    title VARCHAR(200) NOT NULL,
    description TEXT,
    author VARCHAR(100),
    version VARCHAR(20) DEFAULT '1.0.0',
    total_acts INTEGER NOT NULL DEFAULT 3 CHECK (total_acts > 0),
    
    -- [추가] 세션 초기화 설정 (session 생성 시 참조)
    initial_config JSONB NOT NULL DEFAULT '{
        "start_act": 1,
        "start_sequence": 1,
        "start_phase": "exploration"
    }'::jsonb,

    is_published BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- [추가] 시나리오 흐름 구조 (숫자 리스트의 구체화)
CREATE TABLE IF NOT EXISTS scenario_structure (
    scenario_id UUID REFERENCES scenario(scenario_id) ON DELETE CASCADE,
    act_num INTEGER NOT NULL,
    seq_num INTEGER NOT NULL,
    title VARCHAR(200), 
    summary TEXT,
    PRIMARY KEY (scenario_id, act_num, seq_num)
);