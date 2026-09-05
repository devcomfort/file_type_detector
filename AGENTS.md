# Agent Instructions

## Fixture 생성 및 검증 규칙

파일 형식 fixture를 추가하거나 재생성할 때 다음 절차를 따른다.

### 1. 생성 도구가 필요하면 OS별 설치 스크립트를 먼저 작성한다

fixture 생성을 위해 외부 도구나 라이브러리 설치가 필요하면, 해당 fixture를 구현하기 전에 반드시 운영체제별 idempotent 설치 스크립트를 작성한다. 이 의무는 선택 사항이 아니다.

- Linux: [`scripts/install-fixture-tools-linux.sh`](scripts/install-fixture-tools-linux.sh)
- macOS: [`scripts/install-fixture-tools-macos.sh`](scripts/install-fixture-tools-macos.sh)
- Windows: [`scripts/install-fixture-tools-windows.ps1`](scripts/install-fixture-tools-windows.ps1)

각 스크립트는 이미 설치된 도구를 다시 실행해도 안전해야 하며, 지원하지 않는 OS·패키지 관리자·검증 도구가 있으면 명시적인 `unsupported` 오류와 non-zero exit status를 반환해야 한다. 스크립트에 없는 수동 설치 절차만으로 fixture를 추가하지 않는다.

설치와 포맷별 생성·검증 방법은 [`docs/reference/fixture-tool-installation.md`](docs/reference/fixture-tool-installation.md)에 기록한다. dossier에는 확장자, 내부 구성, 생성 방법, 필요한 도구, OS별 설치법, 실제 실행 스크립트 경로, 버전 pinning, 라이선스와 재현성 제약을 포함한다.

문서와 설치 스크립트가 먼저 존재하고, 생성 방법과 설치 재현성이 확인된 뒤에만 fixture를 candidate inventory에 추가한다.

### 2. 생성 방식과 fixture 출처를 분리해 기록한다

각 fixture는 다음 중 하나의 출처를 명시한다.

- 저장소의 deterministic generator가 생성한 bytes
- immutable commit/blob에 고정한 외부 fixture
- 사람이 생성한 bytes를 별도 provenance와 checksum으로 고정한 fixture

generator를 사용하는 경우 generator symbol, recipe hash, tool version, reproducibility tier를 기록한다. 외부 fixture는 source URL, immutable revision/blob, SHA-256, license를 기록한다. 생성기와 committed fixture의 bytes가 일치하는지 확인한 뒤에만 exact-byte로 분류한다.

### 3. 포맷 검증은 명확한 형식 단서를 우선한다

파일이 해당 포맷임을 명확히 보여 주는 단서가 있으면 그 단서를 사용해 검증할 수 있다. 검증 라이브러리가 반드시 존재해야 하는 것은 아니다.

예를 들어 `.pth` 파일이라면, PyTorch 공식 라이브러리의 고정 버전으로 해당 파일을 생성하고 PyTorch가 정의한 저장 형식으로 저장되었다는 생성 과정이 명확하다면, 그 생성 과정과 bytes 재현성 자체가 중요한 형식 근거가 될 수 있다. 이 경우 단순히 Magika나 libmagic이 특정 label을 반환했다는 사실을 형식 검증으로 사용하지 않는다.

검증 우선순위는 다음과 같다.

1. 해당 포맷의 독립 parser, reader, decoder, round-trip 도구
2. 포맷 제작자 또는 표준 라이브러리의 writer/reader를 통한 생성·재오픈
3. 포맷 사양에 따른 구조 검사와 checksum/signature 검사
4. 위 방법이 없을 때 명확한 생성 과정, 고정된 도구 버전, 의미 있는 format-specific bytes, 반복 생성 일치

단순 magic/header 검사만 통과한 fixture는 format-validity verified로 승격하지 않는다. 포맷 식별 단서와 포맷 의미를 구분한다. 예를 들어 ZIP 안에 `AndroidManifest.xml` 이름만 있다고 APK 전체 의미가 증명되는 것은 아니며, CFB magic만 있다고 Outlook MSG가 증명되는 것도 아니다.

### 4. validator가 없으면 한계를 명시한다

검증 라이브러리의 존재를 추측하지 않는다. 먼저 lockfile, 시스템 도구, 공식 문서, upstream parser를 확인한다. 적절한 validator를 찾지 못하면 다음 중 하나를 선택한다.

- validator를 audit 전용 optional dependency로 pin하고 OS별 설치·실행 문서를 추가한다.
- 포맷 사양에 따른 제한된 구조 검사만 수행하고 `needs_review` 또는 `excluded` 상태를 유지한다.
- 명확한 생성 과정과 provenance가 있어도 MIME authority나 의미 검증이 부족하면 promotion하지 않는다.

### 5. 검증 결과와 coverage를 별도로 유지한다

포맷별 파일 존재 여부, 모델 label coverage, format validity, promotion 상태는 서로 다른 지표다. 다음을 혼동하지 않는다.

- fixture가 존재함
- generator가 bytes를 재현함
- 독립 parser가 유효성을 확인함
- detector가 목표 label을 출력함
- authoritative Ground Truth로 promotion됨

파일 coverage 표와 audit matrix에는 fixture ID, 확장자 또는 exact filename, 생성 방식, source/license, SHA-256, validator와 실행 명령, validator 결과, identifiability, evidence gap, promotion 상태를 별도 열로 기록한다. Coverage report는 재현 가능한 스크립트로 생성하고 `--check` 모드에서 committed 결과와 inventory ID 집합 및 수치를 비교한다.

### 6. Promotion 규칙

다음 조건을 모두 충족할 때만 candidate를 authoritative inventory로 promotion한다.

- source integrity와 fixture SHA가 확인됨
- 생성 방식 또는 외부 출처가 재현 가능함
- 독립 parser/reader/round-trip 또는 명확한 format-specific 생성 근거가 있음
- MIME 및 extension 또는 exact filename authority evidence가 있음
- content identifiability가 기록됨
- candidate와 authoritative metadata가 일치함
- promotion은 전용 CLI의 atomic 경로로 실행함

하나라도 부족하면 `needs_review` 또는 `excluded`로 유지한다. detector의 출력 label만으로 Ground Truth를 생성하지 않는다.
