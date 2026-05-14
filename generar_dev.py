"""
Gemelo sintético de la API cloud de diferenciales inteligentes.
Genera un snapshot del estado actual de todos los dispositivos instalados
en las fases de un conjunto de edificios.

Estructura simulada:
  - NUM_EDIFICIOS edificios, cada uno con NUM_FASES_POR_EDIFICIO fases.
  - Cada fase tiene un diferencial inteligente (device_id único).
  - Si el diferencial está abierto (active=false), el consumo es 0.
"""

import json
import random
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# Configuración hardcodeada — ajusta aquí el número de edificios y fases
# ---------------------------------------------------------------------------
NUM_EDIFICIOS = 3
NUM_FASES_POR_EDIFICIO = 4

# Consumo típico por fase en kW (rango realista para circuitos de edificio)
CONSUMO_MIN_KW = 0.1
CONSUMO_MAX_KW = 10.0

# Probabilidad de que un diferencial esté abierto (corte de corriente)
PROB_ABIERTO = 0.05

TZ_OFFSET = "+02:00"


def _timestamp_ahora() -> str:
    tz = timezone(timedelta(hours=2))
    return datetime.now(tz).strftime(f"%Y-%m-%dT%H:%M:%S.000{TZ_OFFSET}")


def generar(seed: int | None = None) -> dict:
    """
    Genera un snapshot del estado de todos los diferenciales.

    Args:
        seed: Semilla para reproducibilidad.

    Returns:
        dict con la estructura de respuesta de la API cloud.
    """
    if seed is not None:
        random.seed(seed)

    timestamp = _timestamp_ahora()
    devices = []

    for edificio_idx in range(1, NUM_EDIFICIOS + 1):
        building_id = f"edificio_{edificio_idx:02d}"

        for fase_idx in range(1, NUM_FASES_POR_EDIFICIO + 1):
            device_id = f"diff_{edificio_idx:02d}_{fase_idx:02d}"
            active = random.random() > PROB_ABIERTO
            consumo_kw = round(random.uniform(CONSUMO_MIN_KW, CONSUMO_MAX_KW), 4) if active else 0.0

            devices.append({
                "building_id": building_id,
                "device_id": device_id,
                "phase_id": "L1",
                "active": active,
                "power_kw": consumo_kw,
                "timestamp": timestamp,
            })

    return {
        "snapshot_time": timestamp,
        "num_buildings": NUM_EDIFICIOS,
        "num_devices": len(devices),
        "devices": devices,
    }


if __name__ == "__main__":
    datos = generar()
    print(json.dumps(datos, ensure_ascii=False))
