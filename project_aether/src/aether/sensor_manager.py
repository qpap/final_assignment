
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

import pandas as pd

from .data_cleaning import DataCleaner
from .persistence import load_realtime_readings, save_realtime_readings
from .sensor import SensorInfo, SensorReading


class UnauthorizedSensorError(Exception):
    pass


class InvalidReadingError(Exception):
    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        super().__init__("Invalid readings")


class SensorNotFoundError(Exception):
    pass


class NoHistoricalDataError(Exception):
    pass


@dataclass
class StatusInfo:
    status: str
    uptime_seconds: float
    active_sensors: int
    total_readings: int
    last_update: Optional[datetime]


class SensorManager:
    def __init__(
        self,
        config: Dict[str, Any],
        sensors: Dict[str, SensorInfo],
        historical_df: pd.DataFrame,
    ) -> None:
        self.config = config
        self.sensors = sensors
        self.historical_df = historical_df

        self.storage_file: str = config["storage_file"]
        self.start_time = datetime.now(timezone.utc)
        self.total_readings: int = 0
        self._last_update: Optional[datetime] = None

        raw = load_realtime_readings(self.storage_file)
        self.readings: List[SensorReading] = []
        for r in raw:
            try:
                ts = datetime.fromisoformat(r["timestamp"])
            except Exception:
                continue
            sr = SensorReading(
                sensor_id=r["sensor_id"],
                readings=r["readings"],
                timestamp=ts,
            )
            self.readings.append(sr)
            self.total_readings += 1
            self._update_sensor_state(sr)

        if not self.historical_df.empty:
            self._attach_province_to_history()

    def _update_sensor_state(self, reading: SensorReading) -> None:
        sensor = self.sensors.get(reading.sensor_id)
        if sensor is None:
            return
        sensor.last_reading = reading.readings
        sensor.last_update = reading.timestamp
        if self._last_update is None or reading.timestamp > self._last_update:
            self._last_update = reading.timestamp

    def _persist_realtime(self) -> None:
        data = [r.to_dict() for r in self.readings]
        save_realtime_readings(self.storage_file, data)

    def _attach_province_to_history(self) -> None:
        meta_rows = []
        for s in self.sensors.values():
            meta_rows.append(
                {
                    "sensor_id": s.id,
                    "province": s.metadata.get("province"),
                    "region": s.metadata.get("region"),
                }
            )
        meta_df = pd.DataFrame(meta_rows)
        if meta_df.empty:
            return
        self.historical_df = self.historical_df.merge(
            meta_df, on="sensor_id", how="left"
        )

    def ingest_reading(
        self,
        sensor_id: str,
        readings: Dict[str, float],
        timestamp: Optional[datetime] = None,
    ) -> SensorReading:
        if sensor_id not in self.sensors:
            raise UnauthorizedSensorError(f"Sensor '{sensor_id}' is not authorized")

        ok, errors = DataCleaner.validate_readings(readings)
        if not ok:
            raise InvalidReadingError(errors)

        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        reading = SensorReading(sensor_id=sensor_id, readings=readings, timestamp=timestamp)
        self.readings.append(reading)
        self.total_readings += 1
        self._update_sensor_state(reading)
        self._persist_realtime()
        return reading

    def get_status(self) -> StatusInfo:
        active = sum(1 for s in self.sensors.values() if s.last_reading is not None)
        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        return StatusInfo(
            status="healthy",
            uptime_seconds=uptime,
            active_sensors=active,
            total_readings=self.total_readings,
            last_update=self._last_update,
        )

    def get_sensor_history(self, sensor_id: str) -> pd.DataFrame:
        if sensor_id not in self.sensors:
            raise SensorNotFoundError(sensor_id)
        if self.historical_df.empty:
            raise NoHistoricalDataError()
        df = self.historical_df[self.historical_df["sensor_id"] == sensor_id].copy()
        if df.empty:
            raise NoHistoricalDataError()
        return df.sort_values("timestamp")

    def get_distribution_data(self, year: int, month: int) -> pd.DataFrame:
        if self.historical_df.empty:
            raise NoHistoricalDataError()

        df = self.historical_df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df[
            (df["timestamp"].dt.year == year)
            & (df["timestamp"].dt.month == month)
        ]
        if df.empty:
            raise NoHistoricalDataError()
        if "province" not in df.columns:
            raise NoHistoricalDataError()
        return df

    def get_sensors_for_map(self) -> Dict[str, SensorInfo]:
        return self.sensors
