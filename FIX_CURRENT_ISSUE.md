# 현재 Git 오류 해결 가이드

현재 발생한 오류들을 해결하는 방법입니다.

## 🔴 발생한 오류

1. ✅ `error: remote origin already exists` - 이미 해결됨 (무시 가능)
2. ⚠️ `Author identity unknown` - **해결 필요**
3. ⚠️ `LF will be replaced by CRLF` - 경고 (무시 가능)

---

## 🛠️ 해결 방법

### 방법 1: 자동 스크립트 사용 (가장 쉬움) ⭐

```cmd
# 1. Git 사용자 정보 및 자격증명 설정
configure_git.bat

# 2. 커밋 및 푸시
quick_setup.bat
```

---

### 방법 2: 수동 명령어 사용

#### 1단계: Git 사용자 정보 설정

```bash
# 사용자 이름 설정 (GitHub 사용자명)
git config --global user.name "bboradoli"

# 이메일 설정 (GitHub 이메일)
git config --global user.email "your@email.com"

# 설정 확인
git config --global user.name
git config --global user.email
```

#### 2단계: Git 자격증명 영구 저장 설정

**옵션 A: Windows Credential Manager 사용 (권장)**

```bash
# Windows 자격증명 관리자에 안전하게 저장
git config --global credential.helper manager-core

# 또는 (위 명령어가 안 되면)
git config --global credential.helper wincred
```

**옵션 B: 파일로 저장 (간단하지만 덜 안전)**

```bash
# ~/.git-credentials 파일에 저장
git config --global credential.helper store
```

**옵션 C: 캐시 사용 (임시 저장)**

```bash
# 15분간 메모리에 저장
git config --global credential.helper cache
```

#### 3단계: 추가 설정 (선택사항)

```bash
# 줄바꿈 문자 자동 변환 (Windows)
git config --global core.autocrlf true

# 기본 브랜치 이름 설정
git config --global init.defaultBranch main

# 한글 파일명 정상 표시
git config --global core.quotepath false
```

#### 4단계: 커밋 및 푸시

```bash
# 파일 추가
git add .

# 커밋
git commit -m "Initial commit: Oracle to BigQuery DDL Generator"

# 푸시
git push -u origin main
```

**인증 정보 입력:**
- Username: `bboradoli`
- Password: `Personal Access Token` (PAT)

---

## 🔐 Personal Access Token (PAT) 생성

### 1. GitHub에서 PAT 생성

1. https://github.com/settings/tokens 접속
2. **Generate new token (classic)** 클릭
3. 설정:
   - **Note**: `oracle-to-bq-schema-gen`
   - **Expiration**: `90 days` (또는 원하는 기간)
   - **Scopes**: ✅ **repo** (전체 선택)
4. **Generate token** 클릭
5. **토큰 복사** (ghp_로 시작하는 긴 문자열)

### 2. PAT 사용

첫 푸시 시:
```
Username: bboradoli
Password: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (복사한 PAT)
```

**자격증명 저장 설정을 했다면:**
- 한 번만 입력하면 됩니다
- 다음부터는 자동으로 인증됩니다

---

## 📋 전체 명령어 순서 (복사해서 사용)

```bash
# 1. 사용자 정보 설정
git config --global user.name "bboradoli"
git config --global user.email "your@email.com"

# 2. 자격증명 영구 저장 설정
git config --global credential.helper manager-core

# 3. 추가 설정
git config --global core.autocrlf true
git config --global init.defaultBranch main
git config --global core.quotepath false

# 4. 브랜치 설정
git branch -M main

# 5. 파일 추가
git add .

# 6. 커밋
git commit -m "Initial commit: Oracle to BigQuery DDL Generator"

# 7. 푸시
git push -u origin main
```

---

## ✅ 설정 확인

```bash
# 모든 글로벌 설정 확인
git config --global --list

# 특정 설정만 확인
git config --global user.name
git config --global user.email
git config --global credential.helper
```

---

## 🔄 이후 업데이트 방법

설정이 완료되면 다음부터는 간단합니다:

```bash
# 파일 수정 후
git add .
git commit -m "Update: 변경 내용"
git push

# 인증 정보 입력 불필요! (자동으로 저장됨)
```

또는:

```cmd
# 간편 스크립트 사용
push_to_github.bat
```

---

## 🎯 권장 순서

1. **`configure_git.bat`** 실행 → Git 사용자 정보 및 자격증명 설정
2. **`quick_setup.bat`** 실행 → 커밋 및 푸시
3. 완료! 🎉

---

## 💡 팁

### Windows Credential Manager 확인

자격증명이 저장되었는지 확인:
1. Windows 검색에서 "자격 증명 관리자" 검색
2. "Windows 자격 증명" 클릭
3. "git:https://github.com" 항목 확인

### 자격증명 삭제 (재설정 필요 시)

```bash
# Windows Credential Manager에서 삭제
git credential-manager-core erase
# 또는
git credential-wincred erase

# 또는 수동으로 Windows 자격증명 관리자에서 삭제
```

### 저장된 자격증명 파일 위치

Store 방식 사용 시:
- Windows: `C:\Users\[사용자명]\.git-credentials`

---

## 🆘 문제 해결

### "fatal: unable to auto-detect email address"

```bash
git config --global user.email "your@email.com"
```

### "error: remote origin already exists"

```bash
# 기존 원격 저장소 제거 후 재추가
git remote remove origin
git remote add origin https://github.com/bboradoli/oracle-to-bq-schema-gen.git
```

### "Permission denied (publickey)"

```bash
# HTTPS 사용 (SSH 대신)
git remote set-url origin https://github.com/bboradoli/oracle-to-bq-schema-gen.git
```

### "Authentication failed"

- Personal Access Token이 올바른지 확인
- 토큰에 `repo` 권한이 있는지 확인
- 토큰이 만료되지 않았는지 확인

---

**준비가 되셨다면 `configure_git.bat`를 실행하세요!** 🚀
