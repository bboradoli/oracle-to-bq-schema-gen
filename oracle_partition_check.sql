-- ============================================================================
-- Oracle 파티션 정보 확인 쿼리
-- ============================================================================
-- Oracle 데이터베이스에서 파티션 테이블과 파티션 키 정보를 확인하는 쿼리입니다.
-- 이 정보를 통해 어떤 테이블이 파티션되어 있는지, 어떤 컬럼이 파티션 키인지 확인할 수 있습니다.
-- ============================================================================

-- ============================================================================
-- 1. 파티션 테이블 목록 조회
-- ============================================================================
-- 스키마 내의 모든 파티션 테이블 정보를 조회합니다.
-- ============================================================================

SELECT 
    OWNER,
    TABLE_NAME,
    PARTITIONING_TYPE,      -- RANGE, LIST, HASH, SYSTEM 등
    SUBPARTITIONING_TYPE,   -- 서브파티션 타입
    PARTITION_COUNT,        -- 파티션 개수
    DEF_SUBPARTITION_COUNT, -- 기본 서브파티션 개수
    PARTITIONING_KEY_COUNT, -- 파티션 키 컬럼 개수
    STATUS,                 -- VALID, UNUSABLE 등
    DEF_TABLESPACE_NAME,    -- 기본 테이블스페이스
    INTERVAL                -- 인터벌 파티션 간격
FROM 
    ALL_PART_TABLES
WHERE 
    OWNER = 'YOUR_SCHEMA_NAME'  -- 스키마명 지정
    -- OWNER IN ('SCHEMA1', 'SCHEMA2')  -- 여러 스키마 지정 시
ORDER BY 
    OWNER,
    TABLE_NAME;


-- ============================================================================
-- 2. 파티션 키 컬럼 조회
-- ============================================================================
-- 각 파티션 테이블의 파티션 키로 사용되는 컬럼 정보를 조회합니다.
-- ============================================================================

SELECT 
    OWNER,
    NAME AS TABLE_NAME,
    COLUMN_NAME,
    COLUMN_POSITION,        -- 파티션 키 순서 (복합 파티션 키의 경우)
    OBJECT_TYPE             -- TABLE 또는 INDEX
FROM 
    ALL_PART_KEY_COLUMNS
WHERE 
    OWNER = 'YOUR_SCHEMA_NAME'  -- 스키마명 지정
    AND OBJECT_TYPE = 'TABLE'   -- 테이블만 조회 (인덱스 제외)
ORDER BY 
    OWNER,
    NAME,
    COLUMN_POSITION;


-- ============================================================================
-- 3. 파티션 테이블과 파티션 키 통합 조회
-- ============================================================================
-- 파티션 테이블 정보와 파티션 키 컬럼을 함께 조회합니다.
-- ============================================================================

SELECT 
    apt.OWNER,
    apt.TABLE_NAME,
    apt.PARTITIONING_TYPE,
    apt.PARTITION_COUNT,
    apkc.COLUMN_NAME AS PARTITION_KEY_COLUMN,
    apkc.COLUMN_POSITION AS KEY_POSITION,
    atc.DATA_TYPE,
    atc.DATA_PRECISION,
    atc.DATA_SCALE
FROM 
    ALL_PART_TABLES apt
    INNER JOIN ALL_PART_KEY_COLUMNS apkc
        ON apt.OWNER = apkc.OWNER
        AND apt.TABLE_NAME = apkc.NAME
        AND apkc.OBJECT_TYPE = 'TABLE'
    LEFT JOIN ALL_TAB_COLUMNS atc
        ON apt.OWNER = atc.OWNER
        AND apt.TABLE_NAME = atc.TABLE_NAME
        AND apkc.COLUMN_NAME = atc.COLUMN_NAME
WHERE 
    apt.OWNER = 'YOUR_SCHEMA_NAME'  -- 스키마명 지정
ORDER BY 
    apt.OWNER,
    apt.TABLE_NAME,
    apkc.COLUMN_POSITION;


-- ============================================================================
-- 4. 개별 파티션 정보 조회
-- ============================================================================
-- 각 파티션 테이블의 개별 파티션 상세 정보를 조회합니다.
-- ============================================================================

SELECT 
    TABLE_OWNER,
    TABLE_NAME,
    PARTITION_NAME,
    PARTITION_POSITION,     -- 파티션 순서
    HIGH_VALUE,             -- 파티션 상한값 (RANGE 파티션)
    TABLESPACE_NAME,
    NUM_ROWS,               -- 파티션 내 행 수 (통계 정보)
    BLOCKS,                 -- 파티션 블록 수
    COMPRESSION,            -- 압축 여부
    LAST_ANALYZED           -- 마지막 분석 일시
FROM 
    ALL_TAB_PARTITIONS
WHERE 
    TABLE_OWNER = 'YOUR_SCHEMA_NAME'  -- 스키마명 지정
    -- AND TABLE_NAME = 'SPECIFIC_TABLE'  -- 특정 테이블만 조회 시
ORDER BY 
    TABLE_OWNER,
    TABLE_NAME,
    PARTITION_POSITION;


-- ============================================================================
-- 5. 서브파티션 정보 조회 (복합 파티션의 경우)
-- ============================================================================
-- 서브파티션이 있는 테이블의 서브파티션 정보를 조회합니다.
-- ============================================================================

SELECT 
    TABLE_OWNER,
    TABLE_NAME,
    PARTITION_NAME,
    SUBPARTITION_NAME,
    SUBPARTITION_POSITION,
    HIGH_VALUE,
    TABLESPACE_NAME,
    NUM_ROWS,
    BLOCKS
FROM 
    ALL_TAB_SUBPARTITIONS
WHERE 
    TABLE_OWNER = 'YOUR_SCHEMA_NAME'  -- 스키마명 지정
ORDER BY 
    TABLE_OWNER,
    TABLE_NAME,
    PARTITION_NAME,
    SUBPARTITION_POSITION;


-- ============================================================================
-- 6. 파티션 타입별 테이블 개수 통계
-- ============================================================================
-- 스키마 내 파티션 타입별 테이블 개수를 집계합니다.
-- ============================================================================

SELECT 
    OWNER,
    PARTITIONING_TYPE,
    COUNT(*) AS TABLE_COUNT,
    SUM(PARTITION_COUNT) AS TOTAL_PARTITIONS
FROM 
    ALL_PART_TABLES
WHERE 
    OWNER = 'YOUR_SCHEMA_NAME'  -- 스키마명 지정
GROUP BY 
    OWNER,
    PARTITIONING_TYPE
ORDER BY 
    OWNER,
    PARTITIONING_TYPE;


-- ============================================================================
-- 7. 파티션 키로 사용된 컬럼 타입 통계
-- ============================================================================
-- 파티션 키로 사용된 컬럼의 데이터 타입별 통계를 조회합니다.
-- ============================================================================

SELECT 
    atc.DATA_TYPE,
    COUNT(DISTINCT apkc.OWNER || '.' || apkc.NAME) AS TABLE_COUNT,
    COUNT(*) AS COLUMN_COUNT
FROM 
    ALL_PART_KEY_COLUMNS apkc
    INNER JOIN ALL_TAB_COLUMNS atc
        ON apkc.OWNER = atc.OWNER
        AND apkc.NAME = atc.TABLE_NAME
        AND apkc.COLUMN_NAME = atc.COLUMN_NAME
WHERE 
    apkc.OWNER = 'YOUR_SCHEMA_NAME'  -- 스키마명 지정
    AND apkc.OBJECT_TYPE = 'TABLE'
GROUP BY 
    atc.DATA_TYPE
ORDER BY 
    TABLE_COUNT DESC;


-- ============================================================================
-- 8. BigQuery 마이그레이션 호환성 체크
-- ============================================================================
-- BigQuery에서 지원하는 파티션 타입(DATE, TIMESTAMP, DATETIME)인지 확인합니다.
-- ============================================================================

SELECT 
    apkc.OWNER,
    apkc.NAME AS TABLE_NAME,
    apkc.COLUMN_NAME AS PARTITION_KEY,
    atc.DATA_TYPE,
    apt.PARTITIONING_TYPE AS ORACLE_PARTITION_TYPE,
    CASE 
        WHEN atc.DATA_TYPE IN ('DATE', 'TIMESTAMP') THEN 'COMPATIBLE'
        WHEN atc.DATA_TYPE LIKE 'TIMESTAMP%' THEN 'COMPATIBLE'
        WHEN atc.DATA_TYPE IN ('NUMBER', 'INTEGER') THEN 'RANGE_PARTITION_NEEDED'
        ELSE 'NOT_COMPATIBLE'
    END AS BIGQUERY_COMPATIBILITY,
    CASE 
        WHEN atc.DATA_TYPE IN ('DATE', 'TIMESTAMP') THEN 'PARTITION BY DATE(column) or DATETIME_TRUNC(column, DAY)'
        WHEN atc.DATA_TYPE LIKE 'TIMESTAMP%' THEN 'PARTITION BY DATETIME_TRUNC(column, DAY)'
        WHEN atc.DATA_TYPE IN ('NUMBER', 'INTEGER') THEN 'PARTITION BY RANGE_BUCKET(column, GENERATE_ARRAY(...))'
        ELSE 'NOT SUPPORTED - Consider alternative partitioning strategy'
    END AS BIGQUERY_RECOMMENDATION
FROM 
    ALL_PART_KEY_COLUMNS apkc
    INNER JOIN ALL_TAB_COLUMNS atc
        ON apkc.OWNER = atc.OWNER
        AND apkc.NAME = atc.TABLE_NAME
        AND apkc.COLUMN_NAME = atc.COLUMN_NAME
    INNER JOIN ALL_PART_TABLES apt
        ON apkc.OWNER = apt.OWNER
        AND apkc.NAME = apt.TABLE_NAME
WHERE 
    apkc.OWNER = 'YOUR_SCHEMA_NAME'  -- 스키마명 지정
    AND apkc.OBJECT_TYPE = 'TABLE'
ORDER BY 
    apkc.OWNER,
    apkc.NAME,
    apkc.COLUMN_POSITION;


-- ============================================================================
-- 9. 파티션되지 않은 대용량 테이블 조회
-- ============================================================================
-- 파티션이 없지만 행 수가 많아 파티션을 고려해야 할 테이블을 조회합니다.
-- ============================================================================

SELECT 
    at.OWNER,
    at.TABLE_NAME,
    at.NUM_ROWS,
    ROUND(at.NUM_ROWS / 1000000, 2) AS ROWS_IN_MILLIONS,
    at.LAST_ANALYZED,
    -- DATE/TIMESTAMP 타입 컬럼 찾기 (파티션 후보)
    LISTAGG(
        CASE 
            WHEN atc.DATA_TYPE IN ('DATE', 'TIMESTAMP') OR atc.DATA_TYPE LIKE 'TIMESTAMP%'
            THEN atc.COLUMN_NAME 
        END, ', '
    ) WITHIN GROUP (ORDER BY atc.COLUMN_ID) AS DATE_COLUMNS
FROM 
    ALL_TABLES at
    LEFT JOIN ALL_TAB_COLUMNS atc
        ON at.OWNER = atc.OWNER
        AND at.TABLE_NAME = atc.TABLE_NAME
        AND (atc.DATA_TYPE IN ('DATE', 'TIMESTAMP') OR atc.DATA_TYPE LIKE 'TIMESTAMP%')
WHERE 
    at.OWNER = 'YOUR_SCHEMA_NAME'  -- 스키마명 지정
    AND at.NUM_ROWS > 1000000      -- 100만 행 이상
    AND NOT EXISTS (
        SELECT 1 
        FROM ALL_PART_TABLES apt 
        WHERE apt.OWNER = at.OWNER 
        AND apt.TABLE_NAME = at.TABLE_NAME
    )
GROUP BY 
    at.OWNER,
    at.TABLE_NAME,
    at.NUM_ROWS,
    at.LAST_ANALYZED
ORDER BY 
    at.NUM_ROWS DESC;


-- ============================================================================
-- 사용 예시
-- ============================================================================
-- 
-- 1. 스키마의 모든 파티션 테이블 확인:
--    쿼리 1번 실행
--
-- 2. 특정 테이블의 파티션 키 확인:
--    쿼리 2번 실행 후 TABLE_NAME 필터 추가
--
-- 3. BigQuery 마이그레이션 호환성 체크:
--    쿼리 8번 실행
--
-- 4. 파티션 추가 고려 대상 테이블 찾기:
--    쿼리 9번 실행
--
-- ============================================================================
