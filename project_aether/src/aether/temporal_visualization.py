
from __future__ import annotations

from typing import Dict, Any

import pandas as pd
import plotly.graph_objects as go


class TemporalVisualizer:
    def create_time_series(
        self,
        df: pd.DataFrame,
        sensor_id: str,
        title: str,
    ) -> str:
        fig = go.Figure()

        pollutants = ["pm25", "pm10", "no2", "o3"]
        for col in pollutants:
            if col in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df["timestamp"],
                        y=df[col],
                        mode="lines",
                        name=col.upper(),
                    )
                )

        fig.update_layout(
            title=title,
            xaxis=dict(
                title="Time",
                rangeslider=dict(visible=True),
            ),
            yaxis=dict(title="Concentration (µg/m³)"),
            hovermode="x unified",
        )
        return fig.to_html(include_plotlyjs="cdn", full_html=True)

    def create_distribution_chart(
        self,
        df: pd.DataFrame,
        thresholds: Dict[str, float],
        year: int,
        month: int,
    ) -> str:
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        def categorize(value: float | None) -> str:
            if value is None:
                return "No data"
            if value <= thresholds["pm25_safe"]:
                return "Safe"
            if value <= thresholds["pm25_moderate"]:
                return "Moderate"
            if value <= thresholds["pm25_danger"]:
                return "Unhealthy"
            return "Dangerous"

        df["category"] = df["pm25"].apply(categorize)

        group = df.groupby(["province", "category"]).size().reset_index(name="count")

        total_per_province = group.groupby("province")["count"].transform("sum")
        group["percentage"] = group["count"] / total_per_province * 100.0

        provinces = group["province"].unique().tolist()
        categories = ["Safe", "Moderate", "Unhealthy", "Dangerous", "No data"]

        fig = go.Figure()

        for cat in categories:
            sub = group[group["category"] == cat]
            y_values = []
            for prov in provinces:
                row = sub[sub["province"] == prov]
                if row.empty:
                    y_values.append(0.0)
                else:
                    y_values.append(float(row["percentage"].iloc[0]))

            fig.add_bar(
                x=provinces,
                y=y_values,
                name=cat,
                text=[f"{v:.1f}%" for v in y_values],
                textposition="inside",
            )

        fig.update_layout(
            barmode="stack",
            title=f"PM2.5 Distribution by Province ({year}-{month:02d})",
            xaxis_title="Province",
            yaxis_title="Percentage of readings",
            yaxis=dict(range=[0, 100]),
        )
        return fig.to_html(include_plotlyjs="cdn", full_html=True)
