# Implementation Plan: Energy Hunter Dashboard MVP
<<<<<<< HEAD
 
## Overview
 
This plan turns the Energy Hunter design into a TDD-driven, incremental Python build. Foundations come first (project scaffolding, dataclasses, Mock API state and endpoints), then the pure logic layer (validation, cost, anomaly detection, panic payload, poller), then the Streamlit UI, then the Kiro stub, and finally integration and accessibility verification.
 
=======

## Overview

This plan turns the Energy Hunter design into a TDD-driven, incremental Python build. Foundations come first (project scaffolding, dataclasses, Mock API state and endpoints), then the pure logic layer (validation, cost, anomaly detection, panic payload, poller), then the Streamlit UI, then the Kiro stub, and finally integration and accessibility verification.

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
Conventions used in this plan:
- **TDD per workspace standard**: every unit of logic has a test sub-task that comes before or alongside the implementation sub-task. Test sub-tasks are marked optional with `*` per the workflow rules — they are still authored first under TDD, but the marker preserves the "skip-for-MVP" affordance defined in the workflow.
- **Property-based tests** (Hypothesis) map 1:1 to the 10 Correctness Properties in `design.md`.
- **Responsive + WCAG 2.1 AA** tasks appear inline with the UI components they apply to, and again as a final accessibility audit task.
- **Conventional Commits**: a suggested commit message is provided for each top-level task.
- **Requirements references** point at granular acceptance criteria (e.g. `1.3`, `8.4`), not just user stories.
<<<<<<< HEAD
 
## Tasks
 
- [x] 1. Bootstrap the project skeleton, dependencies, and tooling
=======

## Tasks

- [-] 1. Bootstrap the project skeleton, dependencies, and tooling
>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
  - Create the package layout described in `design.md` → "Module layout": `energy_hunter/{ui,core,clients,mock_api,data}/` with `__init__.py` files, plus top-level `app.py` placeholder, `tests/`, `pyproject.toml`, `.streamlit/config.toml`, and `README.md` stub.
  - Pin runtime deps in `pyproject.toml`: `streamlit`, `flask`, `pandas`, `altair`, `pydeck`, `requests`.
  - Pin dev deps: `pytest`, `pytest-cov`, `hypothesis`, `ruff`, `mypy`.
  - Add `pytest` config (rootdir, `testpaths=["tests"]`) and `ruff`/`mypy` config sections targeting `core/` and `clients/` for `mypy --strict`.
  - Add `data/historical.csv` placeholder (header row only) so downstream tasks can reference the path.
  - _Requirements: 8.5_
  - _Design refs: "Module layout", "CI gates"_
  - _Suggested commit: `chore: scaffold energy_hunter package and tooling`_
<<<<<<< HEAD
 
=======

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
- [ ] 2. Define core dataclasses and the SessionStore protocol
  - [~] 2.1 Write unit tests for `core/models.py`
    - Verify equality, immutability of frozen dataclasses, default factories, and round-trip via `dataclasses.asdict` / `replace` for `Asset`, `Phase`, `Building`, `Reading`, `PriceTick`, `CostPoint`, `PanicPayload`, `PanicResult`.
    - _Requirements: 1.2, 2.1, 2.2, 2.3, 2.4, 3.2, 3.4, 5.3_
    - _Design refs: "Data Models"_
    - _Suggested commit: `test: add unit tests for core dataclasses`_
  - [~] 2.2 Implement `core/models.py` with all dataclasses from the design
    - Mirror the `Data Models` section exactly: `PhaseStatus = Literal["NORMAL","ECO_MODE"]`, `Asset`, `Phase`, `Building`, `Reading`, `PriceTick`, `CostPoint`, `PanicPayload`, `PanicResult`.
    - _Requirements: 1.2, 2.1, 2.2, 2.3, 2.4, 3.2, 3.4, 5.3_
    - _Design refs: "Data Models"_
    - _Suggested commit: `feat: add core dataclasses for buildings, telemetry, and panic payload`_
  - [~] 2.3 Define `SessionStore` protocol and an in-memory `DictSessionStore` test double
    - Protocol exposes `get(key, default)`, `set(key, value)`, `setdefault(key, factory)` over a dict-like backing.
    - Provide `DictSessionStore` for tests and a `StreamlitSessionStore` adapter (thin wrapper around `st.session_state`) for runtime use.
    - _Requirements: 1.2, 2.4_
    - _Design refs: "Building_Manager", "st.session_state shape"_
    - _Suggested commit: `feat: add SessionStore protocol with dict-based test double`_
<<<<<<< HEAD
 
=======

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
- [ ] 3. Implement Building_Manager with TDD-driven validation and CRUD
  - [~] 3.1 Write the property test for **Property 1: Building round-trip persistence**
    - **Property 1: Building round-trip persistence**
    - **Validates: Requirements 1.2, 2.1, 2.3, 2.4**
    - Use a Hypothesis `@composite` strategy that generates `Building` instances with arbitrary phases, panic flags, and asset lists; assert that after `add_building(b)`, both `get(b.id)` and `list_buildings()` reflect a deeply equal building.
    - Configure `@settings(max_examples=100, derandomize=True)`.
    - _Design refs: "Correctness Properties → Property 1", "Component-level TDD plan"_
    - _Suggested commit: `test: add PBT for building round-trip persistence (Property 1)`_
  - [~] 3.2 Write the property test for **Property 2: Validation predicate matches accept/reject**
    - **Property 2: Validation predicate**
    - **Validates: Requirements 1.3**
    - Generate `(name, address, latitude, longitude)` tuples that are uniformly valid and invalid (using filtered/`one_of` strategies). Assert `ValidationError` iff the documented predicate rejects, and assert the store is unchanged on rejection.
    - _Design refs: "Building_Manager → Validation rules"_
    - _Suggested commit: `test: add PBT for building input validation (Property 2)`_
  - [~] 3.3 Implement `core/building_manager.py`
    - `validate_building_input(name, address, lat, lon)` enforces non-empty trimmed strings, `len(name) ≤ 120`, `lat ∈ [-90, 90]`, `lon ∈ [-180, 180]`; raises `ValidationError(field, message)` on failure.
    - `BuildingManager` provides `add_building`, `update_building`, `delete_building`, `list_buildings`, `get`, `upsert_phase`, `set_phase_status` over a `SessionStore`.
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 5.4_
    - _Design refs: "Building_Manager"_
    - _Suggested commit: `feat: implement BuildingManager CRUD with input validation`_
  - [~] 3.4 Write unit tests for `set_phase_status`, `upsert_phase`, and `delete_building`
    - Cover NORMAL ↔ ECO_MODE transitions, replacing an existing phase by id, and deletion of a nonexistent building (no-op vs. raise — match implementation).
    - _Requirements: 2.4, 5.4_
    - _Suggested commit: `test: add unit tests for phase upsert and status transitions`_
<<<<<<< HEAD
 
=======

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
- [ ] 4. Implement the Mock API Server (Smart Breaker, SIOS, and Eco endpoints)
  - [~] 4.1 Write the property test for **Property 8: Mock server state isolation and Eco reduction**
    - **Property 8: Mock server state isolation and 40% Eco reduction**
    - **Validates: Requirements 8.2, 8.4**
    - Generate sequences of `read`, `set_eco`, `clear_eco` operations across multiple `(building_id, phase_id)` keys, asserting that the observed state of any key depends only on operations targeting that key, and that after `set_eco(k)` a subsequent `GET /breaker/...` reports `0.6 * baseline_power_kw` within the documented jitter tolerance. Use Flask's `test_client` (no real sockets).
    - _Design refs: "Correctness Properties → Property 8", "Mock_API_Server"_
    - _Suggested commit: `test: add PBT for mock server state isolation and eco reduction (Property 8)`_
  - [~] 4.2 Implement `mock_api/state.py`
    - `PhaseState(baseline_power_kw, mode, last_reading_ts)` keyed by `(building_id, phase_id)`.
    - Lazy provisioning helper `get_or_create(building_id, phase_id)` with a deterministic baseline (e.g., hash-seeded jitter range).
    - _Requirements: 8.2_
    - _Design refs: "Mock_API_Server", "State"_
    - _Suggested commit: `feat: add mock api in-memory per-phase state container`_
  - [~] 4.3 Implement `mock_api/server.py` with Flask routes
    - `GET /breaker/{building_id}/{phase_id}` → returns `active_power_kW = baseline * (0.6 if ECO_MODE else 1.0)` with small jitter, plus `voltage_v`, `current_a`, `mode`.
    - `GET /sios/price` → returns `eur_per_mwh` and timestamp for the current hour.
    - `POST /breaker/{building_id}/{phase_id}/eco` → switches mode to `ECO_MODE` (idempotent).
    - `GET /healthz` → `200`.
    - _Requirements: 3.1, 3.3, 8.1, 8.2, 8.3, 8.4_
    - _Design refs: "Mock_API_Server" table_
    - _Suggested commit: `feat: implement mock api server with breaker, sios, and eco endpoints`_
  - [~] 4.4 Add a `python -m energy_hunter.mock_api` entry point
    - `__main__.py` boots the Flask app on `localhost:8000` with a single command and zero external dependencies.
    - _Requirements: 8.1, 8.5_
    - _Design refs: "Process & runtime model"_
    - _Suggested commit: `feat: add single-command entry point for mock api server`_
  - [~] 4.5 Add a smoke test that boots the Flask app via `test_client` and asserts `/healthz` → 200
    - _Requirements: 8.5_
    - _Suggested commit: `test: add smoke test for mock api healthz endpoint`_
<<<<<<< HEAD
 
- [~] 5. Checkpoint — Foundations stable
  - Ensure all tests pass, ask the user if questions arise.
 
=======

- [~] 5. Checkpoint — Foundations stable
  - Ensure all tests pass, ask the user if questions arise.

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
- [ ] 6. Implement HTTP clients for the Mock API
  - [~] 6.1 Write integration tests for `clients/breaker_client.py` and `clients/sios_client.py`
    - Use Flask's `test_client` (no real sockets) and assert the clients return well-formed `Reading` and `PriceTick` instances, propagate timeouts and 5xx as raised exceptions, and never lose data on malformed JSON (raise typed errors instead).
    - _Requirements: 3.1, 3.2, 3.3, 3.5_
    - _Design refs: "Module layout → clients/", "Error Handling"_
    - _Suggested commit: `test: add integration tests for breaker and sios clients`_
  - [~] 6.2 Implement `clients/breaker_client.py`
    - `fetch_reading(building_id, phase_id, *, timeout_s=5.0) -> Reading`; uses `requests` with explicit timeouts and parses into the `Reading` dataclass.
    - _Requirements: 3.1, 3.2, 3.5_
    - _Suggested commit: `feat: add smart breaker http client`_
  - [~] 6.3 Implement `clients/sios_client.py`
    - `fetch_current_price(*, timeout_s=5.0) -> PriceTick`.
    - _Requirements: 3.3, 3.5_
    - _Suggested commit: `feat: add sios http client`_
<<<<<<< HEAD
 
=======

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
- [ ] 7. Implement pure logic: cost calculator, anomaly detector, panic payload builder
  - [~] 7.1 Write the property test for **Property 5: Cost formula**
    - **Property 5: Cost formula**
    - **Validates: Requirements 3.4**
    - Use Hypothesis `floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False)` for both inputs and assert `calculate_cost(p, q) == pytest.approx(p * q / 1000, rel=1e-9, abs=1e-12)`.
    - _Design refs: "Correctness Properties → Property 5"_
    - _Suggested commit: `test: add PBT for cost formula (Property 5)`_
  - [~] 7.2 Implement `core/cost.py`
    - `calculate_cost(power_kw: float, price_eur_per_mwh: float) -> float` returning `power_kw * (price_eur_per_mwh / 1000)`.
    - _Requirements: 3.4_
    - _Suggested commit: `feat: add cost calculator (power × price / 1000)`_
  - [~] 7.3 Write the property test for **Property 4: Sunday anomaly rule**
    - **Property 4: Sunday anomaly rule**
    - **Validates: Requirements 4.1, 4.2**
    - Generate `building_id, timestamp, consumption_kwh` DataFrames with a Hypothesis composite strategy; assert each row's `is_anomaly` matches `(weekday == 6) and (consumption > 1.40 * weekday_baseline[building_id])`. Cover the empty-frame, no-weekday-rows, and zero-baseline edge cases as separate examples.
    - _Design refs: "Correctness Properties → Property 4", "Anomaly_Detector"_
    - _Suggested commit: `test: add PBT for sunday anomaly rule (Property 4)`_
  - [~] 7.4 Implement `core/anomaly_detector.py`
    - `detect_anomalies(df: pd.DataFrame, threshold: float = 1.40) -> pd.DataFrame` adding `is_anomaly` and `weekday_baseline_kwh` columns; handles empty frames, missing weekday data, and zero baselines without raising.
    - _Requirements: 4.1, 4.2, 4.3, 4.5_
    - _Suggested commit: `feat: add anomaly detector for sunday consumption spikes`_
  - [~] 7.5 Write the property test for **Property 10: Panic-enabled phase filter**
    - **Property 10: Panic-enabled phase filter**
    - **Validates: Requirements 5.1**
    - Generate buildings with mixed `panic_enabled` flags and assert `panic_choices(b) == [p for p in b.phases if p.panic_enabled]`, preserving order.
    - _Design refs: "Correctness Properties → Property 10"_
    - _Suggested commit: `test: add PBT for panic-enabled phase filter (Property 10)`_
  - [~] 7.6 Write the property test for the payload half of **Property 7: Panic flow correctness**
    - **Property 7 (payload half): build_payload set-equality and asset union**
    - **Validates: Requirements 5.3**
    - Generate `(building, S)` pairs where `S` is a subset of panic-enabled phase ids; assert `payload.building_id == b.id`, `set(payload.selected_phases) == S`, and `payload.affected_assets` equals the union of asset names across selected phases.
    - _Design refs: "Correctness Properties → Property 7"_
    - _Suggested commit: `test: add PBT for panic payload builder (Property 7 payload half)`_
  - [~] 7.7 Implement `core/panic.py`
    - `panic_choices(b)` returns panic-enabled phases in original order.
    - `build_payload(building, selected_phase_ids)` constructs `PanicPayload` with set-deduplicated selections and the union of asset names from the selected phases.
    - `apply_eco_mode(building, selected_phase_ids)` mutates phase statuses to `ECO_MODE` (used after a successful webhook 2xx response).
    - _Requirements: 5.1, 5.3, 5.4_
    - _Suggested commit: `feat: add panic payload builder and panic-enabled phase filter`_
<<<<<<< HEAD
 
=======

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
- [ ] 8. Implement the Telemetry Poller with deterministic `tick()`
  - [~] 8.1 Write the property test for **Property 6: Telemetry tick semantics**
    - **Property 6: Telemetry tick semantics**
    - **Validates: Requirements 3.2, 3.5, 7.3**
    - Generate sequences of mock breaker/SIOS responses (mix of successful `Reading`s and simulated `Timeout` / 5xx errors). Drive `TelemetryPoller.tick()` with fake clients; assert: on success, the latest `telemetry[building_id]` entry equals the returned `Reading` and `last_error[api] is None`; on failure, `last_known_telemetry[building_id]` is unchanged and `last_error[api]` is set; after `k` successful ticks the deque grew by exactly `k` and its tail equals the last `k` successful readings in order.
    - _Design refs: "Correctness Properties → Property 6", "Telemetry Poller"_
    - _Suggested commit: `test: add PBT for telemetry tick semantics (Property 6)`_
  - [~] 8.2 Implement `core/poller.py`
    - `TelemetryPoller(interval_s, clients, store)` exposes `start(building_id)`, `stop()`, and a deterministic `tick()` for tests.
    - `tick()` fetches one reading per phase, fetches SIOS price once, computes `CostPoint` via `calculate_cost`, appends to bounded `deque(maxlen=720)`s in session state, and updates `last_error` / `last_known_telemetry` per the error-handling table in the design.
    - Use a `threading.Lock` for single-flight semantics and back-off (double interval up to 5 min) after 3 consecutive failures.
    - _Requirements: 3.1, 3.2, 3.5, 7.3_
    - _Design refs: "Telemetry Poller", "Resilience patterns"_
    - _Suggested commit: `feat: add telemetry poller with deterministic tick and backoff`_
  - [~] 8.3 Add an example test that drives the 30-second cadence with a fake clock
    - Verify that a fake-clock advance by `30s` triggers exactly one `tick()` per active building and that two advances trigger exactly two ticks.
    - _Requirements: 3.1_
    - _Suggested commit: `test: add fake-clock test for 30s polling cadence`_
<<<<<<< HEAD
 
- [~] 9. Checkpoint — Pure logic + polling stable
  - Ensure all tests pass, ask the user if questions arise.
 
=======

- [~] 9. Checkpoint — Pure logic + polling stable
  - Ensure all tests pass, ask the user if questions arise.

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
- [ ] 10. Implement the Kiro webhook stub and client (closing the panic loop)
  - [~] 10.1 Write the property test for the webhook half of **Property 7: Panic flow correctness**
    - **Property 7 (webhook half): fan-out, notification dispatch, and 6.4 logging**
    - **Validates: Requirements 5.4, 5.5, 6.2, 6.3, 6.4**
    - Drive the Kiro stub via Flask `test_client` for valid payloads, non-2xx responses, and timeouts, plus an injected failing `Notification_Node`. Assert: on 2xx, exactly one Eco POST per phase id in `selected_phases` (no extras, no missing), notification dispatched once with the three payload fields, and building phase statuses flip to `ECO_MODE`; on non-2xx/timeout, statuses are deeply unchanged and an error is recorded; on notification failure, the webhook still returns 2xx, Eco POSTs are still issued, and a failure log entry is written.
    - _Design refs: "Correctness Properties → Property 7", "Kiro_Webhook integration"_
    - _Suggested commit: `test: add PBT for kiro webhook fan-out and notification (Property 7 webhook half)`_
  - [~] 10.2 Implement `clients/kiro_client.py`
    - `post_panic(payload, *, timeout_s=5.0) -> PanicResult` posts JSON to `KIRO_WEBHOOK_URL` and returns a typed result with `(ok, status_code, error)`.
    - _Requirements: 5.3, 5.4, 5.5_
    - _Suggested commit: `feat: add kiro webhook http client`_
  - [~] 10.3 Implement `mock_api/kiro_stub.py`
    - Flask app on `localhost:9000` exposing `POST /kiro/panic`.
    - Validates payload schema (`building_id`, `selected_phases`, `affected_assets`); rejects invalid payloads with `400`.
    - Fans out one `POST /breaker/{b}/{phase}/eco` call to the Mock API per `selected_phases` entry (Req 6.2).
    - Calls a `Notification_Node.dispatch` collaborator with the three payload fields (Req 6.3); logs and continues on dispatch failure (Req 6.4).
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
    - _Design refs: "Kiro_Webhook integration → Stub side"_
    - _Suggested commit: `feat: add local kiro webhook stub with fan-out and notification`_
  - [~] 10.4 Implement `core/notification.py` with a pluggable `Notification_Node`
    - Abstract `Notification_Node.dispatch(building_id, selected_phases, affected_assets) -> None`.
    - Provide a default `LoggingNotificationNode` for the demo and a test double that can be configured to raise.
    - _Requirements: 6.3, 6.4_
    - _Suggested commit: `feat: add Notification_Node abstraction with logging default`_
<<<<<<< HEAD
 
=======

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
- [ ] 11. Implement Streamlit UI: layout, building form, and Interactive Map
  - [~] 11.1 Implement `ui/layout.py` with responsive grid helpers and theme
    - `st.set_page_config(layout="wide")`; provide `three_column_layout()`, `two_column_layout()`, `single_column_layout()` helpers backed by `st.columns`.
    - Inject a custom CSS block (`st.markdown(..., unsafe_allow_html=True)`) with breakpoint rules: mobile `< 640px` (single column, map height `240px`), tablet `640–1024px` (two columns, sidebar in `st.expander`), desktop `> 1024px` (three columns).
    - Enforce `max-width: 100vw; overflow-x: hidden` on the main container per the WCAG 1.4.10 deviation note.
    - Add `.streamlit/config.toml` theme with foreground/background contrast ≥ 4.5:1 and chart palette ≥ 3:1.
    - _Requirements: 1.4, 1.5, 7.1, 7.2_
    - _Design refs: "Responsive Layout Notes", "Accessibility → What we do"_
    - _Suggested commit: `feat: add responsive streamlit layout helpers and a11y theme`_
  - [~] 11.2 Implement `ui/a11y.py` (custom `aria-live="polite"` component)
    - `streamlit.components.v1.html` component that renders a polite live region used to announce API status changes, panic confirmations, and anomaly counts (WCAG 4.1.3).
    - Expose `announce(message: str)` API.
    - _Requirements: 3.5, 4.5, 5.4_
    - _Design refs: "Accessibility → Custom component"_
    - _Suggested commit: `feat: add aria-live custom component for status announcements`_
  - [~] 11.3 Write an `AppTest` example for the building form (valid + invalid submissions)
    - Use `streamlit.testing.v1.AppTest`. Submit a valid form → assert the new building is in `st.session_state["buildings"]` and a confirmation appears. Submit forms missing each of `name`, `address`, `latitude`, `longitude` and out-of-range coordinates → assert the form is rejected with an inline `role="alert"` error per field.
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4_
    - _Suggested commit: `test: add AppTest scenarios for building form happy-path and validation`_
  - [~] 11.4 Implement `ui/building_form.py`
    - Form with `st.text_input` (name, address), `st.number_input` (latitude, longitude), and a phases editor: per-phase `st.text_input` (name), `st.checkbox` ("Panic-Enabled"), and `st.text_area`/`st.data_editor` for assets.
    - Wire submit → `BuildingManager.add_building(...)`; surface `ValidationError`s inline next to the offending field with `role="alert"` and `aria-live="polite"`.
    - All widgets carry non-empty descriptive labels; tab order follows DOM order; the submit button is `type="primary"`.
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4_
    - _Design refs: "Building_Manager → Validation rules", "Accessibility"_
    - _Suggested commit: `feat: add accessible building and phases form`_
  - [~] 11.5 Write the property test for **Property 3: Map marker projections**
    - **Property 3: Map marker projections**
    - **Validates: Requirements 1.4, 4.4**
    - Generate building lists and anomaly DataFrames; assert `build_marker_frame(buildings)` has length `len(buildings)` and contains each `(id, latitude, longitude)`, and `build_anomaly_marker_frame(buildings, anomalies)` contains exactly the building ids with at least one `is_anomaly == True` row.
    - _Design refs: "Correctness Properties → Property 3"_
    - _Suggested commit: `test: add PBT for map marker projections (Property 3)`_
  - [~] 11.6 Implement `ui/map_view.py`
    - `build_marker_frame(buildings) -> pd.DataFrame` for `st.map`.
    - `build_anomaly_marker_frame(buildings, anomalies) -> pd.DataFrame` for the `pydeck` overlay layer with a distinct shape *and* color (WCAG 1.4.1: not color-only).
    - Render an adjacent textual, keyboard-navigable building list as the accessible alternative to the canvas-rendered map per the documented `st.map` deviation.
    - Wire selection from the list to `st.session_state["active_building_id"]` so it updates telemetry and charts (Req 1.5).
    - _Requirements: 1.4, 1.5, 4.4_
    - _Design refs: "Accessibility → Known deviations", "ui/map_view.py"_
    - _Suggested commit: `feat: add interactive map with anomaly overlay and accessible list`_
<<<<<<< HEAD
 
=======

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
- [ ] 12. Implement live charts and telemetry display
  - [~] 12.1 Write the property test for **Property 9: Chart data filtering and anomaly styling**
    - **Property 9: Chart data filtering and anomaly styling**
    - **Validates: Requirements 7.1, 7.2, 7.4**
    - Generate `(state, building_id)` pairs and assert `consumption_chart_data(state, building_id)` and `cost_chart_data(state, building_id)` only contain rows for that building. For a chart frame, assert `style_consumption(df)` assigns the distinct anomaly marker iff `df.is_anomaly[i]` is `True`.
    - _Design refs: "Correctness Properties → Property 9"_
    - _Suggested commit: `test: add PBT for chart data filtering and anomaly styling (Property 9)`_
  - [~] 12.2 Implement `ui/charts.py`
    - `consumption_chart_data(state, building_id)` and `cost_chart_data(state, building_id)` build Altair-ready frames filtered by `building_id`.
    - `style_consumption(df)` returns an Altair chart with disabled animations (`alt.Transition(duration=0)`) and a distinct shape + color encoding for anomaly rows; pass `use_container_width=True` for fluid width.
    - Append-on-tick: refresh the chart inputs from `st.session_state` on rerun without forcing a full page reload (Req 7.3).
    - Render the underlying tables beneath each chart for keyboard/screen-reader access (WCAG 2.1.1).
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
    - _Design refs: "ui/charts.py", "Accessibility → Known deviations"_
    - _Suggested commit: `feat: add live consumption and cost charts with anomaly markers`_
  - [~] 12.3 Implement `ui/telemetry.py` (per-phase telemetry display)
    - Render per-phase `active_power_kW`, `voltage_v`, `current_a`, and `mode` for the active building. Display a persistent API status pill (green/amber/red) bound to `last_error`, with a polite `aria-live` announcement on transitions.
    - Render the consumption table with anomaly rows visually highlighted (Req 4.3) and announced via the live region (Req 4.5).
    - _Requirements: 3.2, 3.5, 4.3, 4.5_
    - _Design refs: "Error Handling → User-visible error surfaces"_
    - _Suggested commit: `feat: add telemetry panel with api status pill and anomaly highlighting`_
<<<<<<< HEAD
 
=======

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
- [ ] 13. Implement the Panic Panel UI and wire it to the webhook
  - [~] 13.1 Write `AppTest` examples for the panic panel
    - Configure a building with three phases (two Panic-Enabled). Assert only the Panic-Enabled phases are rendered (Req 5.1). Confirm with a 2xx mocked response → assert selected phases flip to `ECO_MODE` (Req 5.4). Confirm with a non-2xx mocked response → assert phase statuses are unchanged and an error banner is shown (Req 5.5).
    - _Requirements: 5.1, 5.2, 5.4, 5.5_
    - _Suggested commit: `test: add AppTest scenarios for panic panel happy and failure paths`_
  - [~] 13.2 Implement `ui/panic_panel.py`
    - Panel renders only `panic_choices(active_building)` (Req 5.1) using `st.checkbox` per phase (Req 5.2) and a primary `st.button("Confirm Panic")` (Req 5.2).
    - On confirm: build payload via `core.panic.build_payload`, call `clients.kiro_client.post_panic`, and on 2xx call `apply_eco_mode` (Req 5.4) plus announce via the `aria-live` region. On non-2xx/timeout, render an error banner with a retry button and leave statuses unchanged (Req 5.5).
    - All controls keyboard-reachable; confirm action announced through the polite live region (WCAG 4.1.3).
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
    - _Design refs: "Panic flow + Eco Mode propagation"_
    - _Suggested commit: `feat: add accessible panic panel with confirm flow and error handling`_
<<<<<<< HEAD
 
=======

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
- [~] 14. Wire `app.py`: assemble pages, start the poller, expose configuration
  - Implement `app.py` to compose the responsive layout: sidebar (`render_sidebar`) holds the building list + add-building form; main area renders the map, telemetry, charts, and panic panel for the active building.
  - Initialize `st.session_state` with the shape from the design (`buildings`, `active_building_id`, `telemetry`, `cost_series`, `anomalies`, `last_error`, `last_known_telemetry`).
  - Start `TelemetryPoller` for the active building and stop it when the active building changes or the user clears it.
  - Read `MOCK_API_BASE_URL` and `KIRO_WEBHOOK_URL` from environment variables with sensible localhost defaults.
  - Run anomaly detection on the loaded `data/historical.csv` once at startup and cache the result in `st.session_state["anomalies"]`.
  - _Requirements: 1.4, 1.5, 3.1, 3.2, 4.3, 4.4, 4.5, 5.1_
  - _Design refs: "Architecture → Process & runtime model", "st.session_state shape"_
  - _Suggested commit: `feat: wire streamlit app entry point with poller and session bootstrap`_
<<<<<<< HEAD
 
=======

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
- [ ] 15. Add end-to-end integration tests across the full local stack
  - [~] 15.1 Add → poll → chart scenario
    - Register a building via `BuildingManager`, advance the fake clock by 30 s, assert telemetry and cost deques append exactly one point each per phase and that the chart frames reflect the new data.
    - _Requirements: 1.2, 3.1, 3.2, 3.4, 7.1, 7.2, 7.3_
    - _Suggested commit: `test: add integration test for add-building → poll → chart`_
  - [~] 15.2 Anomaly highlighting scenario
    - Load a fixture historical CSV with crafted Sunday spikes; assert the anomaly marker appears on the map for the affected building and rows are flagged in the consumption table; assert the polite live region announces the anomaly count.
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
    - _Suggested commit: `test: add integration test for anomaly highlighting`_
  - [~] 15.3 Granular panic scenario
    - Configure a building with three phases (two Panic-Enabled); trigger panic on one Panic-Enabled phase. Assert exactly that phase flips to `ECO_MODE`, the next polling tick reports a 40% reduction in `active_power_kW` for that phase only, and `Notification_Node.dispatch` was called once with the correct payload.
    - _Requirements: 5.1, 5.3, 5.4, 6.2, 6.3, 8.4_
    - _Suggested commit: `test: add integration test for granular panic and eco mode propagation`_
  - [~] 15.4 Resilience scenario
    - Simulate a Mock API 500 response; assert `last_error["breaker"]` is set, the API status pill turns red, and `last_known_telemetry` is preserved. Clear the error; assert the pill returns to green within one tick and the live region announces the recovery.
    - _Requirements: 3.5_
    - _Suggested commit: `test: add integration test for api error resilience`_
<<<<<<< HEAD
 
=======

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
- [ ] 16. Accessibility and responsive verification
  - [~] 16.1 Add an automated `axe-core` audit via Playwright against the running Streamlit app
    - Boot `streamlit run app.py` against the Mock API; run `axe-core` over the main page; fail the test on `serious` or `critical` violations.
    - _Requirements: WCAG 2.1 AA per workspace standard_
    - _Design refs: "Accessibility → Verification"_
    - _Suggested commit: `test: add axe-core accessibility audit via playwright`_
  - [~] 16.2 Add responsive snapshot tests at three breakpoints
    - Drive Playwright at 360px, 768px, and 1280px viewports; assert no horizontal overflow on the main container and that the layout matches the documented mobile/tablet/desktop arrangement.
    - _Requirements: 1.4 (responsive), 7.1, 7.2_
    - _Suggested commit: `test: add responsive snapshot tests at three breakpoints`_
  - [~] 16.3 Document keyboard-only walkthrough and screen-reader spot-check
    - Add `docs/a11y-walkthrough.md` capturing the keyboard path through add-building, polling, anomaly review, and panic flows, plus VoiceOver/NVDA spot-check notes per the design.
    - _Requirements: WCAG 2.1 AA per workspace standard_
    - _Design refs: "Accessibility → Verification"_
    - _Suggested commit: `docs: add keyboard and screen-reader walkthrough notes`_
<<<<<<< HEAD
 
- [~] 17. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
 
## Notes
 
=======

- [~] 17. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
- Tasks marked with `*` are optional and can be skipped for a faster MVP. Under the workspace TDD standard the test sub-tasks are still authored *before* their corresponding implementation; the `*` marker only governs whether the workflow runner skips them.
- Each task references granular acceptance criteria from `requirements.md` (e.g. `1.3`, `8.4`) for traceability.
- Each property-based test sub-task maps 1:1 to a Correctness Property in `design.md`; properties are placed close to the implementation they validate to catch regressions early.
- Checkpoints at tasks 5, 9, and 17 give natural stopping points to confirm direction with the user.
<<<<<<< HEAD
- Suggested Conventional Commits messages follow the workspace standard (`feat:`, `fix:`, `test:`, `docs:`, `style:`, `chore:`).
=======
- Suggested Conventional Commits messages follow the workspace standard (`feat:`, `fix:`, `test:`, `docs:`, `style:`, `chore:`).
>>>>>>> fff278cf87641df0e5688d98efeea69ec5a77893
