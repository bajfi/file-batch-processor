from abc import abstractmethod
from pathlib import Path
from typing import List, Optional

from model.Iprocessor import IProcessor


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


class IBatchProcessor:
    """Handles batch processing of files."""

    def __init__(self, processor: IProcessor, output_path: str | Path):
        """Initialize with a processor and output path."""
        self.processor = processor
        self.output_path = Path(output_path).resolve()
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

    @abstractmethod
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
        return
