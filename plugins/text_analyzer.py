"""
Text analyzer plugin for batch processing.
"""

from pathlib import Path
from typing import override

from model.adjoint_processor import AdjointProcessor


class TextAnalyzer(AdjointProcessor):
    """Processor for analyzing text files."""

    @property
    @override
    def name(self) -> str:
        return "Text Analyzer"

    @property
    @override
    def description(self) -> str:
        return "Analyzes text files to count words, lines, and characters."

    @property
    @override
    def file_types(self) -> tuple:
        """Return the supported file types."""
        return (
            ("Text files", "*.txt"),
            ("All files", "*.*"),
        )

    @property
    @override
    def config_options(self) -> dict:
        return {
            "output_dir": {
                "type": "str",
                "default": "results",
                "description": "The directory to save the results.",
            }
        }

    @property
    @override
    def dependencies(self) -> list:
        return ["pandas"]

    @property
    @override
    def version(self) -> str:
        return "1.0.0"

    @property
    @override
    def save_format(self) -> list:
        return [
            ("Text", "txt"),
        ]

    @override
    def process(self, file: str | Path) -> str:
        # Read the text file
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()

        # Analyze the content
        lines = content.split("\n")
        words = content.split()
        chars = len(content)

        return {
            "file": {Path(file).stem},
            "lines": len(lines),
            "words": len(words),
            "characters": chars,
        }

    @override
    def gather_results(self, results: list, save_format: str) -> None:
        """
        Gather and save all processing results.

        Args:
            results: List of dictionaries with word counts, line counts, etc.
            save_format: Format to save the results in
        """
        if save_format == "txt":
            with open(self.output_path, "w", encoding="utf-8") as f:
                for result in results:
                    f.write(
                        f"{' '.join(f'{key}: {value}' for key, value in result.items())}\n"
                    )
