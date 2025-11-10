# Development Guide

Oracle to BigQuery DDL Generator 개발 가이드입니다.

## 프로젝트 구조

```
windows-portable/
├── build_windows.bat              # Windows 빌드 스크립트
├── build_windows_portable.py      # Windows 빌더 (Python)
├── test_suite.py                  # 단위 테스트
├── BUILD.md                       # 빌드 가이드
├── DEVELOPMENT.md                 # 개발 가이드
├── README.md                      # 사용자 가이드
└── windows/                       # 빌드 결과물
    ├── python/                    # 포터블 Python 런타임
    ├── src/
    │   └── oracle_to_bq_cli.py   # 메인 CLI
    ├── oracle-to-bq.bat          # 실행 스크립트
    ├── config.json               # 설정 파일
    └── schema.csv                # 샘플 데이터
```

## 개발 환경 설정

### 요구사항

- Python 3.8+
- Git

### 로컬 개발

```cmd
# 저장소 클론
git clone <repository-url>
cd windows-portable

# 의존성 설치 (개발용)
pip install PyYAML click typing-extensions

# 소스 코드 직접 실행
python windows/src/oracle_to_bq_cli.py --help
```

## 코드 구조

### SimpleMigrationTool 클래스

메인 DDL 생성 도구 클래스입니다.

**주요 메서드:**

```python
__init__(config_file)                    # 초기화 및 설정 로드
load_config(config_file)                 # 설정 파일 로드
convert_oracle_type(type, prec, scale)   # Oracle → BigQuery 타입 변환
process_csv_file(input, output)          # CSV 처리 및 DDL 생성
create_table_ddl(schema, table, cols)    # 테이블 DDL 생성
generate_partition_cluster_clauses(cols) # 파티션/클러스터 절 생성
format_bigquery_type_with_precision()    # 타입 정밀도 포맷팅
```

### 타입 변환 로직

**NUMBER 타입:**
```python
# NUMBER(p, 0) - 정수형
if scale == 0:
    if precision <= 18: return 'INT64'
    elif precision <= 29: return 'NUMERIC'
    else: return 'BIGNUMERIC'

# NUMBER(p, s) - 소수형
if precision <= 38 and scale <= 9: return 'NUMERIC'
elif precision <= 76 and scale <= 38: return 'BIGNUMERIC'
else: return 'STRING'
```

**날짜/시간 타입:**
```python
DATE → DATETIME
TIMESTAMP → DATETIME
```

### 파티션/클러스터 처리

**지원 타입:**
- DATE, DATETIME, TIMESTAMP → 파티션 생성
- STRING, NUMBER → 파티션 제외 (경고 출력)

**YN 플래그:**
```python
PARTITION_YN='Y' → PARTITION BY 절 생성
CLUSTER_YN='Y' → CLUSTER BY 절 생성
```

## 테스트

### 단위 테스트 실행

```cmd
# 전체 단위 테스트
python test_suite.py --unit-only

# 특정 테스트
python -m unittest test_suite.DDLGeneratorUnitTests.test_numeric_precision_limits
```

### 테스트 커버리지

현재 18개 단위 테스트:
- 타입 변환 테스트
- 정밀도 제한 테스트
- 파티션/클러스터 테스트
- 기본키 제한 테스트
- 대소문자 유지 테스트
- Debug 모드 테스트
- DROP 옵션 테스트

### 통합 테스트

```cmd
cd windows

# 기본 기능 테스트
oracle-to-bq.bat --test

# 실제 변환 테스트
oracle-to-bq.bat convert schema.csv --project-id test-project

# 독립성 검증
verify_standalone.bat
```

## 새 기능 추가

### 1. 새로운 설정 옵션 추가

**config.json:**
```json
{
  "new_option": false
}
```

**Python 코드:**
```python
def __init__(self):
    self.new_option = False

def load_config(self, config_file):
    self.new_option = config.get('new_option', self.new_option)
```

### 2. 새로운 타입 변환 추가

```python
def convert_oracle_type(self, oracle_type, precision, scale):
    if base_type == 'NEW_TYPE':
        return 'BIGQUERY_TYPE'
```

### 3. 단위 테스트 추가

```python
def test_new_feature(self):
    """새 기능 테스트"""
    result = self.tool.new_method()
    self.assertEqual(result, expected)
```

## 코딩 규칙

### 스타일 가이드

- **들여쓰기**: 4 spaces
- **인코딩**: UTF-8
- **줄 길이**: 120자 이하
- **주석**: 한글 사용 가능

### 네이밍 규칙

- **클래스**: PascalCase (`SimpleMigrationTool`)
- **메서드**: snake_case (`convert_oracle_type`)
- **변수**: snake_case (`table_name`)
- **상수**: UPPER_CASE (`TYPE_MAPPINGS`)

### 에러 처리

```python
try:
    # 작업 수행
    result = process_data()
except Exception as e:
    print(f"❌ 오류: {e}")
    return False
```

## 디버깅

### Debug 모드 활성화

**config.json:**
```json
{
  "debug_mode": true
}
```

**출력 예시:**
```
DEBUG: 컬럼 ID - partition_yn: N, cluster_yn: Y
DEBUG: 클러스터 컬럼 추가: ID
WARNING: STRING 타입은 BigQuery 파티션을 지원하지 않습니다.
```

### 로그 추가

```python
if self.debug_mode:
    print(f"DEBUG: {message}")
```

## 성능 최적화

### 1. pandas 제거
- CSV 파싱: 표준 `csv` 모듈 사용
- 메모리 효율: 스트리밍 방식 처리

### 2. 불필요한 패키지 제외
- pandas, numpy, openpyxl 등 제외
- 최소 의존성만 유지

### 3. 파일 크기 최적화
- `__pycache__` 제거
- `.pyc` 파일 제거
- 테스트 파일 제외

## 배포 체크리스트

- [ ] 단위 테스트 모두 통과
- [ ] 독립성 검증 통과
- [ ] 샘플 데이터로 실제 변환 테스트
- [ ] README.md 업데이트
- [ ] 버전 정보 업데이트
- [ ] 빌드 정보 확인 (`build_info.json`)
- [ ] 압축 파일 생성
- [ ] 압축 파일 크기 확인 (50-60MB)

## 버전 관리

### 버전 번호 규칙

`MAJOR.MINOR.PATCH`

- **MAJOR**: 주요 기능 변경, 호환성 깨짐
- **MINOR**: 새 기능 추가, 하위 호환성 유지
- **PATCH**: 버그 수정, 성능 개선

### 버전 업데이트 위치

**oracle_to_bq_cli.py:**
```python
def show_version(self):
    print("Version: 1.0.0")
```

## 알려진 이슈

### 1. 한글 경로 문제
- Windows 일부 환경에서 한글 경로 처리 이슈
- 해결: UTF-8 인코딩 명시

### 2. 대용량 CSV 처리
- 메모리 부족 가능성
- 해결: 스트리밍 방식 처리 고려

### 3. 파티션 타입 제한
- BigQuery는 DATE/DATETIME/TIMESTAMP만 지원
- 해결: 자동 검증 및 제외

## 기여 가이드

### Pull Request 절차

1. Fork 저장소
2. Feature 브랜치 생성
3. 코드 작성 및 테스트
4. 단위 테스트 추가
5. Pull Request 생성

### 코드 리뷰 기준

- 단위 테스트 포함
- 기존 테스트 통과
- 코딩 규칙 준수
- 문서 업데이트

## 참고 자료

- [Python Standalone Builds](https://github.com/indygreg/python-build-standalone)
- [BigQuery DDL Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language)
- [Oracle Data Types](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Data-Types.html)

## 연락처

버그 리포트나 기능 제안은 이슈로 등록해주세요.
