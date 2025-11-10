@echo off
chcp 65001 > nul
echo ============================================
echo Git 사용자 정보 및 자격증명 설정
echo ============================================
echo.

REM Git 설치 확인
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Git이 설치되어 있지 않습니다.
    pause
    exit /b 1
)

echo ✅ Git이 설치되어 있습니다.
git --version
echo.

echo ============================================
echo 1단계: Git 사용자 정보 설정
echo ============================================
echo.

REM 사용자 이름 입력
set /p GIT_NAME="GitHub 사용자 이름을 입력하세요 (예: bboradoli): "
if "%GIT_NAME%"=="" (
    echo ❌ 사용자 이름을 입력해야 합니다.
    pause
    exit /b 1
)

REM 이메일 입력
set /p GIT_EMAIL="GitHub 이메일을 입력하세요 (예: your@email.com): "
if "%GIT_EMAIL%"=="" (
    echo ❌ 이메일을 입력해야 합니다.
    pause
    exit /b 1
)

echo.
echo 📝 Git 사용자 정보를 설정합니다...
git config --global user.name "%GIT_NAME%"
git config --global user.email "%GIT_EMAIL%"

if %ERRORLEVEL% EQU 0 (
    echo ✅ 사용자 정보 설정 완료
    echo.
    echo 설정된 정보:
    echo   이름: %GIT_NAME%
    echo   이메일: %GIT_EMAIL%
) else (
    echo ❌ 사용자 정보 설정 실패
    pause
    exit /b 1
)
echo.

echo ============================================
echo 2단계: Git 자격증명 영구 저장 설정
echo ============================================
echo.

echo 🔐 자격증명 저장 방식을 설정합니다...
echo.
echo 선택 가능한 방식:
echo   1. Windows Credential Manager (권장) - Windows 자격증명 관리자에 안전하게 저장
echo   2. Store (파일) - 홈 디렉토리에 평문으로 저장 (간단하지만 덜 안전)
echo   3. Cache (임시) - 일정 시간 동안만 메모리에 저장
echo.

set /p CRED_CHOICE="선택하세요 (1/2/3, 기본: 1): "
if "%CRED_CHOICE%"=="" set CRED_CHOICE=1

if "%CRED_CHOICE%"=="1" (
    echo.
    echo 📦 Windows Credential Manager를 사용합니다...
    git config --global credential.helper manager-core
    if %ERRORLEVEL% EQU 0 (
        echo ✅ Credential Manager 설정 완료
        echo    첫 푸시 시 인증 정보를 입력하면 Windows에 안전하게 저장됩니다.
    ) else (
        echo ⚠️ manager-core 실패, wincred로 재시도...
        git config --global credential.helper wincred
        if %ERRORLEVEL% EQU 0 (
            echo ✅ Windows Credential 설정 완료
        ) else (
            echo ❌ Credential 설정 실패
        )
    )
) else if "%CRED_CHOICE%"=="2" (
    echo.
    echo 📄 파일 저장 방식을 사용합니다...
    git config --global credential.helper store
    if %ERRORLEVEL% EQU 0 (
        echo ✅ Store 설정 완료
        echo    인증 정보가 ~/.git-credentials 파일에 저장됩니다.
        echo    ⚠️ 주의: 평문으로 저장되므로 보안에 주의하세요.
    ) else (
        echo ❌ Store 설정 실패
    )
) else if "%CRED_CHOICE%"=="3" (
    echo.
    echo ⏱️ 캐시 방식을 사용합니다...
    git config --global credential.helper cache
    if %ERRORLEVEL% EQU 0 (
        echo ✅ Cache 설정 완료
        echo    인증 정보가 15분간 메모리에 저장됩니다.
    ) else (
        echo ❌ Cache 설정 실패
    )
) else (
    echo ❌ 잘못된 선택입니다.
    pause
    exit /b 1
)
echo.

echo ============================================
echo 3단계: 추가 Git 설정 (선택사항)
echo ============================================
echo.

REM 줄바꿈 문자 자동 변환 설정
echo 📝 줄바꿈 문자 자동 변환 설정...
git config --global core.autocrlf true
echo ✅ Windows 스타일 줄바꿈(CRLF) 자동 변환 활성화
echo.

REM 기본 브랜치 이름 설정
echo 🌿 기본 브랜치 이름을 'main'으로 설정...
git config --global init.defaultBranch main
echo ✅ 기본 브랜치 설정 완료
echo.

REM 한글 파일명 표시 설정
echo 🔤 한글 파일명 표시 설정...
git config --global core.quotepath false
echo ✅ 한글 파일명 정상 표시 설정 완료
echo.

echo ============================================
echo 현재 Git 설정 확인
echo ============================================
echo.
git config --global --list | findstr "user\|credential\|core.autocrlf\|init.defaultBranch\|core.quotepath"
echo.

echo ============================================
echo ✅ Git 설정 완료!
echo ============================================
echo.
echo 다음 단계:
echo   1. setup_git.bat 실행 (Git 저장소 초기화)
echo   2. push_to_github.bat 실행 (GitHub에 푸시)
echo.
echo 첫 푸시 시 인증 정보 입력:
echo   Username: %GIT_NAME%
echo   Password: [Personal Access Token]
echo.
echo ⚠️ Personal Access Token 생성 방법:
echo   1. https://github.com/settings/tokens
echo   2. Generate new token (classic)
echo   3. repo 권한 선택
echo   4. 생성된 토큰 복사
echo.
echo 인증 정보는 자동으로 저장되어 다음부터는 입력하지 않아도 됩니다!
echo ============================================
echo.
pause
