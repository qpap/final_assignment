
from __future__ import annotations

from typing import Optional, Dict, Any

import pandas as pd

from .data_cleaning import DataCleaner
from .persistence import load_config, load_historical_data, load_sensors
from .sensor_manager import SensorManager
from .visualization import MapVisualizer
from .temporal_visualization import TemporalVisualizer

_sensor_manager: Optional[SensorManager] = None
_map_visualizer: Optional[MapVisualizer] = None
_temporal_visualizer: Optional[TemporalVisualizer] = None
_config: Optional[Dict[str, Any]] = None


def initialize_services(config_path: str, sensors_path: str) -> None:
    global _sensor_manager, _map_visualizer, _temporal_visualizer, _config

    _config = load_config(config_path)
    sensors = load_sensors(sensors_path)

    hist_df = load_historical_data(_config["historical_data_file"])
    if not hist_df.empty:
        hist_df = DataCleaner.clean_readings_batch(hist_df)
    else:
        hist_df = pd.DataFrame()

    _sensor_manager = SensorManager(
        config=_config,
        sensors=sensors,
        historical_df=hist_df,
    )

    _map_visualizer = MapVisualizer(
        thresholds=_config["thresholds"],
        map_config=_config["map_config"],
    )
    _temporal_visualizer = TemporalVisualizer()


def reset_services() -> None:
    global _sensor_manager, _map_visualizer, _temporal_visualizer, _config
    _sensor_manager = None
    _map_visualizer = None
    _temporal_visualizer = None
    _config = None


def get_sensor_manager() -> SensorManager:
    if _sensor_manager is None:
        raise RuntimeError("SensorManager is not initialized")
    return _sensor_manager


def get_visualizer() -> MapVisualizer:
    if _map_visualizer is None:
        raise RuntimeError("MapVisualizer is not initialized")
    return _map_visualizer


def get_temporal_visualizer() -> TemporalVisualizer:
    if _temporal_visualizer is None:
        raise RuntimeError("TemporalVisualizer is not initialized")
    return _temporal_visualizer


def get_config() -> Dict[str, Any]:
    if _config is None:
        raise RuntimeError("Config is not initialized")
    return _config
