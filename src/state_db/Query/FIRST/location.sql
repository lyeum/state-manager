-- 1. location 테이블 생성
CREATE TABLE IF NOT EXISTS location (
    -- 엔티티 필수
    location_id UUID PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL DEFAULT 'location',
    name VARCHAR(100) NOT NULL,
    description TEXT DEFAULT '',

    -- session/시나리오 참조
    session_id UUID NOT NULL REFERENCES session(session_id) ON DELETE CASCADE,
    scenario_id UUID NOT NULL,
    scenario_location_id UUID NOT NULL,

    -- 공간 정보 (좌표, 타입 등)
    location_type VARCHAR(50) DEFAULT 'room', -- 예: city, room, dungeon
    is_accessible BOOLEAN DEFAULT TRUE,

    -- meta 정보
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- 확장 요소 (장소의 특수 상태 - 예: 밝기, 오염도, 기온 등)
    state JSONB NOT NULL DEFAULT '{
        "numeric": {
            "light_level": 100,
            "temperature": 20,
            "security_level": 1
        },
        "boolean": {
            "is_locked": false,
            "has_trap": false,
            "is_discovered": true
        }
    }'::jsonb,

    -- RELATION 엣지 ID 저장 (인접한 장소들과의 통로 등)
    relations JSONB DEFAULT '[]'::jsonb
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_location_session_id ON location(session_id);
CREATE INDEX IF NOT EXISTS idx_location_scenario_id ON location(scenario_id);
CREATE INDEX IF NOT EXISTS idx_location_scenario_location_id ON location(scenario_location_id);

-- 주석
COMMENT ON TABLE location IS '시나리오에서 정의된 장소(공간) 테이블';
COMMENT ON COLUMN location.location_id IS '장소 고유 ID';
COMMENT ON COLUMN location.session_id IS '장소가 속한 세션 ID';
COMMENT ON COLUMN location.scenario_location_id IS '시나리오에서의 장소 템플릿 ID';

-- 2. updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_location_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_location_updated_at ON location;
CREATE TRIGGER trg_location_updated_at
BEFORE UPDATE ON location
FOR EACH ROW
EXECUTE FUNCTION update_location_updated_at();

-- 3. session 생성 시 초기 장소 자동 생성 트리거
CREATE OR REPLACE FUNCTION initialize_locations()
RETURNS TRIGGER AS $$
BEGIN
    -- 시나리오에 정의된 초기 장소들을 생성 (예시 데이터)
    -- 실제 운영 시 scenario_locations 마스터 테이블에서 SELECT INSERT 하는 구조 권장
    INSERT INTO location (
        location_id,
        session_id,
        scenario_id,
        scenario_location_id,
        name,
        description,
        location_type,
        state,
        created_at
    )
    VALUES (
        gen_random_uuid(),
        NEW.session_id,
        NEW.scenario_id,
        gen_random_uuid(),
        'Starting Point',
        'The adventure begins here.',
        'room',
        '{
            "numeric": { "light_level": 100, "temperature": 20, "security_level": 0 },
            "boolean": { "is_locked": false, "has_trap": false, "is_discovered": true }
        }'::jsonb,
        NEW.started_at
    );

    RAISE NOTICE '[LOCATION] Initial locations created for session %', NEW.session_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_10_initialize_locations ON session;
CREATE TRIGGER trigger_08_initialize_locations
    AFTER INSERT ON session
    FOR EACH ROW
    EXECUTE FUNCTION initialize_locations();