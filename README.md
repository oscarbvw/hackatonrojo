# Energy Hunter

**Energy Hunter** is a B2B Energy Management Dashboard MVP built as a single-page
Streamlit application backed by a local Mock API server. It supports geographic
+ structural management of multiple buildings, real-time per-phase telemetry
with anomaly detection, and a granular Panic Button that fires a Kiro webhook
to put selected phases into Eco Mode.

> Status: scaffolding. See `.kiro/specs/energy-hunter-dashboard/` for the full
> requirements, design, and task plan that drive this implementation.

## Project layout

```
energy_hunter/
├── app.py            # Streamlit entry point (placeholder)
├── ui/               # Streamlit views (layout, map, forms, panic, charts, a11y)
├── core/             # Pure logic: models, building manager, anomaly, cost, panic, poller
├── clients/          # HTTP clients for the Mock API and Kiro webhook
├── mock_api/         # Local Flask Mock API + Kiro webhook stub
└── data/             # Historical dataset (CSV)
tests/                # pytest + hypothesis test suite
```

## Local development

The project targets **Python 3.11+**.

```bash
# Create a virtual environment (Windows PowerShell shown)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install runtime + dev dependencies
pip install -e ".[dev]"

# Run the test suite
pytest

# Lint and type-check (core/ and clients/ run under mypy --strict)
ruff check .
mypy
```

## Running the app

> The Streamlit app and Mock API server are not wired up yet — they land in
> later tasks of the spec. Once implemented, the demo will be:
>
> ```bash
> # Terminal 1 — Mock API server (Smart Breaker + SIOS + Eco endpoints)
> python -m energy_hunter.mock_api
>
> # Terminal 2 — Streamlit dashboard
> streamlit run energy_hunter/app.py
> ```

## Standards

- **TDD** per workspace `development-standards.md`: every behavior change starts
  with a failing test (unit + property-based where applicable).
- **Conventional Commits** for every logical unit of work.
- **WCAG 2.1 AA** target for the UI, to the extent Streamlit allows; deviations
  are documented in `design.md → Accessibility`.
