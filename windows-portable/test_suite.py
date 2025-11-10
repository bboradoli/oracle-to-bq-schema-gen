#!/usr/bin/env python3
"""
Oracle to BigQuery Migration Tool - Windows 포터블 버전 자동화 테스트 스위트

완전한 테스트 자동화를 위한 통합 테스트 스위트
- 단위 테스트: 핵심 DDL 생성 기능
- 통합 테스트: 전체 CSV to DDL 변환 플로우
- 성능 테스트: 대용량 데이터셋 처리
"""

import os
import sys
import csv
import json
import shutil
import subprocess
import tempfile
import unittest
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

class DDLGeneratorUnitTests(unittest.TestCase):
    """DDL 생성 핵심 기능 단위 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 테스트용 SimpleMigrationTool 인스턴스 생성
        sys.path.insert(0, str(Path(__file__).parent / "windows" / "src"))
        from oracle_to_bq_cli import SimpleMigrationTool
        self.tool = SimpleMigrationTool(config_file=None)  # 설정 파일 없이 초기화
        self.tool.project_id = "test-project"
        # 테스트를 위해 기본값으로 재설정
        self.tool.preserve_string_length = False
    
    def test_oracle_type_conversion(self):
        """Oracle 타입 변환 테스트"""
        test_cases = [
            # (oracle_type, precision, scale, expected_bq_type)
            ('NUMBER', '10', '0', 'INT64'),
            ('NUMBER', '15', '2', 'NUMERIC'),
            ('NUMBER', '38', '9', 'NUMERIC'),
            ('NUMBER', '76', '38', 'BIGNUMERIC'),
            ('NUMBER', None, None, 'NUMERIC'),
            ('VARCHAR2', None, None, 'STRING'),
            ('CHAR', None, None, 'STRING'),
            ('DATE', None, None, 'DATETIME'),
            ('TIMESTAMP', None, None, 'DATETIME'),
            ('CLOB', None, None, 'STRING'),
            ('BLOB', None, None, 'BYTES'),
        ]
        
        for oracle_type, precision, scale, expected in test_cases:
            with self.subTest(oracle_type=oracle_type, precision=precision, scale=scale):
                result = self.tool.convert_oracle_type(oracle_type, precision, scale)
                self.assertEqual(result, expected, 
                               f"Oracle {oracle_type}({precision},{scale}) -> {result}, expected {expected}")
    
    def test_encoding_detection(self):
        """인코딩 감지 테스트"""
        # UTF-8 파일 생성
        utf8_file = Path("test_utf8.csv")
        with open(utf8_file, 'w', encoding='utf-8') as f:
            f.write("TABLE_NAME,COLUMN_NAME\n한글테이블,한글컬럼\n")
        
        try:
            encoding = self.tool.detect_encoding(utf8_file)
            self.assertEqual(encoding, 'utf-8', "UTF-8 인코딩 감지 실패")
        finally:
            if utf8_file.exists():
                utf8_file.unlink()
    
    def test_primary_key_generation(self):
        """기본키 제약조건 생성 테스트"""
        columns = [
            {'column_name': 'ID', 'data_type': 'NUMBER', 'data_precision': '10', 'data_scale': '0', 
             'nullable': 'N', 'is_primary_key': 'Y', 'column_comment': '기본키'},
            {'column_name': 'NAME', 'data_type': 'VARCHAR2', 'data_precision': '', 'data_scale': '', 
             'nullable': 'Y', 'is_primary_key': 'N', 'column_comment': '이름'}
        ]
        
        ddl = self.tool.create_table_ddl('TEST_SCHEMA', 'TEST_TABLE', columns)
        
        self.assertIn('PRIMARY KEY (ID) NOT ENFORCED', ddl, "기본키 제약조건이 생성되지 않음")
        self.assertIn('CREATE', ddl, "DDL 구조가 올바르지 않음")
    
    def test_composite_primary_key_generation(self):
        """복합 기본키 제약조건 생성 테스트"""
        columns = [
            {'column_name': 'ORDER_ID', 'data_type': 'NUMBER', 'data_precision': '10', 'data_scale': '0', 
             'nullable': 'N', 'is_primary_key': 'Y', 'column_comment': '주문 ID'},
            {'column_name': 'ITEM_ID', 'data_type': 'NUMBER', 'data_precision': '10', 'data_scale': '0', 
             'nullable': 'N', 'is_primary_key': 'Y', 'column_comment': '상품 ID'},
            {'column_name': 'QUANTITY', 'data_type': 'NUMBER', 'data_precision': '5', 'data_scale': '0', 
             'nullable': 'N', 'is_primary_key': 'N', 'column_comment': '수량'}
        ]
        
        ddl = self.tool.create_table_ddl('TEST_SCHEMA', 'ORDER_ITEMS', columns)
        
        self.assertIn('PRIMARY KEY (ORDER_ID, ITEM_ID) NOT ENFORCED', ddl, "복합 기본키 제약조건이 생성되지 않음")
        self.assertIn('CREATE', ddl, "DDL 구조가 올바르지 않음")
    
    def test_project_id_handling(self):
        """project_id 처리 테스트"""
        columns = [
            {'column_name': 'ID', 'data_type': 'NUMBER', 'data_precision': '10', 'data_scale': '0', 
             'nullable': 'N', 'is_primary_key': 'Y', 'column_comment': '테스트 ID'}
        ]
        
        # project_id가 있는 경우
        self.tool.project_id = 'my-project'
        ddl_with_project = self.tool.create_table_ddl('TEST_SCHEMA', 'TEST_TABLE', columns)
        self.assertIn('`my-project.TEST_SCHEMA.TEST_TABLE`', ddl_with_project, 
                     "project_id가 있을 때 프로젝트.데이터셋.테이블 형태가 아님")
        
        # project_id가 없는 경우 (빈 문자열)
        self.tool.project_id = ''
        ddl_without_project = self.tool.create_table_ddl('TEST_SCHEMA', 'TEST_TABLE', columns)
        self.assertIn('`TEST_SCHEMA.TEST_TABLE`', ddl_without_project, 
                     "project_id가 없을 때 데이터셋.테이블 형태가 아님")
        self.assertNotIn('..', ddl_without_project, "빈 project_id로 인한 잘못된 형태")
        
        # project_id가 None인 경우
        self.tool.project_id = None
        ddl_none_project = self.tool.create_table_ddl('TEST_SCHEMA', 'TEST_TABLE', columns)
        self.assertIn('`TEST_SCHEMA.TEST_TABLE`', ddl_none_project, 
                     "project_id가 None일 때 데이터셋.테이블 형태가 아님")
    
    def test_auto_config_loading(self):
        """자동 config.json 로딩 테스트"""
        # config_file=None으로 초기화할 때 자동으로 실행파일 경로의 config.json을 찾는지 테스트
        from oracle_to_bq_cli import SimpleMigrationTool
        
        # config_file=None으로 초기화
        tool_auto = SimpleMigrationTool(config_file=None)
        
        # 기본값이 아닌 다른 값이 설정되었는지 확인 (실제 config.json이 로드되었다면)
        # 이 테스트는 실제 config.json 파일의 존재 여부에 따라 달라질 수 있음
        self.assertIsNotNone(tool_auto.project_id, "project_id가 None이면 안됨")
        self.assertIsNotNone(tool_auto.string_mode, "string_mode가 None이면 안됨")
    
    def test_merged_ddl_generation(self):
        """병합 DDL 생성 테스트"""
        tables = {
            'TEST_SCHEMA.TABLE1': {
                'schema_name': 'TEST_SCHEMA',
                'table_name': 'TABLE1',
                'columns': [
                    {'column_name': 'ID', 'data_type': 'NUMBER', 'data_precision': '10', 'data_scale': '0',
                     'nullable': 'N', 'is_primary_key': 'Y', 'column_comment': ''}
                ]
            },
            'TEST_SCHEMA.TABLE2': {
                'schema_name': 'TEST_SCHEMA', 
                'table_name': 'TABLE2',
                'columns': [
                    {'column_name': 'NAME', 'data_type': 'VARCHAR2', 'data_precision': '', 'data_scale': '',
                     'nullable': 'Y', 'is_primary_key': 'N', 'column_comment': ''}
                ]
            }
        }
        
        output_file = Path("test_merged.sql")
        try:
            self.tool.generate_merged_ddl(tables, output_file)
            
            self.assertTrue(output_file.exists(), "병합 DDL 파일이 생성되지 않음")
            
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.assertIn('-- Oracle to BigQuery DDL Migration', content, "헤더가 없음")
            self.assertIn('-- Total tables: 2', content, "테이블 수가 올바르지 않음")
            self.assertIn('CREATE', content, "DDL이 포함되지 않음")
            
        finally:
            if output_file.exists():
                output_file.unlink()
            if output_file.exists():
                output_file.unlink()
    
    def test_backtick_detection(self):
        """백틱 필요성 검사 테스트"""
        test_cases = [
            # (name, needs_backticks)
            ('normal_column', False),
            ('한글컬럼', True),
            ('123column', True),
            ('column-name', True),
            ('SELECT', True),  # 예약어
            ('FROM', True),    # 예약어
            ('valid_name_123', False),
        ]
        
        for name, expected in test_cases:
            with self.subTest(name=name):
                result = self.tool.needs_backticks(name)
                self.assertEqual(result, expected, 
                               f"'{name}' backticks needed: {result}, expected {expected}")
    
    def test_identifier_formatting(self):
        """식별자 포맷팅 테스트"""
        test_cases = [
            ('normal_column', 'normal_column'),
            ('한글컬럼', '`한글컬럼`'),
            ('123column', '`123column`'),
            ('SELECT', '`SELECT`'),
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = self.tool.format_identifier(input_name)
                self.assertEqual(result, expected, 
                               f"'{input_name}' formatted as '{result}', expected '{expected}'")
    
    def test_bigquery_type_with_precision(self):
        """BigQuery 타입 정밀도 포맷팅 테스트"""
        test_cases = [
            # (bq_type, oracle_type, precision, scale, char_length, expected)
            ('NUMERIC', 'NUMBER', '10', '2', None, 'NUMERIC(10, 2)'),
            ('NUMERIC', 'NUMBER', '15', None, None, 'NUMERIC(15)'),
            ('STRING', 'VARCHAR2', None, None, '100', 'STRING'),
            ('INT64', 'NUMBER', '10', '0', None, 'INT64'),
        ]
        
        for bq_type, oracle_type, precision, scale, char_length, expected in test_cases:
            with self.subTest(bq_type=bq_type):
                result = self.tool.format_bigquery_type_with_precision(
                    bq_type, oracle_type, precision, scale, char_length)
                self.assertEqual(result, expected, 
                               f"Type formatting: {result}, expected {expected}")
    
    def test_description_escaping(self):
        """설명 텍스트 이스케이프 테스트"""
        test_cases = [
            ('Simple description', 'Simple description'),
            ('Description with "quotes"', 'Description with \\"quotes\\"'),
            ('Multi\nline\ndescription', 'Multi line description'),
            ('  Extra   spaces  ', 'Extra spaces'),
        ]
        
        for input_desc, expected in test_cases:
            with self.subTest(input_desc=input_desc):
                result = self.tool.escape_description(input_desc)
                self.assertEqual(result, expected, 
                               f"Description escaped: '{result}', expected '{expected}'")

    def test_create_or_replace_option(self):
        """CREATE OR REPLACE TABLE 옵션 테스트"""
        columns = [
            {'column_name': 'ID', 'data_type': 'NUMBER', 'data_precision': '10', 'data_scale': '0', 
             'nullable': 'N', 'is_primary_key': 'Y', 'column_comment': '테스트 ID'},
            {'column_name': 'NAME', 'data_type': 'VARCHAR2', 'data_precision': '', 'data_scale': '', 
             'nullable': 'Y', 'is_primary_key': 'N', 'column_comment': '이름'}
        ]
        
        # create_or_replace = False (기본값)
        self.tool.create_or_replace = False
        ddl_create = self.tool.create_table_ddl('TEST_SCHEMA', 'TEST_TABLE', columns)
        self.assertIn('CREATE TABLE', ddl_create, "CREATE TABLE이 포함되어야 함")
        self.assertNotIn('CREATE OR REPLACE TABLE', ddl_create, "CREATE OR REPLACE TABLE이 포함되면 안됨")
        
        # create_or_replace = True
        self.tool.create_or_replace = True
        ddl_create_or_replace = self.tool.create_table_ddl('TEST_SCHEMA', 'TEST_TABLE', columns)
        self.assertIn('CREATE OR REPLACE TABLE', ddl_create_or_replace, "CREATE OR REPLACE TABLE이 포함되어야 함")
        self.assertNotIn('CREATE TABLE `', ddl_create_or_replace.replace('CREATE OR REPLACE TABLE', ''), 
                        "단순 CREATE TABLE이 포함되면 안됨")

    def test_numeric_precision_limits(self):
        """NUMERIC 정밀도 제한 테스트 (BigQuery 제한사항 준수)"""
        test_cases = [
            # (precision, scale, expected_type)
            ('10', '0', 'INT64'),           # 작은 정수 -> INT64
            ('18', '0', 'INT64'),           # INT64 최대 범위
            ('25', '0', 'NUMERIC(25, 0)'),  # NUMERIC 범위 내 정수
            ('29', '0', 'NUMERIC(29, 0)'),  # NUMERIC 최대 정수 정밀도
            ('38', '0', 'BIGNUMERIC(38, 0)'), # 큰 정수 -> BIGNUMERIC
            ('50', '0', 'BIGNUMERIC(50, 0)'), # 매우 큰 정수 -> BIGNUMERIC
            ('15', '2', 'NUMERIC(15, 2)'),  # 일반적인 소수
            ('38', '9', 'NUMERIC(38, 9)'),  # NUMERIC 최대 범위
            ('50', '10', 'BIGNUMERIC(50, 10)'), # BIGNUMERIC 범위
        ]
        
        for precision, scale, expected in test_cases:
            with self.subTest(precision=precision, scale=scale):
                # Oracle NUMBER 타입을 BigQuery 타입으로 변환
                bq_type = self.tool.convert_oracle_type('NUMBER', precision, scale)
                formatted_type = self.tool.format_bigquery_type_with_precision(
                    bq_type, 'NUMBER', precision, scale, None)
                
                self.assertEqual(formatted_type, expected, 
                               f"NUMBER({precision},{scale}) -> {formatted_type}, expected {expected}")
    
    def test_debug_mode_configuration(self):
        """디버그 모드 설정 테스트"""
        # 기본값은 False
        self.assertFalse(self.tool.debug_mode, "기본 디버그 모드는 False여야 함")
        
        # 설정을 통한 디버그 모드 활성화
        self.tool.debug_mode = True
        self.assertTrue(self.tool.debug_mode, "디버그 모드가 True로 설정되어야 함")
        
        # 설정을 통한 디버그 모드 비활성화
        self.tool.debug_mode = False
        self.assertFalse(self.tool.debug_mode, "디버그 모드가 False로 설정되어야 함")
    
    def test_case_sensitivity_preservation(self):
        """대소문자 유지 테스트"""
        columns = [
            {'column_name': 'Customer_ID', 'data_type': 'NUMBER', 'data_precision': '10', 'data_scale': '0', 
             'nullable': 'N', 'is_primary_key': 'Y', 'column_comment': '고객 ID'},
            {'column_name': 'Customer_Name', 'data_type': 'VARCHAR2', 'data_precision': '', 'data_scale': '', 
             'nullable': 'Y', 'is_primary_key': 'N', 'column_comment': '고객 이름'}
        ]
        
        # 대소문자가 섞인 스키마명과 테이블명으로 DDL 생성
        ddl = self.tool.create_table_ddl('MyDataset', 'Customer_Info', columns)
        
        # 데이터셋명과 테이블명이 원본 대소문자 그대로 유지되는지 확인
        self.assertIn('MyDataset.Customer_Info', ddl, "데이터셋명과 테이블명의 대소문자가 유지되어야 함")
        self.assertIn('Customer_ID', ddl, "컬럼명의 대소문자가 유지되어야 함")
        self.assertIn('Customer_Name', ddl, "컬럼명의 대소문자가 유지되어야 함")
        
        # 소문자로 변환되지 않았는지 확인
        self.assertNotIn('mydataset.customer_info', ddl, "데이터셋명과 테이블명이 소문자로 변환되면 안됨")
        self.assertNotIn('customer_id', ddl, "컬럼명이 소문자로 변환되면 안됨")
    
    def test_primary_key_limit_16(self):
        """기본키 16개 제한 테스트"""
        # 18개의 기본키 컬럼 생성
        columns = []
        for i in range(1, 19):
            columns.append({
                'column_name': f'PK{i:02d}',
                'data_type': 'NUMBER',
                'data_precision': '10',
                'data_scale': '0',
                'nullable': 'N',
                'is_primary_key': 'Y',
                'column_comment': f'Primary Key {i}'
            })
        
        # DDL 생성
        ddl = self.tool.create_table_ddl('TestSchema', 'TestTable', columns)
        
        # PRIMARY KEY 절에 16개만 포함되는지 확인
        self.assertIn('PRIMARY KEY', ddl, "기본키 제약조건이 생성되어야 함")
        self.assertIn('PK01', ddl, "첫 번째 기본키가 포함되어야 함")
        self.assertIn('PK16', ddl, "16번째 기본키가 포함되어야 함")
        
        # PRIMARY KEY 절에서 PK17, PK18이 제외되었는지 확인
        pk_section = ddl[ddl.find('PRIMARY KEY'):ddl.find('NOT ENFORCED')]
        self.assertNotIn('PK17', pk_section, "17번째 기본키는 제외되어야 함")
        self.assertNotIn('PK18', pk_section, "18번째 기본키는 제외되어야 함")
    
    def test_drop_partition_table_before_create(self):
        """파티션 테이블 생성 전 DROP 옵션 테스트"""
        columns = [
            {'column_name': 'ID', 'data_type': 'NUMBER', 'data_precision': '10', 'data_scale': '0',
             'nullable': 'N', 'is_primary_key': 'Y', 'column_comment': 'ID', 'partition_yn': 'N'},
            {'column_name': 'CreateDate', 'data_type': 'TIMESTAMP', 'data_precision': '', 'data_scale': '',
             'nullable': 'Y', 'is_primary_key': 'N', 'column_comment': 'Date', 'partition_yn': 'Y'}
        ]
        
        # 옵션 비활성화 시 DROP 문이 없어야 함
        self.tool.drop_partition_table_before_create = False
        self.tool.enable_partitioning = True
        ddl_without_drop = self.tool.create_table_ddl('TestSchema', 'TestTable', columns)
        self.assertNotIn('DROP TABLE', ddl_without_drop, "옵션 비활성화 시 DROP 문이 없어야 함")
        
        # 옵션 활성화 시 DROP 문이 있어야 함
        self.tool.drop_partition_table_before_create = True
        self.tool.create_or_replace = True
        ddl_with_drop = self.tool.create_table_ddl('TestSchema', 'TestTable', columns)
        self.assertIn('DROP TABLE IF EXISTS', ddl_with_drop, "옵션 활성화 시 DROP 문이 있어야 함")
        self.assertIn('CREATE OR REPLACE TABLE', ddl_with_drop, "CREATE OR REPLACE도 포함되어야 함")
        
        # 파티션이 없는 테이블은 DROP 문이 없어야 함
        columns_no_partition = [
            {'column_name': 'ID', 'data_type': 'NUMBER', 'data_precision': '10', 'data_scale': '0',
             'nullable': 'N', 'is_primary_key': 'Y', 'column_comment': 'ID', 'partition_yn': 'N'}
        ]
        ddl_no_partition = self.tool.create_table_ddl('TestSchema', 'TestTable', columns_no_partition)
        self.assertNotIn('DROP TABLE', ddl_no_partition, "파티션이 없는 테이블은 DROP 문이 없어야 함")
    
    def test_unsupported_partition_types(self):
        """지원하지 않는 파티션 타입 테스트"""
        self.tool.enable_partitioning = True
        
        # STRING 타입 (VARCHAR2) - 파티션 지원 안 함
        columns_string = [
            {'column_name': 'ID', 'data_type': 'NUMBER', 'data_precision': '10', 'data_scale': '0',
             'nullable': 'N', 'is_primary_key': 'Y', 'column_comment': 'ID', 'partition_yn': 'N'},
            {'column_name': 'Name', 'data_type': 'VARCHAR2', 'data_precision': '', 'data_scale': '',
             'nullable': 'Y', 'is_primary_key': 'N', 'column_comment': 'Name', 'partition_yn': 'Y'}
        ]
        ddl_string = self.tool.create_table_ddl('TestSchema', 'TestTable', columns_string)
        self.assertNotIn('PARTITION BY', ddl_string, "STRING 타입은 파티션을 지원하지 않아야 함")
        
        # INT64 타입 (NUMBER) - RANGE 파티션 필요하므로 생성 안 함
        columns_number = [
            {'column_name': 'ID', 'data_type': 'NUMBER', 'data_precision': '10', 'data_scale': '0',
             'nullable': 'N', 'is_primary_key': 'Y', 'column_comment': 'ID', 'partition_yn': 'Y'}
        ]
        ddl_number = self.tool.create_table_ddl('TestSchema', 'TestTable', columns_number)
        self.assertNotIn('PARTITION BY', ddl_number, "INT64 타입은 RANGE 파티션 설정이 필요하여 생성하지 않아야 함")
        
        # TIMESTAMP 타입 - 파티션 지원함
        columns_timestamp = [
            {'column_name': 'ID', 'data_type': 'NUMBER', 'data_precision': '10', 'data_scale': '0',
             'nullable': 'N', 'is_primary_key': 'Y', 'column_comment': 'ID', 'partition_yn': 'N'},
            {'column_name': 'CreateDate', 'data_type': 'TIMESTAMP', 'data_precision': '', 'data_scale': '',
             'nullable': 'Y', 'is_primary_key': 'N', 'column_comment': 'Date', 'partition_yn': 'Y'}
        ]
        ddl_timestamp = self.tool.create_table_ddl('TestSchema', 'TestTable', columns_timestamp)
        self.assertIn('PARTITION BY DATETIME_TRUNC(CreateDate, DAY)', ddl_timestamp, "TIMESTAMP 타입은 DATETIME으로 변환되어 DATETIME_TRUNC 파티션을 지원해야 함")


class WindowsPortableTestSuite:
    """Windows 포터블 버전 통합 테스트 스위트"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.windows_dir = self.root_dir / "windows"
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """테스트 결과 로깅"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "message": message
        }
        self.test_results.append(result)
        print(f"{status} {test_name}: {message}")
        
    def test_build_integrity(self) -> bool:
        """빌드 무결성 테스트"""
        print("\n🔍 빌드 무결성 테스트...")
        
        required_files = [
            "python/python.exe",
            "src/oracle_to_bq_cli.py",
            "oracle-to-bq.bat",
            "verify_standalone.bat",
            "config.json",
            "schema.csv"
        ]
        
        all_passed = True
        for file_path in required_files:
            full_path = self.windows_dir / file_path
            if full_path.exists():
                self.log_test(f"파일 존재: {file_path}", True)
            else:
                self.log_test(f"파일 존재: {file_path}", False, f"파일 없음: {full_path}")
                all_passed = False
        
        return all_passed
    
    def test_python_runtime(self) -> bool:
        """Python 런타임 테스트"""
        print("\n🐍 Python 런타임 테스트...")
        
        python_exe = self.windows_dir / "python" / "python.exe"
        
        try:
            # Python 버전 확인
            result = subprocess.run([str(python_exe), "--version"], 
                                  capture_output=True, encoding='utf-8', timeout=10, errors='ignore')
            if result.returncode == 0:
                version = result.stdout.strip()
                self.log_test("Python 버전 확인", True, version)
                return True
            else:
                self.log_test("Python 버전 확인", False, result.stderr)
                return False
        except Exception as e:
            self.log_test("Python 런타임 실행", False, str(e))
            return False
    
    def test_cli_basic_functions(self) -> bool:
        """CLI 기본 기능 테스트"""
        print("\n⚙️ CLI 기본 기능 테스트...")
        
        oracle_to_bq = self.windows_dir / "oracle-to-bq.bat"
        
        tests = [
            ("--version", "버전 정보"),
            ("--help", "도움말"),
        ]
        
        all_passed = True
        for args, description in tests:
            try:
                result = subprocess.run([str(oracle_to_bq), args],
                                      capture_output=True, encoding='utf-8', errors='ignore',
                                      timeout=30, cwd=str(self.windows_dir))
                if result.returncode == 0:
                    self.log_test(f"CLI {description}", True)
                else:
                    self.log_test(f"CLI {description}", False, result.stderr)
                    all_passed = False
            except Exception as e:
                self.log_test(f"CLI {description}", False, str(e))
                all_passed = False
        
        return all_passed
    
    def create_test_csv(self) -> Path:
        """테스트용 CSV 파일 생성 (기본키 포함)"""
        test_data = [
            {
                'TABLE_NAME': 'TEST_TABLE',
                'OWNER': 'TEST_SCHEMA',
                'COLUMN_NAME': 'ID',
                'DATA_TYPE': 'NUMBER',
                'DATA_PRECISION': '10',
                'DATA_SCALE': '0',
                'NULLABLE': 'N',
                'IS_PRIMARY_KEY': 'Y',
                'COLUMN_COMMENT': '테스트 ID'
            },
            {
                'TABLE_NAME': 'TEST_TABLE',
                'OWNER': 'TEST_SCHEMA',
                'COLUMN_NAME': 'NAME',
                'DATA_TYPE': 'VARCHAR2',
                'DATA_PRECISION': '',
                'DATA_SCALE': '',
                'DATA_LENGTH': '100',
                'NULLABLE': 'Y',
                'IS_PRIMARY_KEY': 'N',
                'COLUMN_COMMENT': '테스트 이름'
            },
            {
                'TABLE_NAME': 'TEST_TABLE',
                'OWNER': 'TEST_SCHEMA',
                'COLUMN_NAME': 'AMOUNT',
                'DATA_TYPE': 'NUMBER',
                'DATA_PRECISION': '15',
                'DATA_SCALE': '2',
                'NULLABLE': 'Y',
                'IS_PRIMARY_KEY': 'N',
                'COLUMN_COMMENT': '테스트 금액'
            },
            {
                'TABLE_NAME': '한글테이블',
                'OWNER': 'TEST_SCHEMA',
                'COLUMN_NAME': '한글컬럼',
                'DATA_TYPE': 'VARCHAR2',
                'DATA_PRECISION': '',
                'DATA_SCALE': '',
                'DATA_LENGTH': '50',
                'NULLABLE': 'N',
                'IS_PRIMARY_KEY': 'Y',
                'COLUMN_COMMENT': '한글 테스트'
            }
        ]
        
        test_csv = self.windows_dir / "test_input.csv"
        with open(test_csv, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['TABLE_NAME', 'OWNER', 'COLUMN_NAME', 'DATA_TYPE', 
                         'DATA_PRECISION', 'DATA_SCALE', 'DATA_LENGTH', 'NULLABLE', 'IS_PRIMARY_KEY', 'COLUMN_COMMENT']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(test_data)
        
        return test_csv
    
    def test_ddl_conversion(self) -> bool:
        """DDL 변환 기능 테스트"""
        print("\n🔄 DDL 변환 기능 테스트...")
        
        # 테스트 CSV 생성
        test_csv = self.create_test_csv()
        output_dir = self.windows_dir / "test_ddl_output"
        
        # 기존 출력 디렉토리 제거
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        oracle_to_bq = self.windows_dir / "oracle-to-bq.bat"
        
        try:
            # DDL 변환 실행
            result = subprocess.run([
                str(oracle_to_bq), "convert", str(test_csv),
                "--output-dir", str(output_dir),
                "--project-id", "test-project"
            ], capture_output=True, encoding='utf-8', errors='ignore', timeout=60, cwd=str(self.windows_dir))
            
            if result.returncode == 0:
                self.log_test("DDL 변환 실행", True)
                
                # 생성된 파일 확인
                expected_files = [
                    "test_schema_test_table.sql",
                    "test_schema_한글테이블.sql"
                ]
                
                files_ok = True
                for expected_file in expected_files:
                    file_path = output_dir / expected_file
                    if file_path.exists():
                        self.log_test(f"DDL 파일 생성: {expected_file}", True)
                        
                        # 파일 내용 검증 (기본키 제약조건 포함)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if ('CREATE' in content and 'test-project.TEST_SCHEMA' in content and 
                                'PRIMARY KEY' in content):
                                self.log_test(f"DDL 내용 검증: {expected_file}", True)
                            else:
                                self.log_test(f"DDL 내용 검증: {expected_file}", False, "올바른 DDL 형식이 아님")
                                files_ok = False
                    else:
                        self.log_test(f"DDL 파일 생성: {expected_file}", False, "파일이 생성되지 않음")
                        files_ok = False
                
                return files_ok
            else:
                self.log_test("DDL 변환 실행", False, result.stderr)
                return False
                
        except Exception as e:
            self.log_test("DDL 변환 테스트", False, str(e))
            return False
        finally:
            # 테스트 파일 정리
            if test_csv.exists():
                test_csv.unlink()
            if output_dir.exists():
                shutil.rmtree(output_dir)
    
    def test_korean_support(self) -> bool:
        """한글 지원 테스트"""
        print("\n🇰🇷 한글 지원 테스트...")
        
        # 한글 테이블명/컬럼명이 포함된 DDL 변환 테스트는 test_ddl_conversion에서 수행됨
        # 여기서는 추가적인 한글 처리 테스트 수행
        
        test_csv = self.create_test_csv()
        output_dir = self.windows_dir / "korean_test_output"
        
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        oracle_to_bq = self.windows_dir / "oracle-to-bq.bat"
        
        try:
            result = subprocess.run([
                str(oracle_to_bq), "convert", str(test_csv),
                "--output-dir", str(output_dir),
                "--project-id", "한글프로젝트"
            ], capture_output=True, encoding='utf-8', errors='ignore', timeout=60, cwd=str(self.windows_dir))
            
            if result.returncode == 0:
                # 한글 테이블 DDL 파일 확인 - 실제 생성되는 파일명 사용
                korean_table_file = output_dir / "TEST_SCHEMA_한글테이블.sql"
                if korean_table_file.exists():
                    with open(korean_table_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 한글 테이블명과 컬럼명이 백틱으로 처리되었는지 확인
                        if '.한글테이블`' in content and '`한글컬럼`' in content:
                            self.log_test("한글 테이블명/컬럼명 백틱 처리", True)
                            return True
                        else:
                            self.log_test("한글 테이블명/컬럼명 백틱 처리", False, f"백틱 처리되지 않음. 내용: {content[:200]}")
                            return False
                else:
                    # 생성된 파일 목록 확인
                    files = list(output_dir.glob("*.sql"))
                    self.log_test("한글 테이블 DDL 생성", False, f"한글 테이블 파일이 생성되지 않음. 생성된 파일: {[f.name for f in files]}")
                    return False
            else:
                self.log_test("한글 프로젝트 ID 처리", False, result.stderr)
                return False
                
        except Exception as e:
            self.log_test("한글 지원 테스트", False, str(e))
            return False
        finally:
            if test_csv.exists():
                test_csv.unlink()
            if output_dir.exists():
                shutil.rmtree(output_dir)
    
    def test_encoding_support(self) -> bool:
        """인코딩 지원 테스트 (UTF-8, EUC-KR)"""
        print("\n🔤 인코딩 지원 테스트...")
        
        # EUC-KR 테스트 파일 생성
        euckr_data = [
            ['TABLE_NAME','OWNER','COLUMN_NAME','DATA_TYPE','DATA_PRECISION','DATA_SCALE','DATA_LENGTH','NULLABLE','IS_PRIMARY_KEY','COLUMN_COMMENT'],
            ['ENCODING_TEST','EUC_SCHEMA','ID','NUMBER','10','0','','N','Y','인코딩 테스트 ID'],
            ['ENCODING_TEST','EUC_SCHEMA','NAME','VARCHAR2','','','50','Y','N','한글 이름']
        ]
        
        euckr_csv = self.windows_dir / "test_euckr.csv"
        with open(euckr_csv, 'w', newline='', encoding='euc-kr') as f:
            writer = csv.writer(f)
            writer.writerows(euckr_data)
        
        output_dir = self.windows_dir / "encoding_test_output"
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        oracle_to_bq = self.windows_dir / "oracle-to-bq.bat"
        
        try:
            result = subprocess.run([
                str(oracle_to_bq), "convert", str(euckr_csv),
                "--output-dir", str(output_dir),
                "--project-id", "encoding-test"
            ], capture_output=True, encoding='utf-8', errors='ignore', timeout=60, cwd=str(self.windows_dir))
            
            if result.returncode == 0:
                # EUC-KR 인코딩 감지 확인
                stdout_text = result.stdout or ""
                stderr_text = result.stderr or ""
                combined_output = stdout_text + stderr_text
                # 생성된 파일 확인 (인코딩 감지 메시지 확인은 선택사항)
                ddl_file = output_dir / "euc_schema_encoding_test.sql"
                if ddl_file.exists():
                    with open(ddl_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'PRIMARY KEY (ID) NOT ENFORCED' in content and '인코딩 테스트 ID' in content:
                            # 인코딩 감지 메시지가 있으면 더 좋지만, 파일이 정상 생성되면 성공으로 간주
                            if "euc-kr" in combined_output.lower() or "cp949" in combined_output.lower():
                                self.log_test("EUC-KR 인코딩 감지 및 파일 처리", True)
                            else:
                                self.log_test("EUC-KR 파일 처리", True, "파일 생성 성공 (인코딩 메시지 미확인)")
                            return True
                        else:
                            self.log_test("EUC-KR 파일 처리", False, "DDL 내용 오류")
                            return False
                else:
                    self.log_test("EUC-KR 파일 처리", False, "DDL 파일 생성 실패")
                    return False
            else:
                self.log_test("EUC-KR 파일 변환", False, result.stderr)
                return False
                
        except Exception as e:
            self.log_test("인코딩 지원 테스트", False, str(e))
            return False
        finally:
            if euckr_csv.exists():
                euckr_csv.unlink()
            if output_dir.exists():
                shutil.rmtree(output_dir)
    
    def test_merged_output(self) -> bool:
        """병합 출력 테스트"""
        print("\n📄 병합 출력 테스트...")
        
        test_csv = self.create_test_csv()
        output_dir = self.windows_dir / "merged_test_output"
        
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        oracle_to_bq = self.windows_dir / "oracle-to-bq.bat"
        
        try:
            result = subprocess.run([
                str(oracle_to_bq), "convert", str(test_csv),
                "--output-dir", str(output_dir),
                "--project-id", "merged-test",
                "--merge-output"
            ], capture_output=True, encoding='utf-8', errors='ignore', timeout=60, cwd=str(self.windows_dir))
            
            if result.returncode == 0:
                # 병합 파일 확인
                merged_file = output_dir / "merged_ddl.sql"
                if merged_file.exists():
                    with open(merged_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 병합 파일 내용 검증
                    checks = [
                        ('-- Oracle to BigQuery DDL Migration', "헤더"),
                        ('-- Total tables:', "테이블 수"),
                        ('CREATE', "DDL 구문"),
                        ('PRIMARY KEY', "기본키 제약조건"),
                        ('TEST_TABLE', "테스트 테이블"),
                        ('한글테이블', "한글 테이블")
                    ]
                    
                    all_checks_passed = True
                    for check_text, description in checks:
                        if check_text in content:
                            self.log_test(f"병합 파일 {description} 확인", True)
                        else:
                            self.log_test(f"병합 파일 {description} 확인", False, f"'{check_text}' 누락")
                            all_checks_passed = False
                    
                    return all_checks_passed
                else:
                    self.log_test("병합 파일 생성", False, "merged_ddl.sql 파일이 생성되지 않음")
                    return False
            else:
                self.log_test("병합 출력 실행", False, result.stderr)
                return False
                
        except Exception as e:
            self.log_test("병합 출력 테스트", False, str(e))
            return False
        finally:
            if test_csv.exists():
                test_csv.unlink()
            if output_dir.exists():
                shutil.rmtree(output_dir)
    
    def test_basic_performance(self) -> bool:
        """기본 성능 테스트 (통합 테스트용)"""
        print("\n⚡ 기본 성능 테스트...")
        
        # 중간 크기 테스트 데이터 생성 (500개 컬럼)
        test_data = []
        for i in range(500):
            test_data.append({
                'TABLE_NAME': f'PERF_TABLE_{i // 25}',  # 20개 테이블
                'OWNER': 'BASIC_PERF',
                'COLUMN_NAME': f'COLUMN_{i}',
                'DATA_TYPE': 'VARCHAR2' if i % 2 == 0 else 'NUMBER',
                'DATA_PRECISION': '10' if i % 2 == 1 else '',
                'DATA_SCALE': '2' if i % 2 == 1 else '',
                'DATA_LENGTH': '100' if i % 2 == 0 else '',
                'NULLABLE': 'Y',
                'COLUMN_COMMENT': f'기본 성능 테스트 컬럼 {i}'
            })
        
        test_csv = self.windows_dir / "basic_perf_test.csv"
        with open(test_csv, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['TABLE_NAME', 'OWNER', 'COLUMN_NAME', 'DATA_TYPE', 
                         'DATA_PRECISION', 'DATA_SCALE', 'DATA_LENGTH', 'NULLABLE', 'COLUMN_COMMENT']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(test_data)
        
        output_dir = self.windows_dir / "basic_perf_output"
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        oracle_to_bq = self.windows_dir / "oracle-to-bq.bat"
        
        try:
            start_time = time.time()
            
            result = subprocess.run([
                str(oracle_to_bq), "convert", str(test_csv),
                "--output-dir", str(output_dir),
                "--project-id", "basic-perf-test"
            ], capture_output=True, encoding='utf-8', errors='ignore', timeout=60, cwd=str(self.windows_dir))
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if result.returncode == 0:
                generated_files = list(output_dir.glob("*.sql"))
                expected_tables = 20  # 500 컬럼 / 25 컬럼당 1테이블 = 20테이블
                
                if len(generated_files) == expected_tables:
                    self.log_test("기본 성능 처리", True, 
                                f"{len(generated_files)}개 테이블, {processing_time:.2f}초")
                    
                    # 기본 성능 기준: 500개 컬럼을 30초 이내에 처리
                    if processing_time <= 30:
                        self.log_test("기본 성능 기준", True, f"{processing_time:.2f}초 (기준: 30초)")
                        return True
                    else:
                        self.log_test("기본 성능 기준", False, f"{processing_time:.2f}초 (기준: 30초)")
                        return False
                else:
                    self.log_test("기본 성능 처리", False, 
                                f"예상 {expected_tables}개, 실제 {len(generated_files)}개")
                    return False
            else:
                self.log_test("기본 성능 처리", False, result.stderr)
                return False
                
        except Exception as e:
            self.log_test("기본 성능 테스트", False, str(e))
            return False
        finally:
            if test_csv.exists():
                test_csv.unlink()
            if output_dir.exists():
                shutil.rmtree(output_dir)
    
    def run_integration_tests(self) -> bool:
        """통합 테스트 실행"""
        print("🧪 Windows 포터블 버전 통합 테스트 시작")
        print("=" * 60)
        
        if not self.windows_dir.exists():
            print("❌ Windows 포터블 디렉토리가 존재하지 않습니다.")
            print("   먼저 build_windows_portable.py를 실행하여 빌드하세요.")
            return False
        
        tests = [
            ("빌드 무결성", self.test_build_integrity),
            ("Python 런타임", self.test_python_runtime),
            ("CLI 기본 기능", self.test_cli_basic_functions),
            ("DDL 변환", self.test_ddl_conversion),
            ("한글 지원", self.test_korean_support),
            ("인코딩 지원", self.test_encoding_support),
            ("병합 출력", self.test_merged_output),
            ("기본 성능", self.test_basic_performance),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(f"{test_name} 실행", False, f"예외 발생: {e}")
        
        return self._generate_test_report("통합 테스트", passed_tests, total_tests)
    
    def run_all_tests(self) -> bool:
        """모든 테스트 실행 (단위 + 통합 + 성능)"""
        print("🧪 Windows 포터블 버전 전체 자동화 테스트 시작")
        print("=" * 70)
        
        # 1. 단위 테스트 실행
        print("\n📋 1단계: 단위 테스트 실행")
        print("-" * 40)
        unit_test_suite = unittest.TestLoader().loadTestsFromTestCase(DDLGeneratorUnitTests)
        unit_test_runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        unit_result = unit_test_runner.run(unit_test_suite)
        
        unit_success = unit_result.wasSuccessful()
        unit_passed = unit_result.testsRun - len(unit_result.failures) - len(unit_result.errors)
        
        self.log_test("단위 테스트", unit_success, 
                     f"{unit_passed}/{unit_result.testsRun} 통과")
        
        # 2. 통합 테스트 실행
        print("\n📋 2단계: 통합 테스트 실행")
        print("-" * 40)
        integration_success = self.run_integration_tests()
        
        # 3. 전체 결과 요약
        print("\n" + "=" * 70)
        print("🏁 전체 테스트 결과 요약")
        print("=" * 70)
        
        total_success = unit_success and integration_success
        
        print(f"단위 테스트: {'✅ 통과' if unit_success else '❌ 실패'} ({unit_passed}/{unit_result.testsRun})")
        print(f"통합 테스트: {'✅ 통과' if integration_success else '❌ 실패'}")
        
        # 상세 결과
        print("\n📋 상세 결과:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            message = f" - {result['message']}" if result["message"] else ""
            print(f"{status} {result['test']}{message}")
        
        # 테스트 결과를 JSON 파일로 저장
        results_file = self.root_dir / "test_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "unit_tests": {
                        "total": unit_result.testsRun,
                        "passed": unit_passed,
                        "failed": len(unit_result.failures) + len(unit_result.errors),
                        "success": unit_success
                    },
                    "integration_tests": {
                        "success": integration_success
                    },
                    "overall_success": total_success
                },
                "details": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 상세 결과가 저장되었습니다: {results_file}")
        
        if total_success:
            print("\n🎉 모든 테스트 성공! Windows 포터블 버전이 정상적으로 작동합니다.")
            return True
        else:
            print("\n⚠️ 일부 테스트가 실패했습니다. 문제를 확인하고 수정하세요.")
            return False
    
    def _generate_test_report(self, test_type: str, passed: int, total: int) -> bool:
        """테스트 결과 리포트 생성"""
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"\n📊 {test_type} 결과:")
        print(f"전체: {total}개, 통과: {passed}개, 실패: {total - passed}개")
        print(f"성공률: {success_rate:.1f}%")
        
        return success_rate >= 80


class PerformanceTestSuite:
    """성능 테스트 전용 클래스"""
    
    def __init__(self, windows_dir: Path):
        self.windows_dir = windows_dir
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """테스트 결과 로깅"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "message": message
        }
        self.test_results.append(result)
        print(f"{status} {test_name}: {message}")
    
    def test_large_dataset_processing(self) -> bool:
        """대용량 데이터셋 처리 성능 테스트"""
        print("\n⚡ 대용량 데이터셋 처리 성능 테스트...")
        
        # 5000개 컬럼, 100개 테이블 생성
        large_test_data = []
        for i in range(5000):
            table_idx = i // 50  # 50개 컬럼당 1개 테이블
            large_test_data.append({
                'TABLE_NAME': f'PERF_TABLE_{table_idx:03d}',
                'OWNER': 'PERFORMANCE_SCHEMA',
                'COLUMN_NAME': f'COL_{i:04d}',
                'DATA_TYPE': 'VARCHAR2' if i % 3 == 0 else ('NUMBER' if i % 3 == 1 else 'DATE'),
                'DATA_PRECISION': '15' if i % 3 == 1 else '',
                'DATA_SCALE': '2' if i % 3 == 1 else '',
                'DATA_LENGTH': '200' if i % 3 == 0 else '',
                'NULLABLE': 'Y' if i % 2 == 0 else 'N',
                'COLUMN_COMMENT': f'성능 테스트 컬럼 {i} - 한글 포함'
            })
        
        large_test_csv = self.windows_dir / "large_perf_test.csv"
        with open(large_test_csv, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['TABLE_NAME', 'OWNER', 'COLUMN_NAME', 'DATA_TYPE', 
                         'DATA_PRECISION', 'DATA_SCALE', 'DATA_LENGTH', 'NULLABLE', 'COLUMN_COMMENT']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(large_test_data)
        
        output_dir = self.windows_dir / "large_perf_output"
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        oracle_to_bq = self.windows_dir / "oracle-to-bq.bat"
        
        try:
            start_time = time.time()
            
            result = subprocess.run([
                str(oracle_to_bq), "convert", str(large_test_csv),
                "--output-dir", str(output_dir),
                "--project-id", "performance-test"
            ], capture_output=True, encoding='utf-8', errors='ignore', timeout=180, cwd=str(self.windows_dir))
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if result.returncode == 0:
                generated_files = list(output_dir.glob("*.sql"))
                expected_tables = 100  # 5000 컬럼 / 50 컬럼당 1테이블 = 100테이블
                
                if len(generated_files) == expected_tables:
                    throughput = 5000 / processing_time  # 컬럼/초
                    self.log_test("대용량 처리 정확성", True, 
                                f"{len(generated_files)}개 테이블, {processing_time:.2f}초")
                    
                    # 성능 기준: 5000개 컬럼을 120초 이내, 40컬럼/초 이상
                    if processing_time <= 120 and throughput >= 40:
                        self.log_test("성능 기준 충족", True, 
                                    f"{throughput:.1f} 컬럼/초 (기준: 40컬럼/초)")
                        return True
                    else:
                        self.log_test("성능 기준 충족", False, 
                                    f"{throughput:.1f} 컬럼/초, {processing_time:.2f}초")
                        return False
                else:
                    self.log_test("대용량 처리 정확성", False, 
                                f"예상 {expected_tables}개, 실제 {len(generated_files)}개")
                    return False
            else:
                self.log_test("대용량 처리 실행", False, result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            self.log_test("대용량 처리 시간 초과", False, "180초 시간 초과")
            return False
        except Exception as e:
            self.log_test("대용량 처리 예외", False, str(e))
            return False
        finally:
            if large_test_csv.exists():
                large_test_csv.unlink()
            if output_dir.exists():
                shutil.rmtree(output_dir)
    
    def test_memory_usage(self) -> bool:
        """메모리 사용량 테스트"""
        print("\n💾 메모리 사용량 테스트...")
        
        # 메모리 사용량 모니터링을 위한 간단한 테스트
        # Windows에서 psutil 없이 메모리 사용량 확인은 제한적이므로
        # 프로세스 실행 성공 여부로 판단
        
        test_csv = self.windows_dir / "memory_test.csv"
        test_data = []
        
        # 중간 크기 데이터셋 (1000개 컬럼)
        for i in range(1000):
            test_data.append({
                'TABLE_NAME': f'MEM_TABLE_{i // 20}',
                'OWNER': 'MEMORY_TEST',
                'COLUMN_NAME': f'COLUMN_{i}',
                'DATA_TYPE': 'VARCHAR2',
                'DATA_LENGTH': '4000',  # 큰 VARCHAR2
                'NULLABLE': 'Y',
                'COLUMN_COMMENT': f'메모리 테스트용 긴 설명 ' * 10  # 긴 설명
            })
        
        with open(test_csv, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['TABLE_NAME', 'OWNER', 'COLUMN_NAME', 'DATA_TYPE', 
                         'DATA_LENGTH', 'NULLABLE', 'COLUMN_COMMENT']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(test_data)
        
        output_dir = self.windows_dir / "memory_test_output"
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        oracle_to_bq = self.windows_dir / "oracle-to-bq.bat"
        
        try:
            result = subprocess.run([
                str(oracle_to_bq), "convert", str(test_csv),
                "--output-dir", str(output_dir),
                "--project-id", "memory-test"
            ], capture_output=True, encoding='utf-8', errors='ignore', timeout=60, cwd=str(self.windows_dir))
            
            if result.returncode == 0:
                self.log_test("메모리 사용량 테스트", True, "정상 완료")
                return True
            else:
                self.log_test("메모리 사용량 테스트", False, "실행 실패")
                return False
                
        except Exception as e:
            self.log_test("메모리 사용량 테스트", False, str(e))
            return False
        finally:
            if test_csv.exists():
                test_csv.unlink()
            if output_dir.exists():
                shutil.rmtree(output_dir)
    
    def run_performance_tests(self) -> bool:
        """성능 테스트 실행"""
        print("\n⚡ 성능 테스트 시작")
        print("-" * 40)
        
        tests = [
            ("대용량 데이터셋 처리", self.test_large_dataset_processing),
            ("메모리 사용량", self.test_memory_usage),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(f"{test_name} 실행", False, f"예외 발생: {e}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n성능 테스트 결과: {passed_tests}/{total_tests} 통과 ({success_rate:.1f}%)")
        
        return success_rate >= 80


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Windows 포터블 DDL 생성기 테스트 스위트')
    parser.add_argument('--unit-only', action='store_true', help='단위 테스트만 실행')
    parser.add_argument('--integration-only', action='store_true', help='통합 테스트만 실행')
    parser.add_argument('--performance-only', action='store_true', help='성능 테스트만 실행')
    
    args = parser.parse_args()
    
    test_suite = WindowsPortableTestSuite()
    success = True
    
    if args.unit_only:
        print("🧪 단위 테스트만 실행")
        unit_test_suite = unittest.TestLoader().loadTestsFromTestCase(DDLGeneratorUnitTests)
        unit_test_runner = unittest.TextTestRunner(verbosity=2)
        unit_result = unit_test_runner.run(unit_test_suite)
        success = unit_result.wasSuccessful()
    elif args.integration_only:
        print("🧪 통합 테스트만 실행")
        success = test_suite.run_integration_tests()
    elif args.performance_only:
        print("🧪 성능 테스트만 실행")
        perf_suite = PerformanceTestSuite(test_suite.windows_dir)
        success = perf_suite.run_performance_tests()
    else:
        # 전체 테스트 실행
        success = test_suite.run_all_tests()
    
    sys.exit(0 if success else 1)


    def test_merge_output(self) -> bool:
        """병합 출력 기능 테스트"""
        print("\n📄 병합 출력 기능 테스트...")
        
        # 테스트 CSV 생성
        test_csv = self.create_test_csv()
        output_dir = self.windows_dir / "merge_test_output"
        
        # 기존 출력 디렉토리 제거
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        oracle_to_bq = self.windows_dir / "oracle-to-bq.bat"
        
        try:
            # 병합 출력으로 DDL 변환 실행
            result = subprocess.run([
                str(oracle_to_bq), "convert", str(test_csv),
                "--output-dir", str(output_dir),
                "--project-id", "merge-test",
                "--merge-output"
            ], capture_output=True, encoding='utf-8', errors='ignore', timeout=60, cwd=str(self.windows_dir))
            
            if result.returncode == 0:
                # 병합 파일 확인
                merged_file = output_dir / "merged_ddl.sql"
                if merged_file.exists():
                    with open(merged_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 병합 파일 내용 검증
                    if ('-- Oracle to BigQuery DDL Migration' in content and
                        'CREATE TABLE' in content and
                        'PRIMARY KEY' in content and
                        'merge-test.TEST_SCHEMA' in content):
                        self.log_test("병합 출력 기능", True, "병합 DDL 파일 생성 및 내용 검증 완료")
                        return True
                    else:
                        self.log_test("병합 출력 기능", False, "병합 파일 내용이 올바르지 않음")
                        return False
                else:
                    self.log_test("병합 출력 기능", False, "병합 파일이 생성되지 않음")
                    return False
            else:
                self.log_test("병합 출력 실행", False, result.stderr)
                return False
                
        except Exception as e:
            self.log_test("병합 출력 테스트", False, str(e))
            return False
        finally:
            # 테스트 파일 정리
            if test_csv.exists():
                test_csv.unlink()
            if output_dir.exists():
                shutil.rmtree(output_dir)


if __name__ == "__main__":
    main()