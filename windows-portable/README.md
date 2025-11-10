# Oracle to BigQuery DDL Generator - Windows Portable

Windows 환경에서 Python 설치 없이 실행 가능한 Oracle to BigQuery DDL 변환 도구입니다.

## 주요 특징

- **완전 독립 실행**: 시스템 Python 불필요, 오프라인 작동
- **한글 완벽 지원**: 테이블명/컬럼명 대소문자 유지
- **자동 타입 변환**: Oracle → BigQuery 타입 자동 매핑
- **파티션/클러스터**: YN 플래그로 간단한 설정
- **정밀도 보존**: NUMERIC/BIGNUMERIC 자동 선택

## 빠른 시작

### 기본 사용

```cmd
# 가장 간단한 사용 (입력 파일과 같은 위치에 schema.sql 생성)
oracle-to-bq.bat convert schema.csv --project-id my-project

# 출력 디렉토리 지정
oracle-to-bq.bat convert schema.csv --output-dir output --project-id my-project

# 개별 파일로 생성
oracle-to-bq.bat convert schema.csv --files --project-id my-project
```

### 입력 CSV 형식

필수 컬럼: `TABLE_NAME`, `COLUMN_NAME`, `DATA_TYPE`, `NULLABLE`

선택 컬럼:
- `OWNER`: Oracle 스키마명 (BigQuery 데이터셋명으로 사용)
- `DATA_PRECISION`, `DATA_SCALE`: 숫자 정밀도
- `COLUMN_COMMENT`: 컬럼 설명
- `IS_PRIMARY_KEY`: 기본키 여부 (Y/N)
- `PARTITION_YN`: 파티션 설정 (Y/N)
- `CLUSTER_YN`: 클러스터 설정 (Y/N)

## 주요 기능

### 1. 자동 타입 변환

| Oracle | BigQuery | 규칙 |
|--------|----------|------|
| VARCHAR2, CHAR | STRING | 길이 정보 선택적 보존 |
| NUMBER(p,0) | INT64 / NUMERIC / BIGNUMERIC | p ≤ 18: INT64<br>p ≤ 29: NUMERIC<br>p > 29: BIGNUMERIC |
| NUMBER(p,s) | NUMERIC / BIGNUMERIC | p ≤ 38, s ≤ 9: NUMERIC<br>그 외: BIGNUMERIC |
| DATE | DATETIME | 날짜+시간 정보 보존 |
| TIMESTAMP | DATETIME | 날짜+시간 정보 보존 |
| CLOB | STRING | |
| BLOB, RAW | BYTES | |

### 2. 파티션 & 클러스터

CSV에 `PARTITION_YN`, `CLUSTER_YN` 컬럼 추가:

```csv
TABLE_NAME,COLUMN_NAME,DATA_TYPE,PARTITION_YN,CLUSTER_YN
Orders,OrderDate,TIMESTAMP,Y,N
Orders,CustomerId,NUMBER,N,Y
```

생성되는 DDL:
```sql
CREATE TABLE `project.dataset.Orders` (
  OrderDate DATETIME,
  CustomerId INT64
)
PARTITION BY DATETIME_TRUNC(OrderDate, DAY)
CLUSTER BY CustomerId;
```

**지원 파티션 타입**: DATE, DATETIME, TIMESTAMP  
**미지원 타입**: STRING, NUMBER (자동 제외)

### 3. 기본키 제한

BigQuery는 최대 16개 기본키 지원 → 자동으로 처음 16개만 사용

### 4. 파티션 테이블 DROP 옵션

config.json:
```json
{
  "drop_partition_table_before_create": true
}
```

생성되는 DDL:
```sql
DROP TABLE IF EXISTS `project.dataset.table`;

CREATE OR REPLACE TABLE `project.dataset.table` (...)
PARTITION BY ...;
```

## 설정 파일 (config.json)

```json
{
  "project_id": "",
  "string_mode": "auto",
  "preserve_string_length": true,
  "create_or_replace": true,
  "enable_partitioning": false,
  "enable_clustering": false,
  "debug_mode": false,
  "drop_partition_table_before_create": false
}
```

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| project_id | BigQuery 프로젝트 ID | "" |
| string_mode | 문자열 변환 모드 (auto/string_only) | "auto" |
| preserve_string_length | STRING(100) 형태로 길이 포함 | true |
| create_or_replace | CREATE OR REPLACE 사용 | true |
| enable_partitioning | 파티션 기능 활성화 | false |
| enable_clustering | 클러스터 기능 활성화 | false |
| debug_mode | 디버그 출력 활성화 | false |
| drop_partition_table_before_create | 파티션 테이블 DROP 후 생성 | false |

## 명령행 옵션

```cmd
oracle-to-bq.bat convert <input_file> [옵션]

옵션:
  --output-dir <dir>        출력 디렉토리 (기본: 입력 파일과 같은 위치)
  --project-id <id>         BigQuery 프로젝트 ID
  --config <file>           설정 파일 경로
  --files                   개별 파일로 생성 (기본: 병합 파일)
  --preserve-string-length  STRING 타입에 길이 정보 포함
  --no-primary-keys         기본키 제약조건 생성 안함
  --create-or-replace       CREATE OR REPLACE TABLE 사용
```

## 출력 예시

### 병합 파일 (기본)

```sql
-- Oracle to BigQuery DDL Migration
-- Generated on: 2025-11-10 23:18:39
-- Total tables: 2

-- ========================================
-- Table: Customers
-- Schema: SalesDB
-- ========================================

CREATE OR REPLACE TABLE `my-project.SalesDB.Customers` (
  CustomerId INT64 NOT NULL OPTIONS(description="고객 ID"),
  CustomerName STRING(100) OPTIONS(description="고객명"),
  CreatedDate DATETIME OPTIONS(description="생성일시")
,
  PRIMARY KEY (CustomerId) NOT ENFORCED
)
;

-- ========================================
-- Table: Orders
-- ========================================
...
```

### 개별 파일 (--files 옵션)

- `SalesDB_Customers.sql`
- `SalesDB_Orders.sql`
- `SalesDB_Products.sql`
