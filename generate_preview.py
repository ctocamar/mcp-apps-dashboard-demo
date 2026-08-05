"""Genera `preview.html` a partir del MISMO renderizador que usa el servidor.

Ejecutar con:  uv run python generate_preview.py

Esto garantiza (DRY) que el fichero suelto `preview.html` — pensado para abrirse
directamente en un navegador, sin ningún host MCP — contiene exactamente el
mismo HTML que devuelve el tool `panel_metricas`.
"""

from __future__ import annotations

from pathlib import Path

from metrics_app import HtmlDashboardRenderer, InMemoryMetricsProvider

_OUTPUT = Path(__file__).parent / "preview.html"


def main() -> None:
    provider = InMemoryMetricsProvider()
    renderer = HtmlDashboardRenderer()
    html = renderer.render(provider.get_datasets())
    _OUTPUT.write_text(html, encoding="utf-8")
    print(f"preview.html generado ({len(html)} bytes) en {_OUTPUT}")


if __name__ == "__main__":
    main()
