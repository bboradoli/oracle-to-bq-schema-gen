-- ============================================================================
-- Oracle to BigQuery DDL Generator - Oracle 스키마 정보 추출 쿼리
-- ============================================================================
-- 이 쿼리는 Oracle 데이터베이스에서 테이블 스키마 정보를 추출하여
-- BigQuery DDL 생성기의 입력 CSV 파일로 사용할 수 있는 형식으로 출력합니다.
--
-- 사용법:
--   1. SQL*Plus, SQL Developer, DBeaver 등에서 실행
--   2. 결과를 CSV 파일로 저장 (schema.csv)
--   3. oracle-to-bq convert schema.csv 명령으로 DDL 생성
--
-- 주의사항:
--   - ALL_TAB_COLUMNS: 접근 가능한 모든 테이블 (권장)
--   - DBA_TAB_COLUMNS: DBA 권한 필요
--   - USER_TAB_COLUMNS: 현재 사용자 소유 테이블만
-- ============================================================================

-- ============================================================================
-- 옵션 1: 기본 쿼리 (파티션 정보 자동 감지) ⭐ 권장
-- ============================================================================
SELECT 
    atc.TABLE_NAME,
    atc.OWNER,
    atc.COLUMN_NAME,
    atc.COLUMN_ID,
    atc.DATA_TYPE,
    atc.DATA_LENGTH,
    atc.DATA_PRECISION,
    atc.DATA_SCALE,
    atc.NULLABLE,
    atc.DATA_DEFAULT,
    CASE 
        WHEN acc.CONSTRAINT_TYPE = 'P' THEN 'Y'
        ELSE 'N'
    END AS IS_PRIMARY_KEY,
    acc.CONSTRAINT_NAME AS PK_CONSTRAINT_NAME,
    acc_fk.CONSTRAINT_TYPE AS FK_CONSTRAINT_TYPE,
    acc_fk.CONSTRAINT_NAME AS FK_CONSTRAINT_NAME,
    acc_fk.R_CONSTRAINT_NAME AS REFERENCED_CONSTRAINT,
    acc_uk.CONSTRAINT_TYPE AS UK_CONSTRAINT_TYPE,
    acc_uk.CONSTRAINT_NAME AS UK_CONSTRAINT_NAME,
    acc_ck.CONSTRAINT_TYPE AS CK_CONSTRAINT_TYPE,
    acc_ck.CONSTRAINT_NAME AS CK_CONSTRAINT_NAME,
    acc_ck.SEARCH_CONDITION,
    atc_comments.COMMENTS AS TABLE_COMMENT,
    acc_col_comments.COMMENTS AS COLUMN_COMMENT,
    -- 파티션 정보 자동 감지 (Oracle 파티션 테이블의 파티션 키 컬럼)
    CASE 
        WHEN part_key.COLUMN_NAME IS NOT NULL THEN 'Y'
        ELSE 'N'
    END AS PARTITION_YN,
    'N' AS CLUSTER_YN     -- 클러스터는 수동 설정 필요
FROM 
    ALL_TAB_COLUMNS atc
    -- 테이블 코멘트
    LEFT JOIN ALL_TAB_COMMENTS atc_comments 
        ON atc.OWNER = atc_comments.OWNER 
        AND atc.TABLE_NAME = atc_comments.TABLE_NAME
    -- 컬럼 코멘트
    LEFT JOIN ALL_COL_COMMENTS acc_col_comments 
        ON atc.OWNER = acc_col_comments.OWNER 
        AND atc.TABLE_NAME = acc_col_comments.TABLE_NAME 
        AND atc.COLUMN_NAME = acc_col_comments.COLUMN_NAME
    -- 기본키 제약조건
    LEFT JOIN (
        SELECT 
            acc.OWNER,
            acc.TABLE_NAME,
            acc.CONSTRAINT_NAME,
            acc.CONSTRAINT_TYPE,
            accc.COLUMN_NAME
        FROM 
            ALL_CONSTRAINTS acc
            INNER JOIN ALL_CONS_COLUMNS accc 
                ON acc.OWNER = accc.OWNER 
                AND acc.CONSTRAINT_NAME = accc.CONSTRAINT_NAME
        WHERE 
            acc.CONSTRAINT_TYPE = 'P'
    ) acc ON atc.OWNER = acc.OWNER 
        AND atc.TABLE_NAME = acc.TABLE_NAME 
        AND atc.COLUMN_NAME = acc.COLUMN_NAME
    -- 외래키 제약조건
    LEFT JOIN (
        SELECT 
            acc.OWNER,
            acc.TABLE_NAME,
            acc.CONSTRAINT_NAME,
            acc.CONSTRAINT_TYPE,
            acc.R_CONSTRAINT_NAME,
            accc.COLUMN_NAME
        FROM 
            ALL_CONSTRAINTS acc
            INNER JOIN ALL_CONS_COLUMNS accc 
                ON acc.OWNER = accc.OWNER 
                AND acc.CONSTRAINT_NAME = accc.CONSTRAINT_NAME
        WHERE 
            acc.CONSTRAINT_TYPE = 'R'
    ) acc_fk ON atc.OWNER = acc_fk.OWNER 
        AND atc.TABLE_NAME = acc_fk.TABLE_NAME 
        AND atc.COLUMN_NAME = acc_fk.COLUMN_NAME
    -- 유니크 제약조건
    LEFT JOIN (
        SELECT 
            acc.OWNER,
            acc.TABLE_NAME,
            acc.CONSTRAINT_NAME,
            acc.CONSTRAINT_TYPE,
            accc.COLUMN_NAME
        FROM 
            ALL_CONSTRAINTS acc
            INNER JOIN ALL_CONS_COLUMNS accc 
                ON acc.OWNER = accc.OWNER 
                AND acc.CONSTRAINT_NAME = accc.CONSTRAINT_NAME
        WHERE 
            acc.CONSTRAINT_TYPE = 'U'
    ) acc_uk ON atc.OWNER = acc_uk.OWNER 
        AND atc.TABLE_NAME = acc_uk.TABLE_NAME 
        AND atc.COLUMN_NAME = acc_uk.COLUMN_NAME
    -- 체크 제약조건
    LEFT JOIN (
        SELECT 
            acc.OWNER,
            acc.TABLE_NAME,
            acc.CONSTRAINT_NAME,
            acc.CONSTRAINT_TYPE,
            acc.SEARCH_CONDITION,
            accc.COLUMN_NAME
        FROM 
            ALL_CONSTRAINTS acc
            INNER JOIN ALL_CONS_COLUMNS accc 
                ON acc.OWNER = accc.OWNER 
                AND acc.CONSTRAINT_NAME = accc.CONSTRAINT_NAME
        WHERE 
            acc.CONSTRAINT_TYPE = 'C'
            AND acc.CONSTRAINT_NAME NOT LIKE 'SYS_%'  -- 시스템 제약조건 제외
    ) acc_ck ON atc.OWNER = acc_ck.OWNER 
        AND atc.TABLE_NAME = acc_ck.TABLE_NAME 
        AND atc.COLUMN_NAME = acc_ck.COLUMN_NAME
    -- 파티션 키 컬럼 정보 (Oracle 파티션 테이블)
    LEFT JOIN (
        SELECT 
            apkc.OWNER,
            apkc.NAME AS TABLE_NAME,
            apkc.COLUMN_NAME,
            apkc.COLUMN_POSITION
        FROM 
            ALL_PART_KEY_COLUMNS apkc
        WHERE 
            apkc.OBJECT_TYPE = 'TABLE'
    ) part_key ON atc.OWNER = part_key.OWNER 
        AND atc.TABLE_NAME = part_key.TABLE_NAME 
        AND atc.COLUMN_NAME = part_key.COLUMN_NAME
WHERE 
    atc.OWNER = 'YOUR_SCHEMA_NAME'  -- 스키마명 지정 (필수)
    -- atc.OWNER IN ('SCHEMA1', 'SCHEMA2')  -- 여러 스키마 지정 시
    -- AND atc.TABLE_NAME LIKE 'TB_%'  -- 특정 테이블만 추출 시
ORDER BY 
    atc.OWNER,
    atc.TABLE_NAME,
    atc.COLUMN_ID;


-- ============================================================================
-- 옵션 2: 간단한 쿼리 (파티션 정보 포함, 제약조건 제외)
-- ============================================================================
-- 제약조건 정보가 필요 없지만 파티션 정보는 필요한 경우 사용
-- ============================================================================
/*
SELECT 
    atc.TABLE_NAME,
    atc.OWNER,
    atc.COLUMN_NAME,
    atc.COLUMN_ID,
    atc.DATA_TYPE,
    atc.DATA_LENGTH,
    atc.DATA_PRECISION,
    atc.DATA_SCALE,
    atc.NULLABLE,
    atc.DATA_DEFAULT,
    'N' AS IS_PRIMARY_KEY,  -- 기본키 정보 없음
    '' AS PK_CONSTRAINT_NAME,
    '' AS FK_CONSTRAINT_TYPE,
    '' AS FK_CONSTRAINT_NAME,
    '' AS REFERENCED_CONSTRAINT,
    '' AS UK_CONSTRAINT_TYPE,
    '' AS UK_CONSTRAINT_NAME,
    '' AS CK_CONSTRAINT_TYPE,
    '' AS CK_CONSTRAINT_NAME,
    '' AS SEARCH_CONDITION,
    atc_comments.COMMENTS AS TABLE_COMMENT,
    acc_col_comments.COMMENTS AS COLUMN_COMMENT,
    -- 파티션 정보 자동 감지
    CASE 
        WHEN part_key.COLUMN_NAME IS NOT NULL THEN 'Y'
        ELSE 'N'
    END AS PARTITION_YN,
    'N' AS CLUSTER_YN
FROM 
    ALL_TAB_COLUMNS atc
    LEFT JOIN ALL_TAB_COMMENTS atc_comments 
        ON atc.OWNER = atc_comments.OWNER 
        AND atc.TABLE_NAME = atc_comments.TABLE_NAME
    LEFT JOIN ALL_COL_COMMENTS acc_col_comments 
        ON atc.OWNER = acc_col_comments.OWNER 
        AND atc.TABLE_NAME = acc_col_comments.TABLE_NAME 
        AND atc.COLUMN_NAME = acc_col_comments.COLUMN_NAME
    -- 파티션 키 컬럼 정보
    LEFT JOIN (
        SELECT 
            apkc.OWNER,
            apkc.NAME AS TABLE_NAME,
            apkc.COLUMN_NAME,
            apkc.COLUMN_POSITION
        FROM 
            ALL_PART_KEY_COLUMNS apkc
        WHERE 
            apkc.OBJECT_TYPE = 'TABLE'
    ) part_key ON atc.OWNER = part_key.OWNER 
        AND atc.TABLE_NAME = part_key.TABLE_NAME 
        AND atc.COLUMN_NAME = part_key.COLUMN_NAME
WHERE 
    atc.OWNER = 'YOUR_SCHEMA_NAME'
ORDER BY 
    atc.OWNER,
    atc.TABLE_NAME,
    atc.COLUMN_ID;
*/


-- ============================================================================
-- 옵션 3: 현재 사용자 스키마만 (USER_TAB_COLUMNS 사용, 파티션 정보 포함)
-- ============================================================================
/*
SELECT 
    atc.TABLE_NAME,
    USER AS OWNER,  -- 현재 사용자
    atc.COLUMN_NAME,
    atc.COLUMN_ID,
    atc.DATA_TYPE,
    atc.DATA_LENGTH,
    atc.DATA_PRECISION,
    atc.DATA_SCALE,
    atc.NULLABLE,
    atc.DATA_DEFAULT,
    CASE 
        WHEN acc.CONSTRAINT_TYPE = 'P' THEN 'Y'
        ELSE 'N'
    END AS IS_PRIMARY_KEY,
    acc.CONSTRAINT_NAME AS PK_CONSTRAINT_NAME,
    '' AS FK_CONSTRAINT_TYPE,
    '' AS FK_CONSTRAINT_NAME,
    '' AS REFERENCED_CONSTRAINT,
    '' AS UK_CONSTRAINT_TYPE,
    '' AS UK_CONSTRAINT_NAME,
    '' AS CK_CONSTRAINT_TYPE,
    '' AS CK_CONSTRAINT_NAME,
    '' AS SEARCH_CONDITION,
    utc.COMMENTS AS TABLE_COMMENT,
    ucc.COMMENTS AS COLUMN_COMMENT,
    -- 파티션 정보 자동 감지
    CASE 
        WHEN part_key.COLUMN_NAME IS NOT NULL THEN 'Y'
        ELSE 'N'
    END AS PARTITION_YN,
    'N' AS CLUSTER_YN
FROM 
    USER_TAB_COLUMNS atc
    LEFT JOIN USER_TAB_COMMENTS utc 
        ON atc.TABLE_NAME = utc.TABLE_NAME
    LEFT JOIN USER_COL_COMMENTS ucc 
        ON atc.TABLE_NAME = ucc.TABLE_NAME 
        AND atc.COLUMN_NAME = ucc.COLUMN_NAME
    LEFT JOIN (
        SELECT 
            uc.TABLE_NAME,
            uc.CONSTRAINT_NAME,
            uc.CONSTRAINT_TYPE,
            ucc.COLUMN_NAME
        FROM 
            USER_CONSTRAINTS uc
            INNER JOIN USER_CONS_COLUMNS ucc 
                ON uc.CONSTRAINT_NAME = ucc.CONSTRAINT_NAME
        WHERE 
            uc.CONSTRAINT_TYPE = 'P'
    ) acc ON atc.TABLE_NAME = acc.TABLE_NAME 
        AND atc.COLUMN_NAME = acc.COLUMN_NAME
    -- 파티션 키 컬럼 정보
    LEFT JOIN (
        SELECT 
            upkc.NAME AS TABLE_NAME,
            upkc.COLUMN_NAME,
            upkc.COLUMN_POSITION
        FROM 
            USER_PART_KEY_COLUMNS upkc
        WHERE 
            upkc.OBJECT_TYPE = 'TABLE'
    ) part_key ON atc.TABLE_NAME = part_key.TABLE_NAME 
        AND atc.COLUMN_NAME = part_key.COLUMN_NAME
ORDER BY 
    atc.TABLE_NAME,
    atc.COLUMN_ID;
*/


-- ============================================================================
-- 옵션 4: 특정 테이블만 추출 (파티션 정보 포함)
-- ============================================================================
/*
SELECT 
    atc.TABLE_NAME,
    atc.OWNER,
    atc.COLUMN_NAME,
    atc.COLUMN_ID,
    atc.DATA_TYPE,
    atc.DATA_LENGTH,
    atc.DATA_PRECISION,
    atc.DATA_SCALE,
    atc.NULLABLE,
    atc.DATA_DEFAULT,
    CASE 
        WHEN acc.CONSTRAINT_TYPE = 'P' THEN 'Y'
        ELSE 'N'
    END AS IS_PRIMARY_KEY,
    acc.CONSTRAINT_NAME AS PK_CONSTRAINT_NAME,
    '' AS FK_CONSTRAINT_TYPE,
    '' AS FK_CONSTRAINT_NAME,
    '' AS REFERENCED_CONSTRAINT,
    '' AS UK_CONSTRAINT_TYPE,
    '' AS UK_CONSTRAINT_NAME,
    '' AS CK_CONSTRAINT_TYPE,
    '' AS CK_CONSTRAINT_NAME,
    '' AS SEARCH_CONDITION,
    atc_comments.COMMENTS AS TABLE_COMMENT,
    acc_col_comments.COMMENTS AS COLUMN_COMMENT,
    -- 파티션 정보 자동 감지
    CASE 
        WHEN part_key.COLUMN_NAME IS NOT NULL THEN 'Y'
        ELSE 'N'
    END AS PARTITION_YN,
    'N' AS CLUSTER_YN
FROM 
    ALL_TAB_COLUMNS atc
    LEFT JOIN ALL_TAB_COMMENTS atc_comments 
        ON atc.OWNER = atc_comments.OWNER 
        AND atc.TABLE_NAME = atc_comments.TABLE_NAME
    LEFT JOIN ALL_COL_COMMENTS acc_col_comments 
        ON atc.OWNER = acc_col_comments.OWNER 
        AND atc.TABLE_NAME = acc_col_comments.TABLE_NAME 
        AND atc.COLUMN_NAME = acc_col_comments.COLUMN_NAME
    LEFT JOIN (
        SELECT 
            acc.OWNER,
            acc.TABLE_NAME,
            acc.CONSTRAINT_NAME,
            acc.CONSTRAINT_TYPE,
            accc.COLUMN_NAME
        FROM 
            ALL_CONSTRAINTS acc
            INNER JOIN ALL_CONS_COLUMNS accc 
                ON acc.OWNER = accc.OWNER 
                AND acc.CONSTRAINT_NAME = accc.CONSTRAINT_NAME
        WHERE 
            acc.CONSTRAINT_TYPE = 'P'
    ) acc ON atc.OWNER = acc.OWNER 
        AND atc.TABLE_NAME = acc.TABLE_NAME 
        AND atc.COLUMN_NAME = acc.COLUMN_NAME
    -- 파티션 키 컬럼 정보
    LEFT JOIN (
        SELECT 
            apkc.OWNER,
            apkc.NAME AS TABLE_NAME,
            apkc.COLUMN_NAME,
            apkc.COLUMN_POSITION
        FROM 
            ALL_PART_KEY_COLUMNS apkc
        WHERE 
            apkc.OBJECT_TYPE = 'TABLE'
    ) part_key ON atc.OWNER = part_key.OWNER 
        AND atc.TABLE_NAME = part_key.TABLE_NAME 
        AND atc.COLUMN_NAME = part_key.COLUMN_NAME
WHERE 
    atc.OWNER = 'YOUR_SCHEMA_NAME'
    AND atc.TABLE_NAME IN ('TABLE1', 'TABLE2', 'TABLE3')  -- 특정 테이블만
ORDER BY 
    atc.OWNER,
    atc.TABLE_NAME,
    atc.COLUMN_ID;
*/


-- ============================================================================
-- CSV 파일로 저장하는 방법
-- ============================================================================
-- 
-- 1. SQL*Plus에서:
--    SET COLSEP ','
--    SET PAGESIZE 0
--    SET TRIMSPOOL ON
--    SET HEADSEP OFF
--    SET LINESIZE 32767
--    SET FEEDBACK OFF
--    SPOOL schema.csv
--    @oracle_extract_query.sql
--    SPOOL OFF
--
-- 2. SQL Developer에서:
--    - 쿼리 실행 후 결과 그리드에서 우클릭
--    - "Export" → "CSV" 선택
--    - 파일명: schema.csv
--
-- 3. DBeaver에서:
--    - 쿼리 실행 후 결과 그리드에서 우클릭
--    - "Export Data" → "CSV" 선택
--    - 파일명: schema.csv
--
-- ============================================================================


-- ============================================================================
-- 파티션/클러스터 설정 방법
-- ============================================================================
-- 
-- PARTITION_YN과 CLUSTER_YN 컬럼은 BigQuery에서 파티션과 클러스터를 
-- 설정할 컬럼을 지정합니다.
--
-- 1. 파티션 자동 감지 (PARTITION_YN):
--    ✅ Oracle에서 이미 파티션 테이블로 설정된 경우:
--       - ALL_PART_KEY_COLUMNS 뷰를 통해 자동으로 'Y' 설정
--       - 파티션 키로 사용된 컬럼이 자동으로 감지됨
--       - 수동 수정 불필요!
--
--    ⚠️ Oracle에서 파티션이 아닌 경우:
--       - 기본값 'N'으로 설정됨
--       - BigQuery에서 파티션을 원하면 CSV 파일에서 수동으로 'Y'로 변경
--       - DATE, TIMESTAMP, DATETIME 타입 컬럼에만 설정 가능
--       - 보통 등록일시, 수정일시, 거래일자 등에 설정
--
-- 2. 클러스터 설정 (CLUSTER_YN):
--    ⚠️ 수동 설정 필요:
--       - 기본값 'N'으로 설정됨
--       - CSV 파일을 Excel이나 텍스트 에디터로 열기
--       - 자주 조회되는 컬럼의 CLUSTER_YN을 'Y'로 변경 (최대 4개)
--       - 예: 고객ID, 상품ID, 지역코드 등
--
-- 3. 파티션 정보 확인 쿼리:
--    -- Oracle에서 파티션 테이블 목록 확인
--    SELECT OWNER, TABLE_NAME, PARTITIONING_TYPE, PARTITION_COUNT
--    FROM ALL_PART_TABLES
--    WHERE OWNER = 'YOUR_SCHEMA_NAME';
--
--    -- 파티션 키 컬럼 확인
--    SELECT OWNER, NAME AS TABLE_NAME, COLUMN_NAME, COLUMN_POSITION
--    FROM ALL_PART_KEY_COLUMNS
--    WHERE OWNER = 'YOUR_SCHEMA_NAME'
--    AND OBJECT_TYPE = 'TABLE'
--    ORDER BY NAME, COLUMN_POSITION;
--
-- 4. 예시:
--    Oracle 파티션 테이블:
--      CREATE TABLE SALES (
--        SALE_ID NUMBER,
--        SALE_DATE DATE,
--        AMOUNT NUMBER
--      )
--      PARTITION BY RANGE (SALE_DATE) (...);
--
--    추출 결과:
--      SALE_DATE 컬럼의 PARTITION_YN = 'Y' (자동 설정)
--
--    BigQuery DDL 생성 결과:
--      CREATE TABLE `project.schema.SALES` (...)
--      PARTITION BY DATE(SALE_DATE);
--
-- ============================================================================
