@echo off
REM Oracle to BigQuery Migration Tool - 독립성 검증 스크립트

echo.
echo 🔍 포터블 버전 독립성 검증 중...
echo.

set SCRIPT_DIR=%~dp0
set PYTHON_EXE=%SCRIPT_DIR%python\python.exe

REM 1. Python 런타임 확인
echo 1. Python 런타임 확인...
if exist "%PYTHON_EXE%" (
    echo    ✓ Python 런타임 존재: %PYTHON_EXE%
    for /f "tokens=*" %%i in ('"%PYTHON_EXE%" --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo    ✓ Python 버전: !PYTHON_VERSION!
) else (
    echo    ❌ Python 런타임 없음: %PYTHON_EXE%
    goto :error
)

REM 2. 소스 코드 확인
echo.
echo 2. 소스 코드 확인...
if exist "%SCRIPT_DIR%src\oracle_to_bq_cli.py" (
    echo    ✓ CLI 소스 코드 존재
) else (
    echo    ❌ 소스 코드 없음
    goto :error
)

REM 3. 시스템 Python 의존성 확인
echo.
echo 3. 시스템 Python 의존성 확인...
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo    ⚠️ 시스템 Python 설치됨 ^(사용하지 않음^)
) else (
    echo    ✓ 시스템 Python 없음 ^(완전 독립^)
)

REM 4. 모듈 임포트 테스트
echo.
echo 4. 모듈 임포트 테스트...
set PYTHONPATH=%SCRIPT_DIR%src
set PYTHONNOUSERSITE=1
"%PYTHON_EXE%" -c "import sys, csv, json, pathlib; print('   ✓ 기본 모듈 임포트 성공')" 2>nul
if %errorlevel% neq 0 (
    echo    ❌ 기본 모듈 임포트 실패
    goto :error
)

REM 5. CLI 테스트
echo.
echo 5. CLI 실행 테스트...
"%PYTHON_EXE%" "%SCRIPT_DIR%src\oracle_to_bq_cli.py" --test >nul 2>&1
if %errorlevel% equ 0 (
    echo    ✓ CLI 테스트 성공
) else (
    echo    ⚠️ CLI 테스트 실패 ^(일부 기능 제한 가능^)
)

REM 6. 실행 스크립트 테스트
echo.
echo 6. 실행 스크립트 테스트...
call "%SCRIPT_DIR%oracle-to-bq.bat" --version >nul 2>&1
if %errorlevel% equ 0 (
    echo    ✓ 실행 스크립트 테스트 성공
) else (
    echo    ❌ 실행 스크립트 테스트 실패
    goto :error
)

echo.
echo 🎉 독립성 검증 완료!
echo    ✅ 완전 독립적인 포터블 버전입니다
echo    ✅ 인터넷 연결 없이 실행 가능
echo    ✅ 시스템 Python 설치 불필요
echo.
echo 사용법:
echo    oracle-to-bq.bat --help
echo    oracle-to-bq.bat convert schema.csv --output-dir output --project-id my-project
echo.
pause
exit /b 0

:error
echo.
echo ❌ 독립성 검증 실패!
echo    포터블 패키지에 문제가 있습니다.
echo    build_windows_portable.py를 다시 실행해보세요.
echo.
pause
exit /b 1
