import importlib
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class Processor(ABC):
    """Base class for all file processors."""

    @abstractmethod
    def process(self, file: str, output_dir: str) -> str:
        """Process a file and return the path to the result file."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the processor."""
        pass

    @property
    def description(self) -> str:
        """Return a description of the processor."""
        return "No description provided."

    @property
    def file_types(self) -> Tuple[Tuple[str, str], ...]:
        """Return the supported file types."""
        return (("All files", "*.*"),)

    @property
    def config_options(self) -> Dict[str, Any]:
        """Return configuration options for this processor."""
        return {}  # Default is no configuration options

    @property
    def category(self) -> str:
        """Return the category of this processor."""
        return "General"  # Default category

    @property
    def documentation(self) -> str:
        """Return detailed documentation for this processor."""
        return self.description  # Default to description

    @property
    def dependencies(self) -> List[str]:
        """Return a list of required dependencies."""
        return []  # Default is no dependencies

    @property
    def version(self) -> str:
        """Return the version of this processor."""
        return "1.0.0"  # Default version

    @property
    def metadata(self) -> Dict[str, str]:
        """Return metadata for this processor."""
        return {
            "author": "Unknown",
            "created": "Unknown",
            "updated": "Unknown",
            "license": "Unknown",
        }

    def check_dependencies(self) -> Tuple[bool, List[str]]:
        """Check if all dependencies are installed."""
        missing = []
        for dep in self.dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                missing.append(dep)
        return (len(missing) == 0, missing)
