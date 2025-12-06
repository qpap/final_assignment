
from __future__ import annotations

from typing import Dict, Any, List

import pandas as pd
import plotly.express as px

from .sensor import SensorInfo


class MapVisualizer:
    def __init__(self, thresholds: Dict[str, float], map_config: Dict[str, Any]) -> None:
        self.thresholds = thresholds
        self.map_config = map_config

    def _categorize_pm25(self, value: float | None) -> str:
        if value is None:
            return "No data"
        if value <= self.thresholds["pm25_safe"]:
            return "Safe"
        if value <= self.thresholds["pm25_moderate"]:
            return "Moderate"
        if value <= self.thresholds["pm25_danger"]:
            return "Unhealthy"
        return "Dangerous"

    def create_map(self, sensors: Dict[str, SensorInfo]) -> str:
        rows: List[Dict[str, Any]] = []
        for s in sensors.values():
            pm25 = None
            if s.last_reading is not None:
                pm25 = float(s.last_reading.get("pm25", 0.0))
            category = self._categorize_pm25(pm25)
            rows.append(
                {
                    "sensor_id": s.id,
                    "lat": s.latitude,
                    "lon": s.longitude,
                    "pm25": pm25,
                    "province": s.metadata.get("province"),
                    "region": s.metadata.get("region"),
                    "category": category,
                }
            )

        df = pd.DataFrame(rows)
        if df.empty:
            df = pd.DataFrame(
                [
                    {
                        "lat": 52.1,
                        "lon": 5.3,
                        "sensor_id": "No sensors",
                        "category": "No data",
                        "pm25": 0,
                    }
                ]
            )

        fig = px.scatter_mapbox(
            df,
            lat="lat",
            lon="lon",
            color="category",
            hover_name="sensor_id",
            hover_data={"pm25": True, "province": True, "region": True},
            zoom=self.map_config.get("default_zoom", 7),
        )
        fig.update_layout(
            mapbox_style=self.map_config.get("map_style", "open-street-map"),
            margin={"l": 0, "r": 0, "t": 30, "b": 0},
        )
        return fig.to_html(include_plotlyjs="cdn", full_html=True)
