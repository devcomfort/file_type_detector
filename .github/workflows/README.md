# GitHub Actions Workflows

## update-lock-files.yml

자동으로 dependency lock 파일을 업데이트하고 PR을 생성하는 워크플로우입니다.

### 트리거 조건

1. **자동 트리거**: `main` 브랜치에 `pyproject.toml`의 `version` 필드가 변경되면 자동 실행
2. **수동 트리거**: GitHub Actions UI에서 `workflow_dispatch`로 수동 실행 가능

### 동작 과정

1. **버전 변경 감지**: `pyproject.toml`의 `version` 필드 변경 확인
2. **Lock 파일 업데이트**: `rye sync`와 `rye lock`으로 lock 파일 업데이트
3. **변경사항 확인**: lock 파일에 실제 변경이 있는지 확인
4. **브랜치 및 커밋 생성**: 새로운 브랜치에 변경사항 커밋
5. **PR 생성**: 자동으로 Pull Request 생성 (자세한 PR 메시지 포함)

### PR 메시지 구성

- 버전 정보 (이전 → 새 버전)
- 변경된 패키지 목록
- Lock 파일 diff
- 체크리스트
- 자동 생성 표시

### 필요한 권한

- `contents: write` - 브랜치 생성 및 커밋
- `pull-requests: write` - PR 생성

### 고려사항

#### 장점

- ✅ 버전 업데이트 후 자동으로 lock 파일 동기화
- ✅ 변경사항을 명확히 보여주는 상세한 PR
- ✅ 의존성 변경사항을 리뷰할 수 있는 기회 제공

#### 주의사항

- ⚠️ Lock 파일에 변경이 없으면 PR이 생성되지 않음
- ⚠️ `rye lock` 명령이 실패하면 워크플로우가 실패함
- ⚠️ 동일한 브랜치 이름이 이미 있으면 충돌 발생 가능

#### 개선 가능 사항

1. **테스트 통합**: PR 생성 전에 테스트 실행하여 성공 여부를 PR 메시지에 포함
2. **보안 스캔**: `rye audit` 또는 Dependabot 통합으로 취약점 검사
3. **브랜치 이름 충돌 처리**: 타임스탬프 추가 또는 중복 확인
4. **다중 Python 버전 지원**: 여러 Python 버전에서 lock 파일 생성 테스트

### 사용 예시

```bash
# pyproject.toml에서 버전 변경 후
git add pyproject.toml
git commit -m "chore: Bump version to 0.1.1"
git push origin main

# 워크플로우가 자동으로 실행되어 PR 생성됨
```

### 수동 실행

GitHub Actions 탭에서:
1. "Update Lock Files After Release" 워크플로우 선택
2. "Run workflow" 클릭
3. (선택사항) 버전 번호 입력
4. "Run workflow" 실행

