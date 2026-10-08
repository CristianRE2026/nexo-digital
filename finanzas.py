"""Análisis financiero de Nexo Digital (no depende de Streamlit).

Convierte movimientos y/o estados financieros en lectura de negocio: rentabilidad,
punto de equilibrio, resistencia de la caja ante choques, estacionalidad e indicadores
de estados financieros con su interpretación. Los umbrales son referencias generales de
análisis financiero (criterio experto); la comparación correcta es contra el sector.
"""
import numpy as np
import pandas as pd

import core
import nexo

MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
# Categorías que, por su nombre, suelen ser gastos fijos (estimación; no incluye impuestos ligados a ventas)
FIJOS_KEYS = ("nomina", "salario", "prestacion", "seguridad social", "arriendo", "alquiler", "servicios publicos",
              "credito", "prestamo", "cuota", "interes", "seguro", "contador", "software", "suscripcion", "licencia")

ESCENARIOS = [
    ("Base (sin cambios)", {}),
    ("Ventas -10 %", dict(var_ventas=-10)),
    ("Cobros tardíos (20 % de las ventas se cobra un mes después)", dict(retraso_cobros=20)),
    ("Gastos no laborales +10 %", dict(var_gastos=10)),
    ("Nómina +10 %", dict(alza_nomina=10)),
    ("Combinado: ventas -10 %, cobros tardíos 20 %, nómina +10 %", dict(var_ventas=-10, retraso_cobros=20, alza_nomina=10)),
]

NOMBRES_IND = {
    "razon_corriente": "Razón corriente (veces)",
    "prueba_acida": "Prueba ácida (veces)",
    "capital_trabajo": "Capital de trabajo (COP)",
    "endeudamiento": "Endeudamiento (%)",
    "margen_operacional": "Margen operacional (%)",
    "margen_neto": "Margen neto (%)",
    "rotacion_deudores_dias": "Rotación de deudores (días)",
    "roa": "Rentabilidad del activo, ROA (%)",
    "roe": "Rentabilidad del patrimonio, ROE (%)",
}
DEFINICIONES = {
    "razon_corriente": "Activo corriente / pasivo corriente",
    "prueba_acida": "(Activo corriente - inventarios) / pasivo corriente",
    "capital_trabajo": "Activo corriente - pasivo corriente",
    "endeudamiento": "Pasivo total / activo total",
    "margen_operacional": "Utilidad operacional / ingresos",
    "margen_neto": "Utilidad neta / ingresos",
    "rotacion_deudores_dias": "Cuentas por cobrar / ingresos x 365",
    "roa": "Utilidad neta / activo total",
    "roe": "Utilidad neta / patrimonio",
}


# ------------------------------------------------------------------ Movimientos
def preparar(df):
    """Excluye el último mes si parece incompleto. Devuelve (df_an, aviso, resumen mensual)."""
    aviso = ""
    df_an = df
    if core.mes_incompleto(df):
        ultimo = df["fecha"].max().to_period("M")
        df_an = df[df["fecha"].dt.to_period("M") != ultimo]
        aviso = f"El último mes de datos ({ultimo}) parece incompleto y se excluyó del análisis."
    return df_an, aviso, core.resumen_mensual(df_an)


def indicadores_mov(resumen, df_an, saldo):
    u3 = resumen.tail(3)
    ing, gas = float(u3["ingreso"].mean()), float(u3["gasto"].mean())
    out = dict(meses_datos=len(resumen), ingreso_prom=ing, gasto_prom=gas, neto_prom=ing - gas,
               margen=(ing - gas) / ing if ing > 0 else 0.0,
               cobertura_meses=saldo / gas if gas > 0 else None,
               share_nomina=core.porcentaje_nomina(df_an), crec_ingresos=None, crec_gastos=None)
    if len(resumen) >= 6:
        prev = resumen.iloc[-6:-3]
        if prev["ingreso"].mean() > 0:
            out["crec_ingresos"] = float(u3["ingreso"].mean() / prev["ingreso"].mean() - 1)
        if prev["gasto"].mean() > 0:
            out["crec_gastos"] = float(u3["gasto"].mean() / prev["gasto"].mean() - 1)
    ult12 = resumen.tail(12)
    out["meses_en_rojo"] = int((ult12["neto"] < 0).sum())
    out["meses_considerados"] = len(ult12)
    m = float(ult12["ingreso"].mean())
    out["volatilidad"] = float(ult12["ingreso"].std(ddof=0) / m) if (m > 0 and len(ult12) >= 3) else None
    return out


def es_fijo(categoria):
    t = core._sin_tildes(categoria)
    return any(k in t for k in FIJOS_KEYS)


def punto_equilibrio(df_an, meses=3):
    """Análisis costo-volumen-utilidad con la clasificación fijo/variable estimada por nombre de categoría."""
    periodos = sorted(df_an["fecha"].dt.to_period("M").unique())[-meses:]
    d = df_an[df_an["fecha"].dt.to_period("M").isin(periodos)]
    n = max(len(periodos), 1)
    ing = float(d.loc[d["tipo"] == "ingreso", "monto"].sum()) / n
    g = d[d["tipo"] == "gasto"].groupby("categoria")["monto"].sum() / n
    fijos_cat = [c for c in g.index if es_fijo(c)]
    fijos = float(g[fijos_cat].sum()) if fijos_cat else 0.0
    variables = float(g.sum() - fijos)
    mc = 1 - variables / ing if ing > 0 else None
    pe = fijos / mc if (mc is not None and mc > 0) else None
    return dict(ingreso=ing, fijos=fijos, variables=variables, margen_contribucion=mc,
                ventas_equilibrio=pe, holgura=(ing - pe) / ing if (pe is not None and ing > 0) else None,
                categorias_fijas=fijos_cat)


def composicion_gastos(df_an, meses=3):
    s = core.gastos_por_categoria(df_an, meses)
    if s.empty or s.sum() <= 0:
        return pd.DataFrame(columns=["categoria", "monto_mensual", "participacion", "acumulado"]), {}
    tot = float(s.sum())
    t = pd.DataFrame({"categoria": s.index, "monto_mensual": s.values / meses})
    t["participacion"] = s.values / tot
    t["acumulado"] = t["participacion"].cumsum()
    conc = dict(top1=float(t["participacion"].iloc[0]), top1_nombre=str(t["categoria"].iloc[0]),
                top3=float(t["participacion"].head(3).sum()), hhi=float((t["participacion"] ** 2).sum()))
    return t, conc


def escenarios(resumen, saldo, share, meses=6):
    filas, proys = [], {}
    for nombre, kw in ESCENARIOS:
        p = core.proyectar(resumen, meses, saldo, share_nomina=share, **kw)
        proys[nombre] = p
        filas.append(dict(escenario=nombre, saldo_final=float(p["saldo"].iloc[-1]),
                          saldo_minimo=float(p["saldo"].min()), mes_critico=core.mes_critico(p) or "No se agota"))
    base = proys[ESCENARIOS[0][0]]
    sens = [dict(factor=n, impacto=float(proys[n]["saldo"].iloc[-1] - base["saldo"].iloc[-1]))
            for n, _ in ESCENARIOS[1:5]]
    return dict(tabla=pd.DataFrame(filas), proyecciones=proys, base=base,
                sensibilidad=pd.DataFrame(sens).sort_values("impacto").reset_index(drop=True))


def estacionalidad(resumen):
    if len(resumen) < 12:
        return None
    d = resumen.copy()
    d["mes"] = [p.month for p in d.index]
    idx = d.groupby("mes")["ingreso"].mean()
    if idx.mean() <= 0:
        return None
    idx = idx / idx.mean()
    nombres = [MESES_ES[m - 1] for m in idx.index]
    serie = pd.Series(idx.values, index=nombres)
    return dict(indice=serie, pico=list(serie.sort_values(ascending=False).head(2).index),
                valle=list(serie.sort_values().head(2).index), amplitud=float(serie.max() - serie.min()),
                preliminar=len(resumen) < 24)


# ------------------------------------------------------------------ Estados financieros
def _nivel(clave, v):
    if clave == "razon_corriente":
        if v >= 1.5:
            return "verde", "Cubre con holgura sus deudas de corto plazo."
        if v >= 1.0:
            return "amarillo", "Cubre sus deudas de corto plazo, pero con poco margen."
        return "rojo", "Los activos de corto plazo no alcanzan para las deudas de corto plazo."
    if clave == "prueba_acida":
        if v >= 1.0:
            return "verde", "Puede pagar sus deudas cercanas sin depender de vender inventario."
        if v >= 0.7:
            return "amarillo", "Depende en parte de vender inventario para pagar sus deudas cercanas."
        return "rojo", "Depende fuertemente de vender inventario para pagar sus deudas cercanas."
    if clave == "capital_trabajo":
        return ("verde", "Los recursos de corto plazo superan las obligaciones de corto plazo.") if v > 0 else \
               ("rojo", "Las obligaciones de corto plazo superan los recursos de corto plazo.")
    if clave == "endeudamiento":
        if v <= 50:
            return "verde", "Menos de la mitad de los activos está financiada con deuda."
        if v <= 70:
            return "amarillo", "Una parte importante de los activos está financiada con deuda."
        return "rojo", "Los activos dependen mucho de la deuda; poca capacidad de absorber un mal año."
    if clave in ("margen_operacional", "margen_neto"):
        if v < 0:
            return "rojo", "La operación pierde dinero: los costos y gastos superan los ingresos."
        if v < 5:
            return "amarillo", "Margen estrecho: cualquier alza de costos o caída de ventas lo elimina."
        return "verde", "Margen positivo; compárelo con el de su sector para saber si es competitivo."
    if clave == "rotacion_deudores_dias":
        if v <= 45:
            return "verde", "Cobra en plazos razonables."
        if v <= 90:
            return "amarillo", "Tarda en cobrar; parte de la caja queda atrapada en cartera."
        return "rojo", "Cobra muy lento; la cartera consume la caja."
    return "info", "Indicador informativo; interprételo junto con los demás."


def _clasificar_vs_ref(clave, v, ref):
    if ref is None or pd.isna(ref):
        return ""
    peor_si_mayor = clave in ("endeudamiento", "rotacion_deudores_dias")
    if abs(v - ref) <= 0.05 * abs(ref):
        return "En línea con el sector."
    mejor = (v < ref) if peor_si_mayor else (v > ref)
    return "Mejor que el sector." if mejor else "Peor que el sector."


def analisis_estados(e, ref=None):
    """e: diccionario con los 9 campos anuales. ref: fila con referencias del sector (opcional)."""
    ind = nexo.indicadores_estados(e)
    pat = e["activo_total"] - e["pasivo_total"]
    ind["capital_trabajo"] = e["activo_corriente"] - e["pasivo_corriente"]
    if e["activo_total"] > 0:
        ind["roa"] = e["utilidad_neta"] / e["activo_total"] * 100
    if pat > 0:
        ind["roe"] = e["utilidad_neta"] / pat * 100
    items = []
    for clave in NOMBRES_IND:
        if clave not in ind:
            continue
        v = float(ind[clave])
        nivel, lectura = _nivel(clave, v)
        r = None
        if ref is not None:
            try:
                r = ref.get(clave) if hasattr(ref, "get") else None
                r = None if (r is None or pd.isna(r)) else float(r)
            except Exception:
                r = None
        items.append(dict(clave=clave, nombre=NOMBRES_IND[clave], definicion=DEFINICIONES[clave], valor=v,
                          nivel=nivel, lectura=lectura, referencia=r,
                          vs_sector=_clasificar_vs_ref(clave, v, r) if r is not None else ""))
    dupont = None
    if e["ingresos"] > 0 and e["activo_total"] > 0 and pat > 0:
        mn = e["utilidad_neta"] / e["ingresos"]
        rot = e["ingresos"] / e["activo_total"]
        mult = e["activo_total"] / pat
        dupont = dict(margen_neto=mn * 100, rotacion_activos=rot, multiplicador=mult, roe=mn * rot * mult * 100)
    return dict(indicadores=ind, items=items, dupont=dupont, patrimonio=pat)


def consistencia(resumen, estados):
    """Compara los ingresos de los últimos 12 meses de movimientos con los del estado de resultados."""
    if resumen is None or len(resumen) < 12 or estados is None or estados["ingresos"] <= 0:
        return None
    m12 = float(resumen.tail(12)["ingreso"].sum())
    dif = m12 / estados["ingresos"] - 1
    return dict(ingresos_mov=m12, ingresos_estados=float(estados["ingresos"]), diferencia=float(dif),
                coincide=abs(dif) <= 0.15)


# ------------------------------------------------------------------ Semáforo y conjunto
def semaforo(mov, esc, est):
    """Devuelve dict(nivel 0-2, etiqueta, razones) o None si no hay datos."""
    if mov is None and est is None:
        return None
    nivel, razones = 0, []

    def sube(n, txt):
        nonlocal nivel
        nivel = max(nivel, n)
        razones.append(("rojo" if n == 2 else "amarillo", txt))

    if mov is not None:
        if esc is not None:
            t = esc["tabla"]
            base_crit, comb_crit = t.iloc[0]["mes_critico"], t.iloc[-1]["mes_critico"]
            if base_crit != "No se agota":
                sube(2, f"Sin cambios en el negocio, la caja se agota en {base_crit}.")
            elif comb_crit != "No se agota":
                sube(1, f"Un escenario adverso combinado agotaría la caja en {comb_crit}.")
        if mov["margen"] < 0:
            sube(2, f"Margen de caja negativo ({mov['margen']:.1%}): se gasta más de lo que se vende.")
        elif mov["margen"] < 0.05:
            sube(1, f"Margen de caja muy estrecho ({mov['margen']:.1%}).")
        if mov["cobertura_meses"] is not None and mov["cobertura_meses"] < 1:
            sube(1, f"El saldo de caja equivale a {mov['cobertura_meses']:.1f} meses de gastos (menos de uno).")
        cg, ci = mov.get("crec_gastos"), mov.get("crec_ingresos")
        if cg is not None and ci is not None and cg > ci + 0.03:
            sube(1, f"Los gastos crecen más rápido que las ventas ({cg:+.1%} frente a {ci:+.1%}).")
    if est is not None:
        for it in est["items"]:
            if it["nivel"] == "rojo":
                sube(2, f"{it['nombre']}: {it['lectura']}")
            elif it["nivel"] == "amarillo":
                sube(1, f"{it['nombre']}: {it['lectura']}")
    etiqueta = ["Estable", "Atención", "Riesgo alto"][nivel]
    if not razones:
        razones.append(("verde", "No se detectan señales de alerta con los datos entregados."))
    return dict(nivel=nivel, etiqueta=etiqueta, razones=razones)


def analizar_financiero(df, saldo, estados, ref=None):
    """df: movimientos limpios o None. estados: dict con 9 campos o None. Devuelve el análisis completo."""
    fin = dict(tiene_mov=df is not None, tiene_estados=estados is not None, aviso="", resumen=None, mov=None,
               equilibrio=None, categorias=None, concentracion={}, anomalias=[], escenarios=None, error_proy="",
               estacionalidad=None, alertas=[], estados=None, consistencia=None, cap=None, semaforo=None)
    df_an = None
    if df is not None:
        df_an, fin["aviso"], resumen = preparar(df)
        fin["resumen"] = resumen
        fin["mov"] = indicadores_mov(resumen, df_an, saldo)
        fin["equilibrio"] = punto_equilibrio(df_an)
        fin["categorias"], fin["concentracion"] = composicion_gastos(df_an)
        fin["anomalias"] = core.anomalias_gastos(df_an)
        fin["estacionalidad"] = estacionalidad(resumen)
        try:
            fin["escenarios"] = escenarios(resumen, saldo, fin["mov"]["share_nomina"])
            fin["alertas"] = core.diagnostico(resumen, fin["escenarios"]["base"], saldo, df_an)
        except ValueError as ex:
            fin["error_proy"] = str(ex)
        fin["cap"] = nexo.capacidad_inversion(resumen, saldo)
    if estados is not None:
        fin["estados"] = analisis_estados(estados, ref)
        fin["consistencia"] = consistencia(fin["resumen"], estados)
        if fin["cap"] is None:
            fin["cap"] = nexo.capacidad_desde_estados(estados, saldo)
    fin["semaforo"] = semaforo(fin["mov"], fin["escenarios"], fin["estados"])
    return fin
