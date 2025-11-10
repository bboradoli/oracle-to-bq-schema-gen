#!/usr/bin/env python3
"""
Oracle to BigQuery Migration Tool - Simplified CLI for Portable Version
pandas 의존성 없이 작동하는 간단한 버전
"""

import sys
import csv
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

class SimpleMigrationTool:
    """간단한 마이그레이션 도구 (pandas 없음)"""
    
    def __init__(self, config_file=None):
        """
        Args:
            config_file: 설정 파일 경로
        """
        # 기본 설정값
        self.project_id = 'your_project'
        self.string_mode = 'auto'
        self.preserve_string_length = False
        self.use_schema_as_dataset = True  # Oracle 스키마명을 데이터셋명으로 사용
        self.merge_output = True  # 모든 DDL을 하나의 파일로 병합 (기본값)
        self.create_primary_keys = True  # 기본키 제약조건 생성
        self.create_or_replace = False  # CREATE OR REPLACE TABLE 사용 여부
        self.enable_partitioning = True  # 파티셔닝 기능 활성화
        self.enable_clustering = True  # 클러스터링 기능 활성화
        self.partition_expiration_days = None  # 파티션 만료 일수
        self.debug_mode = False  # 디버그 출력 활성화
        self.drop_partition_table_before_create = False  # 파티션 테이블 생성 전 DROP 실행
        self.output_filename = 'merged_ddl.sql'  # 병합 파일명 (기본값)
        
        # 설정 파일 로드
        self.load_config(config_file)
        
        self.type_mappings = {
            'VARCHAR2': 'STRING',
            'CHAR': 'STRING', 
            'NVARCHAR2': 'STRING',
            'NCHAR': 'STRING',
            'NUMBER': 'INT64',
            'INTEGER': 'INT64',
            'FLOAT': 'FLOAT64',
            'DATE': 'DATE',
            'TIMESTAMP': 'TIMESTAMP',
            'CLOB': 'STRING',
            'BLOB': 'BYTES',
            'RAW': 'BYTES'
        }
    
    def load_config(self, config_file=None):
        """설정 파일 로드 (JSON 형식)"""
        config_paths = []
        
        if config_file:
            config_paths.append(Path(config_file))
        else:
            # --config 옵션이 없을 때 실행파일과 동일한 경로의 config.json을 우선 참조
            script_dir = Path(__file__).parent.parent  # src의 상위 디렉토리 (windows 디렉토리)
            default_config = script_dir / 'config.json'
            config_paths.append(default_config)
        
        # 기본 설정 파일 경로들 (실행파일 경로 config.json이 없을 때 대체)
        config_paths.extend([
            Path('oracle_to_bq_config.json'),
            Path('config.json'),
            Path('config/oracle_to_bq.json'),
            Path('config/config.json')
        ])
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    if config:
                        # 설정값 적용 - project_id가 config에 있으면 사용, 없으면 빈 문자열로 설정
                        if 'project_id' in config:
                            self.project_id = config['project_id']
                        else:
                            self.project_id = ''  # config에 project_id가 없으면 빈 문자열
                        
                        self.string_mode = config.get('string_mode', self.string_mode)
                        self.preserve_string_length = config.get('preserve_string_length', self.preserve_string_length)
                        self.use_schema_as_dataset = config.get('use_schema_as_dataset', self.use_schema_as_dataset)
                        self.create_or_replace = config.get('create_or_replace', self.create_or_replace)
                        self.enable_partitioning = config.get('enable_partitioning', self.enable_partitioning)
                        self.enable_clustering = config.get('enable_clustering', self.enable_clustering)
                        self.partition_expiration_days = config.get('partition_expiration_days', self.partition_expiration_days)
                        self.debug_mode = config.get('debug_mode', self.debug_mode)
                        self.drop_partition_table_before_create = config.get('drop_partition_table_before_create', self.drop_partition_table_before_create)
                        
                        print(f"✓ 설정 파일 로드됨: {config_path}")
                        return
                        
                except Exception as e:
                    print(f"⚠️ 설정 파일 로드 실패 ({config_path}): {e}")
                    continue
    
    def create_default_config(self, config_path='oracle_to_bq_config.json'):
        """기본 설정 파일 생성"""
        default_config = {
            "project_id": "your_project",
            "string_mode": "auto",
            "preserve_string_length": False,
            "use_schema_as_dataset": True,
            "create_or_replace": False,
            "_comments": {
                "project_id": "BigQuery 프로젝트 ID",
                "string_mode": "문자열 변환 모드: 'auto' 또는 'string_only'",
                "preserve_string_length": "STRING 타입에 길이 정보 포함 여부 (예: STRING(100))",
                "use_schema_as_dataset": "Oracle 스키마명을 데이터셋명으로 사용 여부",
                "create_or_replace": "CREATE OR REPLACE TABLE 사용 여부 (true: CREATE OR REPLACE, false: CREATE)"
            }
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            print(f"✓ 기본 설정 파일 생성됨: {config_path}")
            return True
        except Exception as e:
            print(f"❌ 설정 파일 생성 실패: {e}")
            return False
    

    
    def create_config_template(self, output_file: str):
        """설정 파일 템플릿 생성"""
        config_template = {
            "project_id": "your-bigquery-project-id",
            "string_mode": "auto",
            "preserve_string_length": False,
            "description": {
                "project_id": "BigQuery 프로젝트 ID",
                "string_mode": "문자열 변환 모드 (auto 또는 string_only)",
                "preserve_string_length": "STRING 타입에 길이 정보 포함 여부"
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(config_template, f, indent=2, ensure_ascii=False)
            print(f"✓ 설정 파일 템플릿 생성됨: {output_file}")
            print("  파일을 편집하여 프로젝트 ID와 옵션을 설정하세요.")
        except Exception as e:
            print(f"❌ 설정 파일 생성 실패: {e}")
    
    def convert_oracle_type(self, oracle_type: str, precision: Optional[str] = None, scale: Optional[str] = None) -> str:
        """Oracle 타입을 BigQuery 타입으로 변환 (정밀도와 스케일 정보 보존)"""
        base_type = oracle_type.upper().split('(')[0]
        
        # string_only 모드는 문자열 타입에만 영향을 줌 (다른 타입은 정상 변환)
        
        # auto 모드: Oracle 타입에 따라 최적의 BigQuery 타입으로 변환
        if base_type == 'NUMBER':
            # NUMBER 타입의 정밀한 변환 로직
            if precision is None and scale is None:
                # NUMBER without precision/scale -> NUMERIC (정밀도 보존)
                return 'NUMERIC'
            
            # 정밀도와 스케일을 숫자로 변환
            try:
                prec = int(precision) if precision and str(precision).strip() else None
                sc = int(scale) if scale and str(scale).strip() else None
            except (ValueError, TypeError):
                prec = None
                sc = None
            
            # NUMBER with scale 0 (정수형)
            if sc is not None and sc == 0:
                if prec is not None and prec <= 18:
                    return 'INT64'  # INT64 범위 내의 정수
                elif prec is not None and prec <= 29:
                    return 'NUMERIC'  # NUMERIC(P, 0)에서 P <= 29
                else:
                    return 'BIGNUMERIC'  # 큰 정수는 BIGNUMERIC으로 처리
            
            # NUMBER with scale > 0 (소수점 포함)
            if sc is not None and sc > 0:
                if prec is not None:
                    # BigQuery NUMERIC 한계 확인 (38자리 정밀도, 9자리 소수점)
                    if prec <= 38 and sc <= 9:
                        return 'NUMERIC'
                    # BigQuery NUMERIC 한계를 초과하는 경우 BIGNUMERIC 사용
                    elif prec <= 76 and sc <= 38:
                        return 'BIGNUMERIC'
                    else:
                        # 극한의 정밀도는 STRING으로 처리
                        return 'STRING'
                else:
                    return 'NUMERIC'
            
            # NUMBER with negative scale (소수점 왼쪽 반올림)
            if sc is not None and sc < 0:
                return 'NUMERIC'
            
            # 기타 모든 경우 NUMERIC으로 안전하게 처리
            return 'NUMERIC'
        
        # TIMESTAMP 타입들
        if base_type.startswith('TIMESTAMP'):
            return 'DATETIME'
        
        # 문자열 타입들
        if base_type in ['VARCHAR2', 'CHAR', 'NVARCHAR2', 'NCHAR', 'CLOB', 'NCLOB', 'LONG']:
            return 'STRING'
        
        # 바이너리 타입들
        if base_type in ['BLOB', 'RAW']:
            return 'BYTES'
        
        # DATE 타입
        if base_type == 'DATE':
            return 'DATETIME'
        
        # 기타 타입들
        return self.type_mappings.get(base_type, 'STRING')
    
    def detect_encoding(self, file_path: Path) -> str:
        """파일 인코딩을 자동 감지 (UTF-8, EUC-KR 지원)"""
        encodings = ['utf-8', 'euc-kr', 'cp949']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # 파일의 첫 몇 줄을 읽어서 인코딩이 올바른지 확인
                    f.read(1024)
                    print(f"✓ 파일 인코딩 감지: {encoding}")
                    return encoding
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
        
        # 기본값으로 UTF-8 반환
        print("⚠️ 인코딩 감지 실패, UTF-8로 시도합니다.")
        return 'utf-8'
    
    def process_csv_file(self, input_file: Path, output_dir: Path) -> bool:
        """CSV 파일을 처리하여 BigQuery DDL 생성"""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 파일 인코딩 자동 감지
            encoding = self.detect_encoding(input_file)
            
            with open(input_file, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                
                # 테이블별로 그룹화 (스키마명 포함)
                tables = {}
                schemas = set()
                
                for row in reader:
                    table_name = row.get('TABLE_NAME', '')
                    # Oracle 스키마명을 BigQuery 데이터셋명으로 사용
                    # 우선순위: OWNER > SCHEMA_NAME > TABLE_SCHEMA
                    schema_name = row.get('OWNER', '') or row.get('SCHEMA_NAME', '') or row.get('TABLE_SCHEMA', '')
                    
                    if not table_name:
                        continue
                    
                    # Oracle 스키마명이 있으면 수집 (BigQuery 데이터셋명으로 사용됨)
                    if schema_name:
                        schemas.add(schema_name)
                    
                    # 테이블 키 생성 (스키마명 포함 가능)
                    table_key = table_name
                    if schema_name:
                        table_key = f"{schema_name}.{table_name}"
                    
                    if table_key not in tables:
                        tables[table_key] = {
                            'schema_name': schema_name if schema_name else None,
                            'table_name': table_name,
                            'columns': []
                        }
                    
                    column_info = {
                        'column_name': row.get('COLUMN_NAME', ''),
                        'data_type': row.get('DATA_TYPE', ''),
                        'data_precision': row.get('DATA_PRECISION', ''),
                        'data_scale': row.get('DATA_SCALE', ''),
                        'char_length': row.get('CHAR_LENGTH', '') or row.get('DATA_LENGTH', ''),
                        'data_length': row.get('DATA_LENGTH', ''),
                        'nullable': row.get('NULLABLE', 'Y'),
                        'is_primary_key': row.get('IS_PRIMARY_KEY', 'N'),
                        'fk_constraint_name': row.get('FK_CONSTRAINT_NAME', ''),
                        'unique_constraint_name': row.get('UNIQUE_CONSTRAINT_NAME', '') or row.get('UK_CONSTRAINT_NAME', ''),
                        'default_value': row.get('DEFAULT_VALUE', '') or row.get('DATA_DEFAULT', ''),
                        'data_default': row.get('DATA_DEFAULT', ''),
                        'column_comment': row.get('COLUMN_COMMENT', '') or row.get('COMMENTS', ''),
                        # 파티셔닝과 클러스터링 관련 컬럼들 추가 (간소화)
                        'partition_yn': row.get('PARTITION_YN', 'N'),
                        'cluster_yn': row.get('CLUSTER_YN', 'N')
                    }
                    tables[table_key]['columns'].append(column_info)
            
            # 스키마 정보 출력
            if schemas:
                print(f"✓ 발견된 스키마: {', '.join(sorted(schemas))}")
            
            # DDL 생성 방식 결정 (개별 파일 vs 병합 파일)
            if self.merge_output:
                # 모든 DDL을 하나의 파일로 병합
                merged_file = output_dir / self.output_filename
                self.generate_merged_ddl(tables, merged_file)
                print(f"✓ {len(tables)}개 테이블 DDL을 병합 파일로 생성 완료: {merged_file}")
            else:
                # 각 테이블에 대해 개별 DDL 파일 생성
                for table_key, table_info in tables.items():
                    schema_name = table_info['schema_name']
                    table_name = table_info['table_name']
                    columns = table_info['columns']
                    
                    # 파일명 생성 (스키마명 포함)
                    if schema_name:
                        ddl_file = output_dir / f"{schema_name}_{table_name}.sql"
                    else:
                        ddl_file = output_dir / f"{table_name}.sql"
                    
                    self.generate_ddl(schema_name, table_name, columns, ddl_file)
                
                print(f"✓ {len(tables)}개 테이블 DDL 생성 완료: {output_dir}")
            
            return True
            
        except Exception as e:
            print(f"❌ 파일 처리 오류: {e}")
            return False
    
    def needs_backticks(self, name: str) -> bool:
        """이름에 백틱이 필요한지 확인 (한글, 특수문자, 예약어 등)"""
        import re
        
        # 한글이 포함되어 있는지 확인
        if re.search(r'[가-힣]', name):
            return True
        
        # 숫자로 시작하는지 확인
        if name and name[0].isdigit():
            return True
        
        # 특수문자가 포함되어 있는지 확인 (언더스코어 제외)
        if re.search(r'[^a-zA-Z0-9_]', name):
            return True
        
        # BigQuery 예약어 확인 (일부만)
        reserved_words = {
            'ALL', 'AND', 'ANY', 'ARRAY', 'AS', 'ASC', 'ASSERT_ROWS_MODIFIED',
            'AT', 'BETWEEN', 'BY', 'CASE', 'CAST', 'COLLATE', 'CONTAINS',
            'CREATE', 'CROSS', 'CUBE', 'CURRENT', 'DEFAULT', 'DEFINE',
            'DESC', 'DISTINCT', 'ELSE', 'END', 'ENUM', 'ESCAPE', 'EXCEPT',
            'EXCLUDE', 'EXISTS', 'EXTRACT', 'FALSE', 'FETCH', 'FOLLOWING',
            'FOR', 'FROM', 'FULL', 'GROUP', 'GROUPING', 'GROUPS', 'HASH',
            'HAVING', 'IF', 'IGNORE', 'IN', 'INNER', 'INTERSECT', 'INTERVAL',
            'INTO', 'IS', 'JOIN', 'LATERAL', 'LEFT', 'LIKE', 'LIMIT',
            'LOOKUP', 'MERGE', 'NATURAL', 'NEW', 'NO', 'NOT', 'NULL',
            'NULLS', 'OF', 'ON', 'OR', 'ORDER', 'OUTER', 'OVER',
            'PARTITION', 'PRECEDING', 'PROTO', 'RANGE', 'RECURSIVE',
            'RESPECT', 'RIGHT', 'ROLLUP', 'ROWS', 'SELECT', 'SET',
            'SOME', 'STRUCT', 'TABLESAMPLE', 'THEN', 'TO', 'TREAT',
            'TRUE', 'UNBOUNDED', 'UNION', 'UNNEST', 'USING', 'WHEN',
            'WHERE', 'WINDOW', 'WITH', 'WITHIN'
        }
        
        if name.upper() in reserved_words:
            return True
        
        return False
    
    def format_identifier(self, name: str) -> str:
        """식별자를 적절히 포맷팅 (필요시 백틱 추가)"""
        if self.needs_backticks(name):
            return f"`{name}`"
        return name
    
    def generate_ddl(self, schema_name: Optional[str], table_name: str, columns: List[Dict], output_file: Path):
        """BigQuery DDL 생성 (정밀도, 스케일, 길이, 설명 정보 포함)"""
        ddl_content = self.create_table_ddl(schema_name, table_name, columns)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ddl_content)
    
    def generate_merged_ddl(self, tables: Dict, output_file: Path):
        """모든 테이블의 DDL을 하나의 파일로 병합 생성"""
        ddl_sections = []
        
        # 파일 헤더
        ddl_sections.append("-- Oracle to BigQuery DDL Migration")
        ddl_sections.append(f"-- Generated on: {self.get_current_timestamp()}")
        ddl_sections.append(f"-- Total tables: {len(tables)}")
        ddl_sections.append("")
        
        for table_key, table_info in tables.items():
            schema_name = table_info['schema_name']
            table_name = table_info['table_name']
            columns = table_info['columns']
            
            # 테이블별 섹션 구분
            ddl_sections.append(f"-- ========================================")
            ddl_sections.append(f"-- Table: {table_name}")
            if schema_name:
                ddl_sections.append(f"-- Schema: {schema_name}")
            ddl_sections.append(f"-- ========================================")
            ddl_sections.append("")
            
            # 테이블 DDL 생성
            table_ddl = self.create_table_ddl(schema_name, table_name, columns)
            ddl_sections.append(table_ddl)
            ddl_sections.append("")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(ddl_sections))
    
    def create_table_ddl(self, schema_name: Optional[str], table_name: str, columns: List[Dict]) -> str:
        """개별 테이블의 DDL 문자열 생성"""
        # BigQuery 데이터셋명 결정 (Oracle OWNER/스키마명의 원본 대소문자 유지)
        dataset_name = schema_name if schema_name else 'your_dataset'
        
        # 테이블명 포맷팅 (백틱 없이 정리, 원본 대소문자 유지)
        clean_table_name = table_name.strip('`')
        
        # 전체 테이블명 생성 - project_id가 없으면 데이터셋.테이블명 형태로
        if self.project_id and self.project_id.strip():
            full_table_name = f"`{self.project_id}.{dataset_name}.{clean_table_name}`"
        else:
            full_table_name = f"`{dataset_name}.{clean_table_name}`"
        
        # 파티션 테이블 여부 확인 (나중에 사용)
        has_partition = any(col.get('partition_yn', 'N').upper() == 'Y' for col in columns)
        
        # DROP 문 추가 (파티션 테이블이고 옵션이 활성화된 경우)
        ddl_lines = []
        if self.create_or_replace and has_partition and self.drop_partition_table_before_create:
            ddl_lines.append(f"DROP TABLE IF EXISTS {full_table_name};")
            ddl_lines.append("")  # 빈 줄 추가
        
        # CREATE 또는 CREATE OR REPLACE 선택
        create_statement = "CREATE OR REPLACE TABLE" if self.create_or_replace else "CREATE TABLE"
        ddl_lines.append(f"{create_statement} {full_table_name} (")
        
        column_definitions = []
        primary_key_columns = []
        
        for col in columns:
            col_name = col['column_name']
            oracle_type = col['data_type']
            precision = col['data_precision']
            scale = col['data_scale']
            char_length = col.get('char_length') or col.get('data_length')
            nullable = col['nullable']
            is_primary_key = col.get('is_primary_key', 'N').upper()
            
            bq_type = self.convert_oracle_type(oracle_type, precision, scale)
            
            # 컬럼명 포맷팅 (백틱 처리)
            formatted_col_name = self.format_identifier(col_name)
            
            # BigQuery 타입에 정밀도/스케일 정보 추가
            type_with_precision = self.format_bigquery_type_with_precision(
                bq_type, oracle_type, precision, scale, char_length
            )
            
            # 컬럼 정의
            col_def = f"  {formatted_col_name} {type_with_precision}"
            if nullable == 'N':
                col_def += " NOT NULL"
            
            # 설명 추가 (Oracle 타입 정보 포함)
            description = self.create_column_description(col)
            if description:
                # BigQuery에서는 OPTIONS로 description 추가
                col_def += f" OPTIONS(description=\"{self.escape_description(description)}\")"
            
            column_definitions.append(col_def)
            
            # 기본키 컬럼 수집
            if self.create_primary_keys and is_primary_key == 'Y':
                primary_key_columns.append(formatted_col_name)
        
        ddl_lines.append(",\n".join(column_definitions))
        
        # 기본키 제약조건 추가 (BigQuery는 PRIMARY KEY를 지원하지만 enforced되지 않음)
        # BigQuery는 최대 16개의 기본키 컬럼만 지원
        if primary_key_columns:
            if len(primary_key_columns) > 16:
                if self.debug_mode:
                    print(f"WARNING: 기본키 컬럼이 {len(primary_key_columns)}개입니다. BigQuery는 최대 16개만 지원하므로 처음 16개만 사용합니다.")
                primary_key_columns = primary_key_columns[:16]
            
            ddl_lines.append(",")
            pk_constraint = f"  PRIMARY KEY ({', '.join(primary_key_columns)}) NOT ENFORCED"
            ddl_lines.append(pk_constraint)
        
        ddl_lines.append(")")
        
        # 파티셔닝과 클러스터링 추가
        partition_clause, cluster_clause = self.generate_partition_cluster_clauses(columns)
        
        if partition_clause:
            ddl_lines.append(partition_clause)
        
        if cluster_clause:
            ddl_lines.append(cluster_clause)
        
        # 파티션 만료 설정 추가
        if self.enable_partitioning and self.partition_expiration_days:
            expiration_clause = f"OPTIONS(partition_expiration_days={self.partition_expiration_days})"
            ddl_lines.append(expiration_clause)
        
        ddl_lines.append(";")
        
        return "\n".join(ddl_lines)
    
    def get_current_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_partition_cluster_clauses(self, columns: List[Dict]) -> tuple:
        """파티셔닝과 클러스터링 절 생성"""
        partition_clause = None
        cluster_clause = None
        
        if not self.enable_partitioning and not self.enable_clustering:
            return partition_clause, cluster_clause
        
        # 파티셔닝 설정 확인
        partition_columns = []
        partition_type = None
        
        # 클러스터링 설정 확인
        cluster_columns = []
        
        for col in columns:
            column_name = col.get('column_name', '')
            if self.debug_mode:
                print(f"DEBUG: 컬럼 {column_name} - partition_yn: {col.get('partition_yn', 'N')}, cluster_yn: {col.get('cluster_yn', 'N')}")
            
            # 파티셔닝 확인 (PARTITION_YN = 'Y')
            partition_yn = col.get('partition_yn', 'N')
            if (self.enable_partitioning and 
                partition_yn and str(partition_yn).upper() == 'Y'):
                data_type = col.get('data_type', '').upper()
                if column_name:
                    if self.debug_mode:
                        print(f"DEBUG: 파티션 컬럼 추가: {column_name} ({data_type})")
                    partition_columns.append((column_name, data_type))
            
            # 클러스터링 확인 (CLUSTER_YN = 'Y')
            cluster_yn = col.get('cluster_yn', 'N')
            if (self.enable_clustering and 
                cluster_yn and str(cluster_yn).upper() == 'Y'):
                if column_name:
                    if self.debug_mode:
                        print(f"DEBUG: 클러스터 컬럼 추가: {column_name}")
                    cluster_columns.append(column_name)
        
        # 파티션 절 생성 (첫 번째 파티션 컬럼만 사용)
        if partition_columns:
            partition_col, oracle_data_type = partition_columns[0]
            
            # Oracle 타입을 BigQuery 타입으로 변환
            precision = None
            scale = None
            for col in columns:
                if col.get('column_name') == partition_col:
                    precision = col.get('data_precision')
                    scale = col.get('data_scale')
                    break
            
            bq_type = self.convert_oracle_type(oracle_data_type, precision, scale)
            
            # BigQuery에서 파티션을 지원하는 타입만 처리
            # 지원 타입: DATE, TIMESTAMP, DATETIME, INT64 (RANGE 파티션용)
            formatted_col = self.format_identifier(partition_col)
            
            if bq_type == 'DATE':
                partition_clause = f"PARTITION BY DATE({formatted_col})"
            elif bq_type == 'TIMESTAMP':
                partition_clause = f"PARTITION BY DATE({formatted_col})"
            elif bq_type == 'DATETIME':
                partition_clause = f"PARTITION BY DATETIME_TRUNC({formatted_col}, DAY)"
            elif bq_type in ['INT64', 'NUMERIC', 'BIGNUMERIC']:
                # INTEGER RANGE 파티션 (선택적)
                # 기본적으로는 생성하지 않음 (범위 설정이 필요하므로)
                if self.debug_mode:
                    print(f"WARNING: 숫자 타입({bq_type}) 파티션은 RANGE 파티션 설정이 필요하여 생성하지 않습니다.")
                partition_clause = None
            else:
                # 지원하지 않는 타입 (STRING, BYTES 등)
                if self.debug_mode:
                    print(f"WARNING: {bq_type} 타입은 BigQuery 파티션을 지원하지 않습니다. 파티션 절을 생성하지 않습니다.")
                partition_clause = None
        
        # 클러스터 절 생성
        if cluster_columns:
            formatted_clusters = [self.format_identifier(col) for col in cluster_columns]
            cluster_clause = f"CLUSTER BY {', '.join(formatted_clusters)}"
        
        return partition_clause, cluster_clause
    
    def format_bigquery_type_with_precision(self, bq_type: str, oracle_type: str, 
                                          precision: Optional[str], scale: Optional[str], 
                                          char_length: Optional[str]) -> str:
        """BigQuery 타입에 정밀도/스케일 정보 추가"""
        try:
            prec = int(precision) if precision and str(precision).strip() else None
            sc = int(scale) if scale and str(scale).strip() else None
            length = int(char_length) if char_length and str(char_length).strip() else None
        except (ValueError, TypeError):
            prec = None
            sc = None
            length = None
        
        # NUMERIC/BIGNUMERIC 타입에 정밀도와 스케일 추가
        if bq_type in ['NUMERIC', 'BIGNUMERIC']:
            if prec is not None and sc is not None:
                # BigQuery NUMERIC 제한사항 확인
                if bq_type == 'NUMERIC':
                    # NUMERIC(P, 0)에서 P > 29인 경우 BIGNUMERIC으로 변경
                    if sc == 0 and prec > 29:
                        return f"BIGNUMERIC({prec}, {sc})"
                    # NUMERIC(P, S)에서 P > 38 또는 S > 9인 경우 BIGNUMERIC으로 변경
                    elif prec > 38 or sc > 9:
                        return f"BIGNUMERIC({prec}, {sc})"
                return f"{bq_type}({prec}, {sc})"
            elif prec is not None:
                # 정밀도만 있는 경우도 동일한 제한사항 적용
                if bq_type == 'NUMERIC' and prec > 29:
                    return f"BIGNUMERIC({prec})"
                return f"{bq_type}({prec})"
        
        # STRING 타입에 길이 정보 추가 (선택적)
        if bq_type == 'STRING' and length is not None:
            if self.string_mode == 'string_only':
                # string_only 모드: 길이 정보 무시하고 단순 STRING
                return 'STRING'
            elif self.preserve_string_length:
                # auto 모드 + preserve_string_length: 길이 정보 포함
                return f"STRING({length})"
            else:
                # auto 모드: 길이 정보 없이 STRING
                return 'STRING'
        
        return bq_type
    
    def create_column_description(self, col: Dict) -> Optional[str]:
        """컬럼 설명 생성 (Oracle 코멘트만 또는 공란)"""
        # Oracle 코멘트가 있으면 그것만 사용, 없으면 None 반환
        column_comment = col.get('column_comment', '').strip()
        if column_comment:
            return column_comment
        
        # 코멘트가 없으면 None 반환 (description 없음)
        return None
    
    def escape_description(self, description: str) -> str:
        """설명 텍스트를 SQL에서 안전하게 사용할 수 있도록 이스케이프"""
        if not description:
            return ""
        
        # 따옴표 이스케이프
        escaped = description.replace('"', '\\"')
        
        # 줄바꿈 문자 제거
        escaped = escaped.replace('\n', ' ').replace('\r', ' ')
        
        # 연속된 공백을 하나로 줄임
        import re
        escaped = re.sub(r'\s+', ' ', escaped)
        
        return escaped.strip()
    
    def show_version(self):
        """버전 정보 표시"""
        print("Oracle to BigQuery Migration Tool - Portable Version")
        print("Version: 1.0.0")
        print("Python:", sys.version.split()[0])
        print("Platform: Portable (No pandas)")
    
    def show_help(self):
        """도움말 표시"""
        help_text = """
Oracle to BigQuery Migration Tool - Portable Version

사용법:
  oracle-to-bq convert <input_file> [--output-dir <output_dir>] [옵션]
  oracle-to-bq init-config [config_file]
  oracle-to-bq --version
  oracle-to-bq --help
  oracle-to-bq --test

명령어:
  convert     Oracle 스키마 CSV 파일을 BigQuery DDL로 변환
  init-config 설정 파일 템플릿 생성
  --version   버전 정보 표시
  --help      이 도움말 표시
  --test      포터블 패키지 테스트

옵션:
  --output-dir <output_dir>         출력 디렉토리 (기본: 입력 파일과 동일한 위치)
  --project-id <project_id>         BigQuery 프로젝트 ID
  --config <config_file>            설정 파일 경로
  --string-mode auto|string_only    문자열 변환 모드
  --preserve-string-length          STRING 타입에 길이 정보 포함
  --files                           개별 파일로 DDL 생성 (기본: 병합 파일)
  --no-primary-keys                 기본키 제약조건 생성 안함
  --create-or-replace               CREATE OR REPLACE TABLE 사용

예시:
  # 설정 파일 생성
  oracle-to-bq init-config my_config.json
  
  # 기본 변환 (병합 파일로 생성)
  oracle-to-bq convert schema.csv --output-dir bigquery_ddl --project-id my-project
  
  # 설정 파일 사용
  oracle-to-bq convert schema.csv --output-dir output --config my_config.json
  
  # 옵션 사용
  oracle-to-bq convert schema.csv --output-dir output --project-id my-project --preserve-string-length
  
  # 개별 파일로 생성
  oracle-to-bq convert schema.csv --output-dir output --project-id my-project --files

지원하는 입력 형식:
  필수: TABLE_NAME, COLUMN_NAME, DATA_TYPE, NULLABLE
  선택: OWNER (Oracle 스키마명, BigQuery 데이터셋명으로 사용)
        DATA_PRECISION, DATA_SCALE, DATA_LENGTH
        IS_PRIMARY_KEY, DATA_DEFAULT, COLUMN_COMMENT

"""
        print(help_text)

def show_help():
    """도움말 표시"""
    help_text = """
🔄 Oracle to BigQuery Migration Tool - Portable Version

사용법:
  oracle-to-bq convert <input_file> [--output-dir <output_dir>] [옵션]
  oracle-to-bq init-config [config_file]
  oracle-to-bq --version
  oracle-to-bq --help
  oracle-to-bq --test

명령어:
  convert       Oracle 스키마 CSV 파일을 BigQuery DDL로 변환
  init-config   설정 파일 템플릿 생성
  --version     버전 정보 표시
  --help        이 도움말 표시
  --test        포터블 패키지 테스트

옵션:
  --output-dir <output_dir>         출력 디렉토리 (기본: 입력 파일과 동일한 위치, 파일명.sql)
  --project-id <project_id>         BigQuery 프로젝트 ID (필수)
  --config <config_file>            설정 파일 경로 (JSON/YAML)
  --string-mode auto|string_only    문자열 변환 모드
                                    auto: 기본 변환 (기본값)
                                    string_only: 모든 문자열을 STRING으로
  --preserve-string-length          STRING 타입에 길이 정보 포함 (예: STRING(100))
  --files                           개별 파일로 DDL 생성 (기본: 병합 파일)
  --no-primary-keys                 기본키 제약조건 생성 안함
  --create-or-replace               CREATE OR REPLACE TABLE 사용

예시:
  # 기본 변환 (입력 파일과 같은 위치에 schema.sql 생성)
  oracle-to-bq convert schema.csv --project-id my-project
  
  # 출력 디렉토리 지정
  oracle-to-bq convert schema.csv --output-dir bigquery_ddl --project-id my-project
  
  # 설정 파일 사용
  oracle-to-bq convert schema.csv --output-dir output --config my_config.json
  
  # 옵션 사용
  oracle-to-bq convert schema.csv --output-dir output --project-id my-project --preserve-string-length

지원하는 입력 형식:
  필수: TABLE_NAME, COLUMN_NAME, DATA_TYPE, NULLABLE
  선택: OWNER (Oracle 스키마명, BigQuery 데이터셋명으로 사용)
        DATA_PRECISION, DATA_SCALE, DATA_LENGTH
        IS_PRIMARY_KEY, DATA_DEFAULT, COLUMN_COMMENT

출력:
  - Oracle OWNER → BigQuery 데이터셋명 (소문자 변환)
  - Oracle 코멘트가 있으면 description으로 포함, 없으면 description 없음
  - 정밀도/스케일 정보 완벽 보존
  - 한글 테이블명/컬럼명 백틱 처리
"""
    print(help_text)

class OracleToBigQueryConverter:
    """Oracle to BigQuery 변환기"""
    
    def __init__(self, project_id, string_mode='auto', preserve_string_length=False):
        self.project_id = project_id
        self.string_mode = string_mode
        self.preserve_string_length = preserve_string_length
    
    def test_package(self):
        """포터블 패키지 테스트"""
        print("🧪 포터블 패키지 테스트 중...")
        
        # 기본 기능 테스트
        test_data = [
            {'TABLE_NAME': 'TEST_TABLE', 'COLUMN_NAME': 'ID', 'DATA_TYPE': 'NUMBER', 'DATA_PRECISION': '10', 'DATA_SCALE': '0', 'NULLABLE': 'N'},
            {'TABLE_NAME': 'TEST_TABLE', 'COLUMN_NAME': 'NAME', 'DATA_TYPE': 'VARCHAR2', 'DATA_PRECISION': '', 'DATA_SCALE': '', 'NULLABLE': 'Y'}
        ]
        
        # 임시 CSV 파일 생성
        temp_csv = Path("test_schema.csv")
        with open(temp_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['TABLE_NAME', 'COLUMN_NAME', 'DATA_TYPE', 'DATA_PRECISION', 'DATA_SCALE', 'NULLABLE'])
            writer.writeheader()
            writer.writerows(test_data)
        
        # 변환 테스트
        temp_output = Path("test_output")
        success = self.process_csv_file(temp_csv, temp_output)
        
        # 정리
        if temp_csv.exists():
            temp_csv.unlink()
        if temp_output.exists():
            import shutil
            shutil.rmtree(temp_output)
        
        if success:
            print("✅ 포터블 패키지 테스트 성공!")
            return True
        else:
            print("❌ 포터블 패키지 테스트 실패!")
            return False


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        tool = SimpleMigrationTool()
        tool.show_help()
        return
    
    command = sys.argv[1]
    
    if command == '--version':
        tool = SimpleMigrationTool()
        tool.show_version()
    elif command == '--help':
        tool = SimpleMigrationTool()
        tool.show_help()
    elif command == '--test':
        tool = SimpleMigrationTool()
        success = tool.test_package()
        sys.exit(0 if success else 1)
    elif command == 'init-config':
        # 설정 파일 생성
        config_file = 'oracle_to_bq_config.json'
        if len(sys.argv) > 2:
            config_file = sys.argv[2]
        
        tool = SimpleMigrationTool()
        tool.create_config_template(config_file)
        sys.exit(0)
    elif command == 'convert':
        if len(sys.argv) < 3:
            print("❌ 사용법: oracle-to-bq convert <input_file> [--output-dir <output_dir>] [옵션]")
            print("옵션:")
            print("  --project-id <project_id>         BigQuery 프로젝트 ID")
            print("  --config <config_file>            설정 파일 경로")
            print("  --string-mode auto|string_only    문자열 변환 모드 (기본: auto)")
            print("  --preserve-string-length          STRING 타입에 길이 정보 포함")
            print("  --files                           개별 파일로 DDL 생성 (기본: 병합 파일)")
            print("  --no-primary-keys                 기본키 제약조건 생성 안함")
            print("  --create-or-replace               CREATE OR REPLACE TABLE 사용")
            sys.exit(1)
        
        input_file = Path(sys.argv[2])
        
        # 옵션 파싱
        output_dir = None  # 기본값은 None (나중에 입력 파일 기반으로 설정)
        string_mode = 'auto'
        preserve_string_length = False
        project_id = None
        config_file = None
        
        # --output-dir 옵션 찾기
        has_output_dir = False
        try:
            output_idx = sys.argv.index('--output-dir')
            if output_idx + 1 < len(sys.argv):
                output_dir = Path(sys.argv[output_idx + 1])
                has_output_dir = True
        except ValueError:
            pass
        
        # --project-id 옵션 찾기
        try:
            project_idx = sys.argv.index('--project-id')
            if project_idx + 1 < len(sys.argv):
                project_id = sys.argv[project_idx + 1]
        except ValueError:
            pass
        
        # --config 옵션 찾기
        try:
            config_idx = sys.argv.index('--config')
            if config_idx + 1 < len(sys.argv):
                config_file = sys.argv[config_idx + 1]
        except ValueError:
            pass
        
        # --string-mode 옵션 찾기
        try:
            string_mode_idx = sys.argv.index('--string-mode')
            if string_mode_idx + 1 < len(sys.argv):
                string_mode = sys.argv[string_mode_idx + 1]
                if string_mode not in ['auto', 'string_only']:
                    print("❌ --string-mode는 'auto' 또는 'string_only'만 가능합니다.")
                    sys.exit(1)
        except ValueError:
            pass
        
        # --preserve-string-length 옵션 확인
        if '--preserve-string-length' in sys.argv:
            preserve_string_length = True
        
        # --files 옵션 확인 (개별 파일 생성)
        separate_files = '--files' in sys.argv
        
        # --no-primary-keys 옵션 확인
        create_primary_keys = '--no-primary-keys' not in sys.argv
        
        # --create-or-replace 옵션 확인
        create_or_replace = '--create-or-replace' in sys.argv
        
        # 도구 초기화
        tool = SimpleMigrationTool(config_file=config_file)
        
        # 명령행 옵션으로 설정 덮어쓰기
        if project_id:
            tool.project_id = project_id
        if string_mode != 'auto':
            tool.string_mode = string_mode
        if preserve_string_length:
            tool.preserve_string_length = preserve_string_length
        if separate_files:
            tool.merge_output = False  # --files 옵션이 있으면 개별 파일 생성
        if not create_primary_keys:
            tool.create_primary_keys = create_primary_keys
        if create_or_replace:
            tool.create_or_replace = create_or_replace
        
        if not input_file.exists():
            print(f"❌ 입력 파일을 찾을 수 없습니다: {input_file}")
            sys.exit(1)
        
        # output_dir이 지정되지 않았으면 입력 파일 기반으로 설정
        if output_dir is None:
            # 입력 파일과 같은 디렉토리에 파일명만 .sql로 변경
            output_dir = input_file.parent
            # 병합 파일명을 입력 파일명.sql로 설정하기 위해 tool에 전달
            tool.output_filename = input_file.stem + '.sql'
        else:
            tool.output_filename = 'merged_ddl.sql'  # 기본 병합 파일명
        
        success = tool.process_csv_file(input_file, output_dir)
        sys.exit(0 if success else 1)
    else:
        print(f"❌ 알 수 없는 명령어: {command}")
        tool = SimpleMigrationTool()
        tool.show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()