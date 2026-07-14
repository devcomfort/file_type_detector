# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "filetype-detector",
#     "marimo",
#     "tabulate",
# ]
# ///
import marimo

__generated_with = "0.15.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from pathlib import Path
    from tabulate import tabulate

    return Path, mo, tabulate


@app.cell
def _(mo):
    mo.md(
        r"""
        # FileType Detector — Strategy Comparison

        This notebook demonstrates the four inference strategies and compares their results on real sample files.

        ## Architecture

        ```
        filetype_detector/
        ├── core/                    # Domain types
        │   ├── file_type.py         # FileType dataclass
        │   └── base_inferencer.py   # Abstract strategy interface
        └── strategies/              # Concrete strategies
            ├── lexical_inferencer.py   # Extension-only (fastest)
            ├── magic_inferencer.py     # Magic bytes (reliable)
            ├── magika_inferencer.py    # AI model (best for text)
            └── hybrid_inferencer.py    # Magic + Magika cascade (recommended)
        ```

        ## Strategy Decision Flow

        ```
        파일 이름(확장자)를 신뢰할 수 있는가?
        ├─ 예  → LexicalInferencer   (파일 읽기 없음, 가장 빠름)
        └─ 아니오 / 불확실
               ├─ 주로 바이너리?    → MagicInferencer
               ├─ 주로 텍스트?      → MagikaInferencer
               └─ 혼합 / 미확정     → HybridInferencer (기본값)
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## 1. LexicalInferencer

        파일 경로에서 확장자만 추출합니다. 파일 내용을 읽지 않으므로 **가장 빠르지만** 확장자가 없거나 잘못된 경우 탐지할 수 없습니다.

        **Best for**: CI 파이프라인 등 이미 정제된 파일, 확장자를 신뢰할 수 있는 경우
        """
    )
    return


@app.cell
def _(mo, tabulate):
    from filetype_detector import LexicalInferencer

    inferencer = LexicalInferencer()
    cases = [
        ("document.pdf", "Normal file"),
        ("archive.dat", "Wrong extension"),
        ("no_extension", "No extension"),
        ("file.PDF", "Uppercase"),
    ]

    rows = []
    for filename, desc in cases:
        try:
            ft = inferencer.infer(filename)
            result = ", ".join(ft.extensions)
        except ValueError as e:
            result = f"ValueError: {e}"
        rows.append([filename, desc, result])

    mo.stop(
        tabulate(rows, headers=["Filename", "Description", "Result"], tablefmt="pipe")
    )
    return cases, filename, ft, inferencer, result, rows


@app.cell
def _(mo):
    mo.md(
        r"""
        ## 2. MagicInferencer

        `python-magic`(libmagic)을 사용해 파일의 **매직 바이트**를 분석합니다. 확장자와 무관하게 실제 콘텐츠 기반으로 MIME 타입을 판별합니다.

        **Best for**: 확장자가 없거나 잘못된 파일, 바이너리 파일 검증

        **Limitation**: 텍스트 파일의 세부 구분 불가능 (Python, JSON, CSV 모두 `text/plain`)
        """
    )
    return


@app.cell
def _(Path, mo, tabulate):
    from filetype_detector import MagicInferencer

    inferencer = MagicInferencer()
    samples = ["sample.pdf", "sample.json", "sample.py", "sample.txt", "sample.csv"]
    fixtures = Path(__file__).parent.parent / "tests" / "fixtures"

    rows = []
    for name in samples:
        f = fixtures / name
        if f.exists():
            ft = inferencer.infer(f)
            ext = ", ".join(ft.extensions) or "—"
            mime = ft.mime_types[0] if ft.mime_types else "—"
            rows.append([name, ext, mime])

    mo.stop(
        tabulate(rows, headers=["File", "Extensions", "MIME Type"], tablefmt="pipe")
    )
    return ext, f, fixtures, ft, inferencer, mime, name, rows, samples


@app.cell
def _(mo):
    mo.md(
        r"""
        ## 3. MagikaInferencer

        Google의 **딥러닝 모델**로 파일 내용을 분석합니다. 학습된 패턴 기반으로 동작하므로 텍스트 파일의 세부 분류에 뛰어납니다.

        **Best for**: Python, JSON, CSV 등 텍스트 기반 파일의 정확한 분류, 신뢰도 점수가 필요한 경우

        **Limitation**: 바이너리 파일에서는 Magic과 동등하거나 열등, HWP 미지원, ZIP 기반 포맷(HWPX, ODF) 오분류 가능
        """
    )
    return


@app.cell
def _(Path, mo, tabulate):
    from filetype_detector import MagikaInferencer

    inferencer = MagikaInferencer()
    samples = ["sample.pdf", "sample.json", "sample.py", "sample.txt", "sample.csv"]
    fixtures = Path(__file__).parent.parent / "tests" / "fixtures"

    rows = []
    for name in samples:
        f = fixtures / name
        if f.exists():
            ft = inferencer.infer(f)
            ext, score = inferencer.infer_with_score(f)
            ext_str = ", ".join(ft.extensions) or "—"
            rows.append([name, ext_str, ext, f"{score:.3f}"])

    mo.stop(
        tabulate(
            rows,
            headers=["File", "Extensions", "Top Extension", "Score"],
            tablefmt="pipe",
        )
    )
    return ext, ext_str, f, fixtures, ft, inferencer, name, rows, samples, score


@app.cell
def _(mo):
    mo.md(
        r"""
        ## 4. HybridInferencer (Recommended)

        **2단계 파이프라인**: Magic으로 1차 분류 → `text/*` 또는 `application/octet-stream`처럼 모호한 MIME이면 Magika로 재분석.

        - **바이너리 파일**: Magic 결과만 사용 → 빠름
        - **텍스트 파일**: Magika로 세부 분류 → 정확
        - **신뢰도 fallback**: Magika 신뢰도가 낮으면 Magic 결과 사용
        """
    )
    return


@app.cell
def _(Path, mo, tabulate):
    from filetype_detector import HybridInferencer

    inferencer = HybridInferencer()
    samples = ["sample.pdf", "sample.json", "sample.py", "sample.txt", "sample.csv"]
    fixtures = Path(__file__).parent.parent / "tests" / "fixtures"

    rows = []
    for name in samples:
        f = fixtures / name
        if f.exists():
            ft = inferencer.infer(f)
            ext = ", ".join(ft.extensions) or "—"
            mime = ft.mime_types[0] if ft.mime_types else "—"
            rows.append([name, ext, mime])

    mo.stop(
        tabulate(rows, headers=["File", "Extensions", "MIME Type"], tablefmt="pipe")
    )
    return ext, f, fixtures, ft, inferencer, mime, name, rows, samples


@app.cell
def _(Path, mo, tabulate):
    mo.md(
        r"""
        ## Full Comparison

        모든 전략을 15개 샘플 파일에 적용한 결과입니다.
        """
    )

    from filetype_detector import (
        LexicalInferencer,
        MagicInferencer,
        MagikaInferencer,
        HybridInferencer,
    )

    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures"
    sample_files = sorted(fixtures_dir.glob("sample.*"))

    inferencers = {
        "Lexical": LexicalInferencer(),
        "Magic": MagicInferencer(),
        "Magika": MagikaInferencer(),
        "Hybrid": HybridInferencer(),
    }

    table_data = []
    for file_path in sample_files:
        row = [file_path.name]
        for name, inf in inferencers.items():
            try:
                ft = inf.infer(file_path)
                ext_str = ", ".join(ft.extensions) or "—"
                mime_str = ft.mime_types[0] if ft.mime_types else "—"
                row.append(f"{ext_str}\n({mime_str})")
            except Exception as e:
                row.append(f"Error: {type(e).__name__}")
        table_data.append(row)

    mo.stop(
        tabulate(
            table_data,
            headers=["File"] + list(inferencers.keys()),
            tablefmt="pipe",
        )
    )
    return (
        HybridInferencer,
        LexicalInferencer,
        MagikaInferencer,
        MagicInferencer,
        ext_str,
        file_path,
        fixtures_dir,
        ft,
        inf,
        inferencers,
        mime_str,
        name,
        row,
        sample_files,
        table_data,
    )


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Quick Start

        ```python
        from filetype_detector import AutoInferencer

        # Recommended: hybrid backend (Magic + Magika cascade)
        inferencer = AutoInferencer(backend="hybrid")
        result = inferencer.infer("document.pdf")

        print(result.extensions)   # ('.pdf',)
        print(result.mime_types)   # ('application/pdf',)
        ```

        Or use strategies directly:

        ```python
        from filetype_detector import HybridInferencer, MagikaInferencer

        # Direct strategy access
        hybrid = HybridInferencer()
        magika = MagikaInferencer()
        ```
        """
    )
    return


if __name__ == "__main__":
    app.run()
