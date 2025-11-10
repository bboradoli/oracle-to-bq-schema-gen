# Build Guide - Windows Portable Version

Windows 포터블 버전 빌드 가이드입니다.

## 빌드 요구사항

- **Python 3.8 이상** (빌드용)
- **인터넷 연결** (Python 런타임 다운로드용)
- **디스크 공간**: 약 200MB (빌드 과정 포함)
- **운영체제**: Windows 10/11

## 빌드 방법

### 1. 간단한 빌드 (권장)

```cmd
build_windows.bat
```

### 2. Python 직접 실행

```cmd
python build_windows_portable.py
```

## 빌드 과정

### 1단계: Python Runtime 다운로드
- Python Standalone Build (약 30MB) 다운로드
- URL: `https://github.com/indygreg/python-build-standalone/releases`
- 버전: Python 3.8.18 (Windows x64)

### 2단계: Runtime 압축 해제
- `windows/python/` 디렉토리에 압축 해제
- Python 실행 파일 확인: `python.exe`

### 3단계: 의존성 설치
- PyYAML
- click
- typing-extensions

### 4단계: 소스 코드 복사
- `portable/simple_cli.py` → `windows/src/oracle_to_bq_cli.py`
- Windows 환경 적응 (UTF-8 인코딩 명시)

### 5단계: 실행 스크립트 생성
- `oracle-to-bq.bat`: 메인 실행 스크립트
- `verify_standalone.bat`: 독립성 검증 스크립트
- `도움말.bat`: 도움말 스크립트
- `빠른테스트.bat`: 빠른 테스트 스크립트

### 6단계: 최적화
- `__pycache__` 디렉토리 제거
- `.pyc` 파일 제거
- 테스트 파일 제거

### 7단계: 검증
- Python 실행 파일 테스트
- 모듈 임포트 테스트
- CLI 기능 테스트

## 빌드 결과

```
windows/
├── python/                 # 포터블 Python 런타임 (약 130MB)
│   ├── python.exe
│   ├── Lib/
│   └── ...
├── src/                    # 소스 코드
│   └── oracle_to_bq_cli.py
├── oracle-to-bq.bat       # 메인 실행 스크립트
├── verify_standalone.bat   # 독립성 검증
├── 도움말.bat              # 도움말
├── 빠른테스트.bat          # 빠른 테스트
├── config.json            # 설정 파일
├── schema.csv             # 샘플 스키마
└── build_info.json        # 빌드 정보
```

**총 크기**: 약 130-150MB

## 빌드 검증

```cmd
cd windows
verify_standalone.bat
```

검증 항목:
1. Python 런타임 존재 및 실행
2. 소스 코드 파일 존재
3. 시스템 Python 의존성 확인
4. 모듈 임포트 테스트
5. CLI 실행 테스트
6. 배치 스크립트 테스트

## 문제 해결

### 다운로드 실패

```
❌ Python Runtime 다운로드 실패
```

**해결 방법:**
1. 인터넷 연결 확인
2. 방화벽/프록시 설정 확인
3. GitHub 접속 가능 여부 확인
4. 수동 다운로드 후 `temp/` 폴더에 배치

### 패키지 설치 실패

```
❌ 의존성 패키지 설치 실패
```

**해결 방법:**
1. Python pip 정상 작동 확인
2. 디스크 공간 확인
3. 바이러스 백신 일시 중지

### 압축 해제 실패

```
❌ Python Runtime 압축 해제 실패
```

**해결 방법:**
1. 다운로드 파일 재다운로드
2. 디스크 공간 확인
3. 관리자 권한으로 실행

## 재빌드

기존 빌드를 삭제하고 재빌드:

```cmd
rmdir /s /q windows
build_windows.bat
```

## 배포

빌드 완료 후 `windows/` 폴더 전체를 압축하여 배포:

```cmd
# 7-Zip 사용 예시
7z a oracle-to-bq-windows-portable.zip windows\
```

**배포 파일 크기**: 약 50-60MB (압축 후)

## 버전 업데이트

### Python 런타임 업데이트

`build_windows_portable.py` 수정:

```python
self.python_url = "https://github.com/indygreg/python-build-standalone/releases/download/[VERSION]/cpython-[VERSION]-x86_64-pc-windows-msvc-shared-install_only.tar.gz"
```

### 의존성 패키지 업데이트

```python
self.required_packages = [
    "PyYAML==6.0",
    "click==8.1.0",
    "typing-extensions==4.5.0"
]
```

## 빌드 시간

- **첫 빌드**: 약 5-10분 (다운로드 포함)
- **재빌드**: 약 2-3분 (캐시 사용)

## 참고 사항

- 빌드는 개발자/배포 담당자만 수행
- 최종 사용자는 빌드된 `windows/` 폴더만 필요
- 빌드 파일(`build_windows.bat`, `build_windows_portable.py`)은 배포 시 제외 가능
