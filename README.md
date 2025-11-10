# Oracle to BigQuery DDL Generator

Oracle 데이터베이스 스키마를 BigQuery DDL로 자동 변환하는 도구입니다.

## 🎯 주요 특징

- ✅ **자동 타입 변환**: Oracle → BigQuery 타입 자동 매핑
- ✅ **한글 완벽 지원**: 테이블명/컬럼명 한글 및 대소문자 유지
- ✅ **기본키 지원**: PRIMARY KEY 제약조건 자동 생성
- ✅ **파티션/클러스터**: YN 플래그로 간단한 설정
- ✅ **정밀도 보존**: NUMERIC/BIGNUMERIC 자동 선택
- ✅ **인코딩 자동 감지**: UTF-8, EUC-KR 자동 처리

---

## 📦 프로젝트 구조

```
.
├── README.md                          # 메인 가이드 (이 파일)
├── oracle_extract_query.sql           # Oracle 스키마 추출 쿼리
├── ORACLE_EXTRACT_GUIDE.md            # Oracle 추출 상세 가이드
└── windows-portable/                  # Windows 포터블 버전
    ├── README.md                      # Windows 버전 가이드
    ├── BUILD.md                       # 빌드 가이드
    ├── DEVELOPMENT.md                 # 개발 가이드
    └── windows/                       # 빌드된 실행 파일
```

---

## 🚀 빠른 시작

### 1단계: Oracle에서 스키마 정보 추출

Oracle 데이터베이스에서 테이블 스키마 정보를 CSV 파일로 추출합니다.

```sql
-- oracle_extract_query.sql 파일 사용
-- SQL Developer, DBeaver, SQL*Plus 등에서 실행

-- 스키마명 수정 필요
WHERE atc.OWNER = 'YOUR_SCHEMA_NAME'  -- 실제 스키마명으로 변경
```

**상세 가이드:** [ORACLE_EXTRACT_GUIDE.md](ORACLE_EXTRACT_GUIDE.md)

### 2단계: DDL 생성

추출한 CSV 파일을 BigQuery DDL로 변환합니다.

#### **Windows 환경**

```cmd
cd windows-portable\windows
oracle-to-bq.bat convert schema.csv --project-id my-project
```

#### **Linux/Mac 환경**

```bash
# Python 3.8+ 필요
pip install -r requirements.txt
python src/oracle_to_bq_cli.py convert schema.csv --project-id my-project
```

### 3단계: BigQuery에 적용

```bash
# BigQuery CLI로 DDL 실행
bq query --use_legacy_sql=false < schema.sql
```

---

## 📋 입력 CSV 형식

### 필수 컬럼

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| `TABLE_NAME` | 테이블명 | `고객정보` |
| `COLUMN_NAME` | 컬럼명 | `고객ID` |
| `DATA_TYPE` | Oracle 데이터 타입 | `NUMBER`, `VARCHAR2` |
| `NULLABLE` | NULL 허용 여부 | `Y`, `N` |

### 선택 컬럼

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| `OWNER` | Oracle 스키마명 | `MY_SCHEMA` |
| `DATA_PRECISION` | 숫자 정밀도 | `10` |
| `DATA_SCALE` | 숫자 스케일 | `2` |
| `CHAR_LENGTH` | 문자열 길이 | `100` |
| `IS_PRIMARY_KEY` | 기본키 여부 | `Y`, `N` |
| `COLUMN_COMMENT` | 컬럼 설명 | `고객 고유 식별자` |
| `PARTITION_YN` | 파티션 설정 | `Y`, `N` |
| `CLUSTER_YN` | 클러스터 설정 | `Y`, `N` |

### CSV 예시

```csv
"TABLE_NAME","OWNER","COLUMN_NAME","DATA_TYPE","DATA_PRECISION","DATA_SCALE","NULLABLE","IS_PRIMARY_KEY","COLUMN_COMMENT","PARTITION_YN","CLUSTER_YN"
"고객정보","MY_SCHEMA","고객ID","NUMBER","10","0","N","Y","고객 고유 식별자","N","Y"
"고객정보","MY_SCHEMA","고객명","VARCHAR2","","","N","N","고객 성명","N","N"
"고객정보","MY_SCHEMA","등록일시","TIMESTAMP","","6","Y","N","등록 일시","Y","N"
```

---

## 🔧 사용 방법

### 기본 사용

```bash
# 가장 간단한 사용 (입력 파일과 같은 위치에 schema.sql 생성)
oracle-to-bq convert schema.csv --project-id my-project

# 출력 디렉토리 지정
oracle-to-bq convert schema.csv --output-dir output --project-id my-project
```

### 고급 옵션

```bash
# 개별 파일로 생성 (테이블별 SQL 파일)
oracle-to-bq convert schema.csv --files --project-id my-project

# STRING 길이 정보 보존
oracle-to-bq convert schema.csv --preserve-string-length --project-id my-project

# CREATE OR REPLACE TABLE 사용
oracle-to-bq convert schema.csv --create-or-replace --project-id my-project

# 기본키 제약조건 생성 안함
oracle-to-bq convert schema.csv --no-primary-keys --project-id my-project
```

### 설정 파일 사용

```bash
# 1. 설정 파일 템플릿 생성
oracle-to-bq init-config my_config.json

# 2. my_config.json 편집
{
  "project_id": "my-bigquery-project",
  "string_mode": "auto",
  "preserve_string_length": false,
  "create_or_replace": false,
  "enable_partitioning": true,
  "enable_clustering": true
}

# 3. 설정 파일로 변환
oracle-to-bq convert schema.csv --config my_config.json
```

---

## 🎨 타입 변환 규칙

### 숫자 타입

| Oracle | BigQuery | 조건 |
|--------|----------|------|
| `NUMBER(p,0)` | `INT64` | p ≤ 18 |
| `NUMBER(p,0)` | `NUMERIC(p,0)` | 18 < p ≤ 29 |
| `NUMBER(p,0)` | `BIGNUMERIC(p,0)` | p > 29 |
| `NUMBER(p,s)` | `NUMERIC(p,s)` | p ≤ 38, s ≤ 9 |
| `NUMBER(p,s)` | `BIGNUMERIC(p,s)` | p > 38 또는 s > 9 |
| `NUMBER` | `NUMERIC` | 정밀도 미지정 |

### 문자열 타입

| Oracle | BigQuery |
|--------|----------|
| `VARCHAR2` | `STRING` |
| `CHAR` | `STRING` |
| `NVARCHAR2` | `STRING` |
| `NCHAR` | `STRING` |
| `CLOB` | `STRING` |

### 날짜/시간 타입

| Oracle | BigQuery |
|--------|----------|
| `DATE` | `DATETIME` |
| `TIMESTAMP` | `DATETIME` |
| `TIMESTAMP(n)` | `DATETIME` |

### 바이너리 타입

| Oracle | BigQuery |
|--------|----------|
| `BLOB` | `BYTES` |
| `RAW` | `BYTES` |

---

## 🎛️ 파티션 & 클러스터

### 파티션 설정

**✅ 자동 감지 (권장)**

Oracle에서 이미 파티션 테이블인 경우, 추출 쿼리가 자동으로 파티션 키를 감지하여 `PARTITION_YN`을 `Y`로 설정합니다.

```sql
-- Oracle 파티션 테이블
CREATE TABLE SALES (...) PARTITION BY RANGE (SALE_DATE) (...);

-- 추출 결과: SALE_DATE의 PARTITION_YN = 'Y' (자동)
```

**⚠️ 수동 설정 (필요시)**

Oracle에서 파티션이 아니지만 BigQuery에서 파티션을 원하는 경우, CSV 파일에서 `PARTITION_YN`을 `Y`로 변경:

```csv
"등록일시","MY_SCHEMA","등록일시","TIMESTAMP","","6","Y","N","등록 일시","Y","N"
```

**지원 타입:**
- DATE
- TIMESTAMP
- DATETIME

**생성되는 DDL:**
```sql
CREATE TABLE `my-project.MY_SCHEMA.고객정보` (
  ...
)
PARTITION BY DATETIME_TRUNC(등록일시, DAY);
```

### 클러스터 설정

CSV 파일에서 `CLUSTER_YN` 컬럼을 `Y`로 설정 (최대 4개):

```csv
"고객ID","MY_SCHEMA","고객ID","NUMBER","10","0","N","Y","고객 고유 식별자","N","Y"
"상품ID","MY_SCHEMA","상품ID","NUMBER","10","0","N","N","상품 고유 식별자","N","Y"
```

**생성되는 DDL:**
```sql
CREATE TABLE `my-project.MY_SCHEMA.주문내역` (
  ...
)
PARTITION BY DATE(주문일자)
CLUSTER BY 고객ID, 상품ID;
```

---

## 📚 문서

- **[ORACLE_EXTRACT_GUIDE.md](ORACLE_EXTRACT_GUIDE.md)** - Oracle 스키마 추출 상세 가이드
- **[oracle_extract_query.sql](oracle_extract_query.sql)** - Oracle 추출 쿼리 (4가지 옵션)
- **[windows-portable/README.md](windows-portable/README.md)** - Windows 포터블 버전 가이드
- **[windows-portable/BUILD.md](windows-portable/BUILD.md)** - 빌드 가이드
- **[windows-portable/DEVELOPMENT.md](windows-portable/DEVELOPMENT.md)** - 개발 가이드

---

## 🛠️ 설치

### Windows (포터블 버전)

Python 설치 불필요! 압축 해제 후 바로 실행:

```cmd
cd windows-portable\windows
oracle-to-bq.bat --version
```

### Linux/Mac

```bash
# Python 3.8+ 필요
pip install PyYAML click chardet

# 실행
python src/oracle_to_bq_cli.py --version
```

---

## 💡 사용 예시

### 예시 1: 기본 변환

```bash
# Oracle에서 추출한 schema.csv를 BigQuery DDL로 변환
oracle-to-bq convert schema.csv --project-id my-project

# 결과: schema.sql 파일 생성
```

### 예시 2: 여러 스키마 처리

```bash
# 스키마별로 개별 파일 생성
oracle-to-bq convert all_schemas.csv --files --project-id my-project

# 결과:
# - schema1_table1.sql
# - schema1_table2.sql
# - schema2_table1.sql
# ...
```

### 예시 3: 파티션 테이블 생성

```bash
# 1. CSV에서 PARTITION_YN을 'Y'로 설정
# 2. DDL 생성
oracle-to-bq convert schema.csv --project-id my-project --create-or-replace

# 결과: 파티션 테이블 DDL 생성
```

---

## 🔍 문제 해결

### 1. 한글 깨짐

**원인:** CSV 파일 인코딩이 UTF-8이 아님

**해결:**
- Oracle 추출 시 UTF-8 인코딩으로 저장
- 도구가 자동으로 EUC-KR, CP949도 감지하지만 UTF-8 권장

### 2. 기본키가 생성되지 않음

**원인:** CSV에 `IS_PRIMARY_KEY` 컬럼이 없거나 값이 'Y'가 아님

**해결:**
- Oracle 추출 쿼리에서 기본키 정보 포함 (옵션 1 사용)
- 또는 CSV 파일에서 수동으로 `IS_PRIMARY_KEY`를 'Y'로 설정

### 3. 파티션이 생성되지 않음

**원인:** 
- `PARTITION_YN`이 'Y'가 아님
- 또는 지원하지 않는 타입 (STRING, BYTES 등)

**해결:**
- DATE, TIMESTAMP, DATETIME 타입 컬럼에만 `PARTITION_YN`을 'Y'로 설정

---

## 🤝 기여

이슈 리포트, 기능 제안, Pull Request 환영합니다!

---

## 📄 라이선스

MIT License

---

## 📞 문의

문제가 있거나 질문이 있으시면 이슈를 등록해주세요.
