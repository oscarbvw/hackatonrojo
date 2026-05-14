"""Unit tests for ``energy_hunter.core.models`` (Task 2.1).

Per the task brief these tests verify, against the dataclass layer only:

* equality / ``__eq__`` reflexivity for every dataclass,
* ``frozen=True`` enforcement for the immutable runtime values
  (``Asset``, ``Reading``, ``PriceTick``, ``CostPoint``,
  ``PanicPayload``, ``PanicResult``),
* mutability of ``Phase`` / ``Building`` (their fields are reassignable),
  while frozen children they hold remain immutable,
* ``default_factory`` correctness — every new instance gets its own list,
* round-trip via ``dataclasses.asdict`` / ``dataclasses.replace``,
* a contract test that a ``Reading`` is constructible from a
  ``generar_dev`` device payload plus an engine-style ``status``,
  locking the wire-format contract that later tasks will rely on.

Bridges from engine snapshots to ``Building`` / ``CostPoint`` belong to
later tasks and are intentionally out of scope here.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from energy_hunter.core.models import (
    Asset,
    Building,
    CostPoint,
    DifferentialStatus,
    PanicPayload,
    PanicResult,
    Phase,
    PhaseStatus,
    PriceTick,
    Reading,
)


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #

TZ = timezone(timedelta(hours=2))
TS = datetime(2026, 5, 14, 11, 56, 17, tzinfo=TZ)


@pytest.fixture
def asset() -> Asset:
    return Asset(id="hvac_01", name="HVAC Unit 1")


@pytest.fixture
def phase(asset: Asset) -> Phase:
    return Phase(
        id="L1",
        name="Phase A",
        panic_enabled=True,
        assets=[asset],
        status="NORMAL",
    )


@pytest.fixture
def building(phase: Phase) -> Building:
    return Building(
        id="edificio_01",
        name="Main Office",
        address="Calle Falsa 123",
        latitude=40.4168,
        longitude=-3.7038,
        phases=[phase],
    )


@pytest.fixture
def reading() -> Reading:
    return Reading(
        building_id="edificio_01",
        phase_id="diff_01_01",
        timestamp=TS,
        active_power_kw=9.5442,
        status="OK",
    )


@pytest.fixture
def price_tick() -> PriceTick:
    return PriceTick(
        timestamp=TS,
        eur_per_mwh=126.016,
        periodo_tarifario="LLANO",
    )


@pytest.fixture
def cost_point() -> CostPoint:
    return CostPoint(
        building_id="edificio_01",
        timestamp=TS,
        consumption_kwh=9.5442,
        total_cost_eur=1.2025,
        is_anomaly=False,
    )


@pytest.fixture
def panic_payload() -> PanicPayload:
    return PanicPayload(
        building_id="edificio_01",
        selected_phases=["L1"],
        affected_assets=["HVAC Unit 1"],
    )


@pytest.fixture
def panic_result() -> PanicResult:
    return PanicResult(ok=True, status_code=200, error=None)


# Helpers for round-tripping nested dataclasses through asdict.
def _phase_from_dict(d: dict[str, Any]) -> Phase:
    return Phase(
        id=d["id"],
        name=d["name"],
        panic_enabled=d["panic_enabled"],
        assets=[Asset(**a) for a in d["assets"]],
        status=d["status"],
    )


def _building_from_dict(d: dict[str, Any]) -> Building:
    return Building(
        id=d["id"],
        name=d["name"],
        address=d["address"],
        latitude=d["latitude"],
        longitude=d["longitude"],
        phases=[_phase_from_dict(p) for p in d["phases"]],
    )


# --------------------------------------------------------------------------- #
# Equality / reflexivity                                                      #
# --------------------------------------------------------------------------- #


class TestEquality:
    def test_asset_equality_is_reflexive(self, asset: Asset) -> None:
        assert asset == asset
        assert asset == Asset(id="hvac_01", name="HVAC Unit 1")
        assert asset != Asset(id="hvac_01", name="Different")

    def test_phase_equality(self, phase: Phase, asset: Asset) -> None:
        twin = Phase(
            id="L1", name="Phase A", panic_enabled=True, assets=[asset], status="NORMAL"
        )
        assert phase == twin
        assert phase != Phase(
            id="L2", name="Phase A", panic_enabled=True, assets=[asset], status="NORMAL"
        )

    def test_building_equality(self, building: Building, phase: Phase) -> None:
        twin = Building(
            id="edificio_01",
            name="Main Office",
            address="Calle Falsa 123",
            latitude=40.4168,
            longitude=-3.7038,
            phases=[phase],
        )
        assert building == twin

    def test_reading_equality(self, reading: Reading) -> None:
        assert reading == Reading(
            building_id="edificio_01",
            phase_id="diff_01_01",
            timestamp=TS,
            active_power_kw=9.5442,
            status="OK",
        )
        assert reading != dataclasses.replace(reading, status="ANOMALIA")

    def test_pricetick_equality(self, price_tick: PriceTick) -> None:
        assert price_tick == PriceTick(
            timestamp=TS, eur_per_mwh=126.016, periodo_tarifario="LLANO"
        )

    def test_costpoint_equality(self, cost_point: CostPoint) -> None:
        assert cost_point == CostPoint(
            building_id="edificio_01",
            timestamp=TS,
            consumption_kwh=9.5442,
            total_cost_eur=1.2025,
            is_anomaly=False,
        )

    def test_panicpayload_equality(self, panic_payload: PanicPayload) -> None:
        assert panic_payload == PanicPayload(
            building_id="edificio_01",
            selected_phases=["L1"],
            affected_assets=["HVAC Unit 1"],
        )

    def test_panicresult_equality(self, panic_result: PanicResult) -> None:
        assert panic_result == PanicResult(ok=True, status_code=200, error=None)
        assert panic_result != PanicResult(ok=False, status_code=500, error="boom")


# --------------------------------------------------------------------------- #
# Frozen enforcement                                                          #
# --------------------------------------------------------------------------- #


class TestFrozen:
    @pytest.mark.parametrize(
        ("instance_fixture", "field_name", "new_value"),
        [
            ("asset", "name", "renamed"),
            ("reading", "active_power_kw", 0.0),
            ("price_tick", "eur_per_mwh", 0.0),
            ("cost_point", "is_anomaly", True),
            ("panic_payload", "building_id", "edificio_99"),
            ("panic_result", "ok", False),
        ],
    )
    def test_frozen_assignment_raises(
        self,
        request: pytest.FixtureRequest,
        instance_fixture: str,
        field_name: str,
        new_value: object,
    ) -> None:
        instance = request.getfixturevalue(instance_fixture)
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(instance, field_name, new_value)


# --------------------------------------------------------------------------- #
# Mutability of Phase and Building, immutability of frozen children           #
# --------------------------------------------------------------------------- #


class TestMutability:
    def test_phase_fields_are_reassignable(self, phase: Phase) -> None:
        phase.name = "Renamed Phase"
        phase.panic_enabled = False
        phase.status = "ECO_MODE"
        assert phase.name == "Renamed Phase"
        assert phase.panic_enabled is False
        assert phase.status == "ECO_MODE"

    def test_phase_assets_list_is_mutable_but_assets_remain_frozen(
        self, phase: Phase
    ) -> None:
        new_asset = Asset(id="ups_01", name="UPS A")
        phase.assets.append(new_asset)
        assert new_asset in phase.assets
        with pytest.raises(dataclasses.FrozenInstanceError):
            phase.assets[0].name = "Tampered"

    def test_building_fields_are_reassignable(self, building: Building) -> None:
        building.name = "New Name"
        building.address = "Other"
        building.latitude = 0.0
        building.longitude = 0.0
        building.phases = []
        assert building.name == "New Name"
        assert building.phases == []


# --------------------------------------------------------------------------- #
# default_factory correctness                                                 #
# --------------------------------------------------------------------------- #


class TestDefaultFactories:
    def test_phase_assets_default_is_independent_per_instance(self) -> None:
        a = Phase(id="L1", name="A", panic_enabled=False)
        b = Phase(id="L2", name="B", panic_enabled=False)
        assert a.assets == []
        assert b.assets == []
        assert a.assets is not b.assets
        a.assets.append(Asset(id="x", name="x"))
        assert b.assets == []

    def test_building_phases_default_is_independent_per_instance(self) -> None:
        a = Building(id="b1", name="A", address="x", latitude=0.0, longitude=0.0)
        b = Building(id="b2", name="B", address="y", latitude=0.0, longitude=0.0)
        assert a.phases == []
        assert b.phases == []
        assert a.phases is not b.phases
        a.phases.append(Phase(id="L1", name="A", panic_enabled=False))
        assert b.phases == []

    def test_phase_default_status_is_normal(self) -> None:
        p = Phase(id="L1", name="A", panic_enabled=False)
        assert p.status == "NORMAL"

    def test_costpoint_default_is_anomaly_false(self) -> None:
        cp = CostPoint(
            building_id="b", timestamp=TS, consumption_kwh=1.0, total_cost_eur=0.1
        )
        assert cp.is_anomaly is False

    def test_panicresult_default_error_is_none(self) -> None:
        assert PanicResult(ok=True, status_code=200).error is None


# --------------------------------------------------------------------------- #
# Round-trip via dataclasses.asdict and dataclasses.replace                   #
# --------------------------------------------------------------------------- #


class TestAsdictRoundTrip:
    def test_asset_roundtrip(self, asset: Asset) -> None:
        assert Asset(**dataclasses.asdict(asset)) == asset

    def test_reading_roundtrip(self, reading: Reading) -> None:
        assert Reading(**dataclasses.asdict(reading)) == reading

    def test_pricetick_roundtrip(self, price_tick: PriceTick) -> None:
        assert PriceTick(**dataclasses.asdict(price_tick)) == price_tick

    def test_costpoint_roundtrip(self, cost_point: CostPoint) -> None:
        assert CostPoint(**dataclasses.asdict(cost_point)) == cost_point

    def test_panicpayload_roundtrip(self, panic_payload: PanicPayload) -> None:
        assert PanicPayload(**dataclasses.asdict(panic_payload)) == panic_payload

    def test_panicresult_roundtrip(self, panic_result: PanicResult) -> None:
        assert PanicResult(**dataclasses.asdict(panic_result)) == panic_result

    def test_phase_roundtrip_via_helper(self, phase: Phase) -> None:
        d = dataclasses.asdict(phase)
        assert d["assets"] == [{"id": "hvac_01", "name": "HVAC Unit 1"}]
        assert _phase_from_dict(d) == phase

    def test_building_roundtrip_via_helper(self, building: Building) -> None:
        d = dataclasses.asdict(building)
        assert _building_from_dict(d) == building


class TestReplace:
    def test_replace_returns_new_instance_without_mutating_original(
        self, reading: Reading
    ) -> None:
        new = dataclasses.replace(reading, status="PRECIO_ALTO")
        assert new is not reading
        assert new.status == "PRECIO_ALTO"
        assert reading.status == "OK"

    def test_replace_works_on_mutable_dataclasses(self, building: Building) -> None:
        new = dataclasses.replace(building, name="Annex")
        assert new is not building
        assert new.name == "Annex"
        assert building.name == "Main Office"

    def test_replace_preserves_unchanged_fields(
        self, panic_payload: PanicPayload
    ) -> None:
        new = dataclasses.replace(panic_payload, building_id="edificio_99")
        assert new.selected_phases == panic_payload.selected_phases
        assert new.affected_assets == panic_payload.affected_assets


# --------------------------------------------------------------------------- #
# PriceTick conversion contract                                               #
# --------------------------------------------------------------------------- #


class TestPriceTickConversion:
    def test_eur_per_kwh_property_divides_by_one_thousand(
        self, price_tick: PriceTick
    ) -> None:
        assert price_tick.eur_per_kwh == pytest.approx(0.126016, rel=1e-12)

    def test_eur_per_kwh_handles_zero(self) -> None:
        zero = PriceTick(timestamp=TS, eur_per_mwh=0.0, periodo_tarifario="VALLE")
        assert zero.eur_per_kwh == 0.0


# --------------------------------------------------------------------------- #
# Contract: build a Reading from a generar_dev device dict + a status         #
# --------------------------------------------------------------------------- #


class TestGenerarDevContract:
    """Lock the wire-format contract between ``generar_dev`` and ``Reading``.

    The bridge code lives in a later task; this test just ensures the shape
    we assume — ``building_id``, ``device_id`` → ``phase_id``, ``timestamp``,
    ``power_kw``, ``active`` — is representable as a ``Reading`` without
    loss. It guards against accidental drift from the wire contract.
    """

    def test_reading_from_device_payload(self) -> None:
        device = {
            "building_id": "edificio_01",
            "device_id": "diff_01_01",
            "phase_id": "L1",
            "active": True,
            "power_kw": 9.5442,
            "timestamp": "2026-05-14T11:56:17.000+02:00",
        }
        reading = Reading(
            building_id=str(device["building_id"]),
            phase_id=str(device["device_id"]),
            timestamp=datetime.fromisoformat(str(device["timestamp"])),
            active_power_kw=float(device["power_kw"]) if device["active"] else 0.0,
            status="OK",
        )
        assert reading.building_id == "edificio_01"
        assert reading.phase_id == "diff_01_01"
        assert reading.active_power_kw == pytest.approx(9.5442)
        assert reading.status == "OK"
        assert reading.timestamp.utcoffset() == timedelta(hours=2)

    @pytest.mark.parametrize(
        "status", ["OK", "APAGADO", "PRECIO_ALTO", "ANOMALIA", "PANICO"]
    )
    def test_reading_status_accepts_engine_enum_values(self, status: str) -> None:
        r = Reading(
            building_id="b",
            phase_id="L1",
            timestamp=TS,
            active_power_kw=0.0,
            status=status,  # type: ignore[arg-type]
        )
        assert r.status == status


# --------------------------------------------------------------------------- #
# Type aliases must remain stable                                             #
# --------------------------------------------------------------------------- #


def test_phasestatus_alias_exposes_normal_and_eco_mode() -> None:
    """PhaseStatus is consumed by the panic flow and must not drift."""
    assert set(PhaseStatus.__args__) == {"NORMAL", "ECO_MODE"}


def test_differentialstatus_alias_mirrors_engine_enum() -> None:
    """DifferentialStatus must mirror engine.py status enum exactly."""
    assert set(DifferentialStatus.__args__) == {
        "OK",
        "APAGADO",
        "PRECIO_ALTO",
        "ANOMALIA",
        "PANICO",
    }
