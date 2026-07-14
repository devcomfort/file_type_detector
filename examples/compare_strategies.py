"""Compare all inferencer strategies on sample fixture files.

Usage:
    python examples/compare_strategies.py
"""

from pathlib import Path
from tabulate import tabulate

from filetype_detector import (
    LexicalInferencer,
    MagicInferencer,
    MagikaInferencer,
    HybridInferencer,
)


def main():
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures"
    sample_files = sorted(fixtures_dir.glob("sample.*"))

    if not sample_files:
        print(f"Error: No sample files found in {fixtures_dir}")
        return

    inferencers = {
        "Lexical": LexicalInferencer(),
        "Magic": MagicInferencer(),
        "Magika": MagikaInferencer(),
        "Hybrid": HybridInferencer(),
    }

    table_data = []
    for file_path in sample_files:
        row = [file_path.name]
        for name, inferencer in inferencers.items():
            try:
                ft = inferencer.infer(file_path)
                ext_str = ", ".join(ft.extensions) if ft.extensions else "—"
                mime_str = ft.mime_types[0] if ft.mime_types else "—"
                row.append(f"{ext_str}\n({mime_str})")
            except Exception as e:
                row.append(f"Error: {type(e).__name__}")
        table_data.append(row)

    headers = ["File"] + list(inferencers.keys())
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


if __name__ == "__main__":
    main()
