"""
Mock de la API cloud de diferenciales inteligentes (RCCB smart).
Genera un snapshot de todos los dispositivos instalados en los edificios.

Valores simulados realistas (monofásico 230 V, red española):
  - Tensión:         226 – 234 V  (±2 % sobre 230 V nominal)
  - Factor potencia: 0.88 – 0.96  (carga mixta resistiva/inductiva)
  - Intensidad:      derivada de P = V · I · cos(φ)
  - Potencia activa: 0.2 – 10.0 kW por circuito
"""

import json
import math
import random
from datetime import datetime, timedelta, timezone

# ── Topología (modificar aquí para escalar) ──────────────────────────────────
NUM_EDIFICIOS        = 3
NUM_FASES_EDIFICIO   = 4    # diferenciales por edificio

# ── Rangos eléctricos realistas ──────────────────────────────────────────────
CONSUMO_MIN_KW  = 0.2
CONSUMO_MAX_KW  = 10.0
TENSION_NOM_V   = 230.0
TENSION_VAR_V   = 4.0      # ±4 V sobre nominal
FP_MIN, FP_MAX  = 0.88, 0.96

PROB_ABIERTO    = 0.05      # probabilidad de diferencial abierto

_TZ_OFFSET = "+02:00"


def _ts() -> str:
    tz = timezone(timedelta(hours=2))
    return datetime.now(tz).strftime(f"%Y-%m-%dT%H:%M:%S.000{_TZ_OFFSET}")


def generar(seed: int | None = None) -> dict:
    """Snapshot del estado actual de todos los diferenciales."""
    if seed is not None:
        random.seed(seed)

    timestamp = _ts()
    devices   = []

    for e in range(1, NUM_EDIFICIOS + 1):
        for f in range(1, NUM_FASES_EDIFICIO + 1):
            estado = "ABIERTO" if random.random() < PROB_ABIERTO else "CERRADO"

            if estado == "CERRADO":
                potencia_kw    = round(random.uniform(CONSUMO_MIN_KW, CONSUMO_MAX_KW), 3)
                tension_v      = round(random.uniform(TENSION_NOM_V - TENSION_VAR_V,
                                                      TENSION_NOM_V + TENSION_VAR_V), 1)
                factor_potencia = round(random.uniform(FP_MIN, FP_MAX), 3)
                corriente_a    = round(potencia_kw * 1000 / (tension_v * factor_potencia), 2)
            else:
                potencia_kw = corriente_a = tension_v = factor_potencia = 0.0

            devices.append({
                "id_edificio":    f"edificio_{e:02d}",
                "id_diferencial": f"diff_{e:02d}_{f:02d}",
                "id_fase":        "L1",
                "estado":         estado,           # CERRADO | ABIERTO
                "potencia_kw":    potencia_kw,
                "corriente_a":    corriente_a,
                "tension_v":      tension_v,
                "factor_potencia": factor_potencia,
                "timestamp":      timestamp,
            })

    return {"snapshot_time": timestamp, "dispositivos": devices}


if __name__ == "__main__":
    print(json.dumps(generar(), ensure_ascii=False))
