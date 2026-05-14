"""Sanity tests for the project scaffold (Task 1).

These tests verify only that the package skeleton, configuration files,
and data placeholder exist and are importable. Real functional tests
live alongside their respective modules (added in later tasks).
"""

from __future__ import annotations

from pathlib import Path

import energy_hunter


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def test_package_version_is_exposed() -> None:
    """The top-level package exposes a version string."""
    assert isinstance(energy_hunter.__version__, str)
    assert energy_hunter.__version__  # non-empty


def test_subpackages_are_importable() -> None:
    """All declared sub-packages from design.md → 'Module layout' import cleanly."""
    import importlib

    for name in (
        "energy_hunter.ui",
        "energy_hunter.core",
        "energy_hunter.clients",
        "energy_hunter.mock_api",
        "energy_hunter.data",
    ):
        module = importlib.import_module(name)
        assert module is not None, f"failed to import {name}"


def test_historical_csv_placeholder_exists_with_header() -> None:
    """The historical dataset placeholder exists with the documented header row.

    Downstream tasks (anomaly detector, integration tests) reference this path,
    so even an empty file with a header keeps the contract honest.
    """
    csv_path = WORKSPACE_ROOT / "energy_hunter" / "data" / "historical.csv"
    assert csv_path.exists(), f"missing placeholder dataset at {csv_path}"

    header = csv_path.read_text(encoding="utf-8").splitlines()[0]
    assert header == "building_id,timestamp,consumption_kwh"


def test_streamlit_config_present() -> None:
    """The Streamlit theme/runtime config is present at the documented path."""
    config_path = WORKSPACE_ROOT / ".streamlit" / "config.toml"
    assert config_path.exists(), f"missing Streamlit config at {config_path}"
    contents = config_path.read_text(encoding="utf-8")
    # Spot-check the documented contrast-friendly tokens are still in place.
    assert "[theme]" in contents
    assert "primaryColor" in contents
