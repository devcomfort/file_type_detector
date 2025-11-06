# GitHub Actions 환경 설정 가이드

이 문서는 GitHub Actions 워크플로우가 정상 작동하기 위해 필요한 설정을 설명합니다.

## 필요한 환경 변수 및 Secrets

### 자동으로 사용 가능한 Secrets

다음 secrets는 GitHub에서 자동으로 제공되며 **추가 설정이 필요 없습니다**:

- ✅ `GITHUB_TOKEN` - 브랜치 생성, 커밋, PR 생성, GitHub Release 생성에 사용 (자동 제공)

### PyPI 배포를 위한 필수 Secrets

`pypi-release.yml` 워크플로우를 사용하려면 다음 Secrets를 **반드시 설정**해야 합니다:

| Secret 이름          | 설명                              | 필수 여부 | 설정 위치                    |
| -------------------- | --------------------------------- | --------- | ---------------------------- |
| `PYPI_API_TOKEN`     | PyPI API 토큰 (실제 PyPI 배포용)  | ✅ 필수    | Settings → Secrets → Actions |
| `TESTPYPI_API_TOKEN` | TestPyPI API 토큰 (테스트 배포용) | ✅ 필수    | Settings → Secrets → Actions |

**설정 방법:**
1. GitHub 저장소 → **Settings** → **Secrets and variables** → **Actions**
2. "New repository secret" 클릭
3. Name에 `PYPI_API_TOKEN` 또는 `TESTPYPI_API_TOKEN` 입력
4. Value에 해당 API 토큰 입력 (`pypi-`로 시작하는 전체 문자열)
5. "Add secret" 클릭

**토큰 생성 방법:**
- **PyPI 토큰**: https://pypi.org/manage/account/token/
- **TestPyPI 토큰**: https://test.pypi.org/manage/account/token/
- Scope: "Entire account" 선택

### 선택적 Secrets (알림 통합 등)

워크플로우를 확장하여 다음 기능을 추가할 경우:

### Slack/Discord 알림 (선택사항)

배포 완료 시 알림을 받고 싶다면:

| Secret 이름           | 설명                       |
| --------------------- | -------------------------- |
| `SLACK_WEBHOOK_URL`   | Slack Incoming Webhook URL |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL        |

## 워크플로우 권한 확인

워크플로우가 정상 작동하려면 다음 권한이 필요합니다:

- ✅ `contents: read` - 코드 읽기 (`pypi-release.yml`에 포함됨)
- ✅ `contents: write` - GitHub Release 생성 (`pypi-release.yml`에 포함됨)

## 워크플로우 테스트

워크플로우가 정상 작동하는지 테스트하려면:

1. **수동 실행 테스트 (PyPI Release):**
   - GitHub 저장소 → Actions 탭
   - "PyPI Release" 선택
   - "Run workflow" 클릭
   - Release type 선택 (patch/minor/major) 또는 버전 직접 입력
   - 실행

2. **자동 트리거 테스트 (Semantic Version 변경):**
   ```bash
   # pyproject.toml에서 Semantic Version으로 변경
   # 예: 0.1.0 → 0.1.1
   git add pyproject.toml
   git commit -m "chore: Bump version to 0.1.1"
   git push origin main
   
   # 워크플로우가 자동으로 실행되어 PyPI에 배포됨
   ```

## 문제 해결

### 워크플로우가 실행되지 않는 경우

1. **GitHub Actions 활성화 확인**
   - Settings → Actions → General
   - "Allow all actions and reusable workflows" 선택

2. **워크플로우 파일 위치 확인**
   - `.github/workflows/pypi-release.yml` 경로가 정확한지 확인

3. **브랜치 보호 규칙 확인**
   - Settings → Branches
   - `main` 브랜치에 워크플로우 실행을 제한하는 규칙이 있는지 확인

### 권한 오류 발생 시

- 워크플로우의 `permissions` 섹션 확인
- 저장소 Settings → Actions → General → "Workflow permissions" 확인

### 배포가 실패하는 경우

- Semantic Version 형식인지 확인 (X.Y.Z)
- `PYPI_API_TOKEN`, `TESTPYPI_API_TOKEN` Secret이 올바르게 설정되었는지 확인
- GitHub Actions 로그 확인 (Actions 탭에서 실행 결과 클릭)
- 테스트가 모두 통과하는지 확인

## 참고 자료

- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [GitHub Secrets 관리](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [peter-evans/create-pull-request 액션](https://github.com/peter-evans/create-pull-request)

