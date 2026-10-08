"""Nexo Digital - interfaz (Streamlit). Ejecutar con: streamlit run app.py"""
from pathlib import Path

import pandas as pd
import html
import streamlit as st

import analisis
import core
import informe
import evidencia
import marca
import narrativa
import nexo
import preguntas

AQUI = Path(__file__).parent
LOGO_H = AQUI / "assets" / "logo_horizontal.png"
LOGO_I = AQUI / "assets" / "logo_icono.png"

try:
    st.set_page_config(page_title="Nexo Digital", page_icon=str(LOGO_I) if LOGO_I.exists() else "N", layout="wide")
except Exception:
    st.set_page_config(page_title="Nexo Digital", layout="wide")

# Paleta institucional de la Universidad de Antioquia (Manual de Identidad Institucional):
# verde 349 C #026937, 7740 C #35944B, 361 C #43B649, lima 375 C #8DC63F, turquesa 7465 C #3EBDAC, 7718 C #0E7774
V_OSC, V_MED, V_CLA, LIMA, TURQ, V_AZUL = "#026937", "#35944B", "#43B649", "#8DC63F", "#3EBDAC", "#0E7774"
TEXTO, GRIS, BORDE, FONDO = "#14281D", "#5B6B63", "#C9D8CE", "#EEF5EF"

st.markdown(f"""
<style>
.block-container {{ padding-top: 4.2rem; max-width: 1180px; }}
h1, h2, h3 {{ color: {V_OSC}; letter-spacing: -0.01em; }}
h2 {{ border-bottom: 2px solid {LIMA}; padding-bottom: .25rem; }}
[data-testid="stSidebar"] {{ background: {FONDO}; border-right: 1px solid {BORDE}; }}
[data-testid="stMetric"] {{ background: #fff; border: 1px solid {BORDE}; border-top: 3px solid {LIMA};
  border-radius: 8px; padding: 10px 14px; }}
[data-testid="stMetricLabel"] {{ color: {GRIS}; }}
[data-testid="stMetricValue"] {{ color: {V_OSC}; font-size: 1.45rem; }}
[data-testid="stForm"] {{ border: 1px solid {BORDE}; border-radius: 10px; padding: 1.1rem 1.3rem; background: #fff; }}
.nx-hero {{ background: linear-gradient(120deg, #014A27 0%, {V_OSC} 60%, {V_AZUL} 100%); color: #fff; border-radius: 12px;
  padding: 2.2rem 2.4rem; margin: .5rem 0 1.2rem; border-bottom: 5px solid {LIMA}; }}
.nx-hero h1 {{ color: #fff; font-size: 2.1rem; margin: 0 0 .4rem; }}
.nx-hero p {{ color: #E3F1E6; font-size: 1.05rem; margin: 0; max-width: 760px; }}
.nx-card {{ background: #fff; border: 1px solid {BORDE}; border-top: 4px solid {LIMA}; border-radius: 10px;
  padding: 1rem 1.2rem; min-height: 120px; }}
.nx-card b {{ color: {V_OSC}; font-size: 1.05rem; }}
.nx-card p {{ color: #3F4F46; margin: .4rem 0 0; font-size: .95rem; }}
.nx-sem {{ border-radius: 10px; padding: 1rem 1.3rem; color: #fff; margin-bottom: .8rem; }}
.nx-sem b {{ font-size: 1.3rem; }}
.nx-sem ul {{ margin: .4rem 0 0 1.1rem; padding: 0; }}
.nx-nota {{ background: #F4F8F5; border-left: 4px solid {LIMA}; padding: .6rem .9rem; border-radius: 4px; margin: .5rem 0;
  color: #2F3F36; }}
.nx-alerta {{ border-left-color: #B42318; background: #FEF3F2; }}
.nx-step {{ display: flex; gap: .8rem; background: #fff; border: 1px solid {BORDE}; border-left: 5px solid {V_OSC}; border-radius: 8px;
  padding: .7rem 1rem; margin: .4rem 0; }}
.nx-step .n {{ background: {V_OSC}; color: #fff; border-radius: 50%; min-width: 1.8rem; height: 1.8rem; display: flex; align-items: center;
  justify-content: center; font-weight: 700; }}
.nx-step b {{ color: {V_OSC}; }}
.nx-step span.p {{ color: #3F4F46; font-size: .92rem; }}
.nx-lista li {{ margin: .25rem 0; }}
.nx-pie {{ color: {GRIS}; font-size: .85rem; margin-top: 2rem; border-top: 1px solid {BORDE}; padding-top: .6rem; }}
[data-testid="stFormSubmitButton"] button, .stButton button[kind="primary"] {{ background: {V_OSC}; border-color: {V_OSC}; color: #fff;
  font-weight: 600; }}
[data-testid="stFormSubmitButton"] button:hover, .stButton button[kind="primary"]:hover {{ background: {V_MED}; border-color: {V_MED}; color: #fff; }}
[data-testid="stTooltipIcon"] svg {{ color: {V_AZUL}; }}
</style>
""", unsafe_allow_html=True)

ICONO = {"gratuito": "🟢", "freemium": "🟡", "pago": "🟠", "servicio": "🔵", "servicio público": "🟢"}
SEMAFORO = {"verde": "🟢", "amarillo": "🟡", "rojo": "🔴", "info": "⚪"}
COL_SEM = ["#12805C", "#B7791F", "#B42318"]
PELDANOS = {0: "Sin tecnología", 1: "Gratuito o ya disponible", 2: "Bajo costo", 3: "Automatización", 4: "Servicio externo"}
ETIQ_ESTADOS = {"ingresos": "Ingresos operacionales", "utilidad_operacional": "Utilidad operacional",
                "utilidad_neta": "Utilidad neta", "cuentas_por_cobrar": "Cuentas por cobrar",
                "activo_total": "Activo total", "pasivo_total": "Pasivo total",
                "activo_corriente": "Activo corriente", "pasivo_corriente": "Pasivo corriente",
                "inventarios": "Inventarios"}

# ------------------------------------------------------------------ Textos de ayuda (signo "?" al pasar el cursor)
AYUDA = dict(
    caso="Nombre con el que aparecerá la empresa en los informes. Es opcional.",
    sector="Permite comparar los indicadores con los de empresas similares. Es opcional.",
    archivo="Archivo de Excel o CSV con una fila por movimiento y las columnas: fecha, tipo (ingreso o gasto), categoria, descripcion y monto. "
            "Mientras más meses incluya (idealmente 12 o más), más confiable es el análisis. Si no dispone de archivo, puede usar los datos de demostración.",
    demo="Carga un ejemplo ficticio de 18 meses para conocer el funcionamiento de la herramienta. Se ignora si se sube un archivo propio.",
    saldo="Dinero disponible hoy en caja y bancos, en pesos. Permite calcular cuántos meses de gastos cubre la caja y en qué mes se agotaría en cada escenario.",
    estados="Opcional. Si se diligencian, se calculan razones financieras y DuPont, y se contrastan con los movimientos. Use los valores anuales del último cierre.",
    e_ingresos="Ventas u otros ingresos de la operación del último año. Estado de resultados.",
    e_utilidad_operacional="Ingresos menos costos y gastos de operación, antes de intereses e impuestos. Estado de resultados.",
    e_utilidad_neta="Resultado final después de intereses e impuestos. Estado de resultados.",
    e_cuentas_por_cobrar="Valor que los clientes adeudan y aún no han pagado. Balance general.",
    e_activo_total="Todo lo que la empresa posee: caja, cuentas por cobrar, inventarios y equipos. Balance general.",
    e_pasivo_total="Todo lo que la empresa debe: proveedores, créditos, impuestos y obligaciones laborales. Balance general.",
    e_activo_corriente="Recursos que se convierten en dinero en menos de un año: caja, cuentas por cobrar e inventarios. Balance general.",
    e_pasivo_corriente="Obligaciones que deben pagarse en menos de un año. Balance general.",
    e_inventarios="Valor de la mercancía o los materiales almacenados. Balance general.",
    tam="Número de personas que trabajan en la empresa, incluido el propietario. Ajusta las recomendaciones sobre roles, procesos y herramientas.",
    antig="Tiempo de operación de la empresa. Las empresas jóvenes requieren mayor cuidado de la caja.",
    canal="Canal por el que se realiza la mayor parte de las ventas. Define qué recomendaciones de canales, pagos y datos personales son más relevantes.",
    problema="Principal dificultad actual. Aumenta la prioridad de los frentes relacionados; no modifica las demás reglas.",
    ia="Nivel de uso actual de inteligencia artificial generativa (por ejemplo ChatGPT, Gemini o Claude). Define si conviene comenzar con la versión gratuita.",
    horas="Horas semanales que la empresa dedica a tareas administrativas repetitivas (digitar, conciliar, enviar recordatorios). "
          f"Con {nexo.UMBRAL_HORAS_ADMIN} horas o más se recomienda ordenar y luego automatizar.",
    barreras="Seleccione las dificultades que más frenan la adopción de herramientas digitales. Cada una modifica las recomendaciones. Puede dejarlo vacío.",
    enviar="Ejecuta el análisis con los datos del formulario. Es posible modificarlos y volver a ejecutarlo cuantas veces se requiera.",
)

# Respuestas de ejemplo para el caso de demostración
DEMO_RESP = {
    "factura_electronica": 2, "contabilidad_software": 1, "cuenta_separada": 0, "concilia_bancos": 0,
    "base_clientes": 2, "whatsapp_business": 2, "crm": 0, "mide_clientes": 0,
    "pagos_digitales": 2, "presencia_digital": 1, "venta_en_linea": 0, "automatiza_algo": 0,
    "registra_ventas": 2, "inventario_registrado": 1, "revisa_indicadores": 0, "usa_datos_decisiones": 0,
    "procesos_documentados": 0, "control_tareas": 0, "sistemas_integrados": 0, "roles_claros": 1,
    "plan_digital": 0, "presupuesto_digital": 0, "mide_resultados_digitales": 0, "vigila_competencia": 0,
    "backup_nube": 1, "dos_pasos": 1, "contrasenas": 0, "habeas_data": 0,
    "capacitacion": 1, "responsable_digital": 0,
}

ss = st.session_state
ss.setdefault("pantalla", "inicio")
ss.setdefault("ver", 0)
ss.setdefault("demo_default", False)


def k(nombre):
    """Clave de widget con versión: al subir la versión, el formulario queda en blanco."""
    return f"in_{nombre}_{ss['ver']}"


def ir_inicio():
    ss["pantalla"] = "inicio"


def ir_diag(demo=False):
    ss["pantalla"] = "diag"
    if demo:
        ss["ver"] += 1
        ss.pop("resultado", None)
        ss["demo_default"] = True


def nuevo():
    ss["ver"] += 1
    ss["demo_default"] = False
    ss["pantalla"] = "diag"
    ss.pop("resultado", None)


@st.cache_data
def leer_catalogo():
    return nexo.cargar_catalogo(AQUI / "catalogo.xlsx")


@st.cache_data
def leer_refs():
    return nexo.cargar_referencias(AQUI / "referencias_sector.xlsx")


def money(x):
    return core.cop(x)


def pie():
    st.markdown(f'<div class="nx-pie"><b>{marca.PIE_LINEA1}</b><br>{marca.PIE_LINEA2}<br>{marca.PIE_LINEA3}</div>',
                unsafe_allow_html=True)


def experto(ids):
    """Lo que sostienen los expertos sobre una recomendación (complemento opcional, compacto)."""
    for ref in evidencia.obtener(ids):
        if ref.get("frase"):
            st.markdown(f"- **{evidencia.corta(ref)}** señala que {ref['frase']} *Dónde: {ref['donde']}.* [Ver fuente]({ref['url']})")
        else:
            st.markdown(f"- **Lectura recomendada:** {ref['cita']} [Ver fuente]({ref['url']})")


def paso(n, titulo, para):
    st.markdown(f'<div class="nx-step"><div class="n">{n}</div><div><b>{titulo}</b><br><span class="p">{para}</span></div></div>',
                unsafe_allow_html=True)


def nota(texto, alerta=False):
    st.markdown(f'<div class="nx-nota{" nx-alerta" if alerta else ""}">{texto}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ Barra lateral
with st.sidebar:
    if LOGO_H.exists():
        st.image(str(LOGO_H))
    else:
        st.title("Nexo Digital")
    st.caption("Diagnóstico de transformación digital para pequeñas empresas, a partir de datos financieros reales y un cuestionario de 30 preguntas.")
    st.button("Inicio", on_click=ir_inicio, key="b_inicio", help="Vuelve a la pantalla de bienvenida sin borrar los resultados.")
    st.button("Nuevo diagnóstico", on_click=nuevo, key="b_nuevo", type="primary",
              help="Limpia el formulario y los resultados para analizar otra empresa, o la misma con otros datos.")

try:
    catalogo = leer_catalogo()
except Exception as e:
    st.error(f"No se pudo leer catalogo.xlsx ({e}). Ejecute: python crear_catalogo.py")
    st.stop()
refs = leer_refs()

# ------------------------------------------------------------------ Pantalla de inicio
if ss["pantalla"] == "inicio":
    if LOGO_H.exists():
        st.image(str(LOGO_H), width=260)
    st.markdown(
        '<div class="nx-hero"><h1>Diagnóstico de transformación digital para pequeñas empresas</h1>'
        "<p>Nexo Digital combina los datos financieros de la empresa con un cuestionario de 30 preguntas para medir su preparación digital, "
        "definir qué hacer primero, qué inversiones aplazar y cuánto es prudente gastar.</p></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown('<div class="nx-card"><b>1. Parte de datos reales</b><p>Lee ingresos, gastos y estados financieros para calcular la salud '
                "financiera de la empresa y contrastar lo que se declara.</p></div>", unsafe_allow_html=True)
    c2.markdown('<div class="nx-card"><b>2. Mide la preparación digital</b><p>Ocho secciones y 30 preguntas producen un índice y una matriz '
                "que cruza capacidad financiera con preparación digital.</p></div>", unsafe_allow_html=True)
    c3.markdown('<div class="nx-card"><b>3. Entrega un plan</b><p>Prioridades con las cifras de la empresa, ruta de 30 y 90 días, '
                "indicadores de seguimiento e informes en PDF y Excel.</p></div>", unsafe_allow_html=True)
    st.write("")
    b1, b2, _ = st.columns([1, 1.3, 2])
    b1.button("Comenzar diagnóstico", type="primary", on_click=ir_diag, key="b_comenzar",
              help="Abre el formulario para ingresar los datos de la empresa.")
    b2.button("Ver un ejemplo con datos de demostración", on_click=ir_diag, kwargs=dict(demo=True), key="b_demo",
              help="Abre el formulario con un caso ficticio ya cargado para conocer cómo se ven los resultados.")
    st.subheader("Qué hace diferente a Nexo")
    st.markdown(
        "Los autodiagnósticos habituales piden a la empresa calificarse a sí misma. Nexo cambia el punto de partida:\n\n"
        "- **Mide con datos, no solo con opiniones.** Lee los movimientos y los estados financieros y calcula la salud financiera real.\n"
        "- **Aplica modelos financieros reconocidos.** Punto de equilibrio, escenarios de caja, sensibilidad, razones financieras y DuPont.\n"
        "- **Cruza finanzas con preparación digital.** Una matriz indica si conviene invertir ya, ordenar primero u optimizar lo existente.\n"
        "- **Indica qué aplazar** y cuánto es prudente gastar, con una escalera de gasto que va de cero hasta el servicio externo.\n"
        "- **Personaliza cada informe.** Cada recomendación usa las cifras, el tamaño, el canal de venta y las barreras de la empresa.")
    cA, cB = st.columns(2)
    with cA:
        st.subheader("Qué entrega")
        st.markdown(
            "- Semáforo financiero, conclusión y resumen ejecutivo\n- Lectura de caja, punto de equilibrio y escenarios a 6 meses\n"
            "- Razones financieras y DuPont (si se cargan estados)\n- Palancas de mejora cuantificadas\n"
            "- Índice de preparación digital y lectura de cada una de las 30 respuestas\n- Prioridades y recomendaciones por frente\n"
            "- Escalera de gasto e inversiones que conviene aplazar\n- Ruta de 30 y 90 días e indicadores de seguimiento\n- Informe en PDF y libro de Excel")
    with cB:
        st.subheader("Alcance y límites")
        st.markdown(
            "- Pensado para micro y pequeñas empresas colombianas.\n- Orienta decisiones; no reemplaza a un contador, abogado o consultor.\n"
            "- Los escenarios son ejercicios de sensibilidad, no predicciones.\n"
            "- Los precios de las herramientas cambian: confírmelos con el proveedor.\n"
            "- El índice de preparación digital es descriptivo y sirve para comparar a una empresa consigo misma en el tiempo.")
    pie()
    st.stop()

# ------------------------------------------------------------------ Diagnóstico: formulario
st.title("Diagnóstico de la empresa")
st.caption("Siga los pasos en orden. El signo ? junto a cada campo explica qué debe ingresarse.")
if "resultado" not in ss:
    cp1, cp2 = st.columns(2)
    with cp1:
        paso(1, "Cargue los datos financieros", "Movimientos de ingresos y gastos, o la demostración. Con datos reales el análisis es más confiable.")
        paso(2, "Describa el contexto", "Tamaño, antigüedad, canal de venta y barreras ajustan las prioridades.")
    with cp2:
        paso(3, "Responda las 30 preguntas", "Sí, En parte o No, en ocho secciones. Cada respuesta recibe su propia lectura.")
        paso(4, "Pulse Analizar empresa", "Obtendrá el resumen, el análisis financiero, el plan de acción y los informes descargables.")

tiene_res = "resultado" in ss
with st.expander("Datos de la empresa", expanded=not tiene_res):
    st.download_button("Descargar plantilla de movimientos",
                       "fecha,tipo,categoria,descripcion,monto\n2026-01-05,ingreso,Ventas,Pedido cliente A,1500000\n"
                       "2026-01-10,gasto,Arriendo,Local,800000\n", file_name="plantilla_nexo.csv",
                       key="dl_plantilla_" + str(ss["ver"]), help="Archivo de ejemplo con el formato exacto de columnas que espera Nexo.")
    with st.form("form_" + str(ss["ver"])):
        st.subheader("1. Datos financieros")
        c1, c2 = st.columns(2)
        caso = c1.text_input("Nombre de la empresa (opcional)", key=k("caso"), help=AYUDA["caso"])
        if not refs.empty:
            sector = c2.selectbox("Sector (para comparar indicadores)", ["(sin comparar)"] + sorted(set(refs["sector"].astype(str))),
                                  key=k("sector"), help=AYUDA["sector"])
        else:
            sector = c2.text_input("Sector (opcional)", key=k("sector"), help=AYUDA["sector"])
        archivo = st.file_uploader("Movimientos de ingresos y gastos (Excel o CSV)", type=["csv", "xlsx", "xls"],
                                   key=k("archivo"), help=AYUDA["archivo"])
        usar_demo = st.checkbox("Usar datos de demostración (si no se sube archivo)", value=ss["demo_default"],
                                key=k("demo"), help=AYUDA["demo"])
        saldo = st.number_input("Saldo de caja hoy (COP)", min_value=0.0, step=500_000.0, format="%.0f", value=0.0,
                                key=k("saldo"), help=AYUDA["saldo"])
        st.markdown("**Estados financieros (opcional, valores anuales en COP)**")
        with st.container():
            st.caption(AYUDA["estados"])
            ecols = st.columns(3)
            estados_in = {}
            for i, c in enumerate(nexo.CAMPOS_ESTADOS):
                with ecols[i % 3]:
                    estados_in[c] = st.number_input(ETIQ_ESTADOS[c], step=1_000_000.0, format="%.0f", value=0.0,
                                                    key=k("e_" + c), help=AYUDA["e_" + c])

        st.subheader("2. Contexto de la empresa")
        c1, c2, c3 = st.columns(3)
        tam = c1.selectbox("Tamaño del equipo", list(nexo.TAMANOS), format_func=lambda x: nexo.TAMANOS[x], key=k("tam"), help=AYUDA["tam"])
        antig = c2.selectbox("Antigüedad de la empresa", list(nexo.ANTIGUEDAD), index=1, format_func=lambda x: nexo.ANTIGUEDAD[x],
                             key=k("antig"), help=AYUDA["antig"])
        canal = c3.selectbox("Canal principal de venta", list(nexo.CANALES), format_func=lambda x: nexo.CANALES[x], key=k("canal"), help=AYUDA["canal"])
        c1, c2, c3 = st.columns(3)
        problema = c1.selectbox("Principal problema actual", list(nexo.PROBLEMAS), key=k("problema"), help=AYUDA["problema"])
        ia = c2.selectbox("Uso de inteligencia artificial", list(nexo.NIVELES_IA), format_func=lambda x: nexo.NIVELES_IA[x],
                          key=k("ia"), help=AYUDA["ia"])
        horas = c3.slider("Horas semanales en tareas administrativas repetitivas", 0, 40, 5, key=k("horas"), help=AYUDA["horas"])
        barreras = st.multiselect("Barreras para adoptar herramientas digitales (opcional)", list(nexo.BARRERAS),
                                  format_func=lambda x: nexo.BARRERAS[x], key=k("barreras"), help=AYUDA["barreras"])

        st.subheader("3. Cuestionario de preparación digital (30 preguntas)")
        st.caption("Responda cada pregunta con Sí, En parte o No según la situación actual. Son hechos verificables, no opiniones. "
                   "Todas las preguntas son obligatorias.")
        resp_in = {}
        for sec, ps in preguntas.por_seccion().items():
            st.markdown(f"**{sec}**")
            st.caption(preguntas.SECCIONES[sec]["ayuda"])
            for p in ps:
                idx = [2, 1, 0].index(DEMO_RESP[p["key"]]) if ss["demo_default"] else None
                resp_in[p["key"]] = st.radio(p["texto"], [2, 1, 0], index=idx, format_func=lambda v: preguntas.RESP[v],
                                             horizontal=True, key=k("q_" + p["key"]), help=p["ayuda"])
        enviar = st.form_submit_button("Analizar empresa", type="primary", help=AYUDA["enviar"])

if enviar:
    faltan = [kk for kk, v in resp_in.items() if v is None]
    if faltan:
        st.error(f"Faltan {len(faltan)} de las 30 preguntas por responder. Complete el cuestionario y pulse nuevamente Analizar empresa.")
    else:
        try:
            df, rep = None, None
            if archivo is not None:
                df, rep = core.limpiar_datos(core.leer_archivo(archivo))
            elif usar_demo and (AQUI / "datos_demo.csv").exists():
                df, rep = core.limpiar_datos(core.leer_archivo(AQUI / "datos_demo.csv"))
            estados = estados_in if estados_in["ingresos"] > 0 else None
            ref, sec = None, ""
            if not refs.empty and sector != "(sin comparar)":
                ref = refs[refs["sector"].astype(str) == sector].iloc[0]
                sec = sector
            elif refs.empty:
                sec = sector
            with st.spinner("Analizando..."):
                ss["resultado"] = analisis.analizar(caso, df, saldo, estados, resp_in, problema, ia, horas, catalogo, ref, sec,
                                                    contexto=dict(tam=tam, antig=antig, canal=canal, barreras=barreras))
                ss["reporte_datos"] = rep
            st.rerun()
        except Exception as ex:
            st.error(f"No se pudo completar el análisis: {ex}")
            st.caption("Revise que el archivo tenga las columnas fecha, tipo, categoria, descripcion y monto (puede descargar la plantilla).")

if "resultado" not in ss:
    st.info("Al pulsar Analizar empresa, aquí aparecerán el resumen ejecutivo, el análisis financiero, el plan de acción y los informes.")
    pie()
    st.stop()

# ------------------------------------------------------------------ Resultados
r = ss["resultado"]
fin = r["fin"]
re_ = r["resumen_ejecutivo"]
mov = fin["mov"]
st.header(f"Resultados: {r['caso']}")
st.caption(f"Confiabilidad del diagnóstico: {r['confianza']}")
tabs = st.tabs(["Resumen ejecutivo", "Análisis financiero", "Preparación digital", "Plan de acción", "Riesgos y alcance", "Descargas"])


def lect(titulos):
    """Muestra las lecturas redactadas con las cifras de la empresa."""
    for t, x in r["lectura_fin"]:
        if t in titulos:
            nota(f"<b>{t}.</b> {x}")


# ---- 1. Resumen
with tabs[0]:
    sem = re_["semaforo"]
    if sem:
        razones = "".join(f"<li>{t}</li>" for _, t in sem["razones"])
        st.markdown(f'<div class="nx-sem" style="background:{COL_SEM[sem["nivel"]]}"><b>Semáforo financiero: {sem["etiqueta"]}</b>'
                    f"<ul>{razones}</ul></div>", unsafe_allow_html=True)
    else:
        nota("No se calcula el semáforo porque no se cargaron datos financieros. Cargue movimientos o estados financieros y vuelva a analizar.")
    ind, mat = r["indice"], r["matriz"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Índice de preparación digital", f"{ind['valor']:.0f} / 100", ind["banda"], delta_color="off",
              help="Promedio de las ocho secciones del cuestionario (Sí = 2 puntos, En parte = 1, No = 0), expresado de 0 a 100.")
    c2.metric("Estrategia sugerida", mat["nombre"] if mat else "Sin datos",
              help="Resulta de cruzar la capacidad financiera (semáforo) con la preparación digital (índice de 50 o más).")
    c3.metric("Presupuesto digital prudente", informe._pres_corto(r),
              help=f"Hasta {nexo.PRUDENCIA_EXCEDENTE:.0%} del excedente mensual promedio, y solo si la caja cubre al menos "
                   f"{nexo.MESES_COLCHON_MIN:.0f} mes de gastos. Es un tope de prudencia, no una meta.")
    c4.metric("Cobertura de caja", f"{mov['cobertura_meses']:.1f} meses" if mov and mov["cobertura_meses"] is not None else "sin dato",
              help="Cuántos meses de gastos podría pagar la empresa con el saldo actual si no entrara más dinero.")
    st.subheader("Conclusión del diagnóstico")
    for t in r["conclusion"]:
        st.markdown(t)
    st.subheader("Tres prioridades")
    for n, t in re_["prioridades"]:
        st.markdown(f"**{n}.** {t}")
    if re_["primer_paso"]:
        nota(f"<b>Primer paso en 30 días:</b> {re_['primer_paso']}")
    if re_["alerta"]:
        nota(f"<b>Alerta principal:</b> {re_['alerta']}", alerta=True)
    if r["perfil_empresa"]:
        st.subheader("Perfil y contexto de la empresa")
        for t, x in r["perfil_empresa"]:
            st.markdown(f"**{t}.** {x}")

# ---- 2. Financiero
with tabs[1]:
    if mov:
        if fin["aviso"]:
            st.info(fin["aviso"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingresos / mes", money(mov["ingreso_prom"]), help="Promedio mensual de ingresos en los últimos tres meses analizados.")
        c2.metric("Gastos / mes", money(mov["gasto_prom"]), help="Promedio mensual de gastos en los últimos tres meses analizados.")
        c3.metric("Margen de caja", f"{mov['margen']:.1%}", help="De cada 100 pesos que entran, cuántos sobran después de los gastos. Negativo significa que se gasta más de lo que se vende.")
        c4.metric("Meses en rojo (últ. 12)", f"{mov['meses_en_rojo']} de {mov['meses_considerados']}",
                  help="Meses en los que los gastos superaron a los ingresos.")
        lect(("Resultado de caja", "Colchón de caja", "Regularidad", "Estabilidad de los ingresos", "Tendencia reciente"))
        st.subheader("Ingresos y gastos por mes")
        g = fin["resumen"][["ingreso", "gasto"]].copy()
        g.index = [str(p) for p in g.index]
        g.columns = ["Ingresos", "Gastos"]
        st.bar_chart(g, color=[LIMA, "#014A27"])
        eq = fin["equilibrio"]
        if eq and eq.get("ventas_equilibrio"):
            st.subheader("Punto de equilibrio")
            c1, c2, c3 = st.columns(3)
            c1.metric("Ventas de equilibrio / mes", money(eq["ventas_equilibrio"]),
                      help="Ventas mensuales mínimas para cubrir todos los gastos: gastos fijos divididos por el margen de contribución.")
            c2.metric("Gastos fijos estimados", money(eq["fijos"]),
                      help="Gastos que se pagan aunque no se venda (nómina, arriendo, créditos, servicios). Se estiman por el nombre de la categoría.")
            c3.metric("Margen de contribución", f"{eq['margen_contribucion']:.1%}",
                      help="De cada peso vendido, cuánto queda después de los gastos variables para cubrir los fijos.")
            lect(("Punto de equilibrio",))
            st.caption("Categorías tomadas como fijas: " + (", ".join(eq["categorias_fijas"]) or "ninguna detectada") + ". Es una aproximación, no una medición contable.")
        cat = fin["categorias"]
        if cat is not None and len(cat):
            st.subheader("En qué se va el dinero")
            gc = pd.DataFrame({"Participación (%)": (cat["participacion"] * 100).round(1).values}, index=cat["categoria"].astype(str).values)
            st.bar_chart(gc, color=V_OSC)
            lect(("Estructura de gastos",))
        for a in fin["anomalias"][:3]:
            nota(f"Gasto inusual: <b>{html.escape(str(a['categoria']))}</b> subió {a['pct']:+.0%} en el último mes frente a su promedio.", alerta=True)
        esc = fin["escenarios"]
        if esc:
            st.subheader("Resistencia de la caja: escenarios a 6 meses")
            lin = pd.DataFrame({n.split(" (")[0].split(":")[0]: p["saldo"].values for n, p in esc["proyecciones"].items()},
                               index=[str(i) for i in esc["proyecciones"]["Base (sin cambios)"].index])
            st.line_chart(lin)
            t = esc["tabla"].copy()
            t["saldo_final"] = t["saldo_final"].map(money)
            t["saldo_minimo"] = t["saldo_minimo"].map(money)
            t.columns = ["Escenario", "Saldo final", "Saldo mínimo", "Mes en que se agota"]
            st.dataframe(t, hide_index=True)
            lect(("Resistencia de la caja",))
            st.subheader("¿Qué factor pesa más?")
            s = esc["sensibilidad"]
            st.bar_chart(pd.DataFrame({"Efecto en el saldo final (COP)": s["impacto"].values},
                                      index=[f.split(" (")[0] for f in s["factor"]]), color="#B42318")
        elif fin["error_proy"]:
            st.warning(fin["error_proy"])
        est = fin["estacionalidad"]
        if est:
            st.subheader("Estacionalidad de los ingresos")
            st.bar_chart(pd.DataFrame({"Índice (1,0 = promedio)": est["indice"].values}, index=list(est["indice"].index)), color=V_AZUL)
            lect(("Estacionalidad",))
        for a in fin["alertas"]:
            nota(f"<b>{a['titulo']}.</b> {a['detalle']} <i>Acción: {a['accion']}</i>", alerta=a["nivel"] != "verde")
        if r["palancas"]:
            st.subheader("Palancas de mejora cuantificadas")
            st.caption("Ejercicios de sensibilidad con las cifras cargadas; no son promesas de resultado.")
            st.dataframe(pd.DataFrame([{"Palanca": x["nombre"], "Efecto mensual": money(x["mensual"]), "Efecto anual": money(x["anual"]),
                                        "Lectura": x["lectura"]} for x in r["palancas"]]), hide_index=True)
    else:
        for t, x in r["lectura_fin"]:
            if t == "Sin datos financieros":
                st.info(x)
    ests = fin["estados"]
    if ests:
        st.subheader("Indicadores de los estados financieros")
        filas = []
        for it in ests["items"]:
            v = it["valor"]
            filas.append({"Indicador": it["nombre"], "Valor": money(v) if it["clave"] == "capital_trabajo" else round(v, 2),
                          "Lectura": SEMAFORO.get(it["nivel"], "") + " " + it["lectura"], "Cómo se calcula": it["definicion"],
                          "Frente al sector": it["vs_sector"]})
        st.dataframe(pd.DataFrame(filas), hide_index=True)
        lect(("Estados financieros", "Origen de la rentabilidad (DuPont)"))
        if r.get("cartera_10"):
            nota(f"Cada 10 días menos de cartera libera cerca de <b>{money(r['cartera_10'])}</b> de caja (ingresos anuales / 365 x 10).")
        st.caption("Los semáforos usan referencias generales de análisis financiero. La comparación más útil es contra el promedio del sector.")
    lect(("Consistencia entre fuentes",))

# ---- 3. Preparación digital
with tabs[2]:
    ind, mat = r["indice"], r["matriz"]
    c1, c2 = st.columns(2)
    c1.metric("Índice de preparación digital", f"{ind['valor']:.0f} / 100", ind["banda"], delta_color="off",
              help="Promedio simple de las ocho secciones. Es descriptivo: sirve para comparar a la empresa consigo misma en el tiempo.")
    c2.metric("Estrategia sugerida", mat["nombre"] if mat else "Sin datos financieros",
              help="Cruce entre capacidad financiera y preparación digital.")
    if mat:
        nota(f"<b>Matriz de capacidad financiera y preparación digital.</b> Capacidad financiera {'alta' if mat['cap_alta'] else 'limitada'} y "
             f"preparación digital {'alta' if mat['dig_alta'] else 'limitada'}: estrategia <b>{mat['nombre']}</b>. {mat['texto']}")
    st.subheader("Avance por sección")
    for d in r["dimensiones"]:
        st.progress(d["pct"] / 100.0, text=f"{d['seccion']}: {d['pct']:.0f} % ({d['banda']})")
    st.subheader("Lectura por sección")
    for d in r["dimensiones"]:
        with st.expander(f"{d['seccion']}: {d['pct']:.0f} % ({d['banda']})"):
            st.write(d["texto"])
            if d["fortalezas"]:
                st.markdown("**Fortalezas**\n" + "\n".join(f"- {x}" for x in d["fortalezas"]))
            if d["brechas"]:
                st.markdown("**Brechas**\n" + "\n".join(f"- {x}" for x in d["brechas"]))
    st.subheader("Lectura de cada respuesta")
    filtro = st.selectbox("Mostrar", ["Todas las respuestas", "Solo No", "Solo En parte", "Solo Sí"], key="filtro_resp",
                          help="Filtra la tabla por el tipo de respuesta.")
    quitar = {"Solo No": "No", "Solo En parte": "En parte", "Solo Sí": "Sí"}.get(filtro)
    filas = [{"Sección": x["seccion"], "Pregunta": x["pregunta"].strip("¿?"), "Respuesta": x["respuesta"], "Lectura": x["lectura"]}
             for x in r["lectura_preguntas"] if quitar is None or x["respuesta"] == quitar]
    st.dataframe(pd.DataFrame(filas), hide_index=True)
    st.subheader("Contraste de las respuestas con los datos")
    for n in r["notas"]:
        nota(n)

# ---- 4. Plan
with tabs[3]:
    ver_exp = st.toggle("Mostrar lo que sostienen los expertos sobre cada recomendación", value=False, key="ver_exp",
                        help="Complemento opcional: para cada recomendación muestra qué sostienen distintos autores e instituciones y dónde consultarlo.")
    st.subheader("Prioridades y recomendaciones")
    if not r["orden"]:
        st.success("Con las respuestas dadas no se detectan brechas prioritarias. El Chequeo Digital de MinTIC puede servir como segunda opinión.")
    for i, n in enumerate(r["orden"], 1):
        with st.expander(f"{i}. {nexo.NECESIDADES[n]} (prioridad {r['puntaje'][n]})", expanded=i <= 3):
            for x in [x for x in r["disparadas"] if x["nec"] == n]:
                marco = " *(marco normativo)*" if x["tag"] == "normativo" else ""
                st.markdown(f"{x['por_que']}{marco}" + (f"  \n**{x['detalle']}**" if x.get("detalle") else ""))
                if ver_exp:
                    experto(x.get("refs_ids", []))
    st.subheader("Herramientas concretas para cada frente")
    st.caption("Programas, páginas y servicios que resuelven cada necesidad prioritaria. Se ofrecen primero las gratuitas; las de pago aparecen solo si hay presupuesto prudente. Confirme condiciones y precios en el sitio oficial.")
    if r["herramientas"]:
        _hd = pd.DataFrame([{"Frente": nexo.NECESIDADES[x["nec"]], "Herramienta": x["nombre"], "Costo": x["tipo"], "Para qué sirve": x["para"], "Sitio": x["url"] or "—"} for x in r["herramientas"]])
        st.dataframe(_hd, hide_index=True, use_container_width=True)
    st.subheader("Escalera de gasto")
    st.caption("Para cada frente se muestra primero lo más económico que lo resuelve. Los precios son referenciales: confírmelos con el proveedor.")
    for n in r["orden"][:6]:
        if not r["ops"].get(n):
            continue
        st.markdown(f"**{nexo.NECESIDADES[n]}**")
        for o in r["ops"].get(n, []):
            icono_ok = "✅" if o["ok"] else "⏸️"
            with st.expander(f"{icono_ok} Peldaño {o['peldano']} ({PELDANOS[o['peldano']]}): {o['nombre']}"):
                st.write(f"{ICONO.get(o['tipo'], '⚪')} {o['tipo']} · **{o['costo']}**")
                st.write(o["descripcion"])
                if o["motivo"]:
                    st.warning("Conviene aplazarlo: " + o["motivo"])
                if o["advertencia"]:
                    st.caption(o["advertencia"])
                if o["url"]:
                    st.caption(f"Más información: {o['url']}")
    st.subheader("Inversiones que conviene aplazar")
    if r["nct"]:
        st.dataframe(pd.DataFrame(r["nct"], columns=["Frente", "Opción", "Motivo para aplazar"]), hide_index=True)
    else:
        st.write("No hay opciones bloqueadas por ahora.")
    st.subheader("Próximos 30 días")
    for nec, ops in r["d30"]:
        st.write(f"**{nec}:** " + ("; ".join(f"{o['nombre']} ({o['costo']})" for o in ops) or "sin opción disponible en el catálogo"))
    st.subheader("Días 31 a 90")
    st.caption("Solo si lo anterior funcionó y resulta insuficiente.")
    for nec, op, motivo in r["d90"]:
        if op:
            st.write(f"**{nec}:** {op['nombre']} ({op['costo']})")
        elif motivo:
            st.write(f"**{nec}:** aún no. {motivo}")
        else:
            st.write(f"**{nec}:** sin paso siguiente en el catálogo.")
    st.subheader("Agenda sugerida")
    for cuando, titulo, acciones in r["agenda"]:
        st.markdown(f"**{cuando}.** {titulo}")
        for a in acciones:
            st.markdown(f"- {a}")
    st.subheader("Indicadores de seguimiento")
    st.dataframe(pd.DataFrame([{"Frente": x["necesidad"], "Objetivo": x["objetivo"], "Indicador": x["indicador"], "Meta": x["meta"],
                                "Error frecuente": x["error"]} for x in r["seguimiento"]]), hide_index=True)

# ---- 5. Riesgos y alcance
with tabs[4]:
    st.subheader("Riesgos de una transformación mal planteada")
    for titulo, nt in nexo.RIESGOS:
        st.markdown(f"- **{titulo}.** {nt}")
    st.subheader("Cómo se elaboró este diagnóstico")
    st.markdown(
        "- El **índice de preparación digital** resume 30 respuestas en ocho secciones (Sí = 2, En parte = 1, No = 0) y promedia las secciones con el mismo peso.\n"
        "- Las **recomendaciones** salen de reglas explícitas que cruzan las respuestas, los datos financieros y el contexto de la empresa.\n"
        "- La **escalera de gasto** va de 0 (proceso sin tecnología), 1 (gratuito), 2 (bajo costo), 3 (automatización) a 4 (servicio externo).\n"
        "- No se recomienda una herramienta si faltan sus requisitos previos.\n"
        f"- **Presupuesto prudente:** hasta {nexo.PRUDENCIA_EXCEDENTE:.0%} del excedente mensual, y solo si la caja cubre {nexo.MESES_COLCHON_MIN:.0f} mes de gastos.")
    st.subheader("Alcance y límites")
    st.markdown(
        "- Los gastos fijos y variables se estiman por el nombre de la categoría; los escenarios son sensibilidades, no predicciones.\n"
        "- Los semáforos de estados financieros usan referencias generales; la referencia más útil es la del sector.\n"
        "- Los precios y los límites de los planes de las herramientas cambian: confírmelos con cada proveedor.\n"
        "- El diagnóstico orienta decisiones y no reemplaza la asesoría de un contador, un abogado o un consultor.")

# ---- 6. Descargas
with tabs[5]:
    st.subheader("Informes para descargar")
    nombre = "".join(c if c.isalnum() else "_" for c in r["caso"])[:40] or "empresa"
    try:
        html = informe.informe_html(r)
        st.download_button("Informe completo (HTML, imprimible como PDF)", html,
                           file_name=f"informe_nexo_{nombre}.html", mime="text/html", key="dl_html",
                           help="Informe completo con gráficos. Ábralo con doble clic y use Imprimir o Guardar como PDF.")
        st.caption("Ábralo con doble clic (se abre en el navegador) y pulse el botón Imprimir o guardar como PDF.")
    except Exception as ex:
        st.error(f"No se pudo generar el informe HTML: {ex}")
    try:
        st.download_button("Libro de Excel con todas las tablas", informe.informe_excel(r), file_name=f"analisis_nexo_{nombre}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_xlsx",
                           help="Todas las tablas del análisis en hojas separadas, para trabajar con ellas en Excel.")
    except Exception as ex:
        st.error(f"No se pudo generar el Excel: {ex}")
    st.download_button("Datos del diagnóstico (JSON, para investigación)",
                       nexo.resultado_json(r["caso"], r["orden"], r["puntaje"], r["resp"], r["presupuesto"], r["indice"]),
                       file_name=f"resultado_nexo_{nombre}.json", key="dl_json",
                       help="Resumen en formato de datos, útil para reunir varios diagnósticos en una investigación.")

pie()
