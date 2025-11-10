@echo off
chcp 65001 > nul
echo ============================================
echo GitHub 저장소 설정 스크립트
echo ============================================
echo.

REM Git 설치 확인
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Git이 설치되어 있지 않습니다.
    echo.
    echo Git 설치 방법:
    echo 1. https://git-scm.com/download/win 에서 Git 다운로드
    echo 2. 설치 후 이 스크립트를 다시 실행하세요
    echo.
    pause
    exit /b 1
)

echo ✅ Git이 설치되어 있습니다.
git --version
echo.

REM Git 저장소 초기화 확인
if exist .git (
    echo ✅ Git 저장소가 이미 초기화되어 있습니다.
) else (
    echo 📦 Git 저장소를 초기화합니다...
    git init
    if %ERRORLEVEL% EQU 0 (
        echo ✅ Git 저장소 초기화 완료
    ) else (
        echo ❌ Git 저장소 초기화 실패
        pause
        exit /b 1
    )
)
echo.

REM 원격 저장소 확인
git remote -v | findstr origin >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ 원격 저장소가 이미 설정되어 있습니다.
    git remote -v
) else (
    echo 🔗 원격 저장소를 추가합니다...
    git remote add origin https://github.com/bboradoli/oracle-to-bq-schema-gen.git
    if %ERRORLEVEL% EQU 0 (
        echo ✅ 원격 저장소 추가 완료
        git remote -v
    ) else (
        echo ❌ 원격 저장소 추가 실패
        pause
        exit /b 1
    )
)
echo.

REM 기본 브랜치 설정
echo 🌿 기본 브랜치를 main으로 설정합니다...
git branch -M main
echo.

REM 파일 추가
echo 📝 파일을 스테이징합니다...
git add .
if %ERRORLEVEL% EQU 0 (
    echo ✅ 파일 스테이징 완료
) else (
    echo ❌ 파일 스테이징 실패
    pause
    exit /b 1
)
echo.

REM 스테이징된 파일 확인
echo 📋 스테이징된 파일 목록:
git status --short
echo.

REM 커밋
echo 💾 커밋을 생성합니다...
git commit -m "Initial commit: Oracle to BigQuery DDL Generator with partition auto-detection"
if %ERRORLEVEL% EQU 0 (
    echo ✅ 커밋 생성 완료
) else (
    echo ⚠️ 커밋할 변경사항이 없거나 커밋 실패
)
echo.

echo ============================================
echo 다음 단계:
echo ============================================
echo.
echo GitHub에 푸시하려면 다음 명령어를 실행하세요:
echo.
echo   git push -u origin main
echo.
echo 인증 정보 입력:
echo   Username: bboradoli
echo   Password: [Personal Access Token]
echo.
echo Personal Access Token 생성 방법:
echo   1. GitHub 로그인
echo   2. Settings ^> Developer settings ^> Personal access tokens
echo   3. Generate new token (classic)
echo   4. repo 권한 선택
echo   5. 생성된 토큰 복사
echo.
echo 자세한 내용은 GIT_SETUP_GUIDE.md를 참조하세요.
echo ============================================
echo.
pause
