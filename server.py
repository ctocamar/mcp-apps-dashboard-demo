"""Servidor MCP de demostración que expone la MCP App `panel_metricas`.

Este módulo es la capa de composición/wiring: instancia el framework MCP
(`fastmcp`), inyecta las implementaciones concretas del dominio
(`InMemoryMetricsProvider`, `HtmlDashboardRenderer`) tras sus abstracciones y
publica la interfaz interactiva siguiendo la extensión oficial **MCP Apps**
(SEP-1865, id `io.modelcontextprotocol/ui`).

Modelo usado: **recurso `ui://` predeclarado** (no embebido).
    * La UI se registra como un recurso MCP en `ui://panel-metricas/dashboard`
      con mimeType `text/html;profile=mcp-app`.
    * El tool `panel_metricas` NO devuelve el HTML embebido: lo referencia vía
      `_meta.ui.resourceUri` (lo hace `AppConfig`). El host compatible
      (p.ej. Claude Desktop) hace `resources/read` de ese `ui://` y lo pinta en
      un iframe aislado.
Este es el modelo que adopta SEP-1865; el estilo "recurso embebido en el
resultado del tool" (mcp-ui clásico) quedó deferido y varios hosts no lo pintan.

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
  * Aplicar el principio de mínimo privilegio (ver README, sección visibility).

Además: nada de secretos en el código. Cualquier credencial futura debe leerse
de variables de entorno (ver `os.environ` más abajo para el transporte).
"""

from __future__ import annotations

import os

from fastmcp import FastMCP
from fastmcp.apps import UI_MIME_TYPE, AppConfig

from metrics_app import (
    DashboardRenderer,
    HtmlDashboardRenderer,
    InMemoryMetricsProvider,
    MetricsProvider,
)

# URI de la MCP App. Por convención de la extensión MCP Apps debe empezar por
# `ui://`. Es estable para que el host pueda cachear/identificar la app.
_APP_URI = "ui://panel-metricas/dashboard"

# --- Composición (Dependency Injection) --------------------------------------
# El tool y el recurso dependen de las abstracciones `MetricsProvider` y
# `DashboardRenderer` (DIP); aquí se eligen las implementaciones concretas.
_provider: MetricsProvider = InMemoryMetricsProvider()
_renderer: DashboardRenderer = HtmlDashboardRenderer()

mcp: FastMCP = FastMCP("panel-metricas-demo")


def _build_dashboard_html() -> str:
    """Genera el HTML autocontenido del panel a partir de los datos actuales."""
    return _renderer.render(_provider.get_datasets())


@mcp.resource(_APP_URI, mime_type=UI_MIME_TYPE)
def dashboard_ui() -> str:
    """Recurso UI predeclarado (MCP Apps / SEP-1865).

    Devuelve el HTML autocontenido del mini-dashboard (gráfico de barras +
    selector Ventas/Visitas). El host lo carga en un iframe aislado cuando el
    tool `panel_metricas` lo referencia. Los datos van embebidos en el propio
    HTML y el cambio de dataset se resuelve en JS del cliente (sin más red).
    """
    return _build_dashboard_html()


@mcp.tool(app=AppConfig(resourceUri=_APP_URI, visibility=["model", "app"]))
def panel_metricas() -> str:
    """Muestra un panel de métricas interactivo como interfaz embebida (MCP App).

    QUÉ HACE:
        Abre un mini-dashboard renderizable dentro de la conversación: un
        gráfico de barras con un selector para alternar entre dos datasets de
        negocio ("Ventas" y "Visitas"). La interfaz vive en el recurso
        `ui://panel-metricas/dashboard`; este tool solo la referencia (vía
        `_meta.ui.resourceUri`) para que el host la pinte.

    CUÁNDO USARLO:
        Cuando el usuario pida ver, visualizar, graficar o comparar métricas de
        negocio (ventas y/o visitas), o pida "un panel"/"un dashboard". No lo
        uses para preguntas que se respondan solo con texto o un número suelto.

    Returns:
        Un texto breve de confirmación. La interfaz se renderiza a partir del
        recurso UI enlazado, no del texto devuelto aquí.
    """
    return "Panel de métricas listo: usa el selector para alternar entre Ventas y Visitas."


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


@mcp.custom_route("/preview", methods=["GET"])
async def preview(_request):  # type: ignore[no-untyped-def]
    """Sirve el mismo HTML del panel por HTTP para previsualizar en el navegador.

    Útil cuando el servidor corre en un contenedor (ver docker-compose): permite
    abrir `http://localhost:8000/preview` sin necesidad de un host MCP.
    """
    from starlette.responses import HTMLResponse

    return HTMLResponse(_build_dashboard_html())


if __name__ == "__main__":
    main()
