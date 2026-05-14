"""
engine.py — Energy Hunter · Backend core

Punto de entrada único para el front:
  get_data(id_edificio?)  → snapshot completo o filtrado por edificio
  get_ranking()           → lista de edificios ordenada por eficiencia
  panico_energetico(id?)  → corte remoto
  desactivar_panico(id?)  → restaura estado normal
"""

import csv
import os
from datetime import datetime

from generar_elec import generar as _api_elec
from generar_dev  import generar as _api_dev, NUM_EDIFICIOS, CONSUMO_MAX_KW

# ── Umbrales de negocio ───────────────────────────────────────────────────────
PRECIO_ALTO_KWH  = 0.15   # €/kWh — por encima → alerta PRECIO_ALTO
ANOMALIA_KW      = 2.0    # kW/diferencial fuera de horario → alerta ANOMALIA

# ── Estado de pánico en memoria ───────────────────────────────────────────────
_panic: dict[str, bool] = {}

# ── Cortes manuales por diferencial ──────────────────────────────────────────
# Clave: "{id_edificio}/{id_diferencial}"
_diff_off: set[str] = set()

# ── CSV histórico ─────────────────────────────────────────────────────────────
CSV_PATH = "data/historico_consumo.csv"
_CSV_COLS = [
    "timestamp", "periodo_tarifario", "precio_kwh",
    "id_edificio", "id_diferencial", "id_fase",
    "activo", "consumo_diferencial_kw", "corriente_a", "tension_v",
    "consumo_edificio_kw", "coste_hora_eur", "status",
]

# Prioridad para escalar status al nivel de edificio
_PRIO = {"OK": 0, "APAGADO": 1, "CORTADO": 1, "PRECIO_ALTO": 2, "ANOMALIA": 3, "PANICO": 4}

# Textos de alerta por tipo
_TEXTOS_ALERTA = {
    "ANOMALIA":    "⚠️ Consumo anómalo: superado el umbral de {umbral} kW fuera de horario laboral ({consumo} kW activos).",
    "PRECIO_ALTO": "💸 Precio de mercado elevado: {precio} €/kWh. Considera diferir cargas no críticas.",
    "PANICO":      "🔴 Pánico energético activo: circuito cortado remotamente.",
    "CORTADO":     "✂️ Diferencial cortado manualmente por el operador.",
}


# ════════════════════════════════════════════════════════════════════════════════
# Helpers internos
# ════════════════════════════════════════════════════════════════════════════════

def _precio_kwh_actual(datos_elec: dict) -> float:
    hora = datetime.now().hour
    mwh  = datos_elec["included"][0]["attributes"]["values"][hora]["value"]
    return round(mwh / 1000, 6)


def _periodo_tarifario() -> str:
    """Periodos 2.0TD peninsular (REE España)."""
    h, finde = datetime.now().hour, datetime.now().weekday() >= 5
    if finde or h < 8:                    return "VALLE"
    if (10 <= h < 14) or (18 <= h < 22): return "PUNTA"
    return "LLANO"


def _hora_baja_actividad() -> bool:
    ahora = datetime.now()
    return ahora.weekday() >= 5 or ahora.hour < 7 or ahora.hour >= 22


def _calcular_status(activo: bool, consumo_kw: float, precio_kwh: float,
                     eid: str, cortado_manual: bool = False) -> str:
    if _panic.get(eid):                                        return "PANICO"
    if cortado_manual:                                         return "CORTADO"
    if not activo:                                             return "APAGADO"
    if _hora_baja_actividad() and consumo_kw > ANOMALIA_KW:   return "ANOMALIA"
    if precio_kwh > PRECIO_ALTO_KWH:                          return "PRECIO_ALTO"
    return "OK"


def _texto_alerta(status: str, consumo_kw: float, precio_kwh: float) -> str | None:
    if status == "ANOMALIA":
        return _TEXTOS_ALERTA["ANOMALIA"].format(umbral=ANOMALIA_KW, consumo=consumo_kw)
    if status == "PRECIO_ALTO":
        return _TEXTOS_ALERTA["PRECIO_ALTO"].format(precio=round(precio_kwh, 4))
    if status in ("PANICO", "CORTADO"):
        return _TEXTOS_ALERTA[status]
    return None


# ════════════════════════════════════════════════════════════════════════════════
# Núcleo: construir snapshot
# ════════════════════════════════════════════════════════════════════════════════

def _build_snapshot() -> dict:
    datos_elec = _api_elec()
    datos_dev  = _api_dev()
    precio_kwh = _precio_kwh_actual(datos_elec)
    periodo    = _periodo_tarifario()
    ts         = datos_dev["snapshot_time"]

    # ── Paso 1: consumo total por edificio (respetando overrides) ────────────
    consumo_edificio: dict[str, float] = {}
    num_diffs:        dict[str, int]   = {}
    for dev in datos_dev["dispositivos"]:
        eid  = dev["id_edificio"]
        key  = f"{eid}/{dev['id_diferencial']}"
        activo = (dev["estado"] == "CERRADO"
                  and not _panic.get(eid)
                  and key not in _diff_off)
        consumo_edificio[eid] = round(
            consumo_edificio.get(eid, 0.0) + (dev["potencia_kw"] if activo else 0.0), 3
        )
        num_diffs[eid] = num_diffs.get(eid, 0) + 1

    # ── Paso 2: lista plana de diferenciales ──────────────────────────────────
    diferenciales = []
    alertas       = []

    if precio_kwh > PRECIO_ALTO_KWH:
        alertas.append({
            "tipo": "PRECIO_ALTO", "severidad": "WARNING",
            "id_edificio": None, "id_diferencial": None,
            "texto": _texto_alerta("PRECIO_ALTO", 0, precio_kwh),
        })

    for dev in datos_dev["dispositivos"]:
        eid            = dev["id_edificio"]
        key            = f"{eid}/{dev['id_diferencial']}"
        cortado_manual = key in _diff_off
        activo         = (dev["estado"] == "CERRADO"
                          and not _panic.get(eid)
                          and not cortado_manual)
        consumo_kw = round(dev["potencia_kw"], 3) if activo else 0.0
        status     = _calcular_status(activo, consumo_kw, precio_kwh, eid, cortado_manual)
        coste_h    = round(consumo_kw * precio_kwh, 4)
        c_edif     = consumo_edificio[eid]
        texto      = _texto_alerta(status, consumo_kw, precio_kwh)

        diferenciales.append({
            "id_edificio":            eid,
            "id_diferencial":         dev["id_diferencial"],
            "id_fase":                dev["id_fase"],
            "activo":                 activo,
            "cortado_manualmente":    cortado_manual,
            "consumo_diferencial_kw": consumo_kw,
            "corriente_a":            dev["corriente_a"]     if activo else 0.0,
            "tension_v":              dev["tension_v"]       if activo else 0.0,
            "factor_potencia":        dev["factor_potencia"] if activo else 0.0,
            "coste_hora_eur":         coste_h,
            "consumo_edificio_kw":    c_edif,
            "num_diferenciales":      num_diffs[eid],
            "pct_sobre_edificio":     round(consumo_kw / c_edif * 100, 2) if c_edif > 0 else 0.0,
            "status":                 status,
            "texto_alerta":           texto,
        })

        if status in ("ANOMALIA", "PANICO", "CORTADO"):
            alertas.append({
                "tipo":           status,
                "severidad":      "CRITICAL" if status == "PANICO" else "WARNING",
                "id_edificio":    eid,
                "id_diferencial": dev["id_diferencial"],
                "texto":          texto,
            })

    # ── Paso 3: resumen por edificio ──────────────────────────────────────────
    edificios_map: dict[str, dict] = {}
    for d in diferenciales:
        eid = d["id_edificio"]
        if eid not in edificios_map:
            edificios_map[eid] = {
                "id_edificio":       eid,
                "num_diferenciales": d["num_diferenciales"],
                "num_activos":       0,
                "consumo_total_kw":  d["consumo_edificio_kw"],
                "coste_hora_eur":    round(d["consumo_edificio_kw"] * precio_kwh, 4),
                "factor_carga_pct":  round(
                    d["consumo_edificio_kw"] / (d["num_diferenciales"] * CONSUMO_MAX_KW) * 100, 2
                ),
                "_statuses": [],
            }
        edificios_map[eid]["num_activos"]  += int(d["activo"])
        edificios_map[eid]["_statuses"].append(d["status"])

    edificios = []
    for e in edificios_map.values():
        statuses     = e.pop("_statuses")
        e["status"]  = max(statuses, key=lambda s: _PRIO.get(s, 0))
        e["alertas_edificio"] = [a for a in alertas if a["id_edificio"] == e["id_edificio"]]
        edificios.append(e)

    # ── Paso 4: ranking de eficiencia ─────────────────────────────────────────
    ordenados    = sorted(edificios, key=lambda e: e["consumo_total_kw"])
    media_global = round(
        sum(e["consumo_total_kw"] for e in edificios) / len(edificios), 3
    ) if edificios else 0.0
    consumo_peor = ordenados[-1]["consumo_total_kw"] if ordenados else 1.0

    ranking = []
    for pos, e in enumerate(ordenados, 1):
        c = e["consumo_total_kw"]
        ranking.append({
            "posicion":               pos,
            "id_edificio":            e["id_edificio"],
            "consumo_total_kw":       c,
            "coste_hora_eur":         e["coste_hora_eur"],
            "vs_media_pct":           round((c - media_global) / media_global * 100, 2) if media_global else 0.0,
            "ahorro_vs_peor_eur_dia": round((consumo_peor - c) * precio_kwh * 24, 2),
            "status":                 e["status"],
        })

    return {
        "timestamp":          ts,
        "precio_kwh":         precio_kwh,
        "periodo_tarifario":  periodo,
        "alerta_activa":      len(alertas) > 0,
        "num_alertas":        len(alertas),
        "diferenciales":      diferenciales,
        "edificios":          edificios,
        "ranking_eficiencia": ranking,
        "alertas":            alertas,
    }


# ════════════════════════════════════════════════════════════════════════════════
# API pública
# ════════════════════════════════════════════════════════════════════════════════

def get_data(id_edificio: str | None = None) -> dict:
    """
    Snapshot en tiempo real.

    Sin argumentos  → datos completos de todos los edificios.
    Con id_edificio → solo ese edificio (misma estructura, filtrada).

    Nunca lanza excepciones: si los generadores fallan, retorna {"error": str}.
    """
    try:
        snap = _build_snapshot()
    except Exception as exc:
        return {"error": str(exc), "timestamp": datetime.now().isoformat()}

    if id_edificio is None:
        return snap

    return {
        "timestamp":          snap["timestamp"],
        "precio_kwh":         snap["precio_kwh"],
        "periodo_tarifario":  snap["periodo_tarifario"],
        "alerta_activa":      any(a["id_edificio"] == id_edificio for a in snap["alertas"]),
        "num_alertas":        sum(1 for a in snap["alertas"] if a["id_edificio"] == id_edificio),
        "diferenciales":      [d for d in snap["diferenciales"] if d["id_edificio"] == id_edificio],
        "edificios":          [e for e in snap["edificios"]     if e["id_edificio"] == id_edificio],
        "ranking_eficiencia": [r for r in snap["ranking_eficiencia"] if r["id_edificio"] == id_edificio],
        "alertas":            [a for a in snap["alertas"] if a.get("id_edificio") == id_edificio],
    }


def get_ranking() -> list[dict]:
    """
    Ranking de eficiencia energética entre edificios.
    Llamar en cada latido para mantener el panel de ranking actualizado.
    """
    return _build_snapshot()["ranking_eficiencia"]


def panico_energetico(id_edificio: str | None = None) -> dict:
    """
    Corte remoto de todos los diferenciales de un edificio.
    None → aplica a todos los edificios.
    """
    targets = (
        [id_edificio] if id_edificio
        else [f"edificio_{i:02d}" for i in range(1, NUM_EDIFICIOS + 1)]
    )
    for bid in targets:
        _panic[bid] = True
    return {"accion": "PANICO_ENERGETICO", "edificios_afectados": targets, "timestamp": datetime.now().isoformat()}


def toggle_diferencial(id_edificio: str, id_diferencial: str) -> dict:
    """
    Alterna el corte manual de un diferencial individual.
    Si estaba activo → lo corta (CORTADO). Si estaba cortado → lo reactiva.
    """
    key = f"{id_edificio}/{id_diferencial}"
    if key in _diff_off:
        _diff_off.discard(key)
        accion = "ACTIVAR_DIFERENCIAL"
    else:
        _diff_off.add(key)
        accion = "CORTAR_DIFERENCIAL"
    return {"accion": accion, "id_edificio": id_edificio,
            "id_diferencial": id_diferencial, "timestamp": datetime.now().isoformat()}


def desactivar_panico(id_edificio: str | None = None) -> dict:
    """Restaura el estado normal tras un pánico energético."""
    targets = (
        [id_edificio] if id_edificio
        else [f"edificio_{i:02d}" for i in range(1, NUM_EDIFICIOS + 1)]
    )
    for bid in targets:
        _panic[bid] = False
    return {"accion": "RESTAURAR_NORMAL", "edificios_afectados": targets, "timestamp": datetime.now().isoformat()}


def detectar_anomalias() -> dict:
    """
    Devuelve los diferenciales y edificios con STATUS fuera de OK/APAGADO.
    Útil para el botón 'Detectar Anomalías' del dashboard.
    """
    snap = _build_snapshot()
    return {
        "dispositivos": [d for d in snap["diferenciales"]
                         if d["status"] not in ("OK", "APAGADO")],
        "edificios":    [e for e in snap["edificios"]
                         if e["status"] not in ("OK", "APAGADO")],
    }


def ingest() -> dict:
    """
    Igual que get_data() y además persiste una fila por diferencial en el CSV histórico.
    Llamado internamente por watchdog.latido(). No es necesario llamarlo desde el front.
    """
    snap = _build_snapshot()
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    file_exists = os.path.exists(CSV_PATH)

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_COLS)
        if not file_exists:
            writer.writeheader()
        for d in snap["diferenciales"]:
            writer.writerow({
                "timestamp":              snap["timestamp"],
                "periodo_tarifario":      snap["periodo_tarifario"],
                "precio_kwh":             snap["precio_kwh"],
                "id_edificio":            d["id_edificio"],
                "id_diferencial":         d["id_diferencial"],
                "id_fase":                d["id_fase"],
                "activo":                 d["activo"],
                "consumo_diferencial_kw": d["consumo_diferencial_kw"],
                "corriente_a":            d["corriente_a"],
                "tension_v":              d["tension_v"],
                "consumo_edificio_kw":    d["consumo_edificio_kw"],
                "coste_hora_eur":         d["coste_hora_eur"],
                "status":                 d["status"],
            })
    return snap


if __name__ == "__main__":
    import json
    print(json.dumps(get_data(), ensure_ascii=False, indent=2))
