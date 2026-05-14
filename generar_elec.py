"""
Mock de la API de Red Eléctrica — ESIOS/apidatos.ree.es
Devuelve precios PVPC horarios con la misma estructura JSON que el endpoint real.
"""

import json
import random
from datetime import datetime, timedelta, timezone

# Perfil horario España: valle (00-07), rampa mañana, llano, punta tarde
_PERFIL = [
    0.52, 0.48, 0.46, 0.45, 0.46, 0.50,  # 00-05
    0.62, 0.82, 1.08, 1.14, 1.09, 1.04,  # 06-11
    0.99, 0.94, 0.91, 0.89, 0.94, 1.09,  # 12-17
    1.19, 1.24, 1.14, 0.99, 0.79, 0.63,  # 18-23
]

_BASE_MIN, _BASE_MAX = 55.0, 185.0   # €/MWh — rango real mercado España
_TZ = "+02:00"


def generar(fecha: str | None = None, seed: int | None = None) -> dict:
    """
    Genera precios PVPC horarios para la fecha indicada (por defecto hoy).
    Devuelve el mismo esquema JSON que apidatos.ree.es.
    """
    if seed is not None:
        random.seed(seed)

    fecha = fecha or datetime.now().strftime("%Y-%m-%d")
    dia   = datetime.strptime(fecha, "%Y-%m-%d")
    base  = random.uniform(_BASE_MIN, _BASE_MAX)
    last_update = dia.strftime(f"%Y-%m-%dT23:59:59.000{_TZ}")

    values = []
    for h in range(24):
        precio = round(base * _PERFIL[h] * (1 + random.uniform(-0.07, 0.07)), 6)
        values.append({
            "value":      precio,
            "percentage": 100.0,
            "datetime":   (dia + timedelta(hours=h)).strftime(f"%Y-%m-%dT%H:%M:%S.000{_TZ}"),
        })

    return {
        "data": {
            "type": "PVPC",
            "id":   "1001",
            "attributes": {
                "title":       "PVPC T. Defecto",
                "last-update": last_update,
                "magnitude":   "€/MWh",
                "time_trunc":  "hour",
                "delta_time":  {"data": "PT1H"},
            },
        },
        "included": [{
            "type":    "PVPC T. Defecto",
            "id":      "600",
            "attributes": {
                "title":       "PVPC T. Defecto",
                "last-update": last_update,
                "color":       "#ff9900",
                "magnitude":   "€/MWh",
                "values":      values,
            },
        }],
    }


if __name__ == "__main__":
    print(json.dumps(generar(), ensure_ascii=False))
