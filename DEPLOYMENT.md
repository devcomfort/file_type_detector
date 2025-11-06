# PyPI 배포 가이드

이 문서는 `filetype-detector` 패키지를 PyPI에 배포하는 방법을 설명합니다.

## 사전 준비 사항

### 1. 계정 생성

**PyPI와 TestPyPI는 완전히 분리된 서버입니다. 각각 별도의 계정과 토큰이 필요합니다.**

- **PyPI 계정**: [PyPI 회원가입](https://pypi.org/account/register/)
- **TestPyPI 계정**: [TestPyPI 회원가입](https://test.pypi.org/account/register/) (테스트용, 필수 아님)

### 2. API Token 생성

각 서버마다 별도의 API Token을 생성해야 합니다.

#### PyPI API Token 생성

1. [PyPI 토큰 관리 페이지](https://pypi.org/manage/account/token/) 접속
2. "Add API token" 클릭
3. **Token name**: 예) `pypi-upload-token`
4. **Scope**: **"Entire account"** 선택 (또는 특정 프로젝트 선택)
5. "Add token" 클릭
6. 생성된 토큰 복사 (다시 볼 수 없으므로 안전한 곳에 저장)
   - 형식: `pypi-AgEIcHlwaS5vcmcC...`

#### TestPyPI API Token 생성

1. [TestPyPI 토큰 관리 페이지](https://test.pypi.org/manage/account/token/) 접속
2. "Add API token" 클릭
3. **Token name**: 예) `testpypi-upload-token`
4. **Scope**: **"Entire account"** 선택
5. "Add token" 클릭
6. 생성된 토큰 복사 (다시 볼 수 없으므로 안전한 곳에 저장)
   - 형식: `pypi-AgENdGVzdC5weXBpLm9yZw...`

**중요**: PyPI 토큰과 TestPyPI 토큰은 서로 다릅니다. 각각 별도로 생성해야 합니다.

### 3. API Token 설정 (.pypirc 파일)

`.pypirc` 파일을 생성하여 토큰을 자동으로 사용하도록 설정합니다:

```bash
mkdir -p ~ && cat > ~/.pypirc << 'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-여기에PyPI토큰전체입력

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-여기에TestPyPI토큰전체입력
EOF

chmod 600 ~/.pypirc
```

**보안 주의사항:**
- `.pypirc` 파일은 홈 디렉토리에만 생성 (`~/`)
- 파일 권한을 `600`으로 설정하여 소유자만 읽을 수 있도록 함
- 절대 Git에 커밋하지 않음 (이미 `.gitignore`에 포함됨)

## 배포 단계

### 1. 빌드 도구 설치

```bash
pip install build twine
```

또는 rye를 사용하는 경우:

```bash
rye add --dev build twine
```

### 2. 프로젝트 빌드

```bash
python -m build
```

이 명령은 `dist/` 디렉토리에 다음 파일들을 생성합니다:
- `filetype_detector-0.1.0.tar.gz` (소스 배포판)
- `filetype_detector-0.1.0-py3-none-any.whl` (휠 배포판)

### 3. 빌드 결과 확인

```bash
ls -lh dist/
twine check dist/*
```

### 4. TestPyPI에 테스트 업로드 (권장)

먼저 TestPyPI에 업로드하여 모든 것이 정상 작동하는지 확인합니다.

**`.pypirc` 파일을 설정한 경우:**
```bash
twine upload --repository testpypi dist/*
```
토큰이 자동으로 사용되므로 추가 입력이 필요 없습니다.

**`.pypirc` 파일을 사용하지 않는 경우:**
```bash
twine upload --repository testpypi dist/*
```
업로드 시:
- Username: `__token__`
- Password: TestPyPI API Token 전체 입력 (`pypi-`로 시작하는 전체 문자열)

**주의사항:**
- TestPyPI 토큰과 PyPI 토큰은 다릅니다
- 토큰 복사 시 앞뒤 공백이나 줄바꿈이 없어야 합니다
- 토큰은 `pypi-`로 시작하는 전체 문자열입니다

### 5. TestPyPI에서 설치 테스트

```bash
pip install --index-url https://test.pypi.org/simple/ filetype-detector
```

설치가 정상적으로 작동하는지 확인:

```bash
python -c "from filetype_detector.inferencer import FILE_FORMAT_INFERENCER_MAP; print('Success!')"
```

### 6. 실제 PyPI에 업로드

모든 테스트가 완료되면 실제 PyPI에 업로드합니다.

**`.pypirc` 파일을 설정한 경우:**
```bash
twine upload dist/*
```
토큰이 자동으로 사용되므로 추가 입력이 필요 없습니다.

**`.pypirc` 파일을 사용하지 않는 경우:**
```bash
twine upload dist/*
```
업로드 시:
- Username: `__token__`
- Password: PyPI API Token 전체 입력 (`pypi-`로 시작하는 전체 문자열)

**중요:**
- 실제 PyPI에 업로드하면 전 세계 사용자가 설치할 수 있습니다
- 반드시 TestPyPI에서 테스트 후 업로드하세요
- 동일한 버전은 한 번만 업로드할 수 있습니다

### 7. 배포 확인

PyPI에서 패키지가 정상적으로 표시되는지 확인:

```bash
pip install filetype-detector
```

## 버전 관리

새 버전을 배포할 때는 `pyproject.toml`의 `version` 필드를 업데이트합니다:

```toml
version = "0.1.1"  # 패치 버전
# 또는
version = "0.2.0"  # 마이너 버전
# 또는
version = "1.0.0"  # 메이저 버전
```

버전 번호는 [Semantic Versioning](https://semver.org/)을 따르는 것을 권장합니다.

## 자동화 스크립트

빌드 및 배포를 자동화하려면 다음 스크립트를 사용할 수 있습니다:

```bash
#!/bin/bash
# deploy.sh

set -e

echo "Building package..."
python -m build

echo "Checking package..."
twine check dist/*

read -p "Upload to TestPyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Uploading to TestPyPI..."
    twine upload --repository testpypi dist/*
fi

read -p "Upload to PyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Uploading to PyPI..."
    twine upload dist/*
fi

echo "Done!"
```

## 문제 해결

### 403 Forbidden - Invalid or non-existent authentication information

**원인:**
- 잘못된 API Token 또는 토큰 형식 오류
- TestPyPI 토큰을 PyPI에 사용하거나 그 반대의 경우
- 토큰이 만료되거나 삭제됨

**해결 방법:**

1. **토큰 형식 확인**
   ```bash
   # 토큰이 pypi-로 시작하는지 확인
   echo $TWINE_PASSWORD | head -c 10
   # 출력: pypi-AgEIc (pypi-로 시작해야 함)
   ```

2. **올바른 서버의 토큰 사용 확인**
   - TestPyPI 업로드: TestPyPI 토큰 사용
   - PyPI 업로드: PyPI 토큰 사용
   - 각각 별도 토큰 필요

3. **.pypirc 파일 확인**
   ```bash
   cat ~/.pypirc
   # 각 섹션의 password가 올바른 토큰인지 확인
   ```

4. **토큰 재생성**
   - 토큰이 유출되었거나 문제가 있는 경우 즉시 삭제 후 재생성
   - [PyPI 토큰 관리](https://pypi.org/manage/account/token/)
   - [TestPyPI 토큰 관리](https://test.pypi.org/manage/account/token/)

### 400 Bad Request - File already exists

**원인:**
- 동일한 버전이 이미 업로드됨

**해결 방법:**
1. `pyproject.toml`에서 버전 번호 증가
   ```toml
   version = "0.1.1"  # 0.1.0 → 0.1.1
   ```
2. 재빌드 및 업로드
   ```bash
   rm -rf dist/ build/
   python -m build
   twine upload --repository testpypi dist/*
   ```

### Package already exists 오류

- 버전 번호를 업데이트하고 다시 빌드하세요.
- 동일한 버전은 한 번만 업로드할 수 있습니다.
- PyPI는 동일한 버전 삭제/재업로드를 허용하지 않습니다.

### 기타 인증 문제

**환경 변수 사용:**
```bash
# TestPyPI 업로드
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-TestPyPI토큰전체
twine upload --repository testpypi dist/*

# PyPI 업로드
export TWINE_PASSWORD=pypi-PyPI토큰전체
twine upload dist/*
```

**Verbose 모드로 디버깅:**
```bash
twine upload --repository testpypi dist/* --verbose
```
상세한 로그를 확인하여 문제를 진단할 수 있습니다.

## TestPyPI vs PyPI

### 차이점

| 항목        | TestPyPI              | PyPI             |
| ----------- | --------------------- | ---------------- |
| 목적        | 테스트 및 실험용      | 실제 배포용      |
| 계정        | 별도 계정 필요        | 별도 계정 필요   |
| 토큰        | 별도 토큰 필요        | 별도 토큰 필요   |
| URL         | https://test.pypi.org | https://pypi.org |
| 데이터 보존 | 주기적으로 리셋됨     | 영구 보존        |

### 권장 워크플로우

1. **TestPyPI에 먼저 업로드**
   ```bash
   twine upload --repository testpypi dist/*
   ```

2. **TestPyPI에서 설치 및 테스트**
   ```bash
   pip install --index-url https://test.pypi.org/simple/ filetype-detector
   python -c "from filetype_detector.inferencer import FILE_FORMAT_INFERENCER_MAP; print('Success!')"
   ```

3. **모든 테스트 통과 후 PyPI에 업로드**
   ```bash
   twine upload dist/*
   ```

## 보안 모범 사례

1. **토큰 관리**
   - 토큰을 코드나 공개 저장소에 절대 커밋하지 않음
   - `.pypirc` 파일 권한을 `600`으로 설정
   - 토큰 유출 시 즉시 삭제 및 재생성

2. **Scope 최소화**
   - 가능하면 "Entire account" 대신 특정 프로젝트 scope 사용
   - 불필요한 권한 부여 방지

3. **정기적 토큰 교체**
   - 보안을 위해 주기적으로 토큰 재생성 권장

## 추가 리소스

- [PyPI 배포 문서](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/)
- [Twine 문서](https://twine.readthedocs.io/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [TestPyPI 도움말](https://test.pypi.org/help/)
- [PyPI API 토큰 가이드](https://pypi.org/help/#apitoken)

