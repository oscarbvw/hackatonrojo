"""
watchdog.py — Energy Hunter · Servicio de latido

Registra snapshots periódicos en CSV y genera resúmenes diarios.

Uso básico:
    import watchdog
    watchdog.iniciar(intervalo_seg=30)   # arranca en background
    info = watchdog.estado()             # consulta estado
    watchdog.detener()                   # para limpiamente
"""

import csv
import os
import threading
from datetime import date, datetime, timedelta
from typing import Callable

import pandas as pd

from engine import get_data

# ── Configuración por defecto ─────────────────────────────────────────────────
INTERVALO_SEG_DEFAULT = 15 * 60   # 15 minutos
DIR_DATOS             = "data"

_SNAP_COLS = [
    "timestamp", "precio_kwh", "periodo_tarifario",
    "id_edificio", "id_diferencial", "id_fase",
    "activo", "consumo_diferencial_kw", "corriente_a",
    "tension_v", "factor_potencia", "coste_hora_eur",
    "consumo_edificio_kw", "pct_sobre_edificio", "status",
]

# ── Estado interno ────────────────────────────────────────────────────────────
_timer:           threading.Timer | None  = None
_ultimo_dia:      date | None             = None
_ultimo_latido:   datetime | None         = None
_proximo_latido:  datetime | None         = None
_intervalo_seg:   int                     = INTERVALO_SEG_DEFAULT
_on_latido:       Callable | None         = None
_num_latidos:     int                     = 0
_activo:          bool                    = False


# ── Rutas de ficheros ─────────────────────────────────────────────────────────

def ruta_snapshot(dia: date) -> str:
    return os.path.join(DIR_DATOS, f"snapshot_{dia}.csv")


def ruta_resumen(dia: date) -> str:
    return os.path.join(DIR_DATOS, f"resumen_{dia}.csv")


# ── Escritura de snapshot ─────────────────────────────────────────────────────

def _escribir_snapshot(snap: dict, dia: date) -> None:
    os.makedirs(DIR_DATOS, exist_ok=True)
    ruta   = ruta_snapshot(dia)
    existe = os.path.exists(ruta)

    with open(ruta, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_SNAP_COLS, extrasaction="ignore")
        if not existe:
            writer.writeheader()
        for d in snap["diferenciales"]:
            writer.writerow({
                "timestamp":              snap["timestamp"],
                "precio_kwh":             snap["precio_kwh"],
                "periodo_tarifario":      snap["periodo_tarifario"],
                "id_edificio":            d["id_edificio"],
                "id_diferencial":         d["id_diferencial"],
                "id_fase":                d["id_fase"],
                "activo":                 d["activo"],
                "consumo_diferencial_kw": d["consumo_diferencial_kw"],
                "corriente_a":            d["corriente_a"],
                "tension_v":              d["tension_v"],
                "factor_potencia":        d["factor_potencia"],
                "coste_hora_eur":         d["coste_hora_eur"],
                "consumo_edificio_kw":    d["consumo_edificio_kw"],
                "pct_sobre_edificio":     d["pct_sobre_edificio"],
                "status":                 d["status"],
            })


# ── Resumen diario ────────────────────────────────────────────────────────────

def _generar_resumen_diario(dia: date) -> None:
    ruta = ruta_snapshot(dia)
    if not os.path.exists(ruta):
        return

    df = pd.read_csv(ruta)
    cols_media = [
        "consumo_diferencial_kw", "corriente_a", "tension_v",
        "factor_potencia", "coste_hora_eur", "consumo_edificio_kw",
        "pct_sobre_edificio", "precio_kwh",
    ]

    resumen = (
        df.groupby(["id_edificio", "id_diferencial", "id_fase"], as_index=False)[cols_media]
        .mean()
        .round(4)
    )
    resumen.insert(0, "fecha", dia.isoformat())
    resumen["coste_total_dia_eur"]  = (resumen["coste_hora_eur"] * 24).round(4)
    resumen["num_lecturas"]         = df.groupby("id_diferencial").size().values
    resumen["status_predominante"]  = (
        df.groupby("id_diferencial")["status"]
        .agg(lambda s: s.value_counts().index[0])
        .values
    )
    resumen.to_csv(ruta_resumen(dia), index=False, encoding="utf-8")


# ── Latido ────────────────────────────────────────────────────────────────────

def latido() -> dict:
    """
    Ejecuta un ciclo completo:
      1. Obtiene datos frescos
      2. Persiste snapshot en CSV
      3. Si cambia el día, genera resumen diario del día anterior
      4. Llama al callback on_latido si está registrado
      5. Se autoprograma para el siguiente intervalo

    Retorna el snapshot generado (útil si se llama manualmente).
    """
    global _ultimo_dia, _ultimo_latido, _proximo_latido, _num_latidos

    hoy  = date.today()
    snap = get_data()

    if _ultimo_dia is not None and _ultimo_dia != hoy:
        _generar_resumen_diario(_ultimo_dia)

    _ultimo_dia     = hoy
    _ultimo_latido  = datetime.now()
    _proximo_latido = _ultimo_latido + timedelta(seconds=_intervalo_seg)
    _num_latidos   += 1

    _escribir_snapshot(snap, hoy)

    if _on_latido is not None:
        try:
            _on_latido(snap)
        except Exception:
            pass   # el callback nunca debe tumbar el watchdog

    _reschedule()
    return snap


def _reschedule() -> None:
    global _timer
    if _activo:
        _timer = threading.Timer(_intervalo_seg, latido)
        _timer.daemon = True
        _timer.start()


# ── API pública ───────────────────────────────────────────────────────────────

def iniciar(intervalo_seg: int = INTERVALO_SEG_DEFAULT, on_latido: Callable | None = None) -> None:
    """
    Arranca el watchdog en background.

    Args:
        intervalo_seg: segundos entre latidos (por defecto 900 = 15 min).
                       Usa 30 en desarrollo para ver actualizaciones rápidas.
        on_latido:     callback opcional fn(snap: dict) llamado tras cada latido.
                       Útil para invalidar caché o notificar al front.
    """
    global _intervalo_seg, _on_latido, _activo
    _intervalo_seg = intervalo_seg
    _on_latido     = on_latido
    _activo        = True
    latido()   # primer latido inmediato; los siguientes se autoprograman


def detener() -> None:
    """Para el watchdog limpiamente. Los datos ya escritos en CSV no se pierden."""
    global _timer, _activo
    _activo = False
    if _timer is not None:
        _timer.cancel()
        _timer = None


def estado() -> dict:
    """
    Estado actual del watchdog. El front puede consultarlo para mostrar
    el indicador de 'última actualización' y 'próxima actualización'.
    """
    return {
        "activo":           _activo,
        "intervalo_seg":    _intervalo_seg,
        "num_latidos":      _num_latidos,
        "ultimo_latido":    _ultimo_latido.isoformat()  if _ultimo_latido  else None,
        "proximo_latido":   _proximo_latido.isoformat() if _proximo_latido else None,
        "csv_hoy":          ruta_snapshot(date.today()) if _ultimo_dia else None,
    }


if __name__ == "__main__":
    import time, json

    print("Test watchdog — 3 latidos cada 1 s\n")
    iniciar(intervalo_seg=1, on_latido=lambda s: print(f"  callback → alerta_activa={s['alerta_activa']}"))
    time.sleep(3.5)
    detener()

    print("\nEstado final:")
    print(json.dumps(estado(), indent=2))

    df = pd.read_csv(ruta_snapshot(date.today()))
    print(f"\nCSV snapshot → {len(df)} filas, {df['timestamp'].nunique()} lecturas")
