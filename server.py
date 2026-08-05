"""Servidor MCP de demostración que expone la MCP App `panel_metricas`.

Este módulo es la capa de composición/wiring: instancia el framework MCP
(`fastmcp`), inyecta las implementaciones concretas del dominio
(`InMemoryMetricsProvider`, `HtmlDashboardRenderer`) tras sus abstracciones y
publica el tool que devuelve la interfaz interactiva como MCP App
(extensión oficial MCP Apps / SEP-1865), usando `mcp-ui-server`.

──────────────────────────────────────────────────────────────────────────────
NOTA DE AUTORIZACIÓN (importante para cuando esto deje de ser una demo)
──────────────────────────────────────────────────────────────────────────────
Esta demo NO expone datos reales ni requiere autenticación: los datos son
ficticios y viven en memoria. En el momento en que un tool toque datos reales,
hay que seguir la spec de autorización de MCP:

  * OAuth 2.1 como marco de autorización.
  * Tokens de acceso con la audiencia vinculada a ESTE servidor mediante
    Resource Indicators (RFC 8707); validar la audiencia en CADA llamada.
  * Nunca reenviar ("passthrough") a otro servidor un token emitido para uno
    distinto.
  * Aplicar el principio de mínimo privilegio (ver README, sección AppConfig).

Además: nada de secretos en el código. Cualquier credencial futura debe leerse
de variables de entorno (ver `os.environ` más abajo para el transporte).
"""

from __future__ import annotations

import os

from fastmcp import FastMCP
from mcp_ui_server import create_ui_resource
from mcp_ui_server.core import UIResource

from metrics_app import (
    DashboardRenderer,
    HtmlDashboardRenderer,
    InMemoryMetricsProvider,
    MetricsProvider,
)

# URI de la MCP App. Por convención de la extensión MCP Apps debe empezar por
# `ui://`. Es estable para que los hosts puedan cachear/identificar la app.
_APP_URI = "ui://panel-metricas/dashboard"

# --- Composición (Dependency Injection) --------------------------------------
# El tool depende de las abstracciones `MetricsProvider` y `DashboardRenderer`
# (DIP); aquí se eligen las implementaciones concretas. Cambiarlas no obliga a
# tocar la lógica del tool.
_provider: MetricsProvider = InMemoryMetricsProvider()
_renderer: DashboardRenderer = HtmlDashboardRenderer()

mcp: FastMCP = FastMCP("panel-metricas-demo")


def _build_dashboard_html() -> str:
    """Genera el HTML autocontenido del panel a partir de los datos actuales."""
    return _renderer.render(_provider.get_datasets())


@mcp.tool()
def panel_metricas() -> list[UIResource]:
    """Muestra un panel de métricas interactivo como interfaz embebida (MCP App).

    QUÉ HACE:
        Devuelve un mini-dashboard renderizable dentro de la conversación: un
        gráfico de barras con un selector para alternar entre dos datasets de
        negocio ("Ventas" y "Visitas"). Todo el cambio de dataset se resuelve en
        el propio cliente (JS del iframe), sin más llamadas al servidor.

    CUÁNDO USARLO:
        Cuando el usuario pida ver, visualizar, graficar o comparar métricas de
        negocio (ventas y/o visitas), o pida "un panel"/"un dashboard". No lo
        uses para preguntas que se respondan solo con texto o con un número
        suelto.

    Returns:
        Una lista con un único `UIResource` de tipo HTML embebido (rawHtml) que
        el host compatible con MCP Apps renderiza como interfaz interactiva.
    """
    resource = create_ui_resource(
        {
            "uri": _APP_URI,
            "content": {"type": "rawHtml", "htmlString": _build_dashboard_html()},
            "encoding": "text",
        }
    )
    return [resource]


@mcp.custom_route("/preview", methods=["GET"])
async def preview(_request):  # type: ignore[no-untyped-def]
    """Sirve el mismo HTML del panel por HTTP para previsualizar en el navegador.

    Útil cuando el servidor corre en un contenedor (ver docker-compose): permite
    abrir `http://localhost:8000/preview` sin necesidad de un host MCP.
    """
    from starlette.responses import HTMLResponse

    return HTMLResponse(_build_dashboard_html())


def main() -> None:
    """Arranca el servidor con el transporte indicado por variables de entorno.

    Variables (con valores por defecto pensados para uso local vía stdio):
        MCP_TRANSPORT: "stdio" (def.) | "streamable-http" | "sse".
        MCP_HOST:      host de escucha para transportes HTTP (def. "127.0.0.1").
        MCP_PORT:      puerto para transportes HTTP (def. "8000").
    """
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "stdio":
        mcp.run()
        return

    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8000"))
    mcp.run(transport=transport, host=host, port=port)


if __name__ == "__main__":
    main()
