import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, List, Optional, override

from core.batchProcessor.Ibatch_processor import IBatchProcessor
from model.adjoint_processor import AdjointProcessor


class AdjointBatchProcessor(IBatchProcessor):
    """Handles batch processing of files."""

    def __init__(self, processor: AdjointProcessor, output_path: str | Path):
        """Initialize with a processor and output path."""
        super().__init__(processor, output_path)

    @override
    def process_files(
        self,
        files: List[str],
        max_workers: Optional[int] = None,
        save_format: str = "txt",
    ) -> None:
        """
        Process a list of files using the processor.

        Args:
            files: List of file paths to process
            max_workers: Maximum number of parallel workers, or None for auto
        """
        # Ensure output path is not a directory
        if self.output_path.exists() and self.output_path.is_dir():
            raise ValueError("Output path must be a file, not a directory")

        # Make sure parent directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Notify observers that processing has started
        self._notify_start(len(files))

        # Create a thread to handle the processing
        thread = threading.Thread(
            target=self._process_files_thread,
            args=(files, max_workers, save_format),
            daemon=True,
        )
        thread.start()

    def _process_files_thread(
        self,
        files: List[str],
        max_workers: Optional[int] = None,
        save_format: str = "txt",
    ) -> None:
        """
        Process files in a separate thread.

        Args:
            files: List of file paths to process
            max_workers: Maximum number of parallel workers, or None for auto
        """
        results: List[Any] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = []
            for file in files:
                future = executor.submit(self._process_file, file)
                futures.append((future, file))

            # Process results as they complete
            for future, file in futures:
                try:
                    result = future.result()
                    results.append(result)
                    # For AdjointProcessor, the result file is the final output path
                    self._notify_file_complete(file, str(self.output_path), True)
                except Exception as e:
                    self._notify_file_complete(file, "", False, str(e))

        # Set the output path on the processor
        self.processor.output_path = self.output_path

        # Gather all the results and save them to the output file
        self._gather_results(results, save_format)

        # Notify that all processing is complete
        self._notify_complete()

    def _process_file(self, file: str | Path) -> Any:
        """
        Process a single file using the processor.

        Args:
            file: Path to the file to process

        Returns:
            Path to the result file
        """
        return self.processor.process(file)

    def _gather_results(self, results: List[Any], save_format: str) -> None:
        """
        Gather all the results and save them to the output file.

        Delegates to the processor's gather_results method if available.
        """
        # Check if processor has a gather_results method
        if hasattr(self.processor, "gather_results"):
            # Call the processor's method
            self.processor.gather_results(results, save_format)
