"""Compatibility launcher for source checkouts."""

from pathlib import Path
import sys

source_root = Path(__file__).resolve().parent / "src"
if str(source_root) not in sys.path:
    sys.path.insert(0, str(source_root))

from scientific_calculator_service.app import (  # noqa: E402
    VERSION,
    ExpressionError,
    VariableSpec,
    _canonical,
    _evaluate,
    app,
    convert_composition,
    evaluate,
    main,
    plot_expression,
)

__all__ = [
    "VERSION",
    "ExpressionError",
    "VariableSpec",
    "_canonical",
    "_evaluate",
    "app",
    "convert_composition",
    "evaluate",
    "main",
    "plot_expression",
]


if __name__ == "__main__":
    main()
