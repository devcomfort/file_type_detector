# Apache Tika OS 일치성 검증

## 목적과 범위

[Tika OS conformance 워크플로](../../.github/workflows/tika-conformance.yml)는 실제 Linux·macOS·Windows에서 같은 입력에 대한 Tika 출력의 일치성을 검사하는 독립 실험이다. 운영 검출기를 교체하지 않으며, 기존 [Backend Conformance](backend-conformance.md)의 정확성 평가·baseline과 별개다.

- 같은 소스 revision, 입력 목록 해시, 샘플 ID·SHA256, 수집기·Java probe·Tika 식별 정보를 확인한 뒤 비교한다. 누락·중복·오류·무결성 실패는 통과할 수 없다.
- 각 샘플을 `content`(빈 Metadata), `named`(실제 파일명), `wrong_pdf`(`payload.pdf`), `wrong_txt`(`payload.txt`)로 측정한다. 모드마다 Metadata를 새로 만들며, 각 모드의 OS 간 결과를 비교한다. 서로 다른 모드끼리 같아야 하는 것은 아니다.
- **원시 MIME 일치**와 **Tika 내장 확장자 집합 일치**를 따로 보고하며 둘 다 통과해야 한다. MIME 대소문자·매개변수·별칭은 정규화하지 않는다. 확장자 비교만 순서·중복을 무시하고 원본 목록은 보존한다.
- 네이티브 libmagic의 content MIME과 Python 유래 확장자 차이는 참고 정보다. 차이 자체는 Tika 실패 조건이 아니지만 수집 오류는 실패다. [`mimetypes`](https://docs.python.org/3.12/library/mimetypes.html) 역매핑을 Tika 내장 확장자와 혼동하지 않는다.
- 실제 출력 차이와 누락·오류로 인한 **비교 불가**는 구분해 읽는다. 비교 불가를 libmagic의 OS 간 차이로 해석하거나 일치 성공으로 세지 않는다.
- 검토 라벨과의 MIME 호환성은 SHA가 일치하는 공식 검토 샘플만 집계한다. 이는 별칭 동등성이나 형식 인식 정확도가 아니며, OS 일치만으로 정답임을 증명하지 않는다.
- baseline·예외 목록은 없다. 실패한 샘플을 바꾸거나 제외하고, 오류를 성공으로 바꾸어 통과시키지 않는다.

## 고정 실행 환경

워크플로는 Python `3.12.12`, Temurin `11.0.29+7`, Apache Tika `3.3.3`을 사용한다. 컨테이너로 OS를 흉내 내지 않고 다음 네이티브 x64 러너에서 실행한다.

| 러너 라벨 | GitHub 러너 | 네이티브 libmagic |
|---|---|---|
| `ubuntu-x64` | `ubuntu-22.04` | `libmagic1`, `python-magic==0.4.27` |
| `macos-x64` | `macos-15-intel` | Homebrew `libmagic`, `python-magic==0.4.27` |
| `windows-x64` | `windows-2022` | `python-magic-bin==0.4.14` |

Tika JAR은 [고정 계약](../../scripts/conformance/tika_contract.py)의 Maven Central URL에서 내려받고, Java 실행 전에 아래 SHA512를 확인한다. 기존 JAR의 해시가 다르면 덮어쓰지 않고 실패한다. 배포·검증 안내는 [Apache 공식 다운로드](https://tika.apache.org/download.html)를 참고한다.

```text
3c6e62e864e32af234832ec6d928bbc58692d3ddd60564cd8c80dee7e161653d6efcba373b6cc9468c778010bea92bdee5ca75ab24f01923480bec1b29b573fd
```

## 실행

실험 브랜치에서 워크플로를 실행한다. 별도 브랜치·작업 디렉터리는 기존 미커밋 작업을 섞어 게시하지 않기 위한 경계다. 클라우드 입력은 커밋된 후보 **606개·공식 검토 17개**이며, 전날 로컬의 미커밋 **678개·52개** 자료가 아니다.

아래는 저장소 루트에서 실행하는 Bash 명령이다. `GITHUB_SHA`는 세 수집 작업과 비교 작업이 공유하는 커밋의 전체 40자리 SHA다. Actions 밖에서는 해당 값을 직접 설정한다. 각 OS에 위 의존성을 설치하고 `--runner-label`과 출력 경로를 해당 러너에 맞춘다.

```bash
python -m scripts.conformance.tika_collect \
  --root . --runner-label ubuntu-x64 --revision "$GITHUB_SHA" \
  --jar .artifacts/tika/tika-app.jar --download \
  --output .artifacts/tika/ubuntu/ubuntu.json

python -m scripts.conformance.tika_compare \
  --input tika-artifacts/tika-ubuntu/ubuntu.json \
  --input tika-artifacts/tika-macos/macos.json \
  --input tika-artifacts/tika-windows/windows.json \
  --expected-runner ubuntu-x64 --expected-runner macos-x64 \
  --expected-runner windows-x64 --expected-revision "$GITHUB_SHA" \
  --output-dir .artifacts/tika-report
```

비교 명령은 같은 revision의 체크아웃에서 실행한다. 세 수집 artifact를 위 경로에 디렉터리째 풀어 JSON과 `.evidence`를 함께 둔다. `--expected-revision`은 생략하면 비교 체크아웃 HEAD를 사용하지만, 재현 시에는 명시한다. `--download` 없이 검증된 기존 JAR을 재사용할 수 있다. 실제 CLI 계약은 [수집기](../../scripts/conformance/tika_collect.py), [비교기](../../scripts/conformance/tika_compare.py), [Java probe](../../scripts/conformance/TikaProbe.java)에 있다.

## 결과와 실패 증거

결과는 [실제 Actions 실행](https://github.com/devcomfort/file_type_detector/actions/workflows/tika-conformance.yml)의 `tika-conformance-report` artifact에서 확인한다. 해당 실행의 보고서가 확보되기 전에는 클라우드 통과나 OS 일치 성공을 주장하지 않는다.

- OS별 artifact는 `tika-ubuntu`, `tika-macos`, `tika-windows`다. 각각 `<platform>.json`과 `<platform>.evidence/`를 담는다.
- evidence에는 원본 `backend_inventory_candidates.json`, `backend_inventory.json`, `manifest.tsv`, `java.stdout`, `java.stderr`, `run.json`이 있다. 관측 오류와 전체 stack trace도 보존한다.
- `tika-conformance-report`에는 요약 `tika-conformance.md`, 전체 입력·원시 증거·오류·차이를 담은 `tika-conformance.json`, 전체 비교 행 `tika-conformance.csv`가 있다. 실패해도 확보한 증거를 저장하고 CLI는 0이 아닌 종료 코드를 반환한다. 워크플로는 실패 시에도 업로드를 시도하며 보존 기간은 30일이다.
- 세 실제 OS·x86_64 식별 정보, Java 실행 환경·설정 일치, 전체 입력과 관측의 유효성, 모든 Tika 모드의 MIME·확장자 일치가 충족되어야 `cross_os_verified=true`다. 로컬 결과나 복사한 artifact로 대체하지 않는다.
