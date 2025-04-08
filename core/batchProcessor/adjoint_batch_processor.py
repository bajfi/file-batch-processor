import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, List, Optional, override

from core.batchProcessor.Ibatch_processor import IBatchProcessor
from model.Iprocessor import AdjointProcessor


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
        # Ensure output path is a file
        assert self.output_path.is_file(), "Output path must be a file"

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
                    self._notify_file_complete(file, result, True)
                except Exception as e:
                    self._notify_file_complete(file, "", False, str(e))

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
        """
        with open(self.output_path, "w", encoding="utf-8") as f:
            for result in results:
                f.write(result)
