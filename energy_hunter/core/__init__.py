"""Pure logic layer.

This package holds I/O-free business logic so it can be exercised by
property-based tests without spinning up Streamlit or HTTP. Modules
land in later tasks:

- ``models``           — dataclasses (Task 2.2)
- ``building_manager`` — CRUD over a SessionStore (Task 3.3)
- ``cost``             — expense formula (Task 7.2)
- ``anomaly_detector`` — Sunday anomaly rule (Task 7.4)
- ``panic``            — panic payload + phase filter (Task 7.7)
- ``poller``           — telemetry polling (Task 8.2)
- ``notification``     — Notification_Node abstraction (Task 10.4)
"""
