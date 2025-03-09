"""
Text analyzer plugin for batch processing.
"""

import os

import pandas as pd
from model.processor import Processor


class TextAnalyzer(Processor):
    """Processor for analyzing text files."""

    @property
    def name(self) -> str:
        return "Text Analyzer"

    @property
    def description(self) -> str:
        return "Analyzes text files to count words, lines, and characters."

    @property
    def file_types(self) -> tuple:
        """Return the supported file types."""
        return (
            ("Text files", "*.txt"),
            ("All files", "*.*"),
        )

    @property
    def config_options(self) -> dict:
        return {
            "output_dir": {
                "type": "str",
                "default": "results",
                "description": "The directory to save the results.",
            }
        }

    @property
    def dependencies(self) -> list:
        return ["pandas"]

    @property
    def version(self) -> str:
        return "1.0.0"

    def process(self, file: str, output_dir: str = "results") -> str:
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
