@echo off
REM Oracle to BigQuery Migration Tool - Windows 포터블 버전 빌드 스크립트

setlocal enabledelayedexpansion

echo.
echo 🏗️ Oracle to BigQuery Migration Tool - Windows 포터블 버전 빌드
echo ======================================================================
echo.

REM Python 버전 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo.
    echo 해결 방법:
    echo 1. Python 3.8 이상을 설치하세요: https://www.python.org/downloads/
    echo 2. 설치 후 시스템 PATH에 Python이 추가되었는지 확인하세요
    echo 3. 명령 프롬프트를 다시 시작하고 재시도하세요
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python 버전: !PYTHON_VERSION!

REM 인터넷 연결 확인 (선택적)
echo.
echo 📡 인터넷 연결 확인 중...
ping -n 1 github.com >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ 인터넷 연결 정상 - Python 런타임 다운로드 가능
) else (
    echo ⚠️ 인터넷 연결 없음 - 기존 다운로드 파일이 있어야 합니다
)

REM 빌드 실행
echo.
echo 🚀 빌드 시작...
echo.
python build_windows_portable.py

if %errorlevel% equ 0 (
    echo.
    echo 🎉 빌드 완료!
    echo.
    echo 📁 생성된 포터블 버전:
    echo   - windows/     : Windows x64용 완전 독립 포터블 버전
    echo.
    echo 🚀 사용법:
    echo   cd windows ^&^& oracle-to-bq.bat --help
    echo   cd windows ^&^& oracle-to-bq.bat convert schema.csv --output-dir output --project-id my-project
    echo.
    echo 🧪 독립성 검증:
    echo   cd windows ^&^& verify_standalone.bat
    echo   cd windows ^&^& 빠른테스트.bat
    echo.
    echo ✨ 주요 특징:
    echo   - 완전 독립: 시스템 Python 불필요
    echo   - 오프라인: 인터넷 연결 불필요
    echo   - 한글 지원: 테이블명/컬럼명 백틱 처리
    echo   - 경량화: pandas 제거로 크기 최적화
    echo   - Windows 최적화: 배치 파일 및 UTF-8 지원
) else (
    echo.
    echo ❌ 빌드 실패!
    echo.
    echo 문제 해결:
    echo 1. Python 3.8 이상이 설치되어 있는지 확인
    echo 2. 인터넷 연결이 가능한지 확인 (Python 런타임 다운로드용)
    echo 3. 디스크 공간이 충분한지 확인 (약 150MB 필요)
    echo 4. 바이러스 백신이 파일 생성을 차단하지 않는지 확인
    echo.
)

echo.
pause