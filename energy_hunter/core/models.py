"""Core dataclasses for the Energy Hunter dashboard.

Deviation from ``design.md → "Data Models"``
--------------------------------------------
The design predates the canonical backend layer (``engine.py``,
``generar_dev.py``, ``generar_elec.py`` and ``historico_consumo.csv`` at
the workspace root). The wire format those modules produce is now the
source of truth for telemetry / pricing / persistence, so this module
adapts the dataclasses accordingly:

* ``Reading`` no longer carries ``voltage_v`` / ``current_a`` / ``mode``
  (the synthetic API does not emit them). It instead holds a ``status``
  field of type :data:`DifferentialStatus`, which mirrors the per-
  differential enum that ``engine.py`` produces
  (``OK | APAGADO | PRECIO_ALTO | ANOMALIA | PANICO``). The UI renders
  this straight through.
* ``PriceTick`` exposes the canonical ``eur_per_mwh`` value plus a
  derived :pyattr:`PriceTick.eur_per_kwh` property and a
  ``periodo_tarifario`` tag (``VALLE | LLANO | PUNTA``) so consumers
  don't redo the ``/1000`` conversion that ``engine._precio_kwh`` already
  documents.
* :data:`PhaseStatus` (``NORMAL | ECO_MODE``) stays — it is the UI-side
  representation used by the panic flow on user-defined phases — and is
  intentionally distinct from :data:`DifferentialStatus` to avoid
  collision with the engine's enum.
* ``Asset``, ``Phase``, ``Building``, ``PanicPayload``, ``PanicResult``
  remain as the design defines them: they describe the front-end domain
  (user-defined buildings, phases, assets, panic flow), not the wire
  data.
* Immutable runtime values (``Asset``, ``Reading``, ``PriceTick``,
  ``CostPoint``, ``PanicPayload``, ``PanicResult``) are
  ``@dataclass(frozen=True)``. ``Phase`` and ``Building`` stay mutable
  so the front-end CRUD path can replace lists in place per
  ``design.md``.

Zero non-stdlib imports — these dataclasses must remain importable in
test environments without ``streamlit`` / ``pandas``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

__all__ = [
    "Asset",
    "Building",
    "CostPoint",
    "DifferentialStatus",
    "PanicPayload",
    "PanicResult",
    "Phase",
    "PhaseStatus",
    "PriceTick",
    "Reading",
]


# --- Type aliases ---------------------------------------------------------- #

#: UI-side phase status used by the panic flow.
PhaseStatus = Literal["NORMAL", "ECO_MODE"]

#: Engine-side per-differential status (mirrors ``engine.py`` enum).
DifferentialStatus = Literal[
    "OK",
    "APAGADO",
    "PRECIO_ALTO",
    "ANOMALIA",
    "PANICO",
]

#: Tariff period emitted by ``engine._periodo_tarifario``.
PeriodoTarifario = Literal["VALLE", "LLANO", "PUNTA"]


# --- Front-end domain (user-defined) -------------------------------------- #


@dataclass(frozen=True)
class Asset:
    """A discrete piece of equipment hanging off a phase (e.g., HVAC unit)."""

    id: str
    name: str


@dataclass
class Phase:
    """A user-defined electrical phase / segment within a building.

    Mutable so the front-end CRUD path (``BuildingManager.upsert_phase``,
    ``set_phase_status``) can replace fields in place.
    """

    id: str
    name: str
    panic_enabled: bool
    assets: list[Asset] = field(default_factory=list)
    status: PhaseStatus = "NORMAL"


@dataclass
class Building:
    """A user-defined building shown on the Interactive Map."""

    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    phases: list[Phase] = field(default_factory=list)


# --- Runtime / wire payloads ---------------------------------------------- #


@dataclass(frozen=True)
class Reading:
    """A single per-differential telemetry sample.

    Constructed from a ``generar_dev`` device dict joined with the
    engine-computed ``status``. ``phase_id`` carries the ``device_id``
    (e.g., ``diff_01_01``) because that is the granularity the UI groups
    on; the underlying L1/L2/L3 phase tag lives inside the engine's
    differential entry.
    """

    building_id: str
    phase_id: str
    timestamp: datetime
    active_power_kw: float
    status: DifferentialStatus


@dataclass(frozen=True)
class PriceTick:
    """Hourly market price snapshot.

    The canonical field is ``eur_per_mwh`` (the unit ``generar_elec``
    emits and ``engine._precio_kwh`` divides). Use :pyattr:`eur_per_kwh`
    for the front-end-facing value to avoid duplicating state.
    """

    timestamp: datetime
    eur_per_mwh: float
    periodo_tarifario: PeriodoTarifario = "LLANO"

    @property
    def eur_per_kwh(self) -> float:
        """Price in €/kWh. Mirrors ``engine._precio_kwh``'s ``/1000``."""
        return self.eur_per_mwh / 1000.0


@dataclass(frozen=True)
class CostPoint:
    """A computed cost sample stored on the building's cost time series."""

    building_id: str
    timestamp: datetime
    consumption_kwh: float
    total_cost_eur: float
    is_anomaly: bool = False


# --- Panic flow ----------------------------------------------------------- #


@dataclass(frozen=True)
class PanicPayload:
    """Body POSTed to the Kiro webhook on panic confirmation."""

    building_id: str
    selected_phases: list[str]
    affected_assets: list[str]


@dataclass(frozen=True)
class PanicResult:
    """Outcome of a Kiro webhook call."""

    ok: bool
    status_code: int
    error: str | None = None
