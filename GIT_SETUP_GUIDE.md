# GitHub 저장소 설정 가이드

이 프로젝트를 GitHub에 업로드하는 방법을 안내합니다.

## 📋 사전 준비

### 1. Git 설치 확인

```cmd
git --version
```

**Git이 설치되어 있지 않은 경우:**
- [Git 다운로드](https://git-scm.com/download/win)
- 설치 후 터미널을 재시작

### 2. GitHub 계정 준비

- GitHub 계정이 없다면: [GitHub 가입](https://github.com/join)
- 저장소 URL: `https://github.com/bboradoli/oracle-to-bq-schema-gen.git`

---

## 🚀 GitHub 저장소 연결 및 업로드

### 방법 1: 명령줄 사용 (권장)

```bash
# 1. Git 저장소 초기화
git init

# 2. 원격 저장소 연결
git remote add origin https://github.com/bboradoli/oracle-to-bq-schema-gen.git

# 3. 모든 파일 추가 (.gitignore에 따라 자동 제외)
git add .

# 4. 첫 커밋 생성
git commit -m "Initial commit: Oracle to BigQuery DDL Generator"

# 5. GitHub에 푸시
git push -u origin main
```

**인증 필요 시:**
- Username: GitHub 사용자명
- Password: Personal Access Token (PAT) 사용
  - [PAT 생성 방법](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

---

### 방법 2: GitHub Desktop 사용

1. **GitHub Desktop 설치**
   - [GitHub Desktop 다운로드](https://desktop.github.com/)

2. **저장소 추가**
   - File → Add Local Repository
   - 현재 폴더 선택: `C:\workspaces\adw\portable_schema`

3. **커밋 및 푸시**
   - 변경사항 확인
   - Commit 메시지 입력: "Initial commit"
   - Publish repository 클릭
   - Repository name: `oracle-to-bq-schema-gen`
   - Push origin 클릭

---

### 방법 3: Visual Studio Code 사용

1. **VS Code에서 폴더 열기**
   ```
   code .
   ```

2. **Source Control 패널 열기**
   - 왼쪽 사이드바에서 Source Control 아이콘 클릭 (Ctrl+Shift+G)

3. **저장소 초기화**
   - "Initialize Repository" 클릭

4. **원격 저장소 추가**
   - 터미널 열기 (Ctrl+`)
   ```bash
   git remote add origin https://github.com/bboradoli/oracle-to-bq-schema-gen.git
   ```

5. **커밋 및 푸시**
   - 변경사항 스테이징 (+ 버튼)
   - 커밋 메시지 입력
   - "Commit" 클릭
   - "..." 메뉴 → Push

---

## 📁 업로드될 파일 목록

### ✅ 포함되는 파일

```
.
├── .gitignore                      # Git 제외 설정
├── README.md                       # 프로젝트 메인 가이드
├── ORACLE_EXTRACT_GUIDE.md         # Oracle 추출 가이드
├── oracle_extract_query.sql        # Oracle 추출 쿼리
├── oracle_partition_check.sql      # 파티션 확인 쿼리
├── GIT_SETUP_GUIDE.md             # 이 파일
└── windows-portable/               # Windows 포터블 버전
    ├── README.md
    ├── BUILD.md
    ├── DEVELOPMENT.md
    ├── build_windows.bat
    ├── build_windows_portable.py
    ├── requirements.txt
    ├── test_suite.py
    └── windows/
        ├── config.json
        ├── schema.csv (샘플)
        ├── oracle-to-bq.bat
        ├── verify_standalone.bat
        └── src/
            └── oracle_to_bq_cli.py
```

### ❌ 제외되는 파일 (.gitignore)

```
.kiro/                  # Kiro IDE 설정
__pycache__/            # Python 캐시
*.pyc                   # Python 컴파일 파일
venv/                   # 가상환경
.vscode/                # VS Code 설정
.DS_Store               # macOS 파일
windows-portable/windows/python/    # Python 런타임 (빌드 결과)
windows-portable/windows/output/    # 출력 파일
*.zip                   # 압축 파일
test_*.csv              # 테스트 파일
```

---

## 🔐 인증 설정

### Personal Access Token (PAT) 생성

1. **GitHub 설정 이동**
   - GitHub 로그인
   - Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **새 토큰 생성**
   - "Generate new token (classic)" 클릭
   - Note: `oracle-to-bq-schema-gen`
   - Expiration: 90 days (또는 원하는 기간)
   - Scopes 선택:
     - ✅ `repo` (전체 저장소 접근)
   - "Generate token" 클릭

3. **토큰 복사 및 저장**
   - 생성된 토큰을 안전한 곳에 저장 (다시 볼 수 없음)

4. **Git 인증 시 사용**
   ```bash
   Username: bboradoli
   Password: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (PAT)
   ```

---

## 🔄 이후 업데이트 방법

### 파일 수정 후 GitHub에 반영

```bash
# 1. 변경사항 확인
git status

# 2. 변경된 파일 추가
git add .

# 3. 커밋
git commit -m "Update: 변경 내용 설명"

# 4. 푸시
git push
```

### 특정 파일만 업데이트

```bash
# 특정 파일만 추가
git add README.md oracle_extract_query.sql

# 커밋 및 푸시
git commit -m "Update README and query"
git push
```

---

## 📝 커밋 메시지 가이드

### 좋은 커밋 메시지 예시

```bash
# 새 기능 추가
git commit -m "feat: Add partition auto-detection feature"

# 버그 수정
git commit -m "fix: Fix encoding issue in CSV export"

# 문서 업데이트
git commit -m "docs: Update Oracle extraction guide"

# 코드 개선
git commit -m "refactor: Improve type conversion logic"

# 테스트 추가
git commit -m "test: Add unit tests for DDL generation"
```

### 커밋 메시지 규칙

- **feat**: 새로운 기능 추가
- **fix**: 버그 수정
- **docs**: 문서 수정
- **style**: 코드 포맷팅 (기능 변경 없음)
- **refactor**: 코드 리팩토링
- **test**: 테스트 추가/수정
- **chore**: 빌드 설정, 패키지 관리 등

---

## 🌿 브랜치 관리 (선택사항)

### 기능 개발 시 브랜치 사용

```bash
# 새 브랜치 생성 및 이동
git checkout -b feature/new-feature

# 작업 후 커밋
git add .
git commit -m "feat: Add new feature"

# GitHub에 브랜치 푸시
git push -u origin feature/new-feature

# main 브랜치로 돌아가기
git checkout main

# 브랜치 병합
git merge feature/new-feature
```

---

## 🔍 문제 해결

### 1. "fatal: remote origin already exists"

```bash
# 기존 원격 저장소 제거
git remote remove origin

# 다시 추가
git remote add origin https://github.com/bboradoli/oracle-to-bq-schema-gen.git
```

### 2. "Permission denied (publickey)"

```bash
# HTTPS 사용 (SSH 대신)
git remote set-url origin https://github.com/bboradoli/oracle-to-bq-schema-gen.git
```

### 3. "Updates were rejected"

```bash
# 원격 저장소 변경사항 먼저 가져오기
git pull origin main --rebase

# 다시 푸시
git push
```

### 4. ".gitignore가 작동하지 않음"

```bash
# Git 캐시 제거
git rm -r --cached .

# 다시 추가
git add .
git commit -m "fix: Update .gitignore"
git push
```

---

## 📚 추가 리소스

- [Git 공식 문서](https://git-scm.com/doc)
- [GitHub 가이드](https://guides.github.com/)
- [Git 치트시트](https://education.github.com/git-cheat-sheet-education.pdf)
- [Markdown 가이드](https://www.markdownguide.org/)

---

## ✅ 체크리스트

업로드 전 확인사항:

- [ ] Git 설치 완료
- [ ] GitHub 계정 준비
- [ ] .gitignore 파일 확인
- [ ] 민감한 정보 제거 (비밀번호, API 키 등)
- [ ] README.md 작성 완료
- [ ] 테스트 파일 제거
- [ ] 불필요한 파일 제거

---

**준비가 되셨다면 위의 명령어를 순서대로 실행하세요!** 🚀
