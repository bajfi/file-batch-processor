import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional

from model.processor import Processor


class ProcessingObserver:
    """Interface for observers of the processing progress."""

    def on_start(self, total_files: int) -> None:
        """Called when processing starts."""
        pass

    def on_file_complete(
        self, file: str, result: str, success: bool, message: str = ""
    ) -> None:
        """Called when a file is processed."""
        pass

    def on_complete(self) -> None:
        """Called when all processing is complete."""
        pass


class BatchProcessor:
    """Handles batch processing of files."""

    def __init__(self, processor: Processor, output_dir: str = "results"):
        """Initialize with a processor and output directory."""
        self.processor = processor
        self.output_dir = Path(output_dir).resolve()
        self.observers: List[ProcessingObserver] = []

    def add_observer(self, observer: ProcessingObserver) -> None:
        """Add an observer to receive progress updates."""
        if observer not in self.observers:
            self.observers.append(observer)

    def remove_observer(self, observer: ProcessingObserver) -> None:
        """Remove an observer."""
        if observer in self.observers:
            self.observers.remove(observer)

    def _notify_start(self, total_files: int) -> None:
        """Notify observers that processing has started."""
        for observer in self.observers:
            observer.on_start(total_files)

    def _notify_file_complete(
        self, file: str, result: str, success: bool, message: str = ""
    ) -> None:
        """Notify observers that a file has been processed."""
        for observer in self.observers:
            observer.on_file_complete(file, result, success, message)

    def _notify_complete(self) -> None:
        """Notify observers that all processing is complete."""
        for observer in self.observers:
            observer.on_complete()

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
        os.makedirs(self.output_dir, exist_ok=True)

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
        return self.processor.process(file, str(self.output_dir), save_format)
