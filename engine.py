"""
Backend · Energy Hunter
=======================
Único punto de entrada para el front: get_data() → dict

Funciones de control:
  ingest()               → igual que get_data() + persiste en CSV histórico
  panico_energetico(id)  → corte remoto de un edificio o de todos
  desactivar_panico(id)  → restaura estado normal
"""

import csv
import os
from datetime import datetime

from generar_elec import generar as _api_elec
from generar_dev  import generar as _api_dev, NUM_EDIFICIOS, CONSUMO_MAX_KW

# ── Umbrales ────────────────────────────────────────────────────────────────
PRECIO_ALTO_EUR_KWH   = 0.15   # a partir de aquí se emite alerta de precio
ANOMALIA_UMBRAL_KW    = 2.0    # consumo por diferencial que dispara ANOMALIA fuera de horario

# ── Estado de pánico en memoria (se resetea al reiniciar el proceso) ────────
_panic: dict[str, bool] = {}

# ── CSV ─────────────────────────────────────────────────────────────────────
CSV_PATH   = "historico_consumo.csv"
CSV_FIELDS = [
    "timestamp", "periodo_tarifario", "precio_kwh",
    "edificio_id", "diferencial_id", "fase",
    "activo", "consumo_kw", "consumo_edificio_kw",
    "coste_hora_eur", "status",
]


# ════════════════════════════════════════════════════════════════════════════
# Helpers de dominio
# ════════════════════════════════════════════════════════════════════════════

def _precio_kwh(datos_elec: dict) -> float:
    """Precio de la hora actual en €/kWh (la API devuelve €/MWh)."""
    hora    = datetime.now().hour
    valores = datos_elec["included"][0]["attributes"]["values"]
    return round(valores[hora]["value"] / 1000, 6)


def _periodo_tarifario() -> str:
    """
    Periodos 2.0TD (Península, Red Eléctrica):
      VALLE  → 00-08 h entre semana + todo el fin de semana
      LLANO  → 08-10 h, 14-18 h y 22-24 h entre semana
      PUNTA  → 10-14 h y 18-22 h entre semana
    """
    ahora = datetime.now()
    h     = ahora.hour
    finde = ahora.weekday() >= 5

    if finde or h < 8:
        return "VALLE"
    if (10 <= h < 14) or (18 <= h < 22):
        return "PUNTA"
    return "LLANO"


def _hora_baja_actividad() -> bool:
    """True si el edificio debería estar desocupado (finde o fuera de 07-22 h)."""
    ahora = datetime.now()
    return ahora.weekday() >= 5 or ahora.hour < 7 or ahora.hour >= 22


def _status_diferencial(activo: bool, consumo_kw: float, precio_kwh: float, bid: str) -> str:
    if _panic.get(bid):        return "PANICO"
    if not activo:             return "APAGADO"
    if _hora_baja_actividad() and consumo_kw > ANOMALIA_UMBRAL_KW:
        return "ANOMALIA"
    if precio_kwh > PRECIO_ALTO_EUR_KWH:
        return "PRECIO_ALTO"
    return "OK"


# Prioridad para escalar el status al nivel de edificio
_PRIO = {"OK": 0, "APAGADO": 1, "PRECIO_ALTO": 2, "ANOMALIA": 3, "PANICO": 4}

def _status_edificio(statuses: list[str]) -> str:
    return max(statuses, key=lambda s: _PRIO.get(s, 0))


def _alerta(eid: str, did: str | None, tipo: str, severidad: str, msg: str, ts: str) -> dict:
    return {
        "edificio_id":    eid,
        "diferencial_id": did,
        "tipo":           tipo,
        "severidad":      severidad,   # INFO | WARNING | CRITICAL
        "mensaje":        msg,
        "timestamp":      ts,
    }


# ════════════════════════════════════════════════════════════════════════════
# Núcleo: construir snapshot completo
# ════════════════════════════════════════════════════════════════════════════

def _snapshot() -> dict:
    datos_elec    = _api_elec()
    datos_dev     = _api_dev()
    precio_kwh    = _precio_kwh(datos_elec)
    periodo       = _periodo_tarifario()
    ts            = datos_dev["snapshot_time"]
    alerta_precio = precio_kwh > PRECIO_ALTO_EUR_KWH
    alertas_glob: list[dict] = []

    # Alerta global de precio alto (una sola, no por dispositivo)
    if alerta_precio:
        alertas_glob.append(_alerta(
            None, None, "PRECIO_ALTO", "WARNING",
            f"Precio de mercado elevado: {precio_kwh:.4f} €/kWh "
            f"(umbral {PRECIO_ALTO_EUR_KWH} €/kWh)",
            ts,
        ))

    # ── Agrupar devices por edificio ─────────────────────────────────────────
    edificios_raw: dict[str, list] = {}
    for dev in datos_dev["devices"]:
        edificios_raw.setdefault(dev["building_id"], []).append(dev)

    # ── Construir cada edificio ──────────────────────────────────────────────
    edificios_out: list[dict] = []

    for bid, devices in edificios_raw.items():
        en_panico         = bool(_panic.get(bid))
        alertas_edificio: list[dict] = []
        diferenciales_out: list[dict] = []
        consumo_edificio  = 0.0

        for dev in devices:
            activo     = dev["active"] and not en_panico
            consumo_kw = round(dev["power_kw"], 4) if activo else 0.0
            status     = _status_diferencial(dev["active"], consumo_kw, precio_kwh, bid)
            coste_h    = round(consumo_kw * precio_kwh, 4)
            consumo_edificio += consumo_kw

            diferenciales_out.append({
                "id":           dev["device_id"],
                "fase":         dev["phase_id"],
                "activo":       activo,
                "consumo_kw":   consumo_kw,
                "coste_hora_eur": coste_h,
                "status":       status,
            })

            # Alertas a nivel de dispositivo
            if status == "ANOMALIA":
                alertas_edificio.append(_alerta(
                    bid, dev["device_id"], "CONSUMO_ANOMALO", "WARNING",
                    f"{dev['device_id']} consume {consumo_kw} kW fuera de horario laboral",
                    ts,
                ))
            elif status == "PANICO":
                alertas_edificio.append(_alerta(
                    bid, dev["device_id"], "PANICO_ACTIVO", "CRITICAL",
                    f"{dev['device_id']} cortado por pánico energético",
                    ts,
                ))

        consumo_edificio = round(consumo_edificio, 4)
        coste_edificio_h = round(consumo_edificio * precio_kwh, 4)
        num_activos      = sum(1 for d in diferenciales_out if d["activo"])
        num_diffs        = len(diferenciales_out)
        max_teorico_kw   = num_diffs * CONSUMO_MAX_KW
        status_edificio  = _status_edificio([d["status"] for d in diferenciales_out])

        # Añadir pct_sobre_edificio a cada diferencial (necesita consumo_edificio)
        for d in diferenciales_out:
            d["pct_sobre_edificio"] = (
                round(d["consumo_kw"] / consumo_edificio * 100, 2)
                if consumo_edificio > 0 else 0.0
            )

        edificios_out.append({
            "id": bid,
            "resumen": {
                "num_diferenciales":  num_diffs,
                "num_activos":        num_activos,
                "consumo_total_kw":   consumo_edificio,
                "coste_hora_eur":     coste_edificio_h,
                "coste_dia_est_eur":  round(coste_edificio_h * 24, 2),
                "status":             status_edificio,
            },
            "eficiencia": {
                "consumo_medio_diferencial_kw": round(consumo_edificio / num_diffs, 4) if num_diffs else 0.0,
                "factor_carga_pct":             round(consumo_edificio / max_teorico_kw * 100, 2) if max_teorico_kw else 0.0,
                # vs_media_global_pct se enriquece en el paso siguiente
                "vs_media_global_pct": None,
            },
            "diferenciales": diferenciales_out,
            "alertas":       alertas_edificio,
        })

        alertas_glob.extend(alertas_edificio)

    # ── Métricas globales ────────────────────────────────────────────────────
    consumos      = [e["resumen"]["consumo_total_kw"] for e in edificios_out]
    consumo_total = round(sum(consumos), 4)
    media_global  = round(consumo_total / len(consumos), 4) if consumos else 0.0
    coste_total_h = round(sum(e["resumen"]["coste_hora_eur"] for e in edificios_out), 4)

    # Enriquecer eficiencia con vs_media_global_pct
    for e in edificios_out:
        c = e["resumen"]["consumo_total_kw"]
        e["eficiencia"]["vs_media_global_pct"] = (
            round((c - media_global) / media_global * 100, 2) if media_global else 0.0
        )

    # ── Ranking de eficiencia ────────────────────────────────────────────────
    ordenados = sorted(edificios_out, key=lambda e: e["resumen"]["consumo_total_kw"])
    consumo_mejor = ordenados[0]["resumen"]["consumo_total_kw"] if ordenados else 1.0
    consumo_peor  = ordenados[-1]["resumen"]["consumo_total_kw"] if ordenados else 1.0

    ranking = []
    for pos, e in enumerate(ordenados, start=1):
        c = e["resumen"]["consumo_total_kw"]
        ranking.append({
            "posicion":              pos,
            "id":                    e["id"],
            "consumo_total_kw":      c,
            "coste_hora_eur":        e["resumen"]["coste_hora_eur"],
            "vs_media_pct":          e["eficiencia"]["vs_media_global_pct"],
            "vs_peor_pct":           round((c - consumo_peor) / consumo_peor * 100, 2) if consumo_peor else 0.0,
            "status":                e["resumen"]["status"],
        })

    # ── Resumen global ───────────────────────────────────────────────────────
    resumen_global = {
        "num_edificios":              len(edificios_out),
        "num_diferenciales":          sum(e["resumen"]["num_diferenciales"] for e in edificios_out),
        "num_activos":                sum(e["resumen"]["num_activos"] for e in edificios_out),
        "consumo_total_kw":           consumo_total,
        "coste_hora_eur":             coste_total_h,
        "coste_dia_est_eur":          round(coste_total_h * 24, 2),
        "media_consumo_por_edificio_kw": media_global,
        "num_alertas":                len(alertas_glob),
        "edificio_mas_eficiente":     {"id": ordenados[0]["id"],  "consumo_total_kw": consumo_mejor} if ordenados else None,
        "edificio_menos_eficiente":   {"id": ordenados[-1]["id"], "consumo_total_kw": consumo_peor}  if ordenados else None,
    }

    return {
        "snapshot_time": ts,
        "mercado": {
            "precio_kwh":      precio_kwh,
            "periodo_tarifario": periodo,
            "alerta_precio":   alerta_precio,
        },
        "resumen_global":    resumen_global,
        "edificios":         edificios_out,
        "ranking_eficiencia": ranking,
        "alertas":           alertas_glob,
    }


# ════════════════════════════════════════════════════════════════════════════
# API pública
# ════════════════════════════════════════════════════════════════════════════

def get_data() -> dict:
    """
    Devuelve el snapshot completo. Llamar desde el front en cada refresco.
    No produce efectos secundarios (no escribe CSV).
    """
    return _snapshot()


def ingest() -> dict:
    """
    Igual que get_data() pero además persiste una fila por diferencial en el CSV histórico.
    Llamar desde un scheduler o desde el botón "Registrar" del front.
    """
    snap = _snapshot()
    edificios_idx = {e["id"]: e for e in snap["edificios"]}

    file_exists = os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        for e in snap["edificios"]:
            for d in e["diferenciales"]:
                writer.writerow({
                    "timestamp":           snap["snapshot_time"],
                    "periodo_tarifario":   snap["mercado"]["periodo_tarifario"],
                    "precio_kwh":          snap["mercado"]["precio_kwh"],
                    "edificio_id":         e["id"],
                    "diferencial_id":      d["id"],
                    "fase":                d["fase"],
                    "activo":              d["activo"],
                    "consumo_kw":          d["consumo_kw"],
                    "consumo_edificio_kw": e["resumen"]["consumo_total_kw"],
                    "coste_hora_eur":      d["coste_hora_eur"],
                    "status":              d["status"],
                })
    return snap


def panico_energetico(building_id: str | None = None) -> dict:
    """Corte remoto. None → aplica a todos los edificios."""
    targets = (
        [building_id] if building_id
        else [f"edificio_{i:02d}" for i in range(1, NUM_EDIFICIOS + 1)]
    )
    for bid in targets:
        _panic[bid] = True
    return {"accion": "PANICO_ENERGETICO", "edificios_afectados": targets}


def desactivar_panico(building_id: str | None = None) -> dict:
    """Restaura estado normal."""
    targets = (
        [building_id] if building_id
        else [f"edificio_{i:02d}" for i in range(1, NUM_EDIFICIOS + 1)]
    )
    for bid in targets:
        _panic[bid] = False
    return {"accion": "RESTAURAR_NORMAL", "edificios_afectados": targets}


# ════════════════════════════════════════════════════════════════════════════
# Smoke test
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json
    print(json.dumps(get_data(), ensure_ascii=False, indent=2))
