@echo off
chcp 65001 > nul
echo ============================================
echo Git 빠른 설정 및 GitHub 푸시
echo ============================================
echo.

REM Git 설치 확인
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Git이 설치되어 있지 않습니다.
    echo https://git-scm.com/download/win 에서 Git을 설치하세요.
    pause
    exit /b 1
)

echo ✅ Git 설치 확인 완료
echo.

REM 사용자 정보 확인
git config --global user.name >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ Git 사용자 정보가 설정되어 있지 않습니다.
    echo.
    set /p GIT_NAME="GitHub 사용자 이름 (예: bboradoli): "
    set /p GIT_EMAIL="GitHub 이메일 (예: your@email.com): "
    
    git config --global user.name "%GIT_NAME%"
    git config --global user.email "%GIT_EMAIL%"
    
    echo ✅ 사용자 정보 설정 완료
    echo.
) else (
    echo ✅ Git 사용자 정보 확인 완료
    echo   이름: 
    git config --global user.name
    echo   이메일: 
    git config --global user.email
    echo.
)

REM 자격증명 저장 설정
git config --global credential.helper >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 🔐 자격증명 영구 저장 설정...
    git config --global credential.helper manager-core
    if %ERRORLEVEL% NEQ 0 (
        git config --global credential.helper wincred
    )
    echo ✅ 자격증명 저장 설정 완료
    echo.
) else (
    echo ✅ 자격증명 저장 설정 확인 완료
    echo.
)

REM 기본 설정
git config --global core.autocrlf true
git config --global init.defaultBranch main
git config --global core.quotepath false

echo ============================================
echo Git 저장소 설정
echo ============================================
echo.

REM Git 저장소 초기화
if not exist .git (
    echo 📦 Git 저장소 초기화...
    git init
    echo ✅ 초기화 완료
    echo.
)

REM 원격 저장소 확인 및 추가
git remote -v | findstr origin >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 🔗 원격 저장소 추가...
    git remote add origin https://github.com/bboradoli/oracle-to-bq-schema-gen.git
    echo ✅ 원격 저장소 추가 완료
    echo.
) else (
    echo ✅ 원격 저장소 확인 완료
    echo.
)

REM 브랜치 설정
git branch -M main

echo ============================================
echo 파일 커밋 및 푸시
echo ============================================
echo.

REM 파일 추가
echo 📝 파일 스테이징...
git add .
echo ✅ 스테이징 완료
echo.

REM 커밋
echo 💾 커밋 생성...
git commit -m "Initial commit: Oracle to BigQuery DDL Generator with partition auto-detection"
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ 커밋할 변경사항이 없습니다.
    echo.
) else (
    echo ✅ 커밋 완료
    echo.
)

REM 푸시
echo ============================================
echo 🚀 GitHub에 푸시합니다...
echo ============================================
echo.
echo 인증 정보를 입력하세요:
echo   Username: GitHub 사용자명 (예: bboradoli)
echo   Password: Personal Access Token (PAT)
echo.
echo ⚠️ PAT 생성: https://github.com/settings/tokens
echo    - Generate new token (classic)
echo    - repo 권한 선택
echo    - 생성된 토큰 복사
echo.
echo 인증 정보는 자동으로 저장되어 다음부터는 입력 불필요!
echo.

git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo ✅ GitHub 푸시 성공!
    echo ============================================
    echo.
    echo 저장소 확인: https://github.com/bboradoli/oracle-to-bq-schema-gen
    echo.
    echo 🎉 모든 설정이 완료되었습니다!
    echo    다음부터는 인증 정보 입력 없이 푸시할 수 있습니다.
    echo.
) else (
    echo.
    echo ============================================
    echo ❌ GitHub 푸시 실패
    echo ============================================
    echo.
    echo 문제 해결:
    echo   1. Personal Access Token이 올바른지 확인
    echo   2. 토큰에 repo 권한이 있는지 확인
    echo   3. 인터넷 연결 확인
    echo.
    echo 다시 시도하려면 이 스크립트를 재실행하세요.
    echo.
)

pause
