import os
from typing import override

from model.individual_processor import IndividualProcessor


class SampleProcessor(IndividualProcessor):
    """A simple sample processor for demonstration."""

    @property
    @override
    def name(self) -> str:
        return "Sample Processor"

    @property
    @override
    def description(self) -> str:
        return "A simple processor that copies files to demonstrate the plugin system."

    @property
    @override
    def file_types(self) -> tuple:
        return (("All files", "*.*"),)

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
        # Create a simple output file
        output_file = os.path.join(output_dir, f"sample_{os.path.basename(file)}")

        # Just copy the file for demonstration
        with open(file, "rb") as src, open(output_file, "wb") as dst:
            dst.write(src.read())

        return output_file
