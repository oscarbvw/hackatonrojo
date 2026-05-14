"""Local Flask-based Mock API server and Kiro webhook stub.

Modules in this package are added in later tasks:

- ``state``     — per-(building_id, phase_id) in-memory state (Task 4.2)
- ``server``    — Flask app exposing breaker/sios/eco endpoints (Task 4.3)
- ``__main__``  — `python -m energy_hunter.mock_api` entry point (Task 4.4)
- ``kiro_stub`` — local Kiro webhook stub (Task 10.3)
"""
