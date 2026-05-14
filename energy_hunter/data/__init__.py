"""Bundled data assets (e.g., the Historical_Dataset CSV).

This package exists primarily so ``energy_hunter.data`` resolves as a
namespace alongside the rest of the application. The actual dataset is
shipped as a sibling file (``historical.csv``) and is loaded by the
anomaly detector at runtime; downstream tasks read it via
``importlib.resources`` or a relative path.
"""
