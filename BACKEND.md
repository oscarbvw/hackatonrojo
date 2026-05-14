# BACKEND.md — Energy Hunter · Guía de integración para el front

Este documento describe la API completa del backend para que el equipo de front sepa exactamente qué funciones llamar, cuándo llamarlas y qué espera recibir.

---

## Arquitectura general

```
generar_elec.py ──┐
                  ├──► engine.py ──► get_data() / get_ranking()
generar_dev.py  ──┘        │
                           │ ingest()
                      watchdog.py ──► snapshot_YYYY-MM-DD.csv
                           │               │
                           │        resumen_YYYY-MM-DD.csv
                           │
                      analytics.py ──► generar_auditoria()
                                   └──► predecir_consumo()
```

- **`generar_elec.py`** y **`generar_dev.py`** son mocks de APIs reales (Red Eléctrica y dispositivos IoT). No llamarlos directamente desde el front.
- **`engine.py`** es el único punto de entrada para datos en tiempo real.
- **`watchdog.py`** corre en background y persiste histórico en CSV cada N segundos.
- **`analytics.py`** consume los CSV históricos para auditoría y predicción.

---

## Arranque de la aplicación

```python
import watchdog

# Llamar UNA VEZ al inicio de la app (en Streamlit: fuera del loop de refresco)
watchdog.iniciar(
    intervalo_seg=30,          # 30 s en desarrollo; 900 (15 min) en producción
    on_latido=None             # opcional: callback fn(snap: dict) tras cada latido
)
```

El watchdog corre en un hilo daemon: no bloquea Streamlit y muere con el proceso principal.

Para parar limpiamente (opcional, solo si hay botón de stop):
```python
watchdog.detener()
```

---

## Refresco de la vista

El front debe refrescarse cada X segundos de forma independiente al watchdog. En Streamlit:

```python
import time
import streamlit as st

REFRESCO_UI_SEG = 30

# Al final del script de Streamlit:
time.sleep(REFRESCO_UI_SEG)
st.rerun()
```

En cada ciclo de refresco, el front llama a `get_data()` para obtener el snapshot fresco.

---

## Funciones disponibles

### `engine.get_data(id_edificio=None) → dict`

**Cuándo llamar:** en cada ciclo de refresco de la UI.

| Argumento | Tipo | Descripción |
|---|---|---|
| `id_edificio` | `str \| None` | `"edificio_01"`, `"edificio_02"`, … Sin argumento → todos los edificios |

#### Respuesta completa (sin filtro)

```json
{
  "timestamp":         "2026-05-14T12:52:41.000+02:00",
  "precio_kwh":        0.147973,
  "periodo_tarifario": "PUNTA",
  "alerta_activa":     false,
  "num_alertas":       0,

  "diferenciales": [
    {
      "id_edificio":            "edificio_01",
      "id_diferencial":         "diff_01_01",
      "id_fase":                "L1",
      "activo":                 true,
      "consumo_diferencial_kw": 2.532,
      "corriente_a":            12.44,
      "tension_v":              230.0,
      "factor_potencia":        0.885,
      "coste_hora_eur":         0.3747,
      "consumo_edificio_kw":    13.798,
      "num_diferenciales":      4,
      "pct_sobre_edificio":     18.35,
      "status":                 "OK",
      "texto_alerta":           null
    }
  ],

  "edificios": [
    {
      "id_edificio":       "edificio_01",
      "num_diferenciales": 4,
      "num_activos":       4,
      "consumo_total_kw":  13.798,
      "coste_hora_eur":    2.0414,
      "factor_carga_pct":  34.5,
      "status":            "OK",
      "alertas_edificio":  []
    }
  ],

  "ranking_eficiencia": [
    {
      "posicion":               1,
      "id_edificio":            "edificio_03",
      "consumo_total_kw":       11.2,
      "coste_hora_eur":         1.657,
      "vs_media_pct":           -15.2,
      "ahorro_vs_peor_eur_dia": 14.3,
      "status":                 "OK"
    }
  ],

  "alertas": [
    {
      "tipo":           "ANOMALIA",
      "severidad":      "WARNING",
      "id_edificio":    "edificio_01",
      "id_diferencial": "diff_01_03",
      "texto":          "⚠️ Consumo anómalo detectado: se ha superado el umbral de 2.0 kW fuera de horario laboral (7.1 kW activos)."
    }
  ]
}
```

#### Respuesta filtrada por edificio

Misma estructura pero todos los arrays contienen solo los datos de ese edificio. Úsala al seleccionar un edificio en el panel lateral.

```python
datos_edificio = engine.get_data("edificio_02")
```

#### Campos clave para la UI

| Campo | Uso en UI |
|---|---|
| `alerta_activa` | Mostrar badge rojo en cabecera |
| `num_alertas` | Contador de alertas en la barra de estado |
| `precio_kwh` + `periodo_tarifario` | Widget de precio actual |
| `diferenciales[].texto_alerta` | Texto junto a la fila de cada diferencial (`null` si no hay alerta) |
| `edificios[].alertas_edificio` | Alertas a nivel de edificio en el panel de detalle |
| `diferenciales[].status` | Color de la fila: OK=verde, ANOMALIA=naranja, PRECIO_ALTO=amarillo, PANICO=rojo, APAGADO=gris |

---

### `engine.get_ranking() → list[dict]`

**Cuándo llamar:** en cada latido del watchdog (o en cada refresco si quieres el ranking siempre fresco).

```python
ranking = engine.get_ranking()
```

Devuelve la misma lista que `get_data()["ranking_eficiencia"]`, pero sin construir el snapshot completo. Útil si solo necesitas el panel de ranking.

```json
[
  {
    "posicion":               1,
    "id_edificio":            "edificio_03",
    "consumo_total_kw":       11.2,
    "coste_hora_eur":         1.657,
    "vs_media_pct":           -15.2,
    "ahorro_vs_peor_eur_dia": 14.3,
    "status":                 "OK"
  }
]
```

| Campo | Uso en UI |
|---|---|
| `posicion` | Medalla o número de posición |
| `vs_media_pct` | Barra de progreso: negativo=mejor que la media, positivo=peor |
| `ahorro_vs_peor_eur_dia` | "Si este edificio consumiera como el peor, gastaría X € más al día" |

---

### `engine.panico_energetico(id_edificio=None) → dict`

**Cuándo llamar:** al pulsar el botón "Pánico Energético".

```python
# Un solo edificio
engine.panico_energetico("edificio_01")

# Todos los edificios
engine.panico_energetico()
```

Respuesta:
```json
{
  "accion":              "PANICO_ENERGETICO",
  "edificios_afectados": ["edificio_01"],
  "timestamp":           "2026-05-14T12:52:41"
}
```

Tras el pánico, el siguiente `get_data()` devolverá `consumo_diferencial_kw = 0.0` y `status = "PANICO"` para todos los diferenciales del edificio afectado.

---

### `engine.desactivar_panico(id_edificio=None) → dict`

**Cuándo llamar:** al pulsar "Restaurar servicio" tras un pánico.

```python
engine.desactivar_panico("edificio_01")
```

Misma estructura de respuesta que `panico_energetico()` con `accion = "RESTAURAR_NORMAL"`.

---

### `watchdog.estado() → dict`

**Cuándo llamar:** para mostrar el indicador de "última actualización" en el footer.

```python
import watchdog
info = watchdog.estado()
```

```json
{
  "activo":          true,
  "intervalo_seg":   30,
  "num_latidos":     12,
  "ultimo_latido":   "2026-05-14T12:52:45",
  "proximo_latido":  "2026-05-14T12:53:15",
  "csv_hoy":         "data/snapshot_2026-05-14.csv"
}
```

---

### `analytics.generar_auditoria(fecha=None) → dict`

**Cuándo llamar:** al pulsar el botón "Generar Auditoría".

```python
from analytics import generar_auditoria

informe = generar_auditoria()           # hoy
informe = generar_auditoria("2026-05-13")  # otro día
```

Requiere que exista el CSV del día (`data/snapshot_YYYY-MM-DD.csv`). Si no hay datos devuelve `{"error": "..."}`.

#### Respuesta resumida

```json
{
  "fecha":         "2026-05-14",
  "generado_en":   "2026-05-14T12:43:53",
  "periodo_analizado": {
    "inicio": "2026-05-14T08:00:00",
    "fin":    "2026-05-14T12:30:00"
  },
  "global": {
    "consumo_medio_kw":          4.84,
    "consumo_max_kw":            9.99,
    "consumo_min_kw":            0.23,
    "desviacion_tipica_kw":      2.95,
    "coste_acumulado_eur":       15.79,
    "precio_medio_kwh":          0.134,
    "precio_max_kwh":            0.170,
    "precio_min_kwh":            0.100,
    "num_lecturas":              20,
    "pct_diferenciales_activos": 96.88
  },
  "pico_consumo":  { "timestamp": "...", "consumo_kw": 119.0 },
  "valle_consumo": { "timestamp": "...", "consumo_kw": 49.25 },
  "distribucion_periodos_tarifarios": {
    "PUNTA": { "num_lecturas": 12, "consumo_medio_kw": 5.1, "precio_medio_kwh": 0.14, "coste_acumulado_eur": 9.2 },
    "LLANO": { "num_lecturas": 8,  "consumo_medio_kw": 4.3, "precio_medio_kwh": 0.10, "coste_acumulado_eur": 6.6 }
  },
  "edificios":     [...],
  "diferenciales": [...],
  "grafico":       "data/charts/auditoria_2026-05-14.png"
}
```

El campo `grafico` contiene la ruta a un PNG generado con matplotlib. En Streamlit: `st.image(informe["grafico"])`.

---

### `analytics.predecir_consumo(n_predicciones=4, fecha=None) → dict`

**Cuándo llamar:** en cada refresco del dashboard (se muestra siempre).

```python
from analytics import predecir_consumo

pred = predecir_consumo(n_predicciones=4)   # próximos 60 min
```

Requiere al menos 3 lecturas en el CSV del día. Si no hay suficientes datos devuelve `{"error": "..."}`.

#### Respuesta

```json
{
  "fecha":                   "2026-05-14",
  "generado_en":             "2026-05-14T12:44:31",
  "modelo":                  "LinearRegression (PolynomialFeatures degree=2)",
  "n_puntos_entrenamiento":  20,
  "horizonte_lecturas":      4,
  "horizonte_minutos":       60,
  "ultimo_timestamp_real":   "2026-05-14T12:30:00",
  "diferenciales": [
    {
      "id_edificio":              "edificio_01",
      "id_diferencial":           "diff_01_01",
      "r2_train":                 0.985,
      "ultimo_consumo_real_kw":   5.006,
      "predicciones": [
        { "timestamp_est": "2026-05-14T12:45:00", "minutos_desde_medianoche": 765, "consumo_estimado_kw": 5.19 },
        { "timestamp_est": "2026-05-14T13:00:00", "minutos_desde_medianoche": 780, "consumo_estimado_kw": 5.24 },
        { "timestamp_est": "2026-05-14T13:15:00", "minutos_desde_medianoche": 795, "consumo_estimado_kw": 5.21 },
        { "timestamp_est": "2026-05-14T13:30:00", "minutos_desde_medianoche": 810, "consumo_estimado_kw": 5.11 }
      ]
    }
  ],
  "grafico": "data/charts/prediccion_2026-05-14.png"
}
```

| Campo | Uso en UI |
|---|---|
| `r2_train` | Indicador de confianza del modelo (0–1). Si < 0.3 el modelo usa la media |
| `ultimo_consumo_real_kw` | Punto de anclaje del gráfico |
| `predicciones[].consumo_estimado_kw` | Valores a plotear en la línea de predicción |
| `grafico` | PNG con histórico + predicción por diferencial → `st.image(pred["grafico"])` |

---

## Mapeado UI → función

| Elemento de la UI | Función a llamar |
|---|---|
| Arranque de la app | `watchdog.iniciar(intervalo_seg=30)` |
| Refresco automático del dashboard | `engine.get_data()` |
| Selección de edificio en sidebar | `engine.get_data("edificio_0X")` |
| Panel de ranking (se actualiza en cada latido) | `get_data()["ranking_eficiencia"]` o `engine.get_ranking()` |
| Widget "Predicción de consumo" (siempre visible) | `analytics.predecir_consumo()` |
| Botón "Generar auditoría" | `analytics.generar_auditoria()` |
| Botón "Pánico Energético" | `engine.panico_energetico(id_edificio)` |
| Botón "Restaurar servicio" | `engine.desactivar_panico(id_edificio)` |
| Footer "Última actualización" | `watchdog.estado()` |
| Alerta junto a consumo | `diferenciales[i]["texto_alerta"]` (mostrar si no es `null`) |

---

## Valores de `status` y colores sugeridos

| status | Color sugerido | Significado |
|---|---|---|
| `OK` | 🟢 verde | Funcionamiento normal |
| `APAGADO` | ⚫ gris | Diferencial abierto (sin corriente) |
| `PRECIO_ALTO` | 🟡 amarillo | Precio de mercado por encima de 0.15 €/kWh |
| `ANOMALIA` | 🟠 naranja | Consumo elevado fuera de horario laboral (finde o antes 7h / después 22h) |
| `PANICO` | 🔴 rojo | Circuito cortado por el botón de pánico energético |

---

## Periodos tarifarios 2.0TD

| Periodo | Horario | Color sugerido |
|---|---|---|
| `VALLE` | 00:00–08:00 entre semana + todo el fin de semana | 🔵 azul |
| `LLANO` | 08:00–10:00, 14:00–18:00, 22:00–24:00 entre semana | 🟡 amarillo |
| `PUNTA` | 10:00–14:00 y 18:00–22:00 entre semana | 🔴 rojo |

---

## Configuración

Todos los umbrales están en `engine.py` y son modificables:

```python
PRECIO_ALTO_KWH = 0.15   # €/kWh — umbral para alerta de precio
ANOMALIA_KW     = 2.0    # kW/diferencial — umbral para anomalía fuera de horario
```

Topología de edificios en `generar_dev.py`:

```python
NUM_EDIFICIOS       = 3   # número de edificios simulados
NUM_FASES_EDIFICIO  = 4   # diferenciales por edificio
CONSUMO_MAX_KW      = 10.0
```

---

## Manejo de errores

`get_data()` nunca lanza excepciones. Si algo falla devuelve:

```json
{ "error": "descripción del error", "timestamp": "2026-05-14T12:00:00" }
```

El front debe comprobar `"error" in datos` antes de renderizar.

`generar_auditoria()` y `predecir_consumo()` también retornan `{"error": "..."}` si no hay CSV del día o si hay datos insuficientes.
