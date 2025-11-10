# Oracle 스키마 정보 추출 가이드

Oracle 데이터베이스에서 테이블 스키마 정보를 추출하여 BigQuery DDL 생성기의 입력 파일로 사용하는 방법을 설명합니다.

## 📋 목차

1. [추출 쿼리 선택](#추출-쿼리-선택)
2. [쿼리 실행 방법](#쿼리-실행-방법)
3. [CSV 파일 저장](#csv-파일-저장)
4. [파티션/클러스터 설정](#파티션클러스터-설정)
5. [문제 해결](#문제-해결)

---

## 🎯 추출 쿼리 선택

`oracle_extract_query.sql` 파일에는 4가지 옵션이 제공됩니다:

### **옵션 1: 기본 쿼리 (권장)**
- 모든 제약조건 정보 포함 (기본키, 외래키, 유니크, 체크)
- 테이블/컬럼 코멘트 포함
- 가장 완전한 정보 제공

```sql
-- 사용 전 수정 필요:
WHERE atc.OWNER = 'YOUR_SCHEMA_NAME'  -- 실제 스키마명으로 변경
```

### **옵션 2: 간단한 쿼리**
- 제약조건 정보 제외
- 테이블/컬럼 코멘트만 포함
- 빠른 추출이 필요한 경우

### **옵션 3: 현재 사용자 스키마만**
- `USER_TAB_COLUMNS` 사용
- 현재 로그인한 사용자의 테이블만 추출
- 권한이 제한된 경우 유용

### **옵션 4: 특정 테이블만**
- 선택한 테이블만 추출
- 대용량 스키마에서 일부만 마이그레이션할 때 유용

```sql
WHERE atc.TABLE_NAME IN ('TABLE1', 'TABLE2', 'TABLE3')
```

---

## 🔧 쿼리 실행 방법

### 1. **SQL*Plus에서 실행**

```bash
# 1. SQL*Plus 접속
sqlplus username/password@database

# 2. CSV 출력 설정
SET COLSEP ','
SET PAGESIZE 0
SET TRIMSPOOL ON
SET HEADSEP OFF
SET LINESIZE 32767
SET FEEDBACK OFF
SET HEADING ON

# 3. 결과를 파일로 저장
SPOOL schema.csv
@oracle_extract_query.sql
SPOOL OFF

# 4. 종료
EXIT
```

### 2. **SQL Developer에서 실행**

1. SQL Developer 실행 및 데이터베이스 접속
2. `oracle_extract_query.sql` 파일 열기
3. 스키마명 수정 (`YOUR_SCHEMA_NAME` → 실제 스키마명)
4. 쿼리 실행 (F5 또는 실행 버튼)
5. 결과 그리드에서 우클릭 → **Export** → **CSV** 선택
6. 파일명: `schema.csv`
7. 인코딩: **UTF-8** 선택 (한글 지원)
8. 저장

### 3. **DBeaver에서 실행**

1. DBeaver 실행 및 데이터베이스 접속
2. SQL 에디터에서 쿼리 실행
3. 결과 그리드에서 우클릭 → **Export Data**
4. 포맷: **CSV** 선택
5. 설정:
   - Header: **Include**
   - Delimiter: **Comma (,)**
   - Encoding: **UTF-8**
6. 파일명: `schema.csv`
7. Export 실행

### 4. **Toad for Oracle에서 실행**

1. Toad 실행 및 데이터베이스 접속
2. SQL Editor에서 쿼리 실행
3. 결과 그리드에서 우클릭 → **Export Dataset**
4. 포맷: **Delimited Text** 선택
5. Delimiter: **Comma**
6. 파일명: `schema.csv`
7. Export

---

## 💾 CSV 파일 저장

### 필수 설정

- **인코딩**: UTF-8 (한글 테이블명/컬럼명 지원)
- **구분자**: 쉼표 (,)
- **헤더**: 포함 (첫 번째 행에 컬럼명)
- **따옴표**: 텍스트 필드는 큰따옴표로 감싸기

### CSV 파일 구조 예시

```csv
"TABLE_NAME","OWNER","COLUMN_NAME","DATA_TYPE","DATA_PRECISION","DATA_SCALE","NULLABLE","IS_PRIMARY_KEY","COLUMN_COMMENT","PARTITION_YN","CLUSTER_YN"
"고객정보","MY_SCHEMA","고객ID","NUMBER","10","0","N","Y","고객 고유 식별자","N","Y"
"고객정보","MY_SCHEMA","고객명","VARCHAR2","","","N","N","고객 성명","N","N"
"고객정보","MY_SCHEMA","등록일시","TIMESTAMP","","6","Y","N","등록 일시","Y","N"
```

---

## 🎛️ 파티션/클러스터 설정

BigQuery에서 파티션과 클러스터를 사용하려면 CSV 파일을 수정해야 합니다.

### 파티션 설정 (PARTITION_YN)

**✅ 자동 감지 (권장)**

Oracle에서 이미 파티션 테이블로 설정된 경우, 추출 쿼리가 자동으로 파티션 키 컬럼을 감지하여 `PARTITION_YN`을 `Y`로 설정합니다.

```sql
-- Oracle 파티션 테이블 예시
CREATE TABLE SALES (
  SALE_ID NUMBER,
  SALE_DATE DATE,
  AMOUNT NUMBER
)
PARTITION BY RANGE (SALE_DATE) (...);

-- 추출 결과: SALE_DATE의 PARTITION_YN = 'Y' (자동 설정)
```

**Oracle 파티션 정보 확인:**
```sql
-- 파티션 테이블 목록
SELECT OWNER, TABLE_NAME, PARTITIONING_TYPE, PARTITION_COUNT
FROM ALL_PART_TABLES
WHERE OWNER = 'YOUR_SCHEMA_NAME';

-- 파티션 키 컬럼 확인
SELECT OWNER, NAME AS TABLE_NAME, COLUMN_NAME, COLUMN_POSITION
FROM ALL_PART_KEY_COLUMNS
WHERE OWNER = 'YOUR_SCHEMA_NAME'
AND OBJECT_TYPE = 'TABLE'
ORDER BY NAME, COLUMN_POSITION;
```

**⚠️ 수동 설정 (Oracle에서 파티션이 아닌 경우)**

Oracle에서 파티션 테이블이 아니지만 BigQuery에서 파티션을 사용하고 싶은 경우:

1. CSV 파일을 Excel 또는 텍스트 에디터로 열기
2. 파티션으로 사용할 컬럼의 `PARTITION_YN`을 `Y`로 변경
3. 보통 **등록일시**, **수정일시**, **거래일자** 등에 설정

**파티션 가능한 타입:**
- DATE
- TIMESTAMP
- DATETIME

**예시:**
```csv
"등록일시","MY_SCHEMA","등록일시","TIMESTAMP","","6","Y","N","등록 일시","Y","N"
```

### 클러스터 설정 (CLUSTER_YN)

**클러스터 권장 컬럼:**
- 자주 WHERE 절에 사용되는 컬럼
- JOIN에 사용되는 컬럼
- 카디널리티가 높은 컬럼 (고객ID, 상품ID 등)

**제한사항:**
- 최대 4개 컬럼까지 설정 가능

**설정 방법:**
1. CSV 파일을 Excel 또는 텍스트 에디터로 열기
2. 클러스터로 사용할 컬럼의 `CLUSTER_YN`을 `Y`로 변경

**예시:**
```csv
"고객ID","MY_SCHEMA","고객ID","NUMBER","10","0","N","Y","고객 고유 식별자","N","Y"
"상품ID","MY_SCHEMA","상품ID","NUMBER","10","0","N","N","상품 고유 식별자","N","Y"
```

### 파티션 + 클러스터 조합 예시

```csv
"TABLE_NAME","OWNER","COLUMN_NAME","DATA_TYPE","PARTITION_YN","CLUSTER_YN"
"주문내역","MY_SCHEMA","주문일자","DATE","Y","N"
"주문내역","MY_SCHEMA","고객ID","NUMBER","N","Y"
"주문내역","MY_SCHEMA","상품ID","NUMBER","N","Y"
```

이렇게 설정하면:
- `주문일자`로 파티션 생성
- `고객ID`, `상품ID`로 클러스터 생성

---

## 🔍 문제 해결

### 1. **권한 오류 (ORA-00942: table or view does not exist)**

**원인:** `ALL_TAB_COLUMNS` 뷰에 대한 접근 권한 없음

**해결방법:**
- **옵션 A:** DBA에게 권한 요청
  ```sql
  GRANT SELECT ON ALL_TAB_COLUMNS TO your_user;
  GRANT SELECT ON ALL_TAB_COMMENTS TO your_user;
  GRANT SELECT ON ALL_COL_COMMENTS TO your_user;
  ```

- **옵션 B:** `USER_TAB_COLUMNS` 사용 (옵션 3 쿼리)
  ```sql
  -- oracle_extract_query.sql의 옵션 3 사용
  ```

### 2. **한글 깨짐 문제**

**원인:** CSV 파일 인코딩이 UTF-8이 아님

**해결방법:**
- SQL Developer: Export 시 **UTF-8** 인코딩 선택
- DBeaver: Export 시 **UTF-8** 인코딩 선택
- Excel에서 열 때: **데이터 가져오기** → **UTF-8** 선택

### 3. **너무 많은 데이터 (메모리 부족)**

**원인:** 수천 개의 테이블을 한 번에 추출

**해결방법:**
- 스키마별로 분할 추출
  ```sql
  WHERE atc.OWNER = 'SCHEMA1'  -- 첫 번째 실행
  WHERE atc.OWNER = 'SCHEMA2'  -- 두 번째 실행
  ```

- 테이블 그룹별로 분할 추출
  ```sql
  WHERE atc.TABLE_NAME LIKE 'TB_CUSTOMER%'  -- 고객 관련 테이블만
  WHERE atc.TABLE_NAME LIKE 'TB_ORDER%'     -- 주문 관련 테이블만
  ```

### 4. **DATA_DEFAULT 컬럼이 잘림**

**원인:** `DATA_DEFAULT`는 LONG 타입이라 일부 도구에서 잘릴 수 있음

**해결방법:**
- SQL*Plus에서 `SET LONG 32767` 추가
  ```sql
  SET LONG 32767
  SET LONGCHUNKSIZE 32767
  ```

### 5. **제약조건 정보가 중복됨**

**원인:** 복합 제약조건 (여러 컬럼에 걸친 제약조건)

**해결방법:**
- 정상 동작입니다. DDL 생성기가 자동으로 처리합니다.
- 또는 옵션 2 (간단한 쿼리) 사용

---

## 📊 추출 결과 확인

### CSV 파일 검증

```bash
# 1. 행 수 확인 (헤더 제외)
wc -l schema.csv

# 2. 첫 10줄 확인
head -10 schema.csv

# 3. 특정 테이블만 확인
grep "고객정보" schema.csv
```

### 필수 컬럼 확인

CSV 파일의 첫 번째 행(헤더)에 다음 컬럼이 있는지 확인:

**필수:**
- TABLE_NAME
- COLUMN_NAME
- DATA_TYPE
- NULLABLE

**권장:**
- OWNER (스키마명)
- DATA_PRECISION
- DATA_SCALE
- IS_PRIMARY_KEY
- COLUMN_COMMENT

---

## 🚀 다음 단계

CSV 파일 추출이 완료되면:

```bash
# 1. DDL 생성
oracle-to-bq convert schema.csv --project-id my-project --output-dir output

# 2. 생성된 DDL 확인
cat output/merged_ddl.sql

# 3. BigQuery에 적용
bq query --use_legacy_sql=false < output/merged_ddl.sql
```

---

## 📚 참고 자료

- [Oracle Data Dictionary Views](https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/about-static-data-dictionary-views.html)
- [BigQuery DDL 문법](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language)
- [BigQuery 파티션 테이블](https://cloud.google.com/bigquery/docs/partitioned-tables)
- [BigQuery 클러스터 테이블](https://cloud.google.com/bigquery/docs/clustered-tables)

---

**문의사항이나 문제가 있으시면 이슈를 등록해주세요!**
