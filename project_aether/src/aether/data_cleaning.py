
from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd


class DataCleaner:
    @staticmethod
    def validate_readings(readings: Dict[str, float]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if not readings:
            errors.append("No readings provided")
            return False, errors

        series = pd.Series(readings, dtype="float64")

        if (series < 0).any():
            errors.append("Negative pollutant values are not allowed")

        if series.isna().any():
            errors.append("NaN values are not allowed")

        return len(errors) == 0, errors

    @staticmethod
    def clean_readings_batch(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df = df.dropna(subset=["sensor_id", "timestamp"])

        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])

        pollutant_cols = [c for c in df.columns if c.lower() in {"pm25", "pm10", "no2", "o3"}]
        for col in pollutant_cols:
            df = df[df[col].isna() | (df[col] >= 0)]

        if "pm25" in df.columns:
            df = df[df["pm25"].isna() | (df["pm25"] <= 500)]

        return df

    @staticmethod
    def aggregate_by_sensor(df: pd.DataFrame) -> pd.DataFrame:
        pollutant_cols = [c for c in df.columns if c.lower() in {"pm25", "pm10", "no2", "o3"}]
        return df.groupby("sensor_id")[pollutant_cols].mean().reset_index()

    @staticmethod
    def filter_by_threshold(df: pd.DataFrame, col: str, max_value: float) -> pd.DataFrame:
        return df[df[col] <= max_value]

    @staticmethod
    def calculate_statistics(df: pd.DataFrame) -> pd.DataFrame:
        pollutant_cols = [c for c in df.columns if c.lower() in {"pm25", "pm10", "no2", "o3"}]
        stats = df[pollutant_cols].agg(["mean", "median", "min", "max", "std"])
        return stats
