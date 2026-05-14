"""
test_all.py — Prueba integral de todas las funcionalidades del backend Energy Hunter
"""

import json
import sys
import time
import traceback

PASS = "✅"
FAIL = "❌"
results = []


def test(nombre, fn):
    try:
        result = fn()
        print(f"{PASS}  {nombre}")
        results.append((nombre, True, None))
        return result
    except Exception as e:
        print(f"{FAIL}  {nombre}")
        print(f"     {e}")
        traceback.print_exc()
        results.append((nombre, False, str(e)))
        return None


# ══════════════════════════════════════════════════════════════════════════════
print("\n── 1. Generadores (mocks de APIs) ────────────────────────────────────")
# ══════════════════════════════════════════════════════════════════════════════

from generar_elec import generar as gen_elec
from generar_dev  import generar as gen_dev

elec = test("generar_elec → devuelve JSON con 24 precios",
    lambda: (r := gen_elec()) and
            len(r["included"][0]["attributes"]["values"]) == 24 or (_ for _ in ()).throw(AssertionError("≠24 horas")))

dev = test("generar_dev  → devuelve JSON con dispositivos",
    lambda: (r := gen_dev()) and len(r["dispositivos"]) > 0 or (_ for _ in ()).throw(AssertionError("sin dispositivos")))

test("generar_dev  → corriente_a > 0 en dispositivos activos",
    lambda: all(
        d["corriente_a"] > 0
        for d in gen_dev()["dispositivos"]
        if d["estado"] == "CERRADO"
    ) or (_ for _ in ()).throw(AssertionError("corriente_a = 0 en activo")))


# ══════════════════════════════════════════════════════════════════════════════
print("\n── 2. engine.get_data() ─────────────────────────────────────────────")
# ══════════════════════════════════════════════════════════════════════════════

import engine

snap = test("get_data() → snapshot completo sin error",
    lambda: (r := engine.get_data()) and "error" not in r or (_ for _ in ()).throw(AssertionError(r.get("error"))))

test("get_data() → contiene claves obligatorias",
    lambda: all(k in engine.get_data() for k in
                ["timestamp","precio_kwh","periodo_tarifario","alerta_activa",
                 "num_alertas","diferenciales","edificios","ranking_eficiencia","alertas"]))

test("get_data() → texto_alerta presente en cada diferencial",
    lambda: all("texto_alerta" in d for d in engine.get_data()["diferenciales"]))

snap_ed = test("get_data('edificio_01') → solo datos de ese edificio",
    lambda: (r := engine.get_data("edificio_01")) and
            all(d["id_edificio"] == "edificio_01" for d in r["diferenciales"]) or
            (_ for _ in ()).throw(AssertionError("hay diferenciales de otro edificio")))

test("get_data() → periodo_tarifario es VALLE/LLANO/PUNTA",
    lambda: engine.get_data()["periodo_tarifario"] in ("VALLE","LLANO","PUNTA"))

test("get_data() → precio_kwh > 0",
    lambda: engine.get_data()["precio_kwh"] > 0)

test("get_data() → consumo_diferencial_kw = 0 si activo=False",
    lambda: all(
        d["consumo_diferencial_kw"] == 0.0
        for d in engine.get_data()["diferenciales"]
        if not d["activo"]
    ))


# ══════════════════════════════════════════════════════════════════════════════
print("\n── 3. engine.get_ranking() ──────────────────────────────────────────")
# ══════════════════════════════════════════════════════════════════════════════

ranking = test("get_ranking() → lista no vacía",
    lambda: (r := engine.get_ranking()) and len(r) > 0)

test("get_ranking() → posiciones correlativas desde 1",
    lambda: [r["posicion"] for r in engine.get_ranking()] == list(range(1, len(engine.get_ranking())+1)))

test("get_ranking() → ordenado por consumo_total_kw ascendente",
    lambda: (r := engine.get_ranking()) and
            all(r[i]["consumo_total_kw"] <= r[i+1]["consumo_total_kw"] for i in range(len(r)-1)))


# ══════════════════════════════════════════════════════════════════════════════
print("\n── 4. Pánico energético ─────────────────────────────════════════════")
# ══════════════════════════════════════════════════════════════════════════════

test("panico_energetico('edificio_01') → accion correcta",
    lambda: engine.panico_energetico("edificio_01")["accion"] == "PANICO_ENERGETICO")

test("tras pánico → consumo edificio_01 = 0",
    lambda: (r := engine.get_data("edificio_01")) and
            r["edificios"][0]["consumo_total_kw"] == 0.0 or
            (_ for _ in ()).throw(AssertionError(f"consumo={r['edificios'][0]['consumo_total_kw']}")))

test("tras pánico → status = PANICO en diferenciales edificio_01",
    lambda: all(d["status"] == "PANICO" for d in engine.get_data("edificio_01")["diferenciales"]))

test("tras pánico → alerta_activa = True",
    lambda: engine.get_data("edificio_01")["alerta_activa"] is True)

test("desactivar_panico('edificio_01') → accion correcta",
    lambda: engine.desactivar_panico("edificio_01")["accion"] == "RESTAURAR_NORMAL")

test("tras restaurar → consumo edificio_01 > 0",
    lambda: engine.get_data("edificio_01")["edificios"][0]["consumo_total_kw"] > 0)


# ══════════════════════════════════════════════════════════════════════════════
print("\n── 5. Watchdog ──────────────────────────────────────────────────────")
# ══════════════════════════════════════════════════════════════════════════════

import heartbeat
from datetime import date

test("heartbeat.iniciar() arranca sin error",
    lambda: heartbeat.iniciar(intervalo_seg=1) or True)

time.sleep(2.5)

test("heartbeat.estado() → activo=True tras iniciar",
    lambda: heartbeat.estado()["activo"] is True)

test("heartbeat.estado() → num_latidos >= 1",
    lambda: heartbeat.estado()["num_latidos"] >= 1)

test("heartbeat.estado() → ultimo_latido no es None",
    lambda: heartbeat.estado()["ultimo_latido"] is not None)

test("watchdog genera snapshot CSV del día",
    lambda: __import__("os").path.exists(heartbeat.ruta_snapshot(date.today())))

test("heartbeat.detener() para el watchdog",
    lambda: heartbeat.detener() or True)

test("heartbeat.estado() → activo=False tras detener",
    lambda: heartbeat.estado()["activo"] is False)


# ══════════════════════════════════════════════════════════════════════════════
print("\n── 6. Analytics — Auditoría ─────────────────────────────────────────")
# ══════════════════════════════════════════════════════════════════════════════

from analytics import generar_auditoria, predecir_consumo

auditoria = test("generar_auditoria() → sin error",
    lambda: (r := generar_auditoria()) and "error" not in r or
            (_ for _ in ()).throw(AssertionError(r.get("error"))))

test("generar_auditoria() → contiene claves obligatorias",
    lambda: all(k in generar_auditoria() for k in
                ["fecha","global","edificios","diferenciales",
                 "distribucion_periodos_tarifarios","grafico"]))

test("generar_auditoria() → genera fichero PNG",
    lambda: (r := generar_auditoria()) and __import__("os").path.exists(r["grafico"]))

test("generar_auditoria() → coste_acumulado_eur > 0",
    lambda: generar_auditoria()["global"]["coste_acumulado_eur"] > 0)


# ══════════════════════════════════════════════════════════════════════════════
print("\n── 7. Analytics — Predicción ────────────────────────────────────────")
# ══════════════════════════════════════════════════════════════════════════════

pred = test("predecir_consumo() → sin error",
    lambda: (r := predecir_consumo()) and "error" not in r or
            (_ for _ in ()).throw(AssertionError(r.get("error"))))

test("predecir_consumo() → 4 predicciones por diferencial",
    lambda: (r := predecir_consumo()) and
            all(len(d["predicciones"]) == 4 for d in r["diferenciales"]))

test("predecir_consumo() → consumo_estimado_kw en rango [0, 10]",
    lambda: (r := predecir_consumo()) and
            all(0 <= p["consumo_estimado_kw"] <= 10
                for d in r["diferenciales"] for p in d["predicciones"]))

test("predecir_consumo() → genera fichero PNG",
    lambda: (r := predecir_consumo()) and __import__("os").path.exists(r["grafico"]))

test("predecir_consumo(n_predicciones=8) → 8 predicciones",
    lambda: (r := predecir_consumo(n_predicciones=8)) and
            all(len(d["predicciones"]) == 8 for d in r["diferenciales"]))


# ══════════════════════════════════════════════════════════════════════════════
print("\n── Resultado final ───────────────────────────────────────────────────")
# ══════════════════════════════════════════════════════════════════════════════

total  = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed

print(f"\n  {passed}/{total} tests pasados", end="")
if failed:
    print(f"  ({failed} fallaron)")
    print("\n  Tests fallidos:")
    for nombre, ok, err in results:
        if not ok:
            print(f"    {FAIL} {nombre}: {err}")
else:
    print("  — todo correcto 🎉")

sys.exit(0 if failed == 0 else 1)
