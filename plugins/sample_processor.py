import os

from model.processor import Processor


class SampleProcessor(Processor):
    """A simple sample processor for demonstration."""

    @property
    def name(self) -> str:
        return "Sample Processor"

    @property
    def description(self) -> str:
        return "A simple processor that copies files to demonstrate the plugin system."

    @property
    def file_types(self) -> tuple:
        return (("All files", "*.*"),)

    def process(self, file: str, output_dir: str = "results") -> str:
        # Create a simple output file
        output_file = os.path.join(output_dir, f"sample_{os.path.basename(file)}")

        # Just copy the file for demonstration
        with open(file, "rb") as src, open(output_file, "wb") as dst:
            dst.write(src.read())

        return output_file
