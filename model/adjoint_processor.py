from pathlib import Path
from typing import Any, final

from model.Iprocessor import IProcessor, ProcessorCategory


class AdjointProcessor(IProcessor):
    """instead of processing a file and save the result directly,
    this process will keep the result, and the batch processor
    will combine each result and save it to the result file"""

    def process(self, file: str | Path) -> Any:
        return

    @property
    @final
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.ADJOINT
