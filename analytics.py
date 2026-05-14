"""
Analytics · Energy Hunter

generar_auditoria()  → JSON con análisis del día actual (pandas + matplotlib)
predecir_consumo()   → JSON con predicciones de consumo a corto plazo (sklearn LinearRegression)
"""

import json
import os
from datetime import date, datetime, timedelta

import matplotlib
matplotlib.use("Agg")   # sin GUI — necesario en entornos sin pantalla
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures

from generar_dev import CONSUMO_MAX_KW
from heartbeat import ruta_snapshot, ruta_resumen, DIR_DATOS

DIR_CHARTS = os.path.join(DIR_DATOS, "charts")


# ════════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════════

def _cargar_snapshot(dia: date) -> pd.DataFrame | None:
    ruta = ruta_snapshot(dia)
    if not os.path.exists(ruta):
        return None
    df = pd.read_csv(ruta, parse_dates=["timestamp"])
    df["minutos_dia"] = df["timestamp"].dt.hour * 60 + df["timestamp"].dt.minute
    return df


def _guardar_grafico(fig: plt.Figure, nombre: str) -> str:
    os.makedirs(DIR_CHARTS, exist_ok=True)
    ruta = os.path.join(DIR_CHARTS, nombre)
    fig.savefig(ruta, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return ruta


# ════════════════════════════════════════════════════════════════════════════
# Feature 1 · Auditoría diaria
# ════════════════════════════════════════════════════════════════════════════

def generar_auditoria(fecha: str | None = None) -> dict:
    """
    Analiza el snapshot CSV del día con pandas y genera un informe JSON.
    Además exporta un gráfico de evolución de consumo por diferencial.

    Args:
        fecha: 'YYYY-MM-DD'. Por defecto hoy.

    Returns:
        dict con el informe completo.
    """
    dia = date.fromisoformat(fecha) if fecha else date.today()
    df  = _cargar_snapshot(dia)

    if df is None or df.empty:
        return {"error": f"Sin datos para {dia}. Ejecuta heartbeat.iniciar() primero."}

    ts_inicio = df["timestamp"].min().isoformat()
    ts_fin    = df["timestamp"].max().isoformat()

    # ── Métricas globales ────────────────────────────────────────────────────
    global_ = {
        "consumo_medio_kw":       round(df["consumo_diferencial_kw"].mean(), 4),
        "consumo_max_kw":         round(df["consumo_diferencial_kw"].max(),  4),
        "consumo_min_kw":         round(df[df["consumo_diferencial_kw"] > 0]["consumo_diferencial_kw"].min(), 4),
        "desviacion_tipica_kw":   round(df["consumo_diferencial_kw"].std(),  4),
        "coste_acumulado_eur":    round(df["coste_hora_eur"].sum() * (15 / 60), 4),
        "precio_medio_kwh":       round(df["precio_kwh"].mean(), 6),
        "precio_max_kwh":         round(df["precio_kwh"].max(),  6),
        "precio_min_kwh":         round(df["precio_kwh"].min(),  6),
        "num_lecturas":           len(df["timestamp"].unique()),
        "pct_diferenciales_activos": round(df["activo"].astype(bool).mean() * 100, 2),
    }

    # ── Por edificio ─────────────────────────────────────────────────────────
    por_edificio = []
    for eid, g in df.groupby("id_edificio"):
        consumo_total = g.groupby("timestamp")["consumo_diferencial_kw"].sum()
        por_edificio.append({
            "id_edificio":          eid,
            "consumo_medio_kw":     round(consumo_total.mean(), 4),
            "consumo_max_kw":       round(consumo_total.max(),  4),
            "consumo_min_kw":       round(consumo_total.min(),  4),
            "coste_acumulado_eur":  round(g["coste_hora_eur"].sum() * (15 / 60), 4),
            "num_alertas_anomalia": int((g["status"] == "ANOMALIA").sum()),
            "num_alertas_precio":   int((g["status"] == "PRECIO_ALTO").sum()),
            "num_diferenciales":    g["id_diferencial"].nunique(),
        })

    # ── Por diferencial ──────────────────────────────────────────────────────
    por_diferencial = []
    for did, g in df.groupby(["id_edificio", "id_diferencial"]):
        por_diferencial.append({
            "id_edificio":          did[0],
            "id_diferencial":       did[1],
            "consumo_medio_kw":     round(g["consumo_diferencial_kw"].mean(), 4),
            "consumo_max_kw":       round(g["consumo_diferencial_kw"].max(),  4),
            "corriente_media_a":    round(g["corriente_a"].mean(), 3),
            "tension_media_v":      round(g["tension_v"].mean(),   2),
            "fp_medio":             round(g["factor_potencia"].mean(), 3),
            "coste_acumulado_eur":  round(g["coste_hora_eur"].sum() * (15 / 60), 4),
            "pct_tiempo_activo":    round(g["activo"].astype(bool).mean() * 100, 2),
            "status_predominante":  g["status"].value_counts().index[0],
        })

    # ── Distribución por periodo tarifario ────────────────────────────────────
    dist_periodos = {}
    for periodo, g in df.groupby("periodo_tarifario"):
        dist_periodos[periodo] = {
            "num_lecturas":     len(g["timestamp"].unique()),
            "consumo_medio_kw": round(g["consumo_diferencial_kw"].mean(), 4),
            "precio_medio_kwh": round(g["precio_kwh"].mean(), 6),
            "coste_acumulado_eur": round(g["coste_hora_eur"].sum() * (15 / 60), 4),
        }

    # ── Hora pico y hora valle ────────────────────────────────────────────────
    consumo_por_lectura = df.groupby("timestamp")["consumo_diferencial_kw"].sum().reset_index()
    idx_max = consumo_por_lectura["consumo_diferencial_kw"].idxmax()
    idx_min = consumo_por_lectura["consumo_diferencial_kw"].idxmin()
    pico = {
        "timestamp":    consumo_por_lectura.loc[idx_max, "timestamp"].isoformat(),
        "consumo_kw":   round(consumo_por_lectura.loc[idx_max, "consumo_diferencial_kw"], 4),
    }
    valle = {
        "timestamp":    consumo_por_lectura.loc[idx_min, "timestamp"].isoformat(),
        "consumo_kw":   round(consumo_por_lectura.loc[idx_min, "consumo_diferencial_kw"], 4),
    }

    # ── Gráfico: evolución de consumo por edificio ────────────────────────────
    consumo_edificio_t = (
        df.groupby(["timestamp", "id_edificio"])["consumo_diferencial_kw"]
        .sum()
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(12, 5))
    for eid, g in consumo_edificio_t.groupby("id_edificio"):
        ax.plot(g["timestamp"], g["consumo_diferencial_kw"], marker="o", markersize=4, label=eid)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.set_xlabel("Hora")
    ax.set_ylabel("Consumo total (kW)")
    ax.set_title(f"Evolución de consumo por edificio — {dia}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    ruta_chart = _guardar_grafico(fig, f"auditoria_{dia}.png")

    return {
        "fecha":             dia.isoformat(),
        "generado_en":       datetime.now().isoformat(timespec="seconds"),
        "periodo_analizado": {"inicio": ts_inicio, "fin": ts_fin},
        "global":            global_,
        "pico_consumo":      pico,
        "valle_consumo":     valle,
        "distribucion_periodos_tarifarios": dist_periodos,
        "edificios":         por_edificio,
        "diferenciales":     por_diferencial,
        "grafico":           ruta_chart,
    }


# ════════════════════════════════════════════════════════════════════════════
# Feature 2 · Predicción de consumo (regresión lineal polinómica)
# ════════════════════════════════════════════════════════════════════════════

def predecir_consumo(n_predicciones: int = 4, fecha: str | None = None) -> dict:
    """
    Entrena un modelo de regresión lineal (grado 2) por diferencial usando
    los datos del día actual y predice los próximos n_predicciones × 15 min.

    Args:
        n_predicciones: número de pasos futuros a predecir (1 paso = 15 min).
        fecha:          'YYYY-MM-DD'. Por defecto hoy.

    Returns:
        dict con las predicciones por diferencial y métricas del modelo.
    """
    dia = date.fromisoformat(fecha) if fecha else date.today()
    df  = _cargar_snapshot(dia)

    if df is None or df.empty:
        return {"error": f"Sin datos para {dia}. Ejecuta heartbeat.iniciar() primero."}

    n_puntos = df["timestamp"].nunique()
    if n_puntos < 3:
        return {"error": f"Datos insuficientes ({n_puntos} lecturas). Se necesitan al menos 3."}

    # Último timestamp conocido
    ultimo_ts    = df["timestamp"].max()
    futuros_ts   = [ultimo_ts + timedelta(minutes=15 * i) for i in range(1, n_predicciones + 1)]
    futuros_min  = np.array([ts.hour * 60 + ts.minute for ts in futuros_ts]).reshape(-1, 1)

    modelo = Pipeline([
        ("poly",  PolynomialFeatures(degree=2, include_bias=False)),
        ("linreg", LinearRegression()),
    ])

    predicciones_por_diff = []

    for (eid, did), g in df.groupby(["id_edificio", "id_diferencial"]):
        g = g.sort_values("timestamp")
        X = g["minutos_dia"].values.reshape(-1, 1)
        y = g["consumo_diferencial_kw"].values

        modelo.fit(X, y)
        r2   = round(float(modelo.score(X, y)), 4)
        pred = modelo.predict(futuros_min) if r2 >= 0.3 else np.full(len(futuros_min), y.mean())
        pred = np.clip(pred, 0, CONSUMO_MAX_KW)

        predicciones_por_diff.append({
            "id_edificio":    eid,
            "id_diferencial": did,
            "r2_train":       r2,
            "ultimo_consumo_real_kw": round(float(y[-1]), 3),
            "predicciones": [
                {
                    "timestamp_est":          ts.isoformat(),
                    "minutos_desde_medianoche": int(ts.hour * 60 + ts.minute),
                    "consumo_estimado_kw":    round(float(v), 3),
                }
                for ts, v in zip(futuros_ts, pred)
            ],
        })

    # ── Gráfico: histórico + predicciones para cada diferencial ──────────────
    n_diffs = len(predicciones_por_diff)
    n_cols  = 3
    n_rows  = (n_diffs + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 4 * n_rows), squeeze=False)

    for idx, item in enumerate(predicciones_por_diff):
        ax  = axes[idx // n_cols][idx % n_cols]
        g   = df[df["id_diferencial"] == item["id_diferencial"]].sort_values("timestamp")

        # Histórico
        ax.plot(g["timestamp"], g["consumo_diferencial_kw"],
                "o-", color="steelblue", label="Real", linewidth=1.5)

        # Predicciones
        pred_ts  = [p["timestamp_est"] for p in item["predicciones"]]
        pred_kw  = [p["consumo_estimado_kw"] for p in item["predicciones"]]
        ax.plot(pd.to_datetime(pred_ts), pred_kw,
                "s--", color="tomato", label="Predicción", linewidth=1.5)

        ax.set_title(f"{item['id_diferencial']}  (R²={item['r2_train']})", fontsize=9)
        ax.set_ylabel("kW", fontsize=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.tick_params(axis="x", labelsize=7)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

    # Ocultar subplots vacíos
    for idx in range(n_diffs, n_rows * n_cols):
        axes[idx // n_cols][idx % n_cols].set_visible(False)

    fig.suptitle(f"Predicción de consumo — próximos {n_predicciones * 15} min", fontsize=12)
    fig.autofmt_xdate()
    plt.tight_layout()
    ruta_chart = _guardar_grafico(fig, f"prediccion_{dia}.png")

    return {
        "fecha":              dia.isoformat(),
        "generado_en":        datetime.now().isoformat(timespec="seconds"),
        "modelo":             "LinearRegression (PolynomialFeatures degree=2)",
        "n_puntos_entrenamiento": n_puntos,
        "horizonte_lecturas": n_predicciones,
        "horizonte_minutos":  n_predicciones * 15,
        "ultimo_timestamp_real": ultimo_ts.isoformat(),
        "diferenciales":      predicciones_por_diff,
        "grafico":            ruta_chart,
    }


# ════════════════════════════════════════════════════════════════════════════
# Smoke test
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Generar datos de prueba si no existen
    import heartbeat, time
    print("Generando 5 snapshots de prueba...")
    for _ in range(5):
        heartbeat.latido()
        heartbeat.detener()
        time.sleep(0.5)

    print("\n── Auditoría ──────────────────────────────────────────────────")
    auditoria = generar_auditoria()
    print(json.dumps({
        k: v for k, v in auditoria.items()
        if k not in ("edificios", "diferenciales")
    }, indent=2, ensure_ascii=False))
    print(f"  Gráfico → {auditoria.get('grafico')}")

    print("\n── Predicción ─────────────────────────────────────────────────")
    pred = predecir_consumo(n_predicciones=4)
    if "error" not in pred:
        print(json.dumps({
            k: v for k, v in pred.items() if k != "diferenciales"
        }, indent=2, ensure_ascii=False))
        print("  Ejemplo predicciones diff_01_01:")
        diff = next(d for d in pred["diferenciales"] if d["id_diferencial"] == "diff_01_01")
        print(json.dumps(diff["predicciones"], indent=4, ensure_ascii=False))
        print(f"  Gráfico → {pred.get('grafico')}")
    else:
        print(pred["error"])
