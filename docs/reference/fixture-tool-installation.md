# 포맷별 생성·검증 도구 안내서

이 문서는 외부 도구가 필요한 테스트용 샘플 파일을 만들고 확인하는 방법을 설명한다. 문서에는 확장자 설명, 파일 구성, 생성 방법, 필요한 도구, 운영체제별 설치 방법, 실행할 스크립트, 버전과 라이선스를 기록한다.

## 운영체제별 설치

| 운영체제 | 실행할 파일 | 설치 내용과 실패 조건 |
|---|---|---|
| Linux | [`scripts/install-fixture-tools-linux.sh`](https://github.com/devcomfort/file_type_detector/blob/main/scripts/install-fixture-tools-linux.sh) | `ffmpeg`, LibreOffice, `squashfs-tools`, APK/HLP/Mach-O/DS_Store 점검 도구를 설치한다. `apt-get` 또는 `sudo`가 없으면 지원하지 않는 환경으로 보고 실패한다. |
| macOS | [`scripts/install-fixture-tools-macos.sh`](https://github.com/devcomfort/file_type_detector/blob/main/scripts/install-fixture-tools-macos.sh) | Homebrew로 `ffmpeg`, `squashfs-tools`, LibreOffice와 Python 점검 도구를 설치한다. `unsquashfs`를 설치하지 못하면 SquashFS 점검을 지원하지 않는 환경으로 실패한다. |
| Windows | [`scripts/install-fixture-tools-windows.ps1`](https://github.com/devcomfort/file_type_detector/blob/main/scripts/install-fixture-tools-windows.ps1) | `winget`으로 FFmpeg와 LibreOffice를 설치하고 Python 점검 도구를 설치한다. `unsquashfs.exe`가 없으면 SquashFS 점검을 지원하지 않는 환경으로 명확히 실패한다. |

설치 스크립트는 이미 설치된 도구를 다시 실행해도 안전해야 한다. 이 도구들은 `filetype-detector`를 실행할 때 필요한 것이 아니라 테스트용 샘플 파일을 만들고 확인할 때만 필요하다.

## 포맷별 안내

| 확장자 또는 파일명 | 어떤 파일인가 | 파일을 만드는 방법 | 독립 확인 도구 | 설치 방법 | 관련 코드 |
|---|---|---|---|---|---|
| `.dcm` / DICOM | 128바이트 preamble, `DICM`, File Meta와 데이터 요소를 가진 의료 영상 파일 | pydicom으로 고정된 metadata를 기록 | `pydicom.dcmread` | `python -m pip install -r requirements-dev.lock` | `scripts/generators/data_formats.py`, `.audit/w3_validate.py --id sample-dcm` |
| `.pyc` | CPython이 읽는 Python bytecode | 고정된 `<module>` 이름으로 compile 후 marshal 저장 | CPython magic/header와 marshal 읽기 | `python -m pip install -r requirements-dev.lock` | `scripts/generators/executables.py`, `.audit/w3_validate.py --id sample-pyc` |
| `.snap` / `.squashfs` | SquashFS 4.0 압축 파일 시스템. `.snap`은 이를 사용하는 패키지 관례 | 고정된 시간 정보를 사용한 재현 가능한 bytes | `unsquashfs`로 실제 파일 추출 | Linux `sudo apt-get install squashfs-tools`; macOS `brew install squashfs-tools`; Windows는 `unsquashfs.exe`가 따로 있을 때만 지원 | `scripts/generators/archives.py`, `.audit/w3_validate.py` |
| `.DS_Store` | macOS 폴더 표시 정보를 저장하는 파일. `.dsstore` 확장자가 아니라 정확한 파일명 규칙을 사용 | `ds-store==1.3.3`으로 `Iloc` record 생성 | ds-store parser로 다시 열고 record 확인 | `python -m pip install ds-store==1.3.3` | `scripts/generators/macos.py`, `.audit/w3_validate.py --id sample-dsstore` |
| `.apk` | ZIP 안에 Android binary XML, DEX, package 정보가 들어 있는 Android 패키지 | APK generator가 ZIP과 binary AXML/DEX를 구성 | `androguard==4.1.4` | `python -m pip install -r .audit/requirements-apk.txt` | `scripts/generators/archives.py`, `.audit/apk_validate.py` |
| `.hlp` | Windows Help의 header, directory B-tree, `|SYSTEM`, `|TOPIC` 등을 가진 파일 | 고정된 upstream `FXSEARCH.HLP` 사용 | `winhlp==0.3.0` parser | `python -m pip install -r .audit/requirements-hlp.txt` | `.audit/hlp_validate.py --id sample-hlp` |
| `.emf` / `.wmf` | Windows 그림 명령을 record로 저장하는 파일 | EMF/WMF record generator | 구조 검사와 LibreOffice Draw 변환 | Linux/macOS/Windows 설치 스크립트 사용 | `scripts/generators/images.py`, `.audit/metafile_validate.py` |
| `.flac` | FLAC stream, STREAMINFO, 오디오 frame과 checksum을 가진 소리 파일 | 고정된 무음 FLAC bytes | `ffprobe` 또는 `ffmpeg` | Linux `sudo apt-get install ffmpeg`; macOS `brew install ffmpeg`; Windows FFmpeg 설치 | `scripts/generators/audio.py` |
| `.webm` | EBML/WebM header, Segment, track, 영상 payload를 가진 영상 파일 | 고정된 VP9 WebM bytes | `ffprobe` 또는 `ffmpeg` | FLAC과 같은 FFmpeg 설치 방법 | `scripts/generators/video.py` |
| `.woff` | WOFF header와 `head`, `glyf`, `name` 등 글꼴 table을 가진 웹 글꼴 | FontTools로 생성한 WOFF | `fontTools.ttLib.TTFont` | `python -m pip install -r requirements-dev.lock` | `scripts/generators/fonts.py` |
| `.tga` / `.icns` | TGA 이미지 또는 PNG를 담은 ICNS 아이콘 | 고정된 pixel과 PNG bytes 생성 | Pillow로 이미지 열기 | `python -m pip install -r requirements-dev.lock` | `scripts/generators/images.py` |
| `.macho` | 64비트 Mach-O header와 load command를 가진 파일. `.macho`는 표준 확장자가 아님 | Mach-O generator | `macholib==1.16.4` | `python -m pip install -r .audit/requirements-macho.txt` | `scripts/generators/executables.py`, `.audit/macho_validate.py` |
| `.cab`, `.crx`, `.deb`, `.dex`, `.rpm`, `.xar`, `.lha` | 각자 다른 압축·header·record 구조를 가진 파일 | 포맷별 생성기 | 포맷별 구조 검사, 서명 검사, tar/압축 도구 | 운영체제 설치 스크립트 또는 lock 파일 사용 | `scripts/generators/archives.py`, `scripts/generators/executables.py`, `.audit/w3_validate.py` |
| `.ai` | Illustrator가 PDF compatible data를 넣을 수 있는 파일. PDF로 열리는 것만으로 native Illustrator 파일이라고 할 수 없음 | Illustrator marker를 포함한 결정론적 PDF generator | `pdfinfo`로 PDF 구조 확인 | Poppler 설치 필요 | `scripts/generators/documents.py` |

## 공식 정답 등록 기준

감지 프로그램이 특정 이름을 출력했다는 사실만으로는 충분하지 않다. 다음 정보를 모두 기록해야 공식 정답으로 등록할 수 있다.

1. 생성 결과가 다시 만들어지거나 외부 출처가 바뀌지 않도록 고정되어야 한다.
2. 가능하면 독립 parser, reader, decoder 또는 round-trip 도구로 확인한다.
3. 독립 도구가 없으면 공식 producer/writer로 만든 과정, 버전, 생성 조건, 포맷 전용 bytes를 명확히 기록한다.
4. MIME과 확장자 또는 정확한 파일명에 대한 근거를 기록한다.
5. 다른 파일 형식과 구분 가능한지 기록한다.
6. 출처, 라이선스, 사용 도구 버전을 기록한다.

어느 운영체제에서 점검 도구를 사용할 수 없는 경우에는 조용히 통과시키지 않는다. 지원하지 않는 환경이라고 명확히 실패시키고, 그 결과는 파일 커버리지 표에 따로 기록한다.
