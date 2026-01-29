-- ====================================================================
-- L_item.sql
-- 아이템 세션 초기화 로직 (Logic)
-- ====================================================================

CREATE OR REPLACE FUNCTION initialize_items()
RETURNS TRIGGER AS $$
BEGIN
    -- [사용자 원본 로직 유지]
    -- 세션 생성 시 RuleEngine에서 정의한 기본 아이템들을 즉시 삽입
    INSERT INTO item (
        item_id,
        session_id,
        name,
        description,
        item_type,
        created_at
    )
    VALUES
    (
        gen_random_uuid(),
        NEW.session_id,
        'Health Potion',
        'Restores 50 HP',
        'consumable',
        NEW.started_at
    ),
    (
        gen_random_uuid(),
        NEW.session_id,
        'Rusty Sword',
        'An old sword',
        'equipment',
        NEW.started_at
    );

    RAISE NOTICE '[Item] Initial items loaded for session %', NEW.session_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 설정 (불필요한 WHEN 조건 제거)
DROP TRIGGER IF EXISTS trigger_05_initialize_items ON session;
CREATE TRIGGER trigger_05_initialize_items
    AFTER INSERT ON session
    FOR EACH ROW
    EXECUTE FUNCTION initialize_items();