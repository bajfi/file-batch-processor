from pathlib import Path
from typing import Any, List, final

from model.Iprocessor import IProcessor, ProcessorCategory


class AdjointProcessor(IProcessor):
    """instead of processing a file and save the result directly,
    this process will keep the result, and the batch processor
    will combine each result and save it to the result file"""

    # The output path will be set by the AdjointBatchProcessor
    output_path = None

    def process(self, file: str | Path) -> Any:
        """
        Process a single file and return the result.

        The result will be gathered with the results from other files
        by the gather_results method.

        Args:
            file: Path to the file to process

        Returns:
            Any data that will be passed to gather_results
        """
        return ""

    def gather_results(self, results: List[Any], save_format: str) -> None:
        """
        Gather all processing results and save them to the output file.

        This method is called after all files have been processed.
        The default implementation simply writes each result as a string to the output file.

        Args:
            results: List of results from processing each file
            save_format: Format to save the results in
        """
        return

    @property
    @final
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.ADJOINT
