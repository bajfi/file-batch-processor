import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional, override

from core.batchProcessor.Ibatch_processor import IBatchProcessor
from model.individual_processor import IndividualProcessor


class IndividualBatchProcessor(IBatchProcessor):
    """Handles batch processing of files."""

    def __init__(self, processor: IndividualProcessor, output_path: str | Path):
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
        # Ensure output directory exists
        os.makedirs(self.output_path, exist_ok=True)

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
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = []
            for file in files:
                future = executor.submit(self._process_file, file, save_format)
                futures.append((future, file))

            # Process results as they complete
            for future, file in futures:
                try:
                    result = future.result()
                    self._notify_file_complete(file, result, True)
                except Exception as e:
                    self._notify_file_complete(file, "", False, str(e))

        # Notify that all processing is complete
        self._notify_complete()

    def _process_file(self, file: str, save_format: str) -> str:
        """
        Process a single file using the processor.

        Args:
            file: Path to the file to process

        Returns:
            Path to the result file
        """
        return self.processor.process(file, str(self.output_path), save_format)
