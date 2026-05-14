"""
Gemelo sintético de la API de Red Eléctrica (ESIOS/apidatos.ree.es).
Genera datos de precios PVPC por hora con la misma estructura JSON que la API real.

Endpoint real equivalente:
  GET https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real
      ?time_trunc=hour&start_date=YYYY-MM-DDTHH:MM&end_date=YYYY-MM-DDTHH:MM&geo_ids=8741
"""

import json
import random
from datetime import datetime, timedelta, timezone


# Perfil horario típico de precios en España (factores relativos, valle/llano/punta)
_PERFIL_HORARIO = [
    0.55, 0.50, 0.48, 0.47, 0.48, 0.52,  # 00-05 (valle profundo)
    0.65, 0.85, 1.10, 1.15, 1.10, 1.05,  # 06-11 (rampa mañana)
    1.00, 0.95, 0.92, 0.90, 0.95, 1.10,  # 12-17 (llano)
    1.20, 1.25, 1.15, 1.00, 0.80, 0.65,  # 18-23 (punta tarde)
]

# Precio base en €/MWh (rango típico del mercado español 2023-2025)
_PRECIO_BASE_MIN = 60.0
_PRECIO_BASE_MAX = 180.0


def _precio_hora(hora: int, precio_base: float, ruido: float = 0.08) -> float:
    """Devuelve el precio €/MWh para una hora concreta con variación aleatoria."""
    factor = _PERFIL_HORARIO[hora]
    variacion = 1.0 + random.uniform(-ruido, ruido)
    return round(precio_base * factor * variacion, 6)


def generar(
    fecha: str | None = None,
    precio_base: float | None = None,
    seed: int | None = None,
) -> dict:
    """
    Genera un JSON con la estructura de la API de Red Eléctrica para precios PVPC
    horarios del día indicado.

    Args:
        fecha:       Fecha en formato 'YYYY-MM-DD'. Por defecto, hoy.
        precio_base: Precio base €/MWh. Si es None, se elige aleatoriamente.
        seed:        Semilla para reproducibilidad.

    Returns:
        dict con la misma estructura que devuelve apidatos.ree.es
    """
    if seed is not None:
        random.seed(seed)

    if fecha is None:
        fecha = datetime.now().strftime("%Y-%m-%d")

    dia = datetime.strptime(fecha, "%Y-%m-%d")

    if precio_base is None:
        precio_base = random.uniform(_PRECIO_BASE_MIN, _PRECIO_BASE_MAX)

    tz_offset = "+02:00"  # CEST (horario de verano); ajusta a +01:00 en invierno
    last_update = dia.strftime(f"%Y-%m-%dT23:59:59.000{tz_offset}")

    values = []
    for hora in range(24):
        dt_hora = dia + timedelta(hours=hora)
        dt_str = dt_hora.strftime(f"%Y-%m-%dT%H:%M:%S.000{tz_offset}")
        values.append({
            "value": _precio_hora(hora, precio_base),
            "percentage": 100.0,
            "datetime": dt_str,
        })

    return {
        "data": {
            "type": "PVPC",
            "id": "1001",
            "attributes": {
                "title": "PVPC T. Defecto",
                "last-update": last_update,
                "description": None,
                "magnitude": "€/MWh",
                "composite": False,
                "delta_time": {"data": "PT1H"},
                "time_trunc": "hour",
                "geo_trunc": None,
                "geo_limit": None,
                "geo_ids": None,
            },
        },
        "included": [
            {
                "type": "PVPC T. Defecto",
                "id": "600",
                "groupId": None,
                "attributes": {
                    "title": "PVPC T. Defecto",
                    "description": None,
                    "color": "#ff9900",
                    "type": None,
                    "magnitude": None,
                    "composite": False,
                    "last-update": last_update,
                    "values": values,
                },
            }
        ],
    }


if __name__ == "__main__":
    datos = generar()
    print(json.dumps(datos, ensure_ascii=False))
