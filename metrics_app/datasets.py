"""Capa de datos de la demo.

Responsabilidad única (SRP): definir el modelo de un dataset de métricas y
exponer un proveedor de datos. El resto del sistema depende de la abstracción
`MetricsProvider` (DIP), no de la implementación concreta, de modo que cambiar
el origen de datos (fichero, base de datos, API...) no obliga a tocar ni el
renderizador ni el servidor MCP.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Dataset:
    """Un conjunto de métricas listo para graficar como barras.

    Attributes:
        key: Identificador estable y sin espacios (se usa en el `<select>` y en
            los hooks de test del HTML).
        label: Nombre legible mostrado al usuario (p.ej. "Ventas").
        unit: Unidad de la métrica (p.ej. "€" o "visitas").
        categories: Etiquetas del eje X (una por barra).
        values: Valores del eje Y; debe tener la misma longitud que
            `categories`.
    """

    key: str
    label: str
    unit: str
    categories: tuple[str, ...]
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.categories) != len(self.values):
            raise ValueError(
                f"El dataset '{self.key}' tiene {len(self.categories)} "
                f"categorías pero {len(self.values)} valores; deben coincidir."
            )
        if not self.categories:
            raise ValueError(f"El dataset '{self.key}' no tiene datos.")


@runtime_checkable
class MetricsProvider(Protocol):
    """Abstracción de origen de datos (ISP + DIP).

    Cualquier implementación que devuelva una lista de `Dataset` es válida y
    puede sustituir a otra sin afectar al renderizador ni al tool MCP (LSP).
    """

    def get_datasets(self) -> list[Dataset]:
        """Devuelve los datasets disponibles para el panel."""
        ...


class InMemoryMetricsProvider:
    """Proveedor de demo con datos hardcodeados en memoria.

    Los datos son ficticios y no constituyen secretos ni información sensible;
    por eso pueden vivir en el código. En un caso real, este proveedor se
    sustituiría por uno que lea de una fuente autenticada (ver nota de
    Autorización en `server.py`).
    """

    _MESES: tuple[str, ...] = ("Ene", "Feb", "Mar", "Abr", "May", "Jun")

    def get_datasets(self) -> list[Dataset]:
        return [
            Dataset(
                key="ventas",
                label="Ventas",
                unit="€",
                categories=self._MESES,
                values=(12400.0, 15800.0, 14200.0, 19100.0, 22600.0, 20800.0),
            ),
            Dataset(
                key="visitas",
                label="Visitas",
                unit="visitas",
                categories=self._MESES,
                values=(8200.0, 9100.0, 12500.0, 11800.0, 15300.0, 17600.0),
            ),
        ]
