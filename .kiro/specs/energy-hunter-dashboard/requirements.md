# Requirements Document

## Introduction

Energy Hunter is a B2B Energy Management Dashboard MVP. The system allows users to manage multiple buildings, visualizing them through a basic interactive map. It ingests data via read methods from mocked APIs (Smart Breaker and SIOS), detects anomalies in consumption patterns, and provides a granular "Panic Button" routine. This routine allows operators to select specific phases or sections within a building to limit electrical load through an automation flow orchestrated by Kiro.

## Glossary

- **Dashboard**: The Streamlit-based interface executing visualization and management methods.
- **Building_Manager**: The module responsible for the CRUD (Create, Read, Update, Delete) methods for building profiles.
- **Interactive_Map**: A basic geographic visualization (using coordinates) used to select and view building status.
- **Building_Phases**: Internal electrical segments (e.g., Phase A, Phase B, Phase C) or functional areas within a building.
- **Panic_Button**: A UI control that displays building phases with checkmarks to select which are "Panic-ready" or "Critical."
- **Kiro_Webhook**: The HTTP input method that receives the panic event and specific phase parameters.
- **Eco_Mode**: Operational state reducing reported power output by 40% in selected phases.
- **Session_State**: Streamlit's `st.session_state` mechanism used to persist the list of added buildings and their internal phase configurations across UI reruns.
- **Smart_Breaker_API**: The mocked REST API simulating IoT smart circuit breaker telemetry per phase.
- **SIOS_API**: The mocked REST API simulating Spain's Red Eléctrica official market pricing service.
- **Anomaly_Detector**: The Pandas-based rule engine that identifies abnormal consumption patterns in historical data.
- **Historical_Dataset**: The pre-generated dataset containing timestamped building consumption records, including Sunday anomalies.
- **Notification_Node**: The Kiro workflow node responsible for dispatching alerts to messaging channels.
- **Mock_API_Server**: The locally runnable HTTP server that exposes the Smart_Breaker_API and SIOS_API endpoints.

---

## Requirements

### Requirement 1: Building Management and Interactive Map

**User Story:** As an energy operator, I want to register multiple buildings and visualize them on an interactive map, so that I can manage and monitor all my energy assets from a single geographic view.

#### Acceptance Criteria

1. THE Dashboard SHALL provide a form that accepts a building name, an address, and geographic coordinates (latitude and longitude) as inputs to add a new building.
2. WHEN the user submits the add-building form with valid name, address, and coordinates, THE Building_Manager SHALL persist the new building in Session_State.
3. IF the user submits the add-building form with a missing or invalid name, address, latitude, or longitude, THEN THE Dashboard SHALL reject the submission and display a validation error message.
4. THE Dashboard SHALL render an Interactive_Map displaying one marker for each registered building using the building's stored coordinates.
5. WHEN the user selects a building from the Interactive_Map or building list, THE Dashboard SHALL update the telemetry display and charts to reflect that specific building's data.

---

### Requirement 2: Phase and Asset Definition

**User Story:** As an energy operator, I want to define electrical phases and their associated assets within each building, so that I can identify which segments are critical and eligible for emergency load reduction.

#### Acceptance Criteria

1. WHERE a building profile is being edited, THE Dashboard SHALL allow the user to define one or more Building_Phases, each identified by a name (e.g., "Phase A", "Phase B").
2. THE Dashboard SHALL require, for every Building_Phase, a "Panic-Enabled" checkbox indicating whether that phase is eligible for emergency load reduction.
3. WHERE a Building_Phase is being edited, THE Dashboard SHALL allow the user to list one or more specific assets (e.g., "HVAC Unit 1", "Server Rack A", "Emergency Lighting") associated with that phase.
4. THE Building_Manager SHALL persist Building_Phases, their Panic-Enabled flag, and their associated assets in Session_State as part of the building profile.

---

### Requirement 3: Telemetry and SIOS Integration

**User Story:** As an energy operator, I want telemetry and market pricing data polled regularly for the active building, so that I can monitor real-time consumption and the corresponding cost.

#### Acceptance Criteria

1. WHILE a building is selected as active, THE Dashboard SHALL invoke the polling method for the Smart_Breaker_API associated with the active building every 30 seconds.
2. WHEN the Smart_Breaker_API returns a successful response, THE Dashboard SHALL update the displayed per-phase telemetry values within one polling cycle.
3. WHILE a building is selected as active, THE Dashboard SHALL retrieve the current hourly price from the SIOS_API.
4. WHEN both Smart_Breaker_API and SIOS_API data are available, THE Dashboard SHALL execute the expense calculation function using the formula: `Expense = Power * (Price / 1000)`, where `Power` is in kW and `Price` is in EUR/MWh.
5. IF the Smart_Breaker_API or SIOS_API returns an HTTP error or times out, THEN THE Dashboard SHALL display a visible error indicator and retain the last known values.

---

### Requirement 4: Anomaly Detection

**User Story:** As an energy operator, I want the system to automatically flag abnormal Sunday consumption per building, so that I can investigate unexpected energy usage without manually reviewing raw data.

#### Acceptance Criteria

1. WHEN the Anomaly_Detector processes the Historical_Dataset, THE Anomaly_Detector SHALL compute the average weekday (Monday–Friday) consumption per building as the baseline.
2. WHEN a Sunday record's consumption exceeds 140% of that building's weekday baseline, THE Anomaly_Detector SHALL flag the record as an anomaly.
3. THE Dashboard SHALL highlight all anomaly records in the consumption data table for the affected building.
4. THE Dashboard SHALL render a distinct anomaly marker on the Interactive_Map for any building that has at least one detected anomaly.
5. WHEN no anomalies are detected for the selected building, THE Dashboard SHALL display a message indicating that no anomalies were found.

---

### Requirement 5: Panic Button and Granular Phase Control

**User Story:** As an energy operator, I want to selectively trigger load reduction on specific phases of a building via the Panic Button, so that I can limit electrical load on critical segments without disrupting the entire site.

#### Acceptance Criteria

1. WHEN the Panic_Button is initiated for the active building, THE Dashboard SHALL display only the Building_Phases previously marked as Panic-Enabled.
2. THE Dashboard SHALL allow the user to select one or more of the displayed Panic-Enabled Building_Phases prior to confirmation.
3. WHEN the user confirms the Panic_Button selection, THE Dashboard SHALL invoke an HTTP POST request to the Kiro_Webhook with a JSON payload containing at minimum `building_id`, `selected_phases`, and `affected_assets`.
4. WHEN the Kiro_Webhook POST request succeeds with an HTTP 2xx response, THE Dashboard SHALL update the status of each selected phase to "ECO_MODE" in the UI.
5. IF the Kiro_Webhook POST request fails with a non-2xx response or times out, THEN THE Dashboard SHALL display an error message and leave the phase statuses unchanged.

---

### Requirement 6: Kiro Webhook and Automation

**User Story:** As a Kiro orchestrator, I want the webhook to trigger granular automation and dispatch detailed notifications, so that only the selected electrical nodes are affected and stakeholders are informed of the exact scope.

#### Acceptance Criteria

1. THE Kiro_Webhook SHALL expose an HTTP POST endpoint that accepts the panic payload defined in Requirement 5, Acceptance Criterion 3.
2. WHEN the Kiro_Webhook receives a valid panic payload, THE Kiro_Webhook SHALL trigger the automation flow only for the electrical nodes corresponding to the `selected_phases` in the payload.
3. WHEN the automation flow executes, THE Notification_Node SHALL dispatch an alert containing the affected `building_id`, the `selected_phases`, and the `affected_assets` to at least one configured messaging channel.
4. IF the Notification_Node dispatch fails, THEN THE Kiro_Webhook SHALL log the failure and complete the automation flow without blocking the phase state update.

---

### Requirement 7: Analytics and Charts

**User Story:** As an energy operator, I want time-series charts of consumption and cost filtered by the selected building with live updates, so that I can track trends and the financial impact of anomalies in real time.

#### Acceptance Criteria

1. THE Dashboard SHALL render a time-series chart of `Consumption_kWh` filtered by the currently selected building.
2. THE Dashboard SHALL render a time-series chart of `Total_Cost` filtered by the currently selected building.
3. WHEN new telemetry points are received from the Smart_Breaker_API, THE Dashboard SHALL append the new data points to the live charts without triggering a full page reload.
4. WHEN anomaly records are present for the selected building, THE Dashboard SHALL visually mark anomaly data points on the consumption chart with a distinct color or marker symbol.

---

### Requirement 8: Mock API Server

**User Story:** As a developer, I want a locally runnable mock API server that manages independent states for multiple buildings and their phases, so that the full system can be demonstrated without external network dependencies.

#### Acceptance Criteria

1. THE Mock_API_Server SHALL serve the Smart_Breaker_API and SIOS_API endpoints from a single local HTTP server.
2. THE Mock_API_Server SHALL maintain an independent state for each registered building and for each of that building's Building_Phases.
3. THE Mock_API_Server SHALL expose an endpoint that accepts a request to switch a specific Building_Phase of a specific building to "ECO_MODE".
4. WHEN a specific Building_Phase is in "ECO_MODE", THE Mock_API_Server SHALL reduce the reported `active_power_kW` value for that segment by 40% relative to its pre-Eco_Mode baseline value.
5. THE Mock_API_Server SHALL be startable with a single command and SHALL operate with no external service dependencies.
