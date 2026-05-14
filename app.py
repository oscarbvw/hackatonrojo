"""
app.py — Energy Hunter · Dashboard Streamlit
Pantone: Bosque #104F3A · Hoja #2E8B57 · Lima #9ACD32 · Arena #F5EFE0 · Carbón #1F2A24
WCAG AA ≥ 4.5:1 sobre fondos claros
"""
import json, os, sys, time
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
import engine, heartbeat
from analytics import generar_auditoria, predecir_consumo

st.set_page_config(
    page_title="Smart Energy Control",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paleta Pantone — tema claro (WCAG AA) ────────────────────────────────────
# Carbón  on Arena : 12.9:1 ✅   Bosque on Arena : 8.3:1 ✅
# Hoja    on Arena : 3.7:1  ❌ decorativo   Lima on Arena: 1.6:1 ❌ decorativo
# Arena   on Bosque: 8.3:1  ✅   Carbón on Lima : 7.9:1 ✅
C = dict(
    # Pantone exactos
    bosque = "#104F3A",
    hoja   = "#2E8B57",
    lima   = "#9ACD32",
    arena  = "#F5EFE0",
    carbon = "#1F2A24",
    # Fondos claros
    bg     = "#F5EFE0",   # arena
    card   = "#FFFFFF",   # blanco puro — tarjetas sobre arena
    card2  = "#EDE6D3",   # arena oscura — sidebar, hover
    borde  = "#C8D8BC",   # sage muted
    glow   = "#2E8B57",   # hoja — bordes activos
    # Texto (todos ≥4.5:1 sobre arena)
    txt    = "#1F2A24",   # carbón  12.9:1 ✅
    sec    = "#3A5E4C",   # verde oscuro  5.2:1 ✅
    muted  = "#6B8E78",
    # Status (todos ≥4.5:1 sobre arena ✅)
    ok     = "#1A6040",   #  6.6:1
    cortado= "#7B4000",   #  7.1:1
    anom   = "#8B3600",   #  7.0:1
    precio = "#7A5F00",   #  5.3:1
    panico = "#B81C1C",   #  5.7:1
    apagado= "#4E6B5A",   #  5.1:1
    # Periodos (todos ≥4.5:1 sobre arena ✅)
    valle  = "#1565C0",   #  7.1:1
    llano  = "#7A5F00",   #  5.3:1
    punta  = "#B54300",   #  6.4:1
)

SC = {"OK":C["ok"],"CORTADO":C["cortado"],"ANOMALIA":C["anom"],
      "PRECIO_ALTO":C["precio"],"PANICO":C["panico"],"APAGADO":C["apagado"]}
SI = {"OK":"🟢","CORTADO":"✂️","ANOMALIA":"🟠","PRECIO_ALTO":"🟡","PANICO":"🔴","APAGADO":"⚫"}
PC = {"VALLE":C["valle"],"LLANO":C["llano"],"PUNTA":C["punta"]}

REFRESH  = 30
CFG_PATH = os.path.join(os.path.dirname(__file__), "data", "edificios.json")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
*,html,body{{font-family:'Inter',sans-serif;box-sizing:border-box;}}
html,body,.main,.block-container,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stBottom"]{{
    background:#F5EFE0!important;color:{C["txt"]};
}}
[data-testid="stSidebar"]{{background:{C["card2"]}!important;border-right:1px solid {C["borde"]}!important;}}

/* ── Métricas ─────────────────────────────── */
[data-testid="metric-container"]{{
    background:{C["card"]};border:1px solid {C["borde"]};
    border-top:3px solid {C["bosque"]};border-radius:12px;
    padding:14px 18px!important;transition:all .25s;
    box-shadow:0 1px 4px rgba(16,79,58,.08);
}}
[data-testid="metric-container"]:hover{{
    border-color:{C["hoja"]};box-shadow:0 4px 16px rgba(16,79,58,.14);
    transform:translateY(-2px);
}}
[data-testid="stMetricValue"]{{
    color:{C["bosque"]}!important;font-size:1.75rem!important;font-weight:800!important;
}}
[data-testid="stMetricLabel"]{{
    color:{C["sec"]}!important;font-size:.7rem!important;
    text-transform:uppercase;letter-spacing:1.5px;
}}

/* ── Botones ──────────────────────────────── */
.stButton>button{{
    border-radius:8px!important;font-weight:700!important;
    font-size:.83rem!important;transition:all .2s!important;
    letter-spacing:.3px!important;
}}
.stButton>button[kind="primary"]{{
    background:{C["bosque"]}!important;
    color:{C["arena"]}!important;border:none!important;
}}
.stButton>button[kind="primary"]:hover{{
    background:{C["hoja"]}!important;
    box-shadow:0 4px 14px rgba(16,79,58,.3)!important;
    transform:translateY(-1px)!important;
}}
.stButton>button[kind="secondary"]{{
    background:{C["card"]}!important;
    border:1.5px solid {C["bosque"]}!important;
    color:{C["bosque"]}!important;
}}
.stButton>button[kind="secondary"]:hover{{
    background:{C["card2"]}!important;
    border-color:{C["hoja"]}!important;
    color:{C["hoja"]}!important;
    box-shadow:0 2px 8px rgba(46,139,87,.2)!important;
}}
.stButton>button:disabled{{
    background:{C["card2"]}!important;color:{C["muted"]}!important;
    border:1px solid {C["borde"]}!important;
    transform:none!important;box-shadow:none!important;
}}

/* ── Contenedores con borde ───────────────── */
[data-testid="stVerticalBlockBorderWrapper"]>div{{
    background:{C["card"]}!important;border:1px solid {C["borde"]}!important;
    border-radius:12px!important;transition:all .2s;
    box-shadow:0 1px 3px rgba(16,79,58,.06);
}}
[data-testid="stVerticalBlockBorderWrapper"]:hover>div{{
    border-color:{C["hoja"]}!important;
    box-shadow:0 2px 12px rgba(16,79,58,.1)!important;
}}

/* ── Tablas ───────────────────────────────── */
[data-testid="stDataFrame"]{{border:1px solid {C["borde"]}!important;border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(16,79,58,.06);}}
[data-testid="stDataFrame"] thead th{{
    background:{C["card2"]}!important;color:{C["sec"]}!important;
    font-size:.7rem!important;text-transform:uppercase;letter-spacing:1px;
    border-bottom:1px solid {C["borde"]}!important;
}}
[data-testid="stDataFrame"] td{{color:{C["txt"]}!important;font-size:.84rem!important;}}
[data-testid="stDataFrame"] tr:hover td{{background:{C["card2"]}!important;}}

/* ── Tabs ─────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"]{{background:{C["card2"]};border-radius:10px;padding:4px;border:1px solid {C["borde"]};}}
[data-testid="stTabs"] [data-baseweb="tab"]{{border-radius:7px!important;color:{C["sec"]}!important;font-weight:600!important;font-size:.85rem!important;}}
[data-testid="stTabs"] [aria-selected="true"]{{background:{C["bosque"]}!important;color:{C["arena"]}!important;}}

/* ── Progress bar ─────────────────────────── */
[data-testid="stProgress"]>div>div{{
    background:linear-gradient(90deg,{C["hoja"]},{C["lima"]})!important;
    border-radius:4px!important;
}}

/* ── Inputs / Select ──────────────────────── */
[data-testid="stSelectbox"]>div,[data-testid="stDateInput"]>div{{
    background:{C["card"]}!important;border:1px solid {C["borde"]}!important;border-radius:8px!important;
}}
hr{{border-color:{C["borde"]}!important;margin:12px 0!important;}}

/* ── Header ───────────────────────────────── */
.eh-wrap{{display:flex;align-items:center;gap:16px;padding:6px 0 4px;margin-bottom:2px;}}
.eh-icon{{
    background:{C["bosque"]};
    border-radius:14px;padding:10px 12px;
    box-shadow:0 2px 12px rgba(16,79,58,.25);display:flex;align-items:center;
}}
.eh-title{{
    font-size:2rem;font-weight:900;letter-spacing:-1px;margin:0;
    background:linear-gradient(135deg,{C["bosque"]},{C["hoja"]});
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    background-clip:text;line-height:1.1;
}}
.eh-sub{{font-size:.68rem;color:{C["sec"]};letter-spacing:3px;text-transform:uppercase;margin-top:3px;}}

/* ── Sidebar brand ────────────────────────── */
.sb-brand{{display:flex;align-items:center;gap:10px;padding:2px 0 8px;}}
.sb-logo{{
    background:{C["bosque"]};border-radius:10px;
    padding:7px 9px;box-shadow:0 2px 8px rgba(16,79,58,.2);
}}
.sb-title{{font-size:1.05rem;font-weight:800;color:{C["bosque"]};}}
.sb-sub{{font-size:.58rem;color:{C["sec"]};letter-spacing:2px;text-transform:uppercase;}}

/* ── Live dot ─────────────────────────────── */
@keyframes gp{{0%,100%{{transform:scale(1);opacity:1;}}50%{{transform:scale(1.3);opacity:.7;}}}}
.live-dot{{width:9px;height:9px;background:{C["lima"]};border-radius:50%;
    display:inline-block;animation:gp 2s infinite;vertical-align:middle;margin-right:6px;
    box-shadow:0 0 6px {C["lima"]};}}

/* ── Fila diferencial ─────────────────────── */
.drow{{display:flex;align-items:center;gap:10px;padding:9px 13px;
    background:{C["card"]};border:1px solid {C["borde"]};border-radius:9px;
    margin:3px 0;transition:all .15s;}}
.drow:hover{{border-color:{C["hoja"]};background:{C["card2"]};
    box-shadow:0 2px 8px rgba(16,79,58,.08);}}
.ddot{{width:10px;height:10px;border-radius:50%;flex-shrink:0;}}
.did{{font-weight:700;font-size:.82rem;color:{C["txt"]};min-width:90px;}}
.dval{{font-size:.78rem;color:{C["sec"]};flex:1;}}
.dkw{{font-size:.9rem;font-weight:800;min-width:60px;text-align:right;}}

/* ── Alertas ──────────────────────────────── */
.ab{{background:#FFF3E0;border-left:3px solid {C["anom"]};
    border-radius:0 8px 8px 0;padding:9px 13px;margin:5px 0;
    font-size:.8rem;color:{C["anom"]};line-height:1.5;}}
.ab-p{{background:#FFFDE7;border-color:{C["precio"]};color:{C["precio"]};}}
.ab-ok{{background:#F1F8E9;border-color:{C["ok"]};color:{C["ok"]};}}

/* ── Sección ──────────────────────────────── */
.st{{font-size:.68rem;font-weight:700;color:{C["sec"]};text-transform:uppercase;
    letter-spacing:2.5px;margin:18px 0 8px;display:flex;align-items:center;gap:8px;}}
.st::after{{content:'';flex:1;height:1px;background:{C["borde"]};}}

/* ── Chip ─────────────────────────────────── */
.chip{{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;
    border-radius:20px;font-size:.72rem;font-weight:700;}}

/* ── Barra de acción ──────────────────────── */
.action-bar{{
    display:flex;align-items:center;gap:10px;
    background:{C["card"]};border:1px solid {C["borde"]};
    border-radius:12px;padding:10px 16px;margin:8px 0 12px 0;
    flex-wrap:wrap;box-shadow:0 1px 4px rgba(16,79,58,.06);
}}
.action-label{{
    font-size:.68rem;font-weight:700;color:{C["sec"]};
    text-transform:uppercase;letter-spacing:2px;margin-right:4px;
}}

/* ── Scrollbar ────────────────────────────── */
::-webkit-scrollbar{{width:5px;height:5px;}}
::-webkit-scrollbar-track{{background:{C["card2"]};}}
::-webkit-scrollbar-thumb{{background:{C["hoja"]};border-radius:4px;}}
::-webkit-scrollbar-thumb:hover{{background:{C["bosque"]};}}

footer,#MainMenu,[data-testid="stToolbar"]{{display:none!important;}}
</style>
""", unsafe_allow_html=True)

# ── Assets ────────────────────────────────────────────────────────────────────
_B = '<svg width="{s}" height="{s}" viewBox="0 0 28 28"><polygon points="16,1 5,16 14,16 12,27 23,12 14,12" fill="{c}"/></svg>'
LOGO    = _B.format(s=26, c=C["lima"])
LOGO_SM = _B.format(s=18, c=C["lima"])

def hdr(t, s=""):
    st.markdown(
        f'<div class="eh-wrap"><div class="eh-icon">{LOGO}</div>'
        f'<div><div class="eh-title">{t}</div>'
        f'{"<div class=eh-sub>"+s+"</div>" if s else ""}</div></div>',
        unsafe_allow_html=True)

def sec(t):
    st.markdown(f'<div class="st">{t}</div>', unsafe_allow_html=True)

def chip(status, sz=".72rem"):
    c = SC.get(status, C["apagado"]); i = SI.get(status,"")
    return (f'<span class="chip" style="background:{c}22;color:{c};'
            f'border:1px solid {c}44;font-size:{sz};">{i} {status}</span>')

def alert_box(texto, tipo="warning"):
    cls = "ab-p" if tipo=="precio" else ("ab-ok" if tipo=="ok" else "ab")
    st.markdown(f'<div class="ab {cls}">⚠️ {texto}</div>', unsafe_allow_html=True)

def plo(fig, h=300):
    fig.update_layout(
        height=h, margin=dict(l=0,r=0,t=10,b=0),
        plot_bgcolor=C["card"], paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C["txt"], family="Inter"),
        xaxis=dict(showgrid=False, color=C["sec"], linecolor=C["borde"]),
        yaxis=dict(gridcolor=C["borde"], color=C["sec"], zerolinecolor=C["borde"]),
        legend=dict(font=dict(size=9, color=C["txt"]), bgcolor=C["card"],
                    bordercolor=C["borde"], borderwidth=1))
    return fig

def gauge_kw(valor, maximo, status, h=150):
    color = SC.get(status, C["bosque"])
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(valor, 2),
        number=dict(suffix=" kW", font=dict(size=18, color=color, family="Inter")),
        gauge=dict(
            axis=dict(range=[0, maximo], tickfont=dict(size=8, color=C["sec"]),
                      tickcolor=C["sec"]),
            bar=dict(color=color, thickness=.35),
            bgcolor=C["card2"], borderwidth=1, bordercolor=C["borde"],
            steps=[
                dict(range=[0, maximo*.5],  color="#E8F5E9"),   # verde muy suave
                dict(range=[maximo*.5, maximo*.8], color="#FFF8E1"),   # ámbar muy suave
                dict(range=[maximo*.8, maximo], color="#FFEBEE"),   # rojo muy suave
            ],
            threshold=dict(line=dict(color=C["panico"], width=2), value=maximo*.85)
        )
    ))
    fig.update_layout(height=h, margin=dict(l=8,r=8,t=8,b=0),
                      paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=C["txt"], family="Inter"))
    return fig

# ── CRUD ──────────────────────────────────────────────────────────────────────
def _load():
    os.makedirs(os.path.dirname(CFG_PATH), exist_ok=True)
    if not os.path.exists(CFG_PATH):
        try:
            d = [{"id":e["id_edificio"],
                  "nombre":e["id_edificio"].replace("_"," ").title(),
                  "descripcion":"","superficie_m2":1000,
                  "ubicacion":"Campus principal","activo":True}
                 for e in engine.get_data().get("edificios",[])]
        except Exception:
            d = []
        _save(d); return d
    with open(CFG_PATH, encoding="utf-8") as f:
        return json.load(f)

def _save(d):
    os.makedirs(os.path.dirname(CFG_PATH), exist_ok=True)
    with open(CFG_PATH,"w",encoding="utf-8") as f:
        json.dump(d,f,ensure_ascii=False,indent=2)

# ── Watchdog & refresco ───────────────────────────────────────────────────────
if "wd_ok" not in st.session_state:
    heartbeat.iniciar(intervalo_seg=REFRESH)
    st.session_state.wd_ok = True

wd = heartbeat.estado()
cur_lat = wd.get("num_latidos", 0)
if st.session_state.get("_lat", 0) != cur_lat:
    st.session_state._lat = cur_lat; st.rerun()

if "last_ref" not in st.session_state:
    st.session_state.last_ref = time.time()
elapsed = time.time() - st.session_state.last_ref
if elapsed >= REFRESH:
    st.session_state.last_ref = time.time(); st.rerun()

snap     = engine.get_data()
cfg_list = _load()
cfg_map  = {e["id"]: e for e in cfg_list}
act_list = [e for e in cfg_list if e["activo"]]

from generar_dev import NUM_FASES_EDIFICIO, CONSUMO_MAX_KW
MAX_EDIF = NUM_FASES_EDIFICIO * CONSUMO_MAX_KW

# ════════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        f'<div class="sb-brand"><div class="sb-logo">{LOGO_SM}</div>'
        f'<div><div class="sb-title">Smart Energy Control</div>'
        f'<div class="sb-sub">Viewnext · 2026</div></div></div>',
        unsafe_allow_html=True)
    st.divider()

    page = st.radio(
        "Navegación",
        ["🏠  Dashboard","🏢  Edificio","📊  Análisis","⚙️  Gestión"],
    )

    if page == "🏢  Edificio":
        nombres = {e["id"]:e["nombre"] for e in act_list}
        if nombres:
            sel     = st.selectbox("Edificio", list(nombres.values()))
            eid_sel = next(k for k,v in nombres.items() if v==sel)
        else:
            st.caption("Sin edificios activos."); eid_sel = None
    else:
        eid_sel = None

    st.divider()
    periodo = snap.get("periodo_tarifario","—")
    precio  = snap.get("precio_kwh", 0)
    col_p   = PC.get(periodo, C["lima"])
    st.markdown(
        f'<div style="background:{C["card"]};border:1px solid {C["borde"]};'
        f'border-radius:8px;padding:8px 12px;">'
        f'<div style="font-size:.62rem;color:{C["sec"]};text-transform:uppercase;'
        f'letter-spacing:2px;margin-bottom:4px;">Mercado</div>'
        f'<div style="display:flex;align-items:baseline;gap:8px;">'
        f'<span class="chip" style="background:{col_p}22;color:{col_p};'
        f'border:1px solid {col_p}44;">{periodo}</span>'
        f'<b style="color:{C["lima"]};font-size:1.05rem;">{precio:.4f} €/kWh</b>'
        f'</div></div>', unsafe_allow_html=True)

    st.divider()
    ultimo = (wd.get("ultimo_latido") or "")[:19]
    st.markdown(
        f'<div style="background:{C["card"]};border:1px solid {C["borde"]};'
        f'border-radius:8px;padding:8px 12px;">'
        f'<div style="font-size:.62rem;color:{C["sec"]};text-transform:uppercase;'
        f'letter-spacing:2px;margin-bottom:4px;">Sistema</div>'
        f'<div style="font-size:.77rem;color:{C["sec"]};line-height:2.1;">'
        f'<span class="live-dot"></span><b style="color:{C["lima"]};">EN VIVO</b><br>'
        f'🕐 {ultimo or "—"}<br>'
        f'↺ <b style="color:{C["lima"]};">{max(0,int(REFRESH-elapsed))}s</b>'
        f' · #{cur_lat} latidos</div></div>', unsafe_allow_html=True)

    if snap.get("alerta_activa"):
        st.divider()
        st.markdown(
            f'<div style="background:rgba(239,83,80,.12);border:1px solid {C["panico"]}55;'
            f'border-radius:8px;padding:9px 12px;font-size:.8rem;color:#EF9A9A;">'
            f'⚠️ <b>{snap["num_alertas"]} alerta(s) activa(s)</b></div>',
            unsafe_allow_html=True)

    # Acceso rápido en sidebar
    st.divider()
    st.markdown(
        f'<div style="font-size:.62rem;color:{C["sec"]};text-transform:uppercase;'
        f'letter-spacing:2px;margin-bottom:6px;">Acciones rápidas</div>',
        unsafe_allow_html=True)
    if st.button("⚡ Pánico Global", use_container_width=True, type="secondary"):
        st.session_state.panico_global_confirm = True
    if st.button("🔄 Actualizar ahora", use_container_width=True):
        st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# 🏠 DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════
if page == "🏠  Dashboard":

    hdr("Smart Energy Control",
        f"Panel de control energético · {snap.get('timestamp','')[:19]}")

    # ── Barra de acciones (todos los requisitos funcionales) ──────────────────
    st.markdown('<div class="action-bar">'
                f'<span class="action-label">Acciones</span></div>',
                unsafe_allow_html=True)

    ab1,ab2,ab3,ab4,ab5,ab6 = st.columns(6)

    with ab1:
        if st.button("🔄 Actualizar", type="primary", use_container_width=True,
                     help="Forzar refresco de todos los datos"):
            st.rerun()

    with ab2:
        if st.button("🔍 Detectar Anomalías", type="secondary", use_container_width=True,
                     help="Requisito: Detector de anomalías"):
            with st.spinner("Analizando…"):
                anomalias = engine.detectar_anomalias()
            st.session_state.anomalias = anomalias
            st.session_state.show_anomalias = True

    with ab3:
        if st.button("📋 Auditar CSV", type="secondary", use_container_width=True,
                     help="Requisito libre 1: Auditoría con pandas"):
            with st.spinner("Procesando CSV histórico…"):
                st.session_state.audit = generar_auditoria()
            st.session_state.show_audit = True

    with ab4:
        if st.button("🔮 Predecir", type="secondary", use_container_width=True,
                     help="Requisito libre 2: Modelo de regresión lineal"):
            with st.spinner("Entrenando modelo…"):
                st.session_state.pred_quick = predecir_consumo(n_predicciones=4)
            st.session_state.show_pred = True

    with ab5:
        if st.button("⚡ Pánico Global", type="secondary", use_container_width=True,
                     help="Requisito: Botón de pánico energético"):
            st.session_state.panico_global_confirm = True

    with ab6:
        all_panic = all(e.get("status")=="PANICO" for e in snap.get("edificios",[]))
        if all_panic:
            if st.button("🟢 Restaurar Todo", type="primary", use_container_width=True):
                engine.desactivar_panico(); st.rerun()
        else:
            st.button("🟢 Restaurar Todo", type="secondary", use_container_width=True,
                      disabled=True)

    # ── Confirmación pánico global ────────────────────────────────────────────
    if st.session_state.get("panico_global_confirm"):
        with st.container(border=True):
            st.markdown(
                f'<p style="color:{C["panico"]};font-weight:700;font-size:.95rem;margin:0;">'
                f'⚠️ Vas a activar el pánico energético en TODOS los edificios</p>',
                unsafe_allow_html=True)
            pc1,pc2,_ = st.columns([1,1,3])
            if pc1.button("✅ Confirmar pánico", type="primary", key="pg_ok"):
                engine.panico_energetico()
                st.session_state.panico_global_confirm = False
                st.rerun()
            if pc2.button("❌ Cancelar", key="pg_no"):
                st.session_state.panico_global_confirm = False
                st.rerun()

    # ── Resultados inline de anomalías ────────────────────────────────────────
    if st.session_state.get("show_anomalias"):
        anomalias = st.session_state.get("anomalias", {})
        diffs_a   = anomalias.get("dispositivos",[]) if isinstance(anomalias,dict) else anomalias
        edifs_a   = anomalias.get("edificios",[])    if isinstance(anomalias,dict) else []
        with st.container(border=True):
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<b style="color:{C["lima"]}">🔍 Resultado: Detector de Anomalías</b>'
                f'</div>', unsafe_allow_html=True)
            if not diffs_a and not edifs_a:
                st.markdown('<div class="ab ab-ok">✅ Sin anomalías detectadas en este momento.</div>',
                            unsafe_allow_html=True)
            else:
                for d in diffs_a:
                    alert_box(f"{d.get('ID_DIFERENCIAL',d.get('id_diferencial',''))} — "
                              f"{d.get('STATUS',d.get('status',''))} — "
                              f"{d.get('CONSUMO_TOTAL',d.get('consumo_diferencial_kw',0))} kW")
                for e in edifs_a:
                    alert_box(f"Edificio {e.get('ID_EDIFICIO',e.get('id_edificio',''))} — "
                              f"{e.get('STATUS',e.get('status',''))}")
            if st.button("✖ Cerrar", key="close_anom"):
                st.session_state.show_anomalias = False; st.rerun()

    # ── Auditoría rápida inline ───────────────────────────────────────────────
    if st.session_state.get("show_audit"):
        audit = st.session_state.get("audit",{})
        with st.container(border=True):
            st.markdown(f'<b style="color:{C["lima"]}">📋 Auditoría del día</b>',
                        unsafe_allow_html=True)
            if "error" in audit:
                st.warning(audit["error"])
            else:
                g = audit["global"]
                ac1,ac2,ac3,ac4 = st.columns(4)
                ac1.metric("Consumo medio",   f"{g['consumo_medio_kw']:.2f} kW")
                ac2.metric("Coste acumulado", f"{g['coste_acumulado_eur']:.2f} €")
                ac3.metric("Precio medio",    f"{g['precio_medio_kwh']:.4f} €/kWh")
                ac4.metric("Lecturas",        g['num_lecturas'])
                if os.path.exists(audit.get("grafico","")):
                    st.image(audit["grafico"], use_container_width=True)
            if st.button("✖ Cerrar", key="close_audit"):
                st.session_state.show_audit = False; st.rerun()

    # ── Predicción rápida inline ──────────────────────────────────────────────
    if st.session_state.get("show_pred"):
        pred = st.session_state.get("pred_quick",{})
        with st.container(border=True):
            st.markdown(f'<b style="color:{C["lima"]}">🔮 Predicción — próximos 60 min</b>',
                        unsafe_allow_html=True)
            if "error" in pred:
                st.info(pred["error"])
            else:
                if os.path.exists(pred.get("grafico","")):
                    st.image(pred["grafico"], use_container_width=True)
                st.caption(f"Modelo: {pred.get('modelo','')} · "
                           f"R² medio: {round(sum(d['r2_train'] for d in pred.get('diferenciales',[]))/max(len(pred.get('diferenciales',[])),1),3)}")
            if st.button("✖ Cerrar", key="close_pred"):
                st.session_state.show_pred = False; st.rerun()

    # ── Alertas activas ───────────────────────────────────────────────────────
    for a in snap.get("alertas",[]):
        tipo = "precio" if a.get("tipo")=="PRECIO_ALTO" else "warning"
        alert_box(a["texto"], tipo)

    st.divider()

    # ── KPIs globales ─────────────────────────────────────────────────────────
    edifs       = snap.get("edificios",[])
    tot_kw      = sum(e["consumo_total_kw"] for e in edifs)
    tot_eur_h   = sum(e["coste_hora_eur"]   for e in edifs)
    diffs_act   = sum(e["num_activos"]       for e in edifs)
    diffs_tot   = sum(e["num_diferenciales"] for e in edifs)
    num_alertas = snap.get("num_alertas",0)

    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Edificios",          len(edifs))
    k2.metric("Consumo total",      f"{tot_kw:.2f} kW")
    k3.metric("Coste / hora",       f"{tot_eur_h:.3f} €")
    k4.metric("Coste est. / día",   f"{tot_eur_h*24:.2f} €")
    k5.metric("Diferenciales",      f"{diffs_act}/{diffs_tot}",
              delta=f"⚠️ {num_alertas}" if num_alertas else "0 alertas",
              delta_color="inverse" if num_alertas else "off")

    st.divider()
    c_pred, c_rank = st.columns([3,2])

    # ── Predicción ────────────────────────────────────────────────────────────
    with c_pred:
        sec("🔮 Predicción en tiempo real — próximos 60 min")
        pred_live = predecir_consumo(n_predicciones=4)
        if "error" not in pred_live:
            palette = [C["lima"],C["hoja"],"#42A5F5",C["cortado"],"#CE93D8","#80CBC4"]
            fig = go.Figure()
            for i,d in enumerate(pred_live["diferenciales"][:6]):
                col = palette[i % len(palette)]
                did = d["id_diferencial"]
                fig.add_trace(go.Scatter(
                    x=[snap["timestamp"][:19]], y=[d["ultimo_consumo_real_kw"]],
                    mode="markers", marker=dict(size=10,color=col,
                        line=dict(color=C["bg"],width=1.5)),
                    legendgroup=did, showlegend=False))
                fig.add_trace(go.Scatter(
                    x=[p["timestamp_est"][:19] for p in d["predicciones"]],
                    y=[p["consumo_estimado_kw"]  for p in d["predicciones"]],
                    mode="lines+markers", name=did,
                    line=dict(dash="dot",width=2.5,color=col),
                    marker=dict(size=6,color=col,line=dict(color=C["bg"],width=1)),
                    legendgroup=did))
            plo(fig,290)
            fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,x=0))
            st.plotly_chart(fig, use_container_width=True)
            n = len(pred_live.get("diferenciales",[]))
            r2 = round(sum(d["r2_train"] for d in pred_live["diferenciales"])/max(n,1),3) if n else 0
            st.caption(f"LinearRegression (degree=2) · R² medio: {r2} · "
                       f"{pred_live['n_puntos_entrenamiento']} lecturas")
        else:
            st.info(pred_live.get("error","Sin datos suficientes aún (necesita ≥3 lecturas)."))

    # ── Ranking de eficiencia ─────────────────────────────────────────────────
    with c_rank:
        sec("🏆 Ranking de eficiencia — comparativa")
        ranking = snap.get("ranking_eficiencia",[])
        if ranking:
            df_r = pd.DataFrame(ranking)
            df_r["nombre"] = df_r["id_edificio"].map(
                lambda x: cfg_map.get(x,{}).get("nombre",x))
            fig_r = px.bar(df_r, x="consumo_total_kw", y="nombre", orientation="h",
                           color="status", color_discrete_map=SC,
                           text=df_r["consumo_total_kw"].apply(lambda v:f"{v:.1f} kW"),
                           labels={"consumo_total_kw":"kW","nombre":""})
            plo(fig_r,220)
            fig_r.update_layout(showlegend=False, yaxis=dict(showgrid=False))
            fig_r.update_traces(textposition="outside",
                                textfont=dict(color=C["txt"],size=11))
            st.plotly_chart(fig_r, use_container_width=True)
            for r in ranking:
                nombre = cfg_map.get(r["id_edificio"],{}).get("nombre",r["id_edificio"])
                d      = r["vs_media_pct"]
                ahorro = r["ahorro_vs_peor_eur_dia"]
                dc = C["panico"] if d>15 else (C["ok"] if d<-5 else C["sec"])
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0;'
                    f'border-bottom:1px solid {C["borde"]};font-size:.83rem;">'
                    f'<b style="color:{C["lima"]};min-width:22px">#{r["posicion"]}</b>'
                    f'<span>{SI.get(r["status"],"")} {nombre}</span>'
                    f'<span style="margin-left:auto;color:{dc};font-weight:700;">'
                    f'{"+" if d>0 else ""}{d:.1f}%</span>'
                    f'{"<span style=color:"+C["hoja"]+";font-size:.72rem;margin-left:5px;>💰 "+str(ahorro)+"€/d</span>" if ahorro>0 else ""}'
                    f'</div>', unsafe_allow_html=True)

    st.divider()
    sec("🏢 Edificios — consumo y control")

    cols = st.columns(max(len(edifs),1))
    for i,e in enumerate(edifs):
        cfg    = cfg_map.get(e["id_edificio"],{})
        nombre = cfg.get("nombre",e["id_edificio"])
        status = e["status"]
        color  = SC.get(status, C["lima"])
        m2     = cfg.get("superficie_m2",0)
        en_pan = status == "PANICO"

        with cols[i]:
            with st.container(border=True):
                # Header tarjeta
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;'
                    f'align-items:center;margin-bottom:4px;">'
                    f'<b style="color:{C["arena"]};font-size:.95rem;">{nombre}</b>'
                    f'<span class="chip" style="background:{color}22;color:{color};'
                    f'border:1px solid {color}44;">{SI.get(status,"")} {status}</span>'
                    f'</div>', unsafe_allow_html=True)
                if cfg.get("ubicacion"):
                    st.caption(f"📍 {cfg['ubicacion']}")

                # Gauge
                st.plotly_chart(
                    gauge_kw(e["consumo_total_kw"], MAX_EDIF, status),
                    use_container_width=True, key=f"g_{e['id_edificio']}")

                ca,cb = st.columns(2)
                ca.metric("€/hora", f"{e['coste_hora_eur']:.3f}")
                cb.metric("Activos", f"{e['num_activos']}/{e['num_diferenciales']}")
                st.progress(min(e["factor_carga_pct"]/100,1.0),
                            text=f"Carga: {e['factor_carga_pct']:.1f}%")
                if m2 and e["consumo_total_kw"]:
                    wm2 = round(e["consumo_total_kw"]/m2*1000,1)
                    wc  = C["panico"] if wm2>15 else (C["lima"] if wm2<8 else C["sec"])
                    st.markdown(
                        f'<p style="font-size:.78rem;color:{C["sec"]};margin:3px 0;">'
                        f'📐 <b style="color:{wc}">{wm2} W/m²</b></p>',
                        unsafe_allow_html=True)

                # Botón pánico / restaurar por edificio
                if en_pan:
                    if st.button(f"🟢 Restaurar {nombre}",
                                 key=f"rest_{e['id_edificio']}",
                                 type="primary", use_container_width=True):
                        engine.desactivar_panico(e["id_edificio"]); st.rerun()
                else:
                    if st.button(f"🔴 Pánico — {nombre}",
                                 key=f"pan_{e['id_edificio']}",
                                 type="secondary", use_container_width=True,
                                 help="Cortar suministro no crítico de este edificio"):
                        engine.panico_energetico(e["id_edificio"]); st.rerun()

                for a in e.get("alertas_edificio",[]):
                    st.markdown(f'<div class="ab">{a["texto"]}</div>',
                                unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# 🏢 DETALLE EDIFICIO
# ════════════════════════════════════════════════════════════════════════════════
elif page == "🏢  Edificio":

    if not eid_sel:
        st.info("Selecciona un edificio en el menú lateral."); st.stop()

    datos  = engine.get_data(eid_sel)
    cfg    = cfg_map.get(eid_sel,{})
    if "error" in datos: st.error(datos["error"]); st.stop()

    e_info    = datos["edificios"][0] if datos["edificios"] else {}
    nombre    = cfg.get("nombre", eid_sel)
    status_ed = e_info.get("status","OK")
    diffs     = datos.get("diferenciales",[])
    en_panico = all(d["status"]=="PANICO" for d in diffs) if diffs else False

    hl,hr = st.columns([5,1])
    with hl:
        hdr(nombre, " · ".join(filter(None,[cfg.get("descripcion"),cfg.get("ubicacion")])))
        st.markdown(chip(status_ed,".8rem"), unsafe_allow_html=True)
    with hr:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if en_panico:
            if st.button("🟢 Restaurar", type="primary", use_container_width=True):
                engine.desactivar_panico(eid_sel); st.rerun()
        else:
            if st.button("🔴 Pánico", type="secondary", use_container_width=True):
                engine.panico_energetico(eid_sel); st.rerun()

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Consumo total",         f"{e_info.get('consumo_total_kw',0):.3f} kW")
    k2.metric("Coste / hora",          f"{e_info.get('coste_hora_eur',0):.4f} €")
    k3.metric("Factor de carga",       f"{e_info.get('factor_carga_pct',0):.1f} %")
    k4.metric("Diferenciales activos", f"{e_info.get('num_activos',0)}/{e_info.get('num_diferenciales',0)}")

    m2  = cfg.get("superficie_m2",0)
    ckw = e_info.get("consumo_total_kw",0)
    if m2 and ckw:
        wm2 = round(ckw/m2*1000,2)
        wc  = C["panico"] if wm2>15 else (C["lima"] if wm2<8 else C["sec"])
        st.markdown(
            f'<div style="background:{C["card"]};border:1px solid {C["borde"]};'
            f'border-radius:8px;padding:7px 14px;display:inline-block;font-size:.82rem;margin:4px 0;">'
            f'📐 Eficiencia: <b style="color:{wc}">{wm2} W/m²</b>'
            f' · {m2} m²</div>', unsafe_allow_html=True)

    for a in datos.get("alertas",[]):
        tp = "precio" if a.get("tipo")=="PRECIO_ALTO" else "warning"
        alert_box(a["texto"], tp)

    st.divider()
    cl,cr = st.columns([5,3])

    with cl:
        sec("🔌 Control de diferenciales")
        st.markdown(
            f'<div style="display:flex;gap:10px;padding:3px 13px;font-size:.63rem;'
            f'color:{C["sec"]};text-transform:uppercase;letter-spacing:1px;font-weight:600;">'
            f'<span style="width:10px;flex-shrink:0;"></span>'
            f'<span style="min-width:90px;">ID / Estado</span>'
            f'<span style="flex:1;">A · V · FP</span>'
            f'<span style="min-width:60px;text-align:right;">kW</span>'
            f'<span style="min-width:65px;text-align:right;">€/h</span>'
            f'<span style="width:70px;"></span></div>', unsafe_allow_html=True)

        for d in diffs:
            status  = d["status"]
            color   = SC.get(status, C["apagado"])
            cortado = d.get("cortado_manualmente", False)
            gstyle  = f"box-shadow:0 0 10px {color}33;" if status not in ("OK","APAGADO") else ""
            row_c, btn_c = st.columns([6,1])

            with row_c:
                st.markdown(
                    f'<div class="drow" style="{gstyle}">'
                    f'<div class="ddot" style="background:{color};box-shadow:0 0 6px {color}88;"></div>'
                    f'<div class="did">{d["id_diferencial"]}<br>'
                    f'<span style="font-size:.66rem;color:{color};font-weight:600;">'
                    f'{d["id_fase"]} · {SI.get(status,"")} {status}</span></div>'
                    f'<div class="dval">'
                    f'{d["corriente_a"]:.1f}A · {d["tension_v"]:.0f}V · FP {d["factor_potencia"]:.2f}'
                    f'</div>'
                    f'<div class="dkw" style="color:{color};text-shadow:0 0 8px {color}55;">'
                    f'{d["consumo_diferencial_kw"]:.2f}</div>'
                    f'<div style="min-width:65px;text-align:right;font-size:.78rem;color:{C["sec"]};">'
                    f'{d["coste_hora_eur"]:.4f} €</div>'
                    f'</div>', unsafe_allow_html=True)

            with btn_c:
                if status == "PANICO":
                    st.button("🔒", key=f"t_{d['id_diferencial']}", disabled=True,
                              use_container_width=True)
                elif cortado:
                    if st.button("🟢", key=f"t_{d['id_diferencial']}",
                                 type="primary", use_container_width=True,
                                 help="Reactivar"):
                        engine.toggle_diferencial(eid_sel, d["id_diferencial"]); st.rerun()
                else:
                    if st.button("✂️", key=f"t_{d['id_diferencial']}",
                                 type="secondary", use_container_width=True,
                                 help="Cortar"):
                        engine.toggle_diferencial(eid_sel, d["id_diferencial"]); st.rerun()

            if d.get("texto_alerta"):
                st.markdown(f'<div class="ab">{d["texto_alerta"]}</div>',
                            unsafe_allow_html=True)

    with cr:
        sec("📊 Consumo por diferencial")
        if diffs:
            df_c = pd.DataFrame(diffs)
            fig  = px.bar(df_c, x="id_diferencial", y="consumo_diferencial_kw",
                          color="status", color_discrete_map=SC,
                          text=df_c["consumo_diferencial_kw"].apply(lambda v:f"{v:.2f}"),
                          labels={"consumo_diferencial_kw":"kW","id_diferencial":""})
            plo(fig,300)
            fig.update_layout(showlegend=False, xaxis=dict(tickangle=-30))
            fig.update_traces(textposition="outside",
                              textfont=dict(color=C["txt"],size=10))
            st.plotly_chart(fig, use_container_width=True)

        sec("📋 Resumen")
        num_c = sum(1 for d in diffs if d.get("cortado_manualmente"))
        for label,val,color in [
            ("Total diferenciales", len(diffs),  C["txt"]),
            ("Activos",             sum(1 for d in diffs if d["activo"]), C["ok"]),
            ("Cortados (manual)",   num_c,        C["cortado"]),
            ("Apagados (hardware)", sum(1 for d in diffs if d["status"]=="APAGADO"), C["apagado"]),
        ]:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
                f'border-bottom:1px solid {C["borde"]};font-size:.83rem;">'
                f'<span style="color:{C["sec"]}">{label}</span>'
                f'<b style="color:{color}">{val}</b></div>',
                unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# 📊 ANÁLISIS
# ════════════════════════════════════════════════════════════════════════════════
elif page == "📊  Análisis":

    hdr("Análisis energético",
        "Requisito libre 1: Auditoría CSV (pandas) · Requisito libre 2: Regresión lineal")

    tab_a, tab_p = st.tabs(["📋  Auditoría del día", "🔮  Modelo de predicción"])

    with tab_a:
        cc,_ = st.columns([2,4])
        with cc:
            fecha_sel = st.date_input("Fecha", value=date.today())
            if st.button("🔍 Generar auditoría", type="primary", use_container_width=True,
                         help="Analiza el CSV de snapshots con pandas y matplotlib"):
                with st.spinner("Analizando CSV con pandas…"):
                    st.session_state.audit_full = generar_auditoria(str(fecha_sel))

        aud = st.session_state.get("audit_full")
        if not aud:
            st.markdown(
                f'<div style="text-align:center;padding:60px;color:{C["sec"]};">'
                f'<div style="font-size:3rem">📋</div>'
                f'<div style="margin-top:12px;">Selecciona fecha y pulsa '
                f'<b style="color:{C["lima"]}">Generar auditoría</b></div></div>',
                unsafe_allow_html=True)
        elif "error" in aud:
            st.warning(aud["error"])
        else:
            g = aud["global"]
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("Consumo medio",   f"{g['consumo_medio_kw']:.3f} kW")
            c2.metric("Consumo máximo",  f"{g['consumo_max_kw']:.3f} kW")
            c3.metric("Desv. típica",    f"{g['desviacion_tipica_kw']:.3f} kW")
            c4.metric("Coste acumulado", f"{g['coste_acumulado_eur']:.2f} €")
            c5.metric("Precio medio",    f"{g['precio_medio_kwh']:.4f} €/kWh")
            st.divider()
            ci,cd = st.columns([3,2])
            with ci:
                sec("📈 Evolución de consumo por edificio")
                st.image(aud["grafico"], use_container_width=True)
            with cd:
                sec("⏱ Por periodo tarifario")
                for pt, dp in aud.get("distribucion_periodos_tarifarios",{}).items():
                    col = PC.get(pt, C["lima"])
                    with st.container(border=True):
                        st.markdown(
                            f'<span class="chip" style="background:{col}22;color:{col};'
                            f'border:1px solid {col}44;">{pt}</span>',
                            unsafe_allow_html=True)
                        p1,p2 = st.columns(2)
                        p1.metric("Consumo medio", f"{dp['consumo_medio_kw']:.2f} kW")
                        p2.metric("Coste acum.",   f"{dp['coste_acumulado_eur']:.2f} €")
                st.divider()
                pk = aud.get("pico_consumo",{}); vl = aud.get("valle_consumo",{})
                st.success(f"📈 Pico: `{pk.get('timestamp','')[:19]}` · {pk.get('consumo_kw',0):.2f} kW")
                st.info(   f"📉 Valle: `{vl.get('timestamp','')[:19]}` · {vl.get('consumo_kw',0):.2f} kW")
            st.divider()
            sec("Detalle por diferencial")
            df_d = pd.DataFrame(aud.get("diferenciales",[]))
            if not df_d.empty:
                ok_c = [c for c in ["id_edificio","id_diferencial","consumo_medio_kw",
                                    "corriente_media_a","fp_medio","coste_acumulado_eur",
                                    "pct_tiempo_activo","status_predominante"] if c in df_d.columns]
                st.dataframe(df_d[ok_c], use_container_width=True, hide_index=True)

    with tab_p:
        cc2,_ = st.columns([2,4])
        with cc2:
            n_steps = st.slider("Pasos a predecir (×15 min)", 1, 8, 4)
            if st.button("▶ Ejecutar modelo", type="primary", use_container_width=True,
                         help="Entrena LinearRegression (PolynomialFeatures degree=2) por diferencial"):
                with st.spinner("Entrenando LinearRegression…"):
                    st.session_state.pred_full = predecir_consumo(n_predicciones=n_steps)

        pf = st.session_state.get("pred_full")
        if not pf:
            st.markdown(
                f'<div style="text-align:center;padding:60px;color:{C["sec"]};">'
                f'<div style="font-size:3rem">🔮</div>'
                f'<div style="margin-top:12px;">Configura los parámetros y pulsa '
                f'<b style="color:{C["lima"]}">Ejecutar modelo</b></div></div>',
                unsafe_allow_html=True)
        elif "error" in pf:
            st.warning(pf["error"])
        else:
            r2s   = [d["r2_train"] for d in pf["diferenciales"]]
            r2med = round(sum(r2s)/len(r2s),3) if r2s else 0
            rc    = C["ok"] if r2med >= 0.7 else (C["precio"] if r2med >= 0.3 else C["panico"])
            st.markdown(
                f'<div class="ab ab-ok">✅ Modelo entrenado · '
                f'{pf["n_puntos_entrenamiento"]} lecturas · '
                f'Horizonte: {pf["horizonte_minutos"]} min · '
                f'R² medio: <b style="color:{rc}">{r2med}</b></div>',
                unsafe_allow_html=True)
            st.image(pf["grafico"], use_container_width=True)
            sec("Predicciones detalladas por diferencial")
            for d in pf["diferenciales"]:
                r2    = d["r2_train"]
                r2c   = C["ok"] if r2>=0.7 else (C["precio"] if r2>=0.3 else C["panico"])
                with st.expander(
                        f"{d['id_edificio']} / {d['id_diferencial']} "
                        f"— R²: {r2} — último real: {d['ultimo_consumo_real_kw']} kW"):
                    df_p = pd.DataFrame(d["predicciones"])
                    df_p["timestamp_est"] = df_p["timestamp_est"].str[:19]
                    st.dataframe(df_p, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════════
# ⚙️ GESTIÓN CRUD
# ════════════════════════════════════════════════════════════════════════════════
elif page == "⚙️  Gestión":

    hdr("Gestión de edificios","Administración de la topología monitorizada")

    cl,cf = st.columns([2,3])

    with cl:
        sec("Edificios registrados")
        for i,e in enumerate(cfg_list):
            with st.container(border=True):
                ec = C["ok"] if e["activo"] else C["apagado"]
                st.markdown(
                    f'<b style="color:{C["arena"]}">{e["nombre"]}</b>'
                    f' <code style="font-size:.7rem;background:{C["card2"]};'
                    f'padding:2px 6px;border-radius:4px;color:{C["sec"]};">{e["id"]}</code><br>'
                    f'<span style="color:{ec};font-size:.73rem;font-weight:600;">'
                    f'{"✅ Activo" if e["activo"] else "❌ Inactivo"}</span>'
                    f'<span style="color:{C["sec"]};font-size:.73rem;">'
                    f' · {e.get("superficie_m2",0)} m² · {e.get("ubicacion","")}</span>',
                    unsafe_allow_html=True)
                ba,bb,bc = st.columns(3)
                if ba.button("✏️ Editar",  key=f"e{i}", use_container_width=True):
                    st.session_state.crud="editar"; st.session_state.cidx=i
                if bb.button("🗑️ Borrar",  key=f"d{i}", use_container_width=True):
                    st.session_state.crud="borrar"; st.session_state.cidx=i
                tog = "🔇 Desact." if e["activo"] else "🔔 Activar"
                if bc.button(tog, key=f"t{i}", use_container_width=True):
                    cfg_list[i]["activo"] = not cfg_list[i]["activo"]
                    _save(cfg_list); st.rerun()
        st.divider()
        if st.button("➕ Añadir edificio", type="primary", use_container_width=True):
            st.session_state.crud="crear"; st.session_state.cidx=None

    with cf:
        modo = st.session_state.get("crud")
        idx  = st.session_state.get("cidx")

        if modo in ("crear","editar"):
            nuevo = modo=="crear"
            base  = {} if nuevo else cfg_list[idx]
            sec("➕ Nuevo edificio" if nuevo else "✏️ Editar edificio")
            with st.form("f_ed", clear_on_submit=True):
                eid  = st.text_input("ID *",
                                     value=base.get("id",f"edificio_{len(cfg_list)+1:02d}"),
                                     disabled=not nuevo,
                                     help="Debe coincidir con el ID del simulador")
                nom  = st.text_input("Nombre *",    value=base.get("nombre",""))
                desc = st.text_area("Descripción",  value=base.get("descripcion",""), height=70)
                c1,c2 = st.columns(2)
                m2   = c1.number_input("Superficie (m²)", min_value=1,
                                       value=int(base.get("superficie_m2",1000)))
                ubic = c2.text_input("Ubicación",   value=base.get("ubicacion",""))
                sub  = st.form_submit_button("💾 Guardar", type="primary", use_container_width=True)
            if sub:
                if not nom.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    reg = {"id":eid.strip(),"nombre":nom.strip(),
                           "descripcion":desc.strip(),"superficie_m2":m2,
                           "ubicacion":ubic.strip(),"activo":True}
                    if nuevo: cfg_list.append(reg)
                    else:     cfg_list[idx] = reg
                    _save(cfg_list)
                    st.session_state.pop("crud",None)
                    st.success("✅ Guardado."); st.rerun()

        elif modo=="borrar" and idx is not None:
            sec("🗑️ Confirmar eliminación")
            st.warning(f"¿Eliminar **{cfg_list[idx]['nombre']}**? Esta acción es irreversible.")
            b1,b2 = st.columns(2)
            if b1.button("✅ Confirmar", type="primary", use_container_width=True):
                cfg_list.pop(idx); _save(cfg_list)
                st.session_state.pop("crud",None); st.rerun()
            if b2.button("❌ Cancelar", use_container_width=True):
                st.session_state.pop("crud",None); st.rerun()
        else:
            st.markdown(
                f'<div style="text-align:center;padding:50px 20px;color:{C["sec"]};">'
                f'<div style="font-size:2.8rem">🏢</div>'
                f'<div style="margin-top:10px;font-size:.92rem;color:{C["arena"]};line-height:1.8;">'
                f'Selecciona un edificio para editarlo<br>'
                f'o pulsa <b style="color:{C["lima"]}">➕ Añadir</b>.</div>'
                f'<div style="margin-top:18px;padding:12px;background:{C["card"]};'
                f'border:1px solid {C["borde"]};border-radius:8px;'
                f'font-size:.76rem;color:{C["sec"]};line-height:1.7;">'
                f'Los IDs deben coincidir con el simulador '
                f'(<code>edificio_01</code>, <code>edificio_02</code>…).</div></div>',
                unsafe_allow_html=True)
