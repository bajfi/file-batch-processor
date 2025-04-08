"""
Text analyzer plugin for batch processing.
"""

import os
from typing import override

import pandas as pd
from model.individual_processor import IndividualProcessor


class TextAnalyzer(IndividualProcessor):
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
    def process(
        self, file: str, output_dir: str = "results", save_format: str = "txt"
    ) -> str:
        # Read the text file
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()

        # Analyze the content
        lines = content.split("\n")
        words = content.split()
        chars = len(content)

        # Create a results dataframe
        result_df = pd.DataFrame(
            {
                "Metric": ["Lines", "Words", "Characters"],
                "Count": [len(lines), len(words), chars],
            }
        )

        # Save results
        result_file = os.path.join(
            output_dir, os.path.basename(file).replace(".txt", "_analysis.csv")
        )
        result_df.to_csv(result_file, index=False)
        return result_file
