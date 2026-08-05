"""Paquete de dominio de la demo MCP App `panel_metricas`.

Separa responsabilidades (SRP):

- `datasets`: modelo de datos y proveedor de métricas.
- `rendering`: construcción del HTML autocontenido del dashboard.

`server.py` (fuera del paquete) actúa como capa de composición/wiring MCP.
"""

from metrics_app.datasets import (
    Dataset,
    InMemoryMetricsProvider,
    MetricsProvider,
)
from metrics_app.rendering import DashboardRenderer, HtmlDashboardRenderer

__all__ = [
    "Dataset",
    "MetricsProvider",
    "InMemoryMetricsProvider",
    "DashboardRenderer",
    "HtmlDashboardRenderer",
]
