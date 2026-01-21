-- player.sql
-- Entity schema 기반 Player Node 정의
-- Graph 중심 설계를 위한 최소 상태 노드 + JSONB 확장 가능 구조

-- 1. 테이블 생성
CREATE TABLE IF NOT EXISTS player (
    -- entity_schema 필수 요소
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),   -- 엔티티 고유 ID
    entity_type VARCHAR(50) NOT NULL DEFAULT 'character',  -- 엔티티 유형
    name VARCHAR(100) NOT NULL,                     -- 플레이어 이름
    description TEXT DEFAULT '',                     -- 설명
    
    -- meta 정보
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],           -- 검색 / 분류용 태그

    -- 2차 확장 요소
    state JSONB DEFAULT '{}'::jsonb,               -- HP, MP, 상태 등 동적 정보 저장
    relations JSONB DEFAULT '{}'::jsonb            -- 다른 엔티티와의 관계 정보 저장 (edge)
);

-- 2. updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_player_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_player_updated_at
BEFORE UPDATE ON player
FOR EACH ROW
EXECUTE FUNCTION update_player_updated_at();

-- 3. 초기 데이터 (player1)
INSERT INTO player (
    name,
    description,
    tags,
    state,
    relations
) VALUES (
    'Player1',
    '초기 플레이어 노드 (edge 기반 확장 전제)',
    ARRAY['player', 'main_character'],
    '{"HP": 100, "MP": 50}'::jsonb,                -- 초기 상태
    '{}'::jsonb                                     -- 초기 관계는 빈 객체
);
