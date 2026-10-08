"""Nexo Digital - motor de reglas (no depende de Streamlit).

Principio: las reglas deciden, de forma explícita y auditable. Cada hallazgo nace de una respuesta del
cuestionario (30 preguntas), de los datos financieros cargados o del contexto de la empresa.
"""
import json
from datetime import date

import numpy as np
import pandas as pd

import core
import evidencia
import preguntas

# ---- Parámetros de prudencia (criterio de gestión, ajustables) ----
PRUDENCIA_EXCEDENTE = 0.25  # fracción del excedente mensual promedio que se puede comprometer
MESES_COLCHON_MIN = 1.0     # meses de gasto que debe cubrir la caja antes de asumir gastos nuevos
UMBRAL_HORAS_ADMIN = 10     # horas/semana en tareas administrativas repetitivas

HECHOS = {p["key"]: p["texto"] for p in preguntas.PREGUNTAS}
EXTRA_REQ = {"ia_gratuita": "Usar IA en su versión gratuita de forma constante"}

NECESIDADES = {
    "FAC": "Facturación electrónica",
    "CON": "Contabilidad y control de costos",
    "CLI": "Relación y seguimiento de clientes",
    "CAJ": "Control de caja, cobros y liquidez",
    "DAT": "Registro y uso de datos",
    "AUT": "Automatización de tareas repetitivas",
    "SEG": "Seguridad y protección de datos personales",
    "FOR": "Formación y responsables digitales",
    "IA": "Inteligencia artificial de uso general",
    "PRO": "Procesos y organización del trabajo",
    "EST": "Estrategia y dirección digital",
    "CAN": "Canales de venta, pagos y presencia en línea",
}
PROBLEMAS = {
    "No tengo claro por dónde empezar": [],
    "Pocas ventas o clientes que no regresan": ["CLI", "CAN"],
    "Falta de caja o cobros lentos": ["CAJ"],
    "Costos altos o poco margen": ["CON", "DAT"],
    "Demasiado tiempo en tareas administrativas": ["AUT", "PRO"],
    "Desorden de inventario": ["DAT"],
    "Todo depende de una sola persona": ["PRO", "EST", "FOR"],
}
TAMANOS = {"1-3": "1 a 3 personas", "4-10": "4 a 10 personas", "11-50": "11 a 50 personas"}
ANTIGUEDAD = {"<2": "Menos de 2 años", "2-5": "Entre 2 y 5 años", ">5": "Más de 5 años"}
CANALES = {"presencial": "Principalmente presencial", "redes": "WhatsApp y redes sociales",
           "en_linea": "Tienda o página en línea", "b2b": "Venta a otras empresas (B2B)", "mixto": "Mixto"}
BARRERAS = {"dinero": "Falta de recursos económicos", "tiempo": "Falta de tiempo", "conocimiento": "Falta de conocimiento",
            "seguridad": "Preocupación por la seguridad o la privacidad de los datos",
            "no_se": "Dificultad para elegir la herramienta adecuada",
            "resistencia": "Resistencia o poca disposición del equipo"}
NIVELES_IA = {"ninguna": "No utiliza inteligencia artificial", "gratuita": "La utiliza ocasionalmente en versión gratuita",
              "paga": "La utiliza en versión de pago"}

KEYS_SW = ("software", "suscripcion", "licencia", "hosting", "dominio", "siigo", "alegra", "hubspot", "zoho",
           "google workspace", "microsoft 365", "office 365", "canva", "zoom", "chatgpt", "openai", "notion",
           "slack", "shopify", "wix", "wompi")

CAMPOS_ESTADOS = ["ingresos", "utilidad_operacional", "utilidad_neta", "cuentas_por_cobrar", "activo_total",
                  "pasivo_total", "activo_corriente", "pasivo_corriente", "inventarios"]

RIESGOS = [
    ("Comprar tecnología antes de ordenar los procesos y los datos",
     "Una herramienta nueva sobre procesos desordenados multiplica el desorden. Documente y simplifique primero."),
    ("Subestimar el costo total (suscripciones sin uso, implementación y capacitación)",
     "Revise cada mes qué se paga y qué se usa; cancele lo que no genere valor."),
    ("Falta de habilidades en el equipo para usar lo adquirido",
     "Incluya la capacitación en el presupuesto de cada herramienta y designe un responsable."),
    ("Datos dispersos o sistemas que no se conectan",
     "Antes de comprar otro sistema, verifique qué permite integrar el software que ya utiliza."),
    ("Ciberseguridad y manejo de datos personales de clientes (Ley 1581 de 2012)",
     "No cargue datos personales en herramientas sin revisar sus condiciones y sin autorización de los titulares."),
    ("Planes gratuitos cuyos límites y precios cambian",
     "Confirme siempre las condiciones en la página oficial del proveedor antes de decidir."),
    ("Subcontratar sin un alcance claro",
     "Solicite tres cotizaciones por entregables y exija que los datos y la configuración queden a nombre de la empresa."),
    ("Invertir con la caja ajustada",
     "Condicione cada compra recurrente a que la caja cubra, como mínimo, un mes de gastos."),
]

# ------------------------------------------------------------------ Datos
def cargar_catalogo(ruta):
    df = pd.read_excel(ruta)
    for c in ("costo_cop_min", "costo_cop_max"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["peldano"] = df["peldano"].astype(int)
    for c in df.columns:
        if c not in ("costo_cop_min", "costo_cop_max", "peldano"):
            df[c] = df[c].fillna("").astype(str)
    return df


def cargar_referencias(ruta):
    try:
        df = pd.read_excel(ruta)
        return df.dropna(subset=["sector"]) if "sector" in df.columns else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def hechos_extendidos(h, ia):
    e = dict(h)
    e["ia_gratuita"] = ia in ("gratuita", "paga")
    return e


def capacidad_inversion(resumen, saldo):
    u = resumen.tail(6)
    excedente = float(max(u["neto"].mean(), 0.0))
    gasto = float(u["gasto"].mean())
    cobertura = saldo / gasto if gasto > 0 else float("nan")
    colchon = (not np.isnan(cobertura)) and cobertura >= MESES_COLCHON_MIN
    ingreso = float(u["ingreso"].sum())
    return dict(excedente=excedente, gasto_mensual=gasto, cobertura_meses=cobertura,
                presupuesto=excedente * PRUDENCIA_EXCEDENTE if colchon else 0.0,
                margen=float(u["neto"].sum() / ingreso) if ingreso > 0 else 0.0, origen="movimientos")


def capacidad_desde_estados(e, saldo):
    """Aproximación anual -> mensual cuando solo hay estados financieros."""
    ing = e["ingresos"]
    gasto = max(ing - e["utilidad_neta"], 0.0) / 12
    excedente = max(e["utilidad_neta"], 0.0) / 12
    cobertura = saldo / gasto if gasto > 0 else float("nan")
    colchon = (not np.isnan(cobertura)) and cobertura >= MESES_COLCHON_MIN
    return dict(excedente=excedente, gasto_mensual=gasto, cobertura_meses=cobertura,
                presupuesto=excedente * PRUDENCIA_EXCEDENTE if colchon else 0.0,
                margen=(e["utilidad_neta"] / ing) if ing > 0 else 0.0, origen="estados financieros (aprox. anual/12)")


def indicadores_estados(e):
    """Mismas definiciones que usa la Superintendencia de Sociedades en sus informes sectoriales."""
    out, ing = {}, e["ingresos"]
    if ing > 0:
        out["margen_operacional"] = e["utilidad_operacional"] / ing * 100
        out["margen_neto"] = e["utilidad_neta"] / ing * 100
        out["rotacion_deudores_dias"] = e["cuentas_por_cobrar"] / ing * 365
    if e["activo_total"] > 0:
        out["endeudamiento"] = e["pasivo_total"] / e["activo_total"] * 100
    if e["pasivo_corriente"] > 0:
        out["razon_corriente"] = e["activo_corriente"] / e["pasivo_corriente"]
        out["prueba_acida"] = (e["activo_corriente"] - e["inventarios"]) / e["pasivo_corriente"]
    return out


def detectar_software(df):
    """Pagos recurrentes (2+ meses) que parecen suscripciones de software."""
    vacio = pd.DataFrame(columns=["meses", "promedio"])
    if df is None:
        return vacio
    g = df[df["tipo"] == "gasto"].copy()
    if g.empty:
        return vacio
    txt = (g["categoria"].astype(str) + " " + g["descripcion"].astype(str)).map(core._sin_tildes)
    s = g[txt.map(lambda t: any(k in t for k in KEYS_SW))]
    if s.empty:
        return vacio
    s = s.assign(mes=s["fecha"].dt.to_period("M"))
    res = s.groupby("categoria").agg(meses=("mes", "nunique"), promedio=("monto", "mean"))
    return res[res["meses"] >= 2]



def verificar(h, df, sw):
    """Contrasta lo declarado con lo que muestran los datos cargados."""
    if df is None:
        return ["No se cargaron movimientos: las respuestas no pudieron contrastarse con datos, por lo que el diagnóstico tiene menor confiabilidad."]
    notas = []
    if h["contabilidad_software"] and sw.empty:
        notas.append("Se declara contabilidad en software, pero el archivo no muestra pagos recurrentes a un software "
                     "(puede ser gratuito o pagarse desde otra cuenta).")
    if not h["contabilidad_software"] and not sw.empty:
        notas.append("Se declara no usar software contable, pero hay pagos recurrentes que parecen suscripciones: "
                     + ", ".join(map(str, sw.index)) + ".")
    if not h["registra_ventas"] and int((df["tipo"] == "ingreso").sum()) >= 3:
        notas.append("Se declara que no se registran las ventas, pero el archivo cargado sí contiene ingresos registrados. Conviene revisar la respuesta.")
    return notas or ["Las respuestas son consistentes con los datos cargados."]


# ------------------------------------------------------------------ Respuestas, índice y matriz
def hechos_desde_respuestas(resp):
    """resp: {clave: 0|1|2}. h[k] es verdadero solo con 'Sí' (2)."""
    return {k: int(resp.get(k, 0)) == 2 for k in HECHOS}


def perfil(resp):
    """{sección: (puntos, máximo)} con Sí=2, En parte=1, No=0."""
    out = {}
    for sec, ps in preguntas.por_seccion().items():
        out[sec] = (sum(int(resp.get(p["key"], 0)) for p in ps), 2 * len(ps))
    return out


def _banda(v):
    return "Inicial" if v < 25 else "Básico" if v < 50 else "Intermedio" if v < 75 else "Avanzado"


def indice_preparacion(resp):
    """Índice 0-100: promedio simple del porcentaje alcanzado en las 8 secciones. Es descriptivo."""
    det = {}
    for sec, (n, m) in perfil(resp).items():
        pct = 100.0 * n / m if m else 0.0
        det[sec] = dict(puntos=n, maximo=m, pct=pct, banda=_banda(pct))
    valor = sum(d["pct"] for d in det.values()) / len(det)
    return dict(valor=valor, banda=_banda(valor), detalle=det)


MATRIZ = {
    (False, False): ("Cimientos sin gasto",
                     "La capacidad financiera y la preparación digital son limitadas. Conviene ordenar procesos y datos con herramientas gratuitas y aplazar las compras."),
    (False, True): ("Optimizar lo que ya se tiene",
                    "La preparación digital es buena, pero la caja es frágil. Conviene aprovechar mejor las herramientas actuales, cancelar las que no se usan y proteger el flujo de caja."),
    (True, False): ("Invertir con método",
                    "Hay capacidad financiera para avanzar, pero la base digital es incipiente. Conviene invertir en lo fundamental (facturación, datos y procesos) siguiendo la escalera de gasto."),
    (True, True): ("Escalar",
                   "Caja y preparación son sólidas. Es viable evaluar automatización e integración, midiendo siempre el retorno de cada inversión."),
}


def matriz_estrategica(semaforo, indice):
    """Cruza capacidad financiera (semáforo) con preparación digital (índice >= 50)."""
    if semaforo is None:
        return None
    cap_alta = semaforo["nivel"] == 0
    dig_alta = indice["valor"] >= 50
    nombre, texto = MATRIZ[(cap_alta, dig_alta)]
    return dict(nombre=nombre, texto=texto, cap_alta=cap_alta, dig_alta=dig_alta)


# ------------------------------------------------------------------ Reglas
def _ind(c, k):
    e = c["fin"]["estados"]
    return None if not e else e["indicadores"].get(k)


def _pct(x):
    return f"{x:.0%}"


def _cob(c):
    return c["cap"]["cobertura_meses"]


REGLAS = [
    dict(id="R05", nec="CAJ", prio=3, tag="criterio", fuente="Liquidez y continuidad del negocio",
         cond=lambda c: c["cap"] is not None and (_cob(c) < MESES_COLCHON_MIN or c["cap"]["margen"] < 0.05),
         por_que="La caja cubre poco tiempo de gastos o el margen es muy estrecho, lo que limita la capacidad de absorber imprevistos.",
         detalle=lambda c: f"La caja cubre {_cob(c):.1f} meses de gastos y el margen de caja de los últimos seis meses es {c['cap']['margen']:.1%}. "
                           "Antes de asumir compromisos recurrentes conviene reconstruir el colchón de caja."),
    dict(id="R08", nec="AUT", prio=2, tag="criterio", fuente="Productividad administrativa",
         cond=lambda c: c["horas"] >= UMBRAL_HORAS_ADMIN,
         por_que=f"Se dedican {UMBRAL_HORAS_ADMIN} o más horas semanales a tareas administrativas repetitivas.",
         detalle=lambda c: f"Se declaran {c['horas']} horas semanales, equivalentes a unas {c['horas'] * 4.3:.0f} horas al mes. "
                           "El orden recomendado es documentar, simplificar y solo después automatizar."),
    dict(id="R11", nec="IA", prio=1, tag="prudencia", fuente="Gradualidad en la adopción",
         cond=lambda c: c["ia"] == "ninguna",
         por_que="No se utiliza inteligencia artificial. Conviene probarla en su versión gratuita con tareas simples antes de pagar un plan.",
         detalle=lambda c: "Casos de bajo riesgo: redactar mensajes a clientes, resumir documentos, ordenar ideas. No ingresar datos personales ni información confidencial."),
    dict(id="R12", nec="CAJ", prio=3, tag="normativo", fuente="Ley 2024 de 2020, art. 3 (plazos de pago)",
         cond=lambda c: (_ind(c, "rotacion_deudores_dias") or 0) > 45,
         por_que="Los clientes pagan más tarde de lo que la ley de plazos de pago permite entre empresas.",
         detalle=lambda c: f"Las cuentas por cobrar equivalen a {_ind(c, 'rotacion_deudores_dias'):.0f} días de ventas. "
                           "La Ley 2024 de 2020 fija plazos máximos de 60 días (primer año) y 45 días (después) entre empresas, con excepciones como las operaciones entre grandes empresas. "
                           "Conviene revisar las condiciones de pago y establecer recordatorios de cobro."),
    dict(id="R13", nec="CON", prio=2, tag="criterio", fuente="Estructura de costos",
         cond=lambda c: bool(c["fin"]["concentracion"]) and c["fin"]["concentracion"]["top1"] > 0.40 and c["cap"] is not None and c["cap"]["margen"] < 0.10,
         por_que="Un solo rubro concentra gran parte de los gastos y el margen es estrecho: allí está la principal palanca de ahorro.",
         detalle=lambda c: f"'{c['fin']['concentracion']['top1_nombre']}' representa {_pct(c['fin']['concentracion']['top1'])} de los gastos y el margen es {c['cap']['margen']:.1%}. "
                           "Negociar o reducir ese rubro tiene más efecto que cualquier otro ajuste."),
    dict(id="R14", nec="CAJ", prio=3, tag="criterio", fuente="Análisis costo-volumen-utilidad",
         cond=lambda c: c["fin"]["equilibrio"] is not None and c["fin"]["equilibrio"]["holgura"] is not None and c["fin"]["equilibrio"]["holgura"] < 0,
         por_que="Las ventas actuales están por debajo del punto de equilibrio estimado con los movimientos cargados.",
         detalle=lambda c: f"Se requieren ventas cercanas a {core.cop(c['fin']['equilibrio']['ventas_equilibrio'])} al mes para cubrir costos fijos y variables; "
                           f"hoy las ventas están {abs(c['fin']['equilibrio']['holgura']):.0%} por debajo. Antes de invertir en tecnología conviene cerrar esa brecha."),
    dict(id="R15", nec="CAJ", prio=3, tag="prudencia", fuente="Proyección de caja con escenarios",
         cond=lambda c: c["fin"]["escenarios"] is not None and any(
             "Combinado" in str(x["escenario"]) and x["mes_critico"] != "No se agota" for _, x in c["fin"]["escenarios"]["tabla"].iterrows()),
         por_que="Si varios factores adversos coinciden, la caja se agotaría dentro del horizonte analizado.",
         detalle=lambda c: "En el escenario combinado (ventas -10 %, cobros tardíos y nómina +10 %) la caja se agota en "
                           + str([x["mes_critico"] for _, x in c["fin"]["escenarios"]["tabla"].iterrows() if "Combinado" in str(x["escenario"])][0])
                           + ". Conviene constituir un colchón antes de contratar herramientas de pago."),
    dict(id="R16", nec="CON", prio=2, tag="criterio", fuente="Evolución de gastos frente a ventas",
         cond=lambda c: c["fin"]["mov"] is not None and c["fin"]["mov"].get("crec_gastos") is not None and c["fin"]["mov"].get("crec_ingresos") is not None
         and c["fin"]["mov"]["crec_gastos"] > c["fin"]["mov"]["crec_ingresos"] + 0.03,
         por_que="Los gastos crecen más rápido que las ventas, por lo que el margen se está erosionando.",
         detalle=lambda c: f"Gastos {c['fin']['mov']['crec_gastos']:+.1%} frente a ventas {c['fin']['mov']['crec_ingresos']:+.1%}. "
                           "El primer paso es un control de costos por categoría."),
    dict(id="R17", nec="DAT", prio=1, tag="criterio", fuente="Estacionalidad de los ingresos",
         cond=lambda c: c["fin"]["estacionalidad"] is not None and c["fin"]["estacionalidad"]["amplitud"] >= 0.30,
         por_que="Los ingresos varían de forma marcada a lo largo del año, por lo que conviene planear caja y compras por temporada.",
         detalle=lambda c: f"Los meses fuertes son {', '.join(c['fin']['estacionalidad']['pico'])} y los débiles {', '.join(c['fin']['estacionalidad']['valle'])}. "
                           "Se recomienda reservar excedente en los meses fuertes para cubrir los débiles."),
    dict(id="R18", nec="CAJ", prio=2, tag="criterio", fuente="Endeudamiento",
         cond=lambda c: (_ind(c, "endeudamiento") or 0) > 70,
         por_que="El nivel de endeudamiento es alto: nuevas cuotas fijas aumentan el riesgo financiero.",
         detalle=lambda c: f"El endeudamiento es {_ind(c, 'endeudamiento'):.0f} % (pasivo sobre activo). Conviene preferir soluciones gratuitas o de pago mensual cancelable."),
    dict(id="R19", nec="DAT", prio=2, tag="criterio", fuente="Consistencia entre fuentes",
         cond=lambda c: c["fin"]["consistencia"] is not None and not c["fin"]["consistencia"]["coincide"],
         por_que="Los movimientos y los estados financieros no cuentan la misma historia.",
         detalle=lambda c: f"Los ingresos de los movimientos difieren {abs(c['fin']['consistencia']['diferencia']):.0%} de los del estado de resultados. "
                           "Antes de decidir, se recomienda conciliar ambas fuentes."),
    dict(id="R23", nec="PRO", prio=2, tag="criterio", fuente="Orden previo a la automatización",
         cond=lambda c: not c["h"]["procesos_documentados"] and c["horas"] >= 5,
         por_que="Se pierden horas en tareas repetitivas que todavía no están documentadas: no se puede automatizar lo que no está escrito.",
         detalle=lambda c: f"Se dedican {c['horas']} horas semanales a tareas repetitivas. Se recomienda documentar primero los tres procesos principales en una página cada uno."),
    dict(id="R27", nec="FOR", prio=2, tag="criterio", fuente="Gestión del cambio",
         cond=lambda c: "resistencia" in c["barreras"],
         por_que="Se indicó resistencia del equipo: el cambio fracasa si las personas no participan.",
         detalle=lambda c: "Involucrar al equipo desde el inicio, comenzar con una sola herramienta y comunicar el primer resultado."),
    dict(id="R28", nec="EST", prio=1, tag="prudencia", fuente="Gradualidad en la inversión",
         cond=lambda c: "dinero" in c["barreras"],
         por_que="Se indicó falta de recursos económicos: Nexo prioriza opciones de costo cero antes que cualquier pago.",
         detalle=lambda c: "Comenzar por los peldaños 0 y 1 de la escalera de gasto; contratar un servicio de pago solo cuando lo gratuito resulte insuficiente."),
    dict(id="R29", nec="EST", prio=2, tag="criterio", fuente="Segunda opinión externa",
         cond=lambda c: "no_se" in c["barreras"],
         por_que="Se indicó dificultad para elegir herramientas: un autodiagnóstico externo ofrece una segunda opinión sin costo.",
         detalle=lambda c: "Realizar el Chequeo Digital de MinTIC (unos 25 minutos) y contrastar sus resultados con los de este diagnóstico."),
    dict(id="R30", nec="EST", prio=1, tag="criterio", fuente="Etapa de vida de la empresa",
         cond=lambda c: c["antig"] == "<2",
         por_que="La empresa es joven: los primeros años concentran el mayor riesgo, por lo que conviene cuidar la caja.",
         detalle=lambda c: "Priorizar lo que protege la caja y ordenar la información desde el inicio."),
    dict(id="R32", nec="SEG", prio=2, tag="criterio", fuente="Seguridad como barrera de adopción",
         cond=lambda c: "seguridad" in c["barreras"],
         por_que="Se indicó preocupación por seguridad y privacidad: es el mejor argumento para activar primero las medidas gratuitas.",
         detalle=lambda c: "Activar la verificación en dos pasos y la copia de seguridad antes de cargar datos de clientes en cualquier herramienta."),
    dict(id="R33", nec="CAJ", prio=2, tag="criterio", fuente="Cartera en ventas a empresas",
         cond=lambda c: c["canal"] == "b2b" and (_ind(c, "rotacion_deudores_dias") or 0) <= 45,
         por_que="Al vender a otras empresas, el plazo de cobro condiciona la caja.",
         detalle=lambda c: "Formalizar condiciones de pago por escrito, enviar recordatorios antes del vencimiento y revisar la cartera cada semana."),
    dict(id="R34", nec="SEG", prio=3, tag="normativo", fuente="Ley 1581 de 2012",
         cond=lambda c: c["canal"] in ("redes", "en_linea", "mixto") and not c["h"]["habeas_data"],
         por_que="Al vender por canales digitales se recogen datos personales con más frecuencia, y su tratamiento requiere autorización.",
         detalle=lambda c: "Incluir el aviso y la autorización de datos en el primer contacto (mensaje, formulario o pedido) y conservar la evidencia."),
    dict(id="R36", nec="AUT", prio=2, tag="criterio", fuente="Equipos pequeños",
         cond=lambda c: c["tam"] == "1-3" and c["horas"] >= 10,
         por_que="Con un equipo de 1 a 3 personas, cada hora en tareas repetitivas pesa mucho sobre el tiempo comercial.",
         detalle=lambda c: "Priorizar automatizaciones gratuitas (plantillas, respuestas rápidas, recordatorios) sobre cualquier sistema nuevo."),
    dict(id="R37", nec="CAJ", prio=3, tag="prudencia", fuente="Semáforo financiero",
         cond=lambda c: c["fin"]["semaforo"] is not None and c["fin"]["semaforo"]["nivel"] == 2,
         por_que="El semáforo financiero indica riesgo alto: no conviene adquirir compromisos recurrentes de tecnología.",
         detalle=lambda c: "Principal señal: " + c["fin"]["semaforo"]["razones"][0][1]),
    dict(id="R38", nec="DAT", prio=2, tag="criterio", fuente="Confiabilidad del diagnóstico",
         cond=lambda c: not c["fin"]["tiene_mov"] and c["h"]["registra_ventas"],
         por_que="Se declara que se registran las ventas, pero no se cargaron movimientos: el análisis financiero no pudo realizarse.",
         detalle=lambda c: "Al cargar los movimientos (aunque sea una hoja simple de ingresos y gastos) se habilitan el punto de equilibrio, los escenarios de caja y el presupuesto digital prudente."),
    dict(id="R39", nec="EST", prio=1, tag="criterio", fuente="Retorno de la inversión",
         cond=lambda c: c["ia"] == "paga" and not c["h"]["mide_resultados_digitales"],
         por_que="Se paga por herramientas de inteligencia artificial sin medir su retorno.",
         detalle=lambda c: "Definir un indicador (horas ahorradas o ventas atribuidas) y compararlo con el costo mensual del plan."),
]

# Información adicional por pregunta que usa el contexto de la empresa
def _qdet(c, key):
    ctx = c
    if key == "presencia_digital":
        return ("Como la venta se apoya en redes y mensajería, es el paso de mayor retorno." if ctx["canal"] == "redes"
                else "Para un negocio de venta principalmente presencial, la ficha en Google Maps suele traer clientes nuevos sin costo." if ctx["canal"] == "presencial"
                else "")
    if key == "pagos_digitales":
        return "Para ventas a otras empresas, aceptar transferencia con soporte de pago agiliza el cobro." if ctx["canal"] == "b2b" else ""
    if key == "factura_electronica" and c["fin"]["estados"]:
        return "Con ingresos anuales declarados en los estados financieros, formalizar la facturación es aún más relevante para sustentar esos ingresos."
    if key == "registra_ventas" and c["fin"]["tiene_mov"]:
        return "Los movimientos cargados en esta herramienta pueden servir como punto de partida del registro."
    if key == "inventario_registrado" and _ind(c, "razon_corriente") is not None and c["fin"]["estados"]["indicadores"].get("prueba_acida", 9) < 1:
        return "La prueba ácida indica dependencia del inventario para pagar deudas cercanas, lo que hace más importante controlarlo."
    if key == "backup_nube" and ctx["tam"] in ("4-10", "11-50"):
        return "Con varias personas accediendo a los archivos, una copia compartida y automática reduce el riesgo de pérdida."
    if key == "roles_claros" and ctx["tam"] in ("4-10", "11-50"):
        return f"Con un equipo de {preguntas_tam(ctx['tam'])}, la ausencia de roles claros genera tareas sin dueño."
    if key == "responsable_digital" and ctx["tam"] == "1-3":
        return "En equipos muy pequeños el responsable suele ser el propietario: lo importante es reservar tiempo semanal para el tema."
    if key == "crm":
        return "Una hoja de cálculo con última compra y próxima acción es suficiente para comenzar."
    return ""


def preguntas_tam(t):
    return TAMANOS.get(t, t).lower()


def reglas_preguntas(resp, ctx):
    """Una regla por cada pregunta respondida 'No' o 'En parte', salvo que falte un prerrequisito."""
    out = []
    for p in preguntas.PREGUNTAS:
        v = int(resp.get(p["key"], 0))
        if v == 2:
            continue
        if any(int(resp.get(r, 0)) < 2 for r in p["req"]):
            continue  # primero debe resolverse el prerrequisito
        prio = p["prio"] if v == 0 else max(1, p["prio"] - 1)
        det = ""
        try:
            det = _qdet(ctx, p["key"])
        except Exception:
            det = ""
        out.append(dict(id="Q:" + p["key"], key=p["key"], nec=p["nec"], prio=prio, tag="normativo" if p["norma"] else "criterio",
                        fuente=p["sec"], respuesta=v, texto=p["texto"], cond=None,
                        por_que=preguntas.lectura(p, v), detalle=det))
    return out


def evaluar(ctx):
    disparadas = []
    for r in REGLAS:
        try:
            ok = bool(r["cond"](ctx))
        except Exception:
            ok = False
        if ok:
            d = dict(r)
            try:
                d["detalle"] = r["detalle"](ctx)
            except Exception:
                d["detalle"] = ""
            disparadas.append(d)
    disparadas += reglas_preguntas(ctx["resp"], ctx)
    for d in disparadas:
        d["refs_ids"] = evidencia.refs_de(d["id"], ctx.get("semilla", ""))
    puntaje = {}
    for r in disparadas:
        puntaje[r["nec"]] = max(puntaje.get(r["nec"], 0), r["prio"])
    for n in list(puntaje):
        if n in PROBLEMAS.get(ctx["problema"], []):
            puntaje[n] += 1
    claves = list(NECESIDADES)
    orden = sorted(puntaje, key=lambda n: (-puntaje[n], claves.index(n)))
    disparadas.sort(key=lambda d: (-d["prio"], d["id"]))
    return orden, puntaje, disparadas


def opciones(nec, catalogo, h, presupuesto):
    cat = catalogo[catalogo["necesidad"].map(lambda s: nec in s.split(";"))].sort_values(["peldano", "id"])
    filas = []
    for r in cat.itertuples():
        omitir = [p for p in r.omitir_si.split(";") if p]
        if any(h.get(p, False) for p in omitir):
            continue  # ya lo resolvió: no se recomienda
        faltan = [p for p in r.prerrequisitos.split(";") if p and not h.get(p, False)]
        motivos = []
        if faltan:
            motivos.append("Faltan requisitos previos: " + "; ".join(HECHOS.get(p, EXTRA_REQ.get(p, p)).rstrip("?").strip("¿") for p in faltan))
        if r.peldano >= 2:
            if pd.isna(r.costo_cop_min):
                if presupuesto <= 0:
                    motivos.append("Costo por cotizar y sin presupuesto prudente disponible")
            elif r.costo_cop_min > presupuesto:
                motivos.append(f"Cuesta desde {core.cop(r.costo_cop_min)} al mes y el presupuesto prudente es {core.cop(presupuesto)}")
        filas.append(dict(id=r.id, nombre=r.nombre, peldano=r.peldano, tipo=r.tipo, costo=r.costo_texto,
                          descripcion=r.descripcion, advertencia=r.advertencia, url=r.fuente_url,
                          verificado=r.fecha_verificacion, confianza=r.confianza,
                          ok=not motivos, motivo="; ".join(motivos)))
    return filas


def no_compres_todavia(orden, catalogo, h, presupuesto):
    salida = []
    for nec in orden:
        for o in opciones(nec, catalogo, h, presupuesto):
            if o["peldano"] >= 2 and not o["ok"]:
                salida.append((NECESIDADES[nec], o["nombre"], o["motivo"]))
    return salida


def ruta(orden, catalogo, h, presupuesto, n=4):
    d30, d90 = [], []
    for nec in orden[:n]:
        ops = opciones(nec, catalogo, h, presupuesto)
        d30.append((NECESIDADES[nec], [o for o in ops if o["ok"] and o["peldano"] <= 1][:2]))
        sig = [o for o in ops if o["peldano"] >= 2]
        pos = [o for o in sig if o["ok"]]
        d90.append((NECESIDADES[nec], pos[0] if pos else None, sig[0]["motivo"] if (sig and not pos) else ""))
    return d30, d90


def informe_md(caso, orden, puntaje, disparadas, d30, d90, presupuesto, notas):
    L = [f"# Nexo Digital: informe de {caso or 'la empresa'}", f"Fecha: {date.today().isoformat()}", "",
         f"Presupuesto mensual prudente para lo digital: {core.cop(presupuesto)}", ""]
    L.append("## Contraste de las respuestas con los datos")
    L += [f"- {n}" for n in notas]
    L += ["", "## Prioridades"]
    for i, n in enumerate(orden[:6], 1):
        L.append(f"{i}. {NECESIDADES[n]} (prioridad {puntaje[n]})")
        for r in [r for r in disparadas if r["nec"] == n]:
            L.append(f"   - {r['por_que']} {r.get('detalle', '')}")
    L += ["", "## Próximos 30 días"]
    for nec, ops in d30:
        L.append(f"- {nec}: " + ("; ".join(f"{o['nombre']} ({o['costo']})" for o in ops) or "sin opción disponible"))
    L += ["", "## Días 31 a 90 (solo si lo anterior funcionó y resulta insuficiente)"]
    for nec, op, motivo in d90:
        L.append(f"- {nec}: " + (f"{op['nombre']} ({op['costo']})" if op else f"aún no. {motivo}" if motivo else "sin paso siguiente en el catálogo"))
    L += ["", "## Riesgos a vigilar"] + [f"- {t}. {nota}" for t, nota in RIESGOS]
    L += ["", "Nota: los precios y límites de las herramientas cambian; confirme en la página oficial antes de decidir."]
    return "\n".join(L)


def resultado_json(caso, orden, puntaje, resp, presupuesto, indice=None):
    return json.dumps(dict(caso=caso, fecha=date.today().isoformat(), top=orden[:3], prioridad=puntaje,
                           respuestas={k: int(v) for k, v in resp.items()}, presupuesto=presupuesto,
                           indice_preparacion=None if indice is None else round(indice["valor"], 1)),
                      ensure_ascii=False, indent=2)
