"""
Date processor plugin for batch processing.
"""

import os
from typing import override

import numpy as np
import pandas as pd
from model.individual_processor import IndividualProcessor


class DateProcessor(IndividualProcessor):
    """Processor for date-based data files."""

    @property
    @override
    def name(self) -> str:
        return "Date Processor"

    @property
    @override
    def description(self) -> str:
        return "Calculates MSE statistics for time series data."

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
    def save_format(self) -> list:
        return [
            ("Text", "txt"),
            ("CSV", "csv"),
            ("Excel", "xlsx"),
        ]

    @override
    def process(
        self, file: str, output_dir: str = "results", save_format: str = "csv"
    ) -> str:
        # Check dependencies before processing
        deps_ok, missing = self.check_dependencies()
        if not deps_ok:
            raise ImportError(f"Missing dependencies: {', '.join(missing)}")

        # Read file for different date formats
        if file.endswith(".csv"):
            df = pd.read_csv(file)
        elif file.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        else:
            raise ValueError(f"Unsupported file type: {file}")

        # Process date
        columns = df.columns
        # The first column is the time step, we do not need it
        columns = columns[1:]
        # For remaining columns, we calculate the MSE for each column
        mse_columns = [col + "_mse" for col in columns]
        # Calculate the mean of each column
        col_means = df[columns].mean(axis=0)
        # Calculate the MSE for each column
        for i, col in enumerate(mse_columns):
            df[col] = np.nan
            df.loc[0, col] = (
                (df[columns[i]] - col_means[columns[i]]) ** 2
            ).mean() ** 0.5

        # Calculate the mean of the MSEs
        df["mse_mean"] = np.nan
        df.loc[0, "mse_mean"] = df.loc[0, mse_columns].mean()

        # Calculate the RMS of the MSEs
        df["mse_rms"] = np.nan
        df.loc[0, "mse_rms"] = np.sqrt((df.loc[0, mse_columns] ** 2).mean())

        # Save the result
        result_file = os.path.join(
            output_dir, os.path.basename(file).replace(".csv", "_result.csv")
        )
        df.to_csv(result_file, index=False)
        return result_file
