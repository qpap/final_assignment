
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from .sensor import SensorInfo, parse_wkt_point


def load_config(path: str) -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_sensors(path: str) -> Dict[str, SensorInfo]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    sensors: Dict[str, SensorInfo] = {}
    for entry in raw:
        sensor_id = entry["id"]
        location = entry["location"]
        metadata = entry.get("metadata", {})

        parsed = parse_wkt_point(location)
        if parsed is None:
            continue

        lon, lat = parsed
        sensors[sensor_id] = SensorInfo(
            id=sensor_id,
            location=location,
            latitude=lat,
            longitude=lon,
            metadata=metadata,
        )

    return sensors


def load_historical_data(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


def load_realtime_readings(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    if isinstance(data, list):
        return data
    return []


def save_realtime_readings(path: str, readings: List[Dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(readings, f, ensure_ascii=False, indent=2)
