
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict

WKT_POINT_PATTERN = re.compile(
    r"POINT\s*\(\s*(?P<lon>-?\d+\.?\d*)\s+(?P<lat>-?\d+\.?\d*)\s*\)",
    re.IGNORECASE,
)


class SensorReading:
    def __init__(
        self,
        sensor_id: str,
        readings: Dict[str, float],
        timestamp: datetime,
    ) -> None:
        self.sensor_id = sensor_id
        self.readings = readings
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "readings": self.readings,
            "timestamp": self.timestamp.isoformat(),
        }


class SensorInfo:
    def __init__(
        self,
        id: str,
        location: str,
        latitude: float,
        longitude: float,
        metadata: Dict[str, Any],
    ) -> None:
        self.id = id
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
        self.metadata = metadata
        self.last_reading: Dict[str, float] | None = None
        self.last_update: datetime | None = None


def parse_wkt_point(wkt: str) -> tuple[float, float] | None:
    match = WKT_POINT_PATTERN.fullmatch(wkt)
    if not match:
        return None
    lon = float(match.group("lon"))
    lat = float(match.group("lat"))
    if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
        return None
    return lon, lat
