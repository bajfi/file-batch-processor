import os
from typing import override

import pandas as pd
from model.individual_processor import IndividualProcessor


class StatisticsProcessor(IndividualProcessor):
    """Processor for calculating basic statistics on data files."""

    @property
    @override
    def name(self) -> str:
        return "Statistics Calculator"

    @property
    @override
    def description(self) -> str:
        return "Calculates basic statistics (mean, median, std, min, max) for numeric columns."

    @property
    @override
    def file_types(self) -> tuple:
        return (
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx *.xls"),
            ("All files", "*.*"),
        )

    @property
    @override
    def config_options(self) -> dict:
        return {
            "output_dir": {
                "type": "str",
                "default": "results",
                "description": "The directory to save the results.",
            }
        }

    @property
    @override
    def dependencies(self) -> list:
        return ["pandas"]

    @property
    @override
    def version(self) -> str:
        return "1.0.0"

    @property
    @override
    def metadata(self) -> dict:
        return {}

    @property
    @override
    def save_format(self) -> list:
        return [
            ("Text", "txt"),
            ("CSV", "csv"),
            ("Excel", "xlsx"),
            ("Parquet", "parquet"),
        ]

    @override
    def process(
        self, file: str, output_dir: str = "results", save_format: str = "csv"
    ) -> str:
        # read file
        if file.endswith(".csv"):
            df = pd.read_csv(file)
        elif file.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        else:
            raise ValueError(f"Unsupported file type: {file}")

        # Create a new dataframe for results
        result_df = pd.DataFrame()

        # Calculate basic statistics for each numeric column
        for column in df.select_dtypes(include=["number"]).columns:
            result_df.loc["mean", column] = df[column].mean()
            result_df.loc["median", column] = df[column].median()
            result_df.loc["std", column] = df[column].std()
            result_df.loc["min", column] = df[column].min()
            result_df.loc["max", column] = df[column].max()

        # Save results
        result_file = os.path.join(
            output_dir, os.path.basename(file).replace(".", "_stats.")
        )
        result_df.to_csv(result_file)
        return result_file
