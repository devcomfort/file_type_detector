# GitHub Actions 환경 설정 가이드

이 문서는 GitHub Actions 워크플로우가 정상 작동하기 위해 필요한 설정을 설명합니다.

## 필요한 환경 변수 및 Secrets

### 자동으로 사용 가능한 Secrets

다음 secrets는 GitHub에서 자동으로 제공되며 **추가 설정이 필요 없습니다**:

- ✅ `GITHUB_TOKEN` - 브랜치 생성, 커밋, PR 생성에 사용 (자동 제공)

### 추가 설정이 필요한 경우

현재 워크플로우는 기본 `GITHUB_TOKEN`만 사용하므로 **추가 환경 변수 설정이 필요 없습니다**.

## 향후 확장 시 필요한 Secrets

워크플로우를 확장하여 다음 기능을 추가할 경우, GitHub Secrets에 다음 값들을 설정해야 합니다:

### PyPI 배포 자동화 (선택사항)

만약 자동으로 PyPI 배포까지 포함하고 싶다면:

| Secret 이름 | 설명 | 예시 |
|------------|------|------|
| `PYPI_API_TOKEN` | PyPI API 토큰 | `pypi-AgEIcHlwaS5...` |
| `TESTPYPI_API_TOKEN` | TestPyPI API 토큰 | `pypi-AgENdGVzdC5...` |

**설정 방법:**
1. GitHub 저장소 → Settings → Secrets and variables → Actions
2. "New repository secret" 클릭
3. Name과 Value 입력

⚠️ **보안 주의사항**: 
- 토큰은 절대 코드에 직접 작성하지 마세요
- Secrets에만 저장하고 워크플로우에서 `${{ secrets.SECRET_NAME }}` 형식으로 참조하세요

### Slack/Discord 알림 (선택사항)

PR 생성 시 알림을 받고 싶다면:

| Secret 이름 | 설명 |
|------------|------|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL |

## 워크플로우 권한 확인

워크플로우가 정상 작동하려면 다음 권한이 필요합니다:

- ✅ `contents: write` - 브랜치 생성 및 커밋 (워크플로우에 이미 포함됨)
- ✅ `pull-requests: write` - PR 생성 (워크플로우에 이미 포함됨)

이 권한들은 `update-lock-files.yml`의 `permissions` 섹션에 이미 설정되어 있습니다.

## 워크플로우 테스트

워크플로우가 정상 작동하는지 테스트하려면:

1. **수동 실행 테스트:**
   - GitHub 저장소 → Actions 탭
   - "Update Lock Files After Release" 선택
   - "Run workflow" 클릭
   - 버전 번호 입력 (선택사항)
   - 실행

2. **자동 트리거 테스트:**
   ```bash
   # pyproject.toml에서 버전 변경
   # 예: 0.1.0 → 0.1.1
   git add pyproject.toml
   git commit -m "chore: Bump version to 0.1.1"
   git push origin main
   
   # 워크플로우가 자동으로 실행되어 PR 생성됨
   ```

## 문제 해결

### 워크플로우가 실행되지 않는 경우

1. **GitHub Actions 활성화 확인**
   - Settings → Actions → General
   - "Allow all actions and reusable workflows" 선택

2. **워크플로우 파일 위치 확인**
   - `.github/workflows/update-lock-files.yml` 경로가 정확한지 확인

3. **브랜치 보호 규칙 확인**
   - Settings → Branches
   - `main` 브랜치에 워크플로우 실행을 제한하는 규칙이 있는지 확인

### 권한 오류 발생 시

- 워크플로우의 `permissions` 섹션 확인
- 저장소 Settings → Actions → General → "Workflow permissions" 확인

### PR이 생성되지 않는 경우

- Lock 파일에 실제 변경이 있는지 확인
- GitHub Actions 로그 확인 (Actions 탭에서 실행 결과 클릭)
- 브랜치 이름 충돌 여부 확인 (동일한 버전으로 이미 PR이 있는 경우)

## 참고 자료

- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [GitHub Secrets 관리](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [peter-evans/create-pull-request 액션](https://github.com/peter-evans/create-pull-request)

