"""Tests unitarios del dominio (sin navegador).

Cubren el proveedor de datos y el renderizador HTML. La verificación de la
interacción real en el navegador (cambio de dataset, redibujado del canvas) se
hace en vivo con la extensión Claude in Chrome, no aquí.
"""

from __future__ import annotations

import json
import re

import pytest

from metrics_app import (
    Dataset,
    HtmlDashboardRenderer,
    InMemoryMetricsProvider,
)


def test_provider_devuelve_ventas_y_visitas() -> None:
    datasets = InMemoryMetricsProvider().get_datasets()
    keys = {d.key for d in datasets}
    assert keys == {"ventas", "visitas"}
    for d in datasets:
        assert len(d.categories) == len(d.values)
        assert len(d.values) > 0


def test_dataset_rechaza_longitudes_incoherentes() -> None:
    with pytest.raises(ValueError):
        Dataset(key="x", label="X", unit="u", categories=("a", "b"), values=(1.0,))


def test_render_produce_html_autocontenido() -> None:
    html = HtmlDashboardRenderer().render(InMemoryMetricsProvider().get_datasets())

    # Estructura y contenido esperados.
    for needle in ("<canvas", "<select", "Ventas", "Visitas", "const MCP_DATA ="):
        assert needle in html, f"falta en el HTML: {needle}"

    # El token de datos debe haber sido sustituido.
    assert "__MCP_DATA__" not in html

    # Sin dependencias externas ni llamadas de red desde el iframe.
    assert "http://" not in html and "https://" not in html
    for banned in ("fetch(", "XMLHttpRequest", "WebSocket", "<script src"):
        assert banned not in html, f"el HTML no debe usar {banned}"

    # Los datos inyectados deben ser JSON válido.
    match = re.search(r"const MCP_DATA = (.*?);", html, re.S)
    assert match is not None
    data = json.loads(match.group(1))
    assert [d["key"] for d in data] == ["ventas", "visitas"]


def test_render_lista_vacia_lanza_error() -> None:
    with pytest.raises(ValueError):
        HtmlDashboardRenderer().render([])


def test_render_plantilla_sin_token_lanza_error() -> None:
    renderer = HtmlDashboardRenderer(template="<html>sin token</html>")
    with pytest.raises(ValueError):
        renderer.render(InMemoryMetricsProvider().get_datasets())
