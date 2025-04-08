from pathlib import Path
from typing import final

from model.Iprocessor import IProcessor, ProcessorCategory


class IndividualProcessor(IProcessor):
    """Base class for all file processors."""

    def process(
        self, file: str | Path, output_dir: str | Path, save_format: str
    ) -> str:
        """Process a file and return the path to the result file."""
        return ""

    @property
    @final
    def category(self) -> ProcessorCategory:
        """Return the category of this processor."""
        return ProcessorCategory.INDIVIDUAL  # Default category
