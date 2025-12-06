
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from aether.dependencies import (
    get_sensor_manager,
    get_visualizer,
    get_temporal_visualizer,
    initialize_services,
    reset_services,
    get_config,
)
from .models import IngestRequest, IngestResponse, StatusResponse
from .sensor_manager import (
    SensorManager,
    UnauthorizedSensorError,
    InvalidReadingError,
    SensorNotFoundError,
    NoHistoricalDataError,
)
from .visualization import MapVisualizer
from .temporal_visualization import TemporalVisualizer


def create_app(
    config_path: str = "config/server_config.json",
    sensors_path: str = "config/sensors.json",
) -> FastAPI:
    app = FastAPI(title="Project Aether - AQMS Backend")

    @app.on_event("startup")
    def startup_event() -> None:
        initialize_services(config_path, sensors_path)

    @app.on_event("shutdown")
    def shutdown_event() -> None:
        reset_services()

    @app.post("/ingest", response_model=IngestResponse)
    def ingest_data(
        request: IngestRequest,
        sensor_manager: Annotated[SensorManager, Depends(get_sensor_manager)],
    ) -> IngestResponse:
        try:
            reading = sensor_manager.ingest_reading(
                sensor_id=request.sensor_id,
                readings=request.readings,
            )
        except UnauthorizedSensorError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except InvalidReadingError as e:
            raise HTTPException(status_code=400, detail="; ".join(e.errors))

        return IngestResponse(
            status="ok",
            message="Reading ingested successfully",
            sensor_id=reading.sensor_id,
            timestamp=reading.timestamp,
        )

    @app.get("/map", response_class=HTMLResponse)
    def get_map(
        sensor_manager: Annotated[SensorManager, Depends(get_sensor_manager)],
        visualizer: Annotated[MapVisualizer, Depends(get_visualizer)],
    ) -> HTMLResponse:
        sensors = sensor_manager.get_sensors_for_map()
        html = visualizer.create_map(sensors)
        return HTMLResponse(content=html)

    @app.get("/status", response_model=StatusResponse)
    def get_status(
        sensor_manager: Annotated[SensorManager, Depends(get_sensor_manager)],
    ) -> StatusResponse:
        info = sensor_manager.get_status()
        return StatusResponse(
            status=info.status,
            uptime_seconds=info.uptime_seconds,
            active_sensors=info.active_sensors,
            total_readings=info.total_readings,
            last_update=info.last_update,
        )

    @app.get("/history/{sensor_id}", response_class=HTMLResponse)
    def get_history(
        sensor_id: str,
        sensor_manager: Annotated[SensorManager, Depends(get_sensor_manager)],
        temporal_visualizer: Annotated[TemporalVisualizer, Depends(get_temporal_visualizer)],
    ) -> HTMLResponse:
        try:
            df = sensor_manager.get_sensor_history(sensor_id)
        except SensorNotFoundError:
            raise HTTPException(status_code=404, detail="Sensor not found")
        except NoHistoricalDataError:
            raise HTTPException(status_code=404, detail="No historical data")

        html = temporal_visualizer.create_time_series(
            df=df,
            sensor_id=sensor_id,
            title=f"Historical readings for {sensor_id}",
        )
        return HTMLResponse(content=html)

    @app.get("/distribution/{year}/{month}", response_class=HTMLResponse)
    def get_distribution(
        year: int,
        month: int,
        sensor_manager: Annotated[SensorManager, Depends(get_sensor_manager)],
        temporal_visualizer: Annotated[TemporalVisualizer, Depends(get_temporal_visualizer)],
    ) -> HTMLResponse:
        if not (1 <= month <= 12):
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

        try:
            df = sensor_manager.get_distribution_data(year, month)
        except NoHistoricalDataError:
            raise HTTPException(status_code=404, detail="No data for specified period")

        config = get_config()
        thresholds = config["thresholds"]
        html = temporal_visualizer.create_distribution_chart(
            df=df,
            thresholds=thresholds,
            year=year,
            month=month,
        )
        return HTMLResponse(content=html)

    @app.get("/", response_class=HTMLResponse)
    def root() -> HTMLResponse:
        html = (
            "<html>"
            "<head><title>Project Aether</title></head>"
            "<body>"
            "<h1>Project Aether - Air Quality Monitoring</h1>"
            "<ul>"
            '<li><a href="/docs">API Docs (Swagger)</a></li>'
            '<li><a href="/status">System Status</a></li>'
            '<li><a href="/map">Real-Time Map</a></li>'
            '<li>History example: <a href="/history/sensor_amsterdam_001">/history/sensor_amsterdam_001</a></li>'
            '<li>Distribution example: <a href="/distribution/2024/1">/distribution/2024/1</a></li>'
            "</ul>"
            "</body>"
            "</html>"
        )
        return HTMLResponse(content=html)

    return app


app = create_app()
