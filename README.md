# mcp-apps-dashboard-demo

Servidor **MCP** de demostración en Python que expone un tool, **`panel_metricas`**,
el cual —en lugar de devolver solo texto— devuelve una **MCP App**: una interfaz
interactiva (mini-dashboard con gráfico de barras y un selector para alternar
entre los datasets *Ventas* y *Visitas*) que se renderiza dentro de la
conversación del host, siguiendo la extensión oficial **MCP Apps** (SEP-1865).

- **Framework de servidor:** [`fastmcp`](https://gofastmcp.com)
- **UI del tool:** [`mcp-ui-server`](https://pypi.org/project/mcp-ui-server/) con `create_ui_resource` y content type `rawHtml`
- **Python:** 3.10+ · **Gestor de dependencias:** [`uv`](https://docs.astral.sh/uv/)

> El cambio de dataset se resuelve **íntegramente en el cliente** (JS dentro del
> iframe): el HTML es autocontenido, sin dependencias externas ni llamadas de
> red desde la interfaz.

---

## ¿Qué es una "MCP App"?

MCP Apps (SEP-1865) es la extensión oficial de MCP que permite que un tool
devuelva una interfaz de usuario (HTML) que el host renderiza en un iframe
aislado, en lugar de solo texto. Esta demo usa el enfoque de **recurso UI
embebido** de `mcp-ui-server`: el tool devuelve un `UIResource` de tipo
`rawHtml` que los hosts compatibles con MCP Apps / mcp-ui saben pintar.

---

## Estructura del proyecto

```
.
├── server.py                     # Wiring MCP: instancia FastMCP + tool panel_metricas + ruta /preview
├── metrics_app/
│   ├── datasets.py               # Modelo de datos + proveedor de métricas (abstracción + impl. en memoria)
│   ├── rendering.py              # Renderizador del HTML autocontenido (abstracción + impl. HTML)
│   └── templates/dashboard.html  # Plantilla HTML/CSS/JS 100% autocontenida (canvas + selector)
├── generate_preview.py           # Regenera preview.html desde el MISMO renderizador (DRY)
├── preview.html                  # Copia suelta abrible en el navegador sin ningún host MCP
├── tests/test_rendering.py       # Tests unitarios (renderizador y proveedor)
├── Dockerfile / docker-compose.yml / .dockerignore
├── pyproject.toml / uv.lock / requirements.txt
├── .gitignore / LICENSE (MIT)
└── README.md
```

---

## Ejecución

### Con `uv` (recomendado, local)

```bash
uv sync                      # instala dependencias (crea .venv a partir de uv.lock)
uv run python server.py      # arranca el servidor MCP por stdio (transporte por defecto)
```

Ejecutar en modo HTTP (útil para probar sin un host MCP):

```bash
MCP_TRANSPORT=streamable-http MCP_HOST=127.0.0.1 MCP_PORT=8000 uv run python server.py
# En PowerShell:
#   $env:MCP_TRANSPORT="streamable-http"; $env:MCP_PORT="8000"; uv run python server.py
```

- Endpoint MCP: `http://localhost:8000/mcp`
- Previsualización HTML: `http://localhost:8000/preview`

### Con Docker / Compose (levantar fácil)

```bash
docker compose up --build
```

Levanta un único contenedor en modo `streamable-http`:

- MCP: `http://localhost:8000/mcp`
- Preview: `http://localhost:8000/preview`

### Ver el dashboard sin nada instalado

Abre **`preview.html`** directamente en el navegador. Para regenerarlo tras
cambiar los datos o la plantilla:

```bash
uv run python generate_preview.py
```

---

## Testing

Tests unitarios (renderizador y proveedor de datos, sin navegador):

```bash
uv run pytest
```

**Verificación de la interfaz en el navegador:** se realiza de forma interactiva
con la extensión **Claude in Chrome** (o abriendo `preview.html` a mano):
cargar la página, comprobar que el gráfico de barras se dibuja, cambiar el
selector de *Ventas* a *Visitas* y verificar que el canvas se redibuja. El HTML
expone hooks de observabilidad para facilitar esa comprobación sin leer píxeles:

- `document.body.dataset.currentDataset` → clave del dataset activo.
- `window.__chartTotal` / `window.__chartLabel` → total y etiqueta del dataset activo.

---

## Buenas prácticas aplicadas (y por qué)

- **Autorización (documentada, no implementada en la demo).** Esta demo no toca
  datos reales ni requiere auth. En cuanto un tool exponga datos reales hay que
  seguir la spec de autorización de MCP: **OAuth 2.1**, tokens de acceso con la
  **audiencia vinculada a este servidor** vía **Resource Indicators (RFC 8707)**,
  **validación en cada llamada**, y **nunca reenviar** un token emitido para otro
  servidor. *Por qué:* evita que un token robado o mal dirigido dé acceso a
  recursos que no le corresponden (confused deputy). Ver el bloque de nota en
  `server.py`.

- **Mínimo privilegio (least privilege).** Si se añadieran tools que **solo**
  debe invocar la interfaz (y no el modelo), se marcarían con
  `AppConfig(visibility=["app"])` para que no aparezcan en la lista de tools que
  ve el modelo:

  ```python
  from fastmcp.apps import AppConfig

  @mcp.tool(app=AppConfig(visibility=["app"]))
  def _solo_para_la_ui(...): ...
  ```

  *Por qué:* reduce la superficie de lo que el modelo puede llamar directamente.
  En esta demo **no** hace falta: hay un único tool y el cambio de dataset es JS
  del cliente, así que no se añade un tool que no se usa. (Nota: `AppConfig` es un
  concepto *native-apps* de `fastmcp` y no se mezcla con `create_ui_resource`;
  por eso aquí solo se documenta.)

- **Nada de secretos en el código.** No hay claves ni credenciales. La
  configuración sensible (si la hubiera) se lee de **variables de entorno**
  (ver `MCP_TRANSPORT`/`MCP_HOST`/`MCP_PORT`). *Por qué:* los secretos en el
  repositorio se filtran y son difíciles de rotar.

- **HTML autocontenido en iframe.** Sin CDNs, sin `fetch`/XHR/WebSocket, sin
  scripts externos. *Por qué:* la interfaz corre en un iframe *sandboxed*; no
  depender de la red la hace reproducible y reduce el riesgo de inyección o
  exfiltración.

- **Type hints y manejo de errores.** Funciones tipadas y validaciones con
  errores claros (`ValueError`/`FileNotFoundError`) en el proveedor y el
  renderizador. Sin dependencias sin usar (solo `fastmcp` y `mcp-ui-server`).

- **Reproducibilidad con `uv` + `uv.lock`.** El lockfile fija todas las versiones
  (incluidas transitivas). *Por qué:* mismos builds en local, en CI y en Docker.

- **Contenedores.** `Dockerfile` + `docker-compose.yml` para levantar el servidor
  con un comando. *Por qué:* paridad de entornos y arranque sin fricción.

### Arquitectura SOLID

- **SRP** — datos (`datasets.py`), presentación (`rendering.py`) y wiring
  MCP/HTTP (`server.py`) están separados.
- **OCP** — añadir un dataset nuevo = añadir un `Dataset` en el proveedor; no se
  toca ni el renderizador ni el tool.
- **LSP / ISP** — interfaces mínimas (`get_datasets()`, `render(datasets)`);
  cualquier implementación es intercambiable.
- **DIP** — el tool depende de las abstracciones `MetricsProvider` y
  `DashboardRenderer` (`typing.Protocol`); `server.py` inyecta las
  implementaciones concretas.
- **DRY** — el tool y `preview.html` comparten el mismo renderizador, así que el
  HTML es idéntico por construcción.

---

## Compatibilidad

El `UIResource` se renderiza en hosts que soporten la extensión **MCP Apps** /
`mcp-ui`. En hosts que aún no la soporten, el tool sigue siendo válido pero la
interfaz puede mostrarse como recurso en lugar de renderizarse.

## Licencia

[MIT](./LICENSE)
