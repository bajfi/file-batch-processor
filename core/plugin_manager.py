import importlib
import inspect
import sys
from pathlib import Path
from typing import Dict, List, Type

from model.processor import Processor


class PluginManager:
    """Manages processor plugins."""

    def __init__(self, plugin_dir: str = "plugins"):
        """Initialize with the plugin directory path."""
        self.plugin_dir = Path(plugin_dir).resolve()
        self.processor_classes: Dict[str, Type[Processor]] = {}
        self.processors: Dict[str, Processor] = {}

    def discover_plugins(self) -> List[Type[Processor]]:
        """
        Discover all available processor plugins.
        Returns a list of processor classes.
        """
        # Clear existing processor classes
        self.processor_classes = {}

        # Ensure the plugin directory exists
        self.plugin_dir.mkdir(parents=True, exist_ok=True)

        # Add the plugin directory to sys.path if needed
        plugin_dir_str = str(self.plugin_dir)
        if plugin_dir_str not in sys.path:
            sys.path.insert(0, plugin_dir_str)

        # Also add the parent directory to sys.path if needed
        parent_dir = str(self.plugin_dir.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # Find all potential plugin files
        plugin_files = [
            item
            for item in self.plugin_dir.glob("*.py")
            if item.is_file() and not item.name.startswith("_")
        ]

        # Debug output to help diagnose issues
        # print(f"Looking for plugins in: {self.plugin_dir}")
        # print(f"Found potential plugin files: {[f.name for f in plugin_files]}")

        # Load each plugin file
        processors = []
        for plugin_file in plugin_files:
            # Import directly by filename without the plugins prefix
            module_name = plugin_file.stem
            try:
                # Import the module
                # print(f"Attempting to import {module_name}")
                module = importlib.import_module(module_name)

                # Find all Processor subclasses in the module
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, Processor)
                        and obj != Processor
                    ):
                        # print(f"Found processor class: {name}")
                        processors.append(obj)
                        self.processor_classes[obj.__name__] = obj
            except Exception as e:
                print(f"Error loading plugin {plugin_file}: {e}")
                # Try alternate import path as fallback
                try:
                    module_name = f"plugins.{plugin_file.stem}"
                    # print(f"Trying alternate import: {module_name}")
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module):
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, Processor)
                            and obj != Processor
                        ):
                            # print(f"Found processor class using alternate path: {name}")
                            processors.append(obj)
                            self.processor_classes[obj.__name__] = obj
                except Exception as e2:
                    print(f"Error with alternate import path: {e2}")

        return processors

    def get_processor_instances(self) -> List[Processor]:
        """
        Get instances of all available processors.
        """
        # Discover plugins if not already done
        if not self.processor_classes:
            self.discover_plugins()

        # Create instances
        self.processors = {name: cls() for name, cls in self.processor_classes.items()}
        return list(self.processors.values())

    def get_processor_by_name(self, name: str) -> Processor:
        """
        Get a processor instance by its name.
        """
        for processor in self.get_processor_instances():
            if processor.name == name:
                return processor
        raise ValueError(f"No processor found with name: {name}")

    def get_processors_by_category(self, category: str) -> List[Processor]:
        """
        Get all processor instances in a specific category.
        """
        return [p for p in self.get_processor_instances() if p.category == category]
