from pathlib import Path
from typing import Dict, Type, Union

from core.batchProcessor.adjoint_batch_processor import AdjointBatchProcessor
from core.batchProcessor.Ibatch_processor import IBatchProcessor
from core.batchProcessor.individual_batch_processor import IndividualBatchProcessor
from model.Iprocessor import IProcessor, ProcessorCategory


class BatchProcessorFactory:
    """Factory for creating batch processors based on processor type."""

    _processor_map: Dict[ProcessorCategory, Type[IBatchProcessor]] = {
        ProcessorCategory.INDIVIDUAL: IndividualBatchProcessor,
        ProcessorCategory.ADJOINT: AdjointBatchProcessor,
    }

    @classmethod
    def create_batch_processor(
        cls, processor: IProcessor, output_path: Union[str, Path]
    ) -> IBatchProcessor:
        """
        Create and return the appropriate batch processor based on processor category.

        Args:
            processor: The processor instance to use for file processing
            output_path: The path where processed results will be saved

        Returns:
            An instance of IBatchProcessor appropriate for the processor's category

        Raises:
            ValueError: If the processor category is not supported
        """
        processor_class = cls._processor_map.get(processor.category)
        if processor_class is None:
            raise ValueError(f"Unsupported processor category: {processor.category}")

        return processor_class(processor, output_path)
