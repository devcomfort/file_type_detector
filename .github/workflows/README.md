# GitHub Actions Workflows

이 디렉토리에는 프로젝트의 CI/CD 워크플로우가 포함되어 있습니다.

## 워크플로우 개요

| 워크플로우         | 목적             | 트리거                        | 필요한 Secrets                         |
| ------------------ | ---------------- | ----------------------------- | -------------------------------------- |
| `pypi-release.yml` | PyPI 자동 배포   | Semantic Version 변경 (X.Y.Z) | `PYPI_API_TOKEN`, `TESTPYPI_API_TOKEN` |

---

## pypi-release.yml

Semantic Version (X.Y.Z 형식)이 업데이트되면 자동으로 PyPI에 배포하는 워크플로우입니다.

### 트리거 조건

1. **자동 트리거**: 
   - `main` 브랜치에 `pyproject.toml`의 `version` 필드가 Semantic Version 형식으로 변경되면 자동 실행
   - 형식: `X.Y.Z` (예: `0.1.0`, `1.2.3`)
   - `0.1.0-dev` 같은 pre-release 버전은 무시됨

2. **수동 트리거**: 
   - `workflow_dispatch`로 수동 실행
   - Release type 선택: `patch`, `minor`, `major`
   - 또는 특정 버전 번호 직접 입력

### 동작 과정

1. **버전 검증**: Semantic Version 형식 (X.Y.Z) 확인
2. **테스트 실행**: 모든 테스트가 통과하는지 확인
3. **패키지 빌드**: `python -m build`로 배포 패키지 생성
4. **패키지 검증**: `twine check`로 패키지 검증
5. **TestPyPI 배포**: 먼저 TestPyPI에 배포하여 검증
6. **PyPI 배포**: TestPyPI 성공 후 실제 PyPI에 배포
7. **GitHub Release 생성**: 자동으로 GitHub Release 태그 및 릴리스 노트 생성

### 배포 프로세스

```
버전 변경 감지
    ↓
테스트 실행 (실패 시 중단)
    ↓
패키지 빌드 및 검증
    ↓
TestPyPI 배포
    ↓
PyPI 배포
    ↓
GitHub Release 생성
```

### 필요한 Secrets

⚠️ **반드시 설정해야 합니다:**

| Secret 이름          | 설명              | 생성 위치                                   |
| -------------------- | ----------------- | ------------------------------------------- |
| `PYPI_API_TOKEN`     | PyPI API 토큰     | https://pypi.org/manage/account/token/      |
| `TESTPYPI_API_TOKEN` | TestPyPI API 토큰 | https://test.pypi.org/manage/account/token/ |

**설정 방법:** `.github/workflows/SETUP.md` 참조

### 필요한 권한

- `contents: read` - 코드 읽기
- `contents: write` - GitHub Release 생성
- TestPyPI/PyPI 배포 권한 (API Token으로 관리)

### Semantic Version 체크

워크플로우는 다음 형식만 자동 배포합니다:

- ✅ `0.1.0`
- ✅ `1.2.3`
- ✅ `10.0.0`
- ❌ `0.1.0-dev` (pre-release, 자동 배포되지 않음)
- ❌ `0.1.0a1` (pre-release)
- ❌ `0.1` (형식 오류)

### 사용 예시

#### 자동 배포 (Semantic Version 변경)

```bash
# pyproject.toml에서 버전 변경
version = "0.1.1"  # Semantic Version 형식

git add pyproject.toml
git commit -m "chore: Bump version to 0.1.1"
git push origin main

# 워크플로우가 자동으로 실행되어 PyPI에 배포됨
```

#### 수동 배포

1. GitHub Actions 탭에서 "PyPI Release" 선택
2. "Run workflow" 클릭
3. Release type 선택:
   - `patch`: 0.1.0 → 0.1.1
   - `minor`: 0.1.0 → 0.2.0
   - `major`: 0.1.0 → 1.0.0
4. 또는 특정 버전 직접 입력: `0.2.5`

### 환경 보호 규칙 (권장)

GitHub Environments를 사용하여 배포 전 승인을 설정할 수 있습니다:

1. Settings → Environments
2. `testpypi`, `pypi` 환경 생성
3. Required reviewers 설정 (선택사항)

이렇게 설정하면 배포 전에 승인을 받을 수 있습니다.

### 문제 해결

#### 배포가 실행되지 않는 경우

- Semantic Version 형식인지 확인 (X.Y.Z)
- `PYPI_API_TOKEN`, `TESTPYPI_API_TOKEN` Secret이 설정되었는지 확인
- GitHub Actions 로그에서 오류 메시지 확인

#### 테스트 실패로 배포가 중단되는 경우

- 로컬에서 테스트 실행: `rye run pytest tests/ -v`
- 모든 테스트가 통과하는지 확인

---

## Lock 파일 관리

Dependency lock 파일(`requirements.lock`, `requirements-dev.lock`)은 개발자가 수동으로 업데이트합니다.

### Lock 파일 업데이트 방법

```bash
# 의존성 동기화 및 lock 파일 업데이트
rye sync
rye lock

# 변경사항 확인
git diff requirements*.lock

# 변경사항 커밋
git add requirements.lock requirements-dev.lock
git commit -m "chore: Update lock files"
```

### 언제 업데이트해야 하나요?

- `pyproject.toml`의 의존성 버전 변경 시
- 새로운 의존성 추가 시
- 기존 의존성 제거 시
- `rye sync` 실행 후 lock 파일이 변경된 경우

---

## 공통 고려사항

### 장점

- ✅ 자동화로 인한 실수 방지
- ✅ 일관된 배포 프로세스
- ✅ 변경사항 추적 용이
- ✅ Lock 파일을 수동으로 관리하여 변경사항을 명확히 파악 가능

### 주의사항

- ⚠️ Semantic Version만 자동 배포됨 (pre-release는 수동 배포 필요)
- ⚠️ Secrets 설정이 반드시 필요함 (`pypi-release.yml` 사용 시)
- ⚠️ 배포 후에는 PyPI에서 패키지를 삭제할 수 없음 (버전 업데이트 필요)
- ⚠️ Lock 파일은 수동으로 업데이트해야 하므로 의존성 변경 시 주의 필요

### 개선 가능 사항

1. **채널 슬랙/디스코드 알림 통합**
2. **Dependabot 자동 업데이트**
3. **보안 스캔 통합** (`rye audit`)
4. **다중 Python 버전 테스트**
