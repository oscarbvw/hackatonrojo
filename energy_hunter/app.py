"""Streamlit entry point for Energy Hunter.

This is a placeholder scaffolded by Task 1. The real assembly (sidebar,
map, telemetry, charts, panic panel, poller wiring) is implemented in
later tasks (see `.kiro/specs/energy-hunter-dashboard/tasks.md` → Task 14).

Run locally (once implemented):

    streamlit run energy_hunter/app.py
"""

from __future__ import annotations


def main() -> None:
    """Render the Energy Hunter dashboard.

    Implementation deferred to Task 14: "Wire app.py: assemble pages,
    start the poller, expose configuration".
    """
    # Intentionally empty placeholder. Streamlit does not require a function
    # entry point — `streamlit run app.py` simply executes the module — but
    # we expose `main()` so the module is importable and unit-testable
    # without side effects.
    return None


if __name__ == "__main__":  # pragma: no cover - executed by `streamlit run`
    main()
