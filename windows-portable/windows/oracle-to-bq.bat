@echo off
REM Oracle to BigQuery Migration Tool - Portable Windows Launcher

REM 스크립트 디렉토리 확인
set SCRIPT_DIR=%~dp0
set PYTHON_EXE=%SCRIPT_DIR%python\python.exe
set SRC_DIR=%SCRIPT_DIR%src

REM Python 실행 파일 확인
if not exist "%PYTHON_EXE%" (
    echo ❌ Python 런타임을 찾을 수 없습니다: %PYTHON_EXE%
    echo.
    echo 해결 방법:
    echo 1. build_windows_portable.py를 실행하여 포터블 버전을 다시 빌드하세요
    echo 2. python 폴더가 올바른 위치에 있는지 확인하세요
    pause
    exit /b 1
)

REM 완전 독립 환경 설정
set PYTHONPATH=%SRC_DIR%
set PYTHONNOUSERSITE=1
set PYTHONIOENCODING=utf-8

REM Python 모듈 실행 (간단한 CLI 사용)
if exist "%SRC_DIR%\oracle_to_bq_cli.py" (
    "%PYTHON_EXE%" "%SRC_DIR%\oracle_to_bq_cli.py" %*
) else (
    echo ❌ CLI 스크립트를 찾을 수 없습니다: %SRC_DIR%\oracle_to_bq_cli.py
    echo.
    echo 해결 방법:
    echo 1. src 폴더가 올바른 위치에 있는지 확인하세요
    echo 2. build_windows_portable.py를 실행하여 포터블 버전을 다시 빌드하세요
    pause
    exit /b 1
)
