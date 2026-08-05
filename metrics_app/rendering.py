"""Capa de presentación: construye el HTML autocontenido del dashboard.

Responsabilidad única (SRP): transformar una lista de `Dataset` en una cadena
HTML completa y autocontenida (sin CDNs, sin llamadas de red desde el iframe).
El servidor MCP y el generador de `preview.html` comparten este mismo
renderizador (DRY), de forma que el HTML que ve el modelo/host y el que se abre
en el navegador son idénticos por construcción.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from importlib import resources
from typing import Protocol, runtime_checkable

from metrics_app.datasets import Dataset

# Token que se sustituye por el JSON de datos dentro de la plantilla. Se usa un
# `str.replace` (y no `str.format` ni f-strings) a propósito: la plantilla
# contiene muchas llaves `{}` de CSS y JS que romperían el formateo.
_DATA_TOKEN = "__MCP_DATA__"  # noqa: S105 (no es un secreto, es un placeholder)

_TEMPLATE_PACKAGE = "metrics_app.templates"
_TEMPLATE_NAME = "dashboard.html"


@runtime_checkable
class DashboardRenderer(Protocol):
    """Abstracción de renderizado (DIP).

    Permite intercambiar la tecnología de presentación (HTML, otro motor de
    plantillas, etc.) sin tocar el servidor MCP.
    """

    def render(self, datasets: list[Dataset]) -> str:
        """Devuelve el HTML completo del panel para los datasets dados."""
        ...


class HtmlDashboardRenderer:
    """Renderizador concreto basado en una plantilla HTML autocontenida."""

    def __init__(self, template: str | None = None) -> None:
        """Crea el renderizador.

        Args:
            template: HTML de plantilla a usar. Si es `None`, se carga el
                recurso empaquetado `metrics_app/templates/dashboard.html`.
                Inyectar la plantilla facilita los tests (DIP).
        """
        self._template = template if template is not None else self._load_template()

    @staticmethod
    def _load_template() -> str:
        try:
            return (
                resources.files(_TEMPLATE_PACKAGE)
                .joinpath(_TEMPLATE_NAME)
                .read_text(encoding="utf-8")
            )
        except (FileNotFoundError, ModuleNotFoundError) as exc:
            raise FileNotFoundError(
                f"No se encontró la plantilla '{_TEMPLATE_NAME}' en el paquete "
                f"'{_TEMPLATE_PACKAGE}'."
            ) from exc

    def render(self, datasets: list[Dataset]) -> str:
        """Inyecta los datasets en la plantilla y devuelve el HTML final.

        Args:
            datasets: Datasets a mostrar. No puede estar vacío.

        Returns:
            HTML completo y autocontenido.

        Raises:
            ValueError: Si `datasets` está vacío o si la plantilla no contiene
                el token de datos esperado.
        """
        if not datasets:
            raise ValueError("Se requiere al menos un dataset para renderizar.")
        if _DATA_TOKEN not in self._template:
            raise ValueError(
                f"La plantilla no contiene el token de datos '{_DATA_TOKEN}'."
            )

        payload = [asdict(ds) for ds in datasets]
        # `ensure_ascii=False` mantiene los acentos legibles; el JSON se inserta
        # dentro de una etiqueta <script> como literal de objeto JS.
        data_json = json.dumps(payload, ensure_ascii=False)
        return self._template.replace(_DATA_TOKEN, data_json)
