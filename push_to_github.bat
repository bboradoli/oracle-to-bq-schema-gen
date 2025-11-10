@echo off
chcp 65001 > nul
echo ============================================
echo GitHub 푸시 스크립트
echo ============================================
echo.

REM Git 설치 확인
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Git이 설치되어 있지 않습니다.
    echo setup_git.bat를 먼저 실행하세요.
    pause
    exit /b 1
)

REM 변경사항 확인
echo 📋 변경사항 확인 중...
git status
echo.

REM 사용자에게 계속 진행할지 확인
set /p CONTINUE="변경사항을 커밋하고 푸시하시겠습니까? (Y/N): "
if /i not "%CONTINUE%"=="Y" (
    echo 취소되었습니다.
    pause
    exit /b 0
)
echo.

REM 커밋 메시지 입력
set /p COMMIT_MSG="커밋 메시지를 입력하세요 (기본: Update files): "
if "%COMMIT_MSG%"=="" set COMMIT_MSG=Update files
echo.

REM 파일 추가
echo 📝 파일을 스테이징합니다...
git add .
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 파일 스테이징 실패
    pause
    exit /b 1
)
echo ✅ 파일 스테이징 완료
echo.

REM 커밋
echo 💾 커밋을 생성합니다...
git commit -m "%COMMIT_MSG%"
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ 커밋할 변경사항이 없거나 커밋 실패
    echo.
    set /p FORCE_PUSH="그래도 푸시하시겠습니까? (Y/N): "
    if /i not "%FORCE_PUSH%"=="Y" (
        pause
        exit /b 0
    )
) else (
    echo ✅ 커밋 생성 완료
)
echo.

REM 푸시
echo 🚀 GitHub에 푸시합니다...
echo.
echo 인증 정보를 입력하세요:
echo   Username: bboradoli
echo   Password: [Personal Access Token]
echo.
git push -u origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo ✅ GitHub 푸시 완료!
    echo ============================================
    echo.
    echo 저장소 확인: https://github.com/bboradoli/oracle-to-bq-schema-gen
    echo.
) else (
    echo.
    echo ============================================
    echo ❌ GitHub 푸시 실패
    echo ============================================
    echo.
    echo 문제 해결:
    echo 1. Personal Access Token이 올바른지 확인
    echo 2. 인터넷 연결 확인
    echo 3. 저장소 권한 확인
    echo.
    echo 자세한 내용은 GIT_SETUP_GUIDE.md를 참조하세요.
    echo.
)

pause
