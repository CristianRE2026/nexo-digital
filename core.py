"""Radar de Caja - lógica de negocio (no depende de Streamlit)."""
import unicodedata
import warnings

import numpy as np
import pandas as pd

REQUERIDAS = ["fecha", "tipo", "categoria", "monto"]
TIPOS_INGRESO = {"ingreso", "ingresos", "venta", "ventas", "entrada", "entradas"}
TIPOS_GASTO = {"gasto", "gastos", "egreso", "egresos", "costo", "costos", "salida", "salidas"}
PALABRAS_NOMINA = ("nomina", "salario", "prestaciones", "seguridad social", "personal")


def _sin_tildes(texto):
    t = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in t if not unicodedata.combining(c)).strip().lower()


def _a_numero(v):
    """Convierte '$1.250.000', '1,250,000.50', '(500)' a número. Devuelve NaN si no puede."""
    if isinstance(v, (int, float, np.number)):
        return float(v)
    s = str(v).strip().replace("$", "").replace(" ", "")
    if not s:
        return np.nan
    negativo = s.startswith("-") or (s.startswith("(") and s.endswith(")"))
    s = s.strip("-()")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        partes = s.split(",")
        s = s.replace(",", "") if (len(partes) > 1 and len(partes[-1]) == 3) else s.replace(",", ".")
    elif s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[1]) == 3):
        s = s.replace(".", "")
    try:
        x = float(s)
    except ValueError:
        return np.nan
    return -x if negativo else x


def _parsear_fechas(serie):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fechas = pd.to_datetime(serie, errors="coerce", format="ISO8601")
        pendientes = fechas.isna() & serie.notna()
        if pendientes.any():
            fechas.loc[pendientes] = pd.to_datetime(serie[pendientes], errors="coerce", dayfirst=True)
    return fechas


def _normalizar_tipo(v):
    t = _sin_tildes(v)
    if t in TIPOS_INGRESO:
        return "ingreso"
    if t in TIPOS_GASTO:
        return "gasto"
    return np.nan


def leer_archivo(archivo):
    """Lee un CSV o Excel (acepta rutas o el archivo subido en Streamlit)."""
    nombre = getattr(archivo, "name", str(archivo)).lower()
    if nombre.endswith((".xlsx", ".xls")):
        return pd.read_excel(archivo)
    return pd.read_csv(archivo, sep=None, engine="python")  # detecta , o ;


def limpiar_datos(crudo):
    """Valida y limpia. Devuelve (DataFrame limpio, reporte de calidad)."""
    df = crudo.copy()
    df.columns = [_sin_tildes(c) for c in df.columns]
    faltan = [c for c in REQUERIDAS if c not in df.columns]
    if faltan:
        raise ValueError(
            f"Faltan estas columnas: {', '.join(faltan)}. "
            "El archivo debe tener: fecha, tipo, categoria, monto (y opcional: descripcion)."
        )
    if "descripcion" not in df.columns:
        df["descripcion"] = ""
    df = df.dropna(how="all").reset_index(drop=True)
    total = len(df)

    df["fecha"] = _parsear_fechas(df["fecha"])
    df["tipo"] = df["tipo"].map(_normalizar_tipo)
    df["monto"] = df["monto"].map(_a_numero)

    reporte = {
        "filas_totales": total,
        "fechas_invalidas": int(df["fecha"].isna().sum()),
        "tipos_invalidos": int(df["tipo"].isna().sum()),
        "montos_invalidos": int(df["monto"].isna().sum()),
        "montos_negativos": int((df["monto"] < 0).sum()),
    }
    valido = df["fecha"].notna() & df["tipo"].notna() & df["monto"].notna()
    df = df[valido].copy()
    df["monto"] = df["monto"].abs()
    df["categoria"] = (
        df["categoria"].fillna("Sin categoría").astype(str).str.replace(r"[<>&\"]", "", regex=True).str.strip().replace("", "Sin categoría")
    )
    df["descripcion"] = df["descripcion"].fillna("").astype(str)
    reporte["posibles_duplicados"] = int(
        df.duplicated(subset=["fecha", "tipo", "categoria", "monto"], keep="first").sum()
    )
    reporte["filas_validas"] = len(df)
    reporte["filas_descartadas"] = total - len(df)
    return df.sort_values("fecha").reset_index(drop=True), reporte


def mes_incompleto(df):
    """True si el último mes de datos parece incompleto (faltan más de 4 días)."""
    ultima = df["fecha"].max()
    return ultima.day < ultima.days_in_month - 4


def resumen_mensual(df):
    d = df.copy()
    d["mes"] = d["fecha"].dt.to_period("M")
    piv = d.pivot_table(index="mes", columns="tipo", values="monto", aggfunc="sum", fill_value=0.0)
    for c in ("ingreso", "gasto"):
        if c not in piv.columns:
            piv[c] = 0.0
    piv = piv.reindex(pd.period_range(piv.index.min(), piv.index.max(), freq="M"), fill_value=0.0)
    piv["neto"] = piv["ingreso"] - piv["gasto"]
    return piv[["ingreso", "gasto", "neto"]]


def porcentaje_nomina(df, meses=3):
    """Qué fracción de los gastos recientes corresponde a nómina/personal."""
    g = df[df["tipo"] == "gasto"].copy()
    g["mes"] = g["fecha"].dt.to_period("M")
    ultimos = sorted(g["mes"].unique())[-meses:]
    g = g[g["mes"].isin(ultimos)]
    if g["monto"].sum() == 0:
        return 0.0
    es_nomina = g["categoria"].map(lambda c: any(p in _sin_tildes(c) for p in PALABRAS_NOMINA))
    return float(g.loc[es_nomina, "monto"].sum() / g["monto"].sum())


def _tendencia(serie, meses, amortiguacion=0.5):
    """Promedio de los últimos 3 meses + media tendencia (método simple y explicable)."""
    y = serie.to_numpy(dtype=float)
    pendiente = np.polyfit(np.arange(len(y)), y, 1)[0] if len(y) >= 3 else 0.0
    nivel = y[-3:].mean()
    return np.maximum(nivel + pendiente * amortiguacion * np.arange(1, meses + 1), 0.0)


def proyectar(resumen, meses, saldo_inicial, var_ventas=0.0, var_gastos=0.0,
              alza_nomina=0.0, retraso_cobros=0.0, share_nomina=0.0, ventana=6):
    """Proyecta caja mensual. Los porcentajes se dan en % (ej. -10 = baja 10%)."""
    if len(resumen) < 3:
        raise ValueError("Se necesitan al menos 3 meses completos de datos para proyectar.")
    hist = resumen.tail(ventana)
    ing = _tendencia(hist["ingreso"], meses) * (1 + var_ventas / 100)
    gas_base = _tendencia(hist["gasto"], meses)
    gas = gas_base * ((1 - share_nomina) * (1 + var_gastos / 100) + share_nomina * (1 + alza_nomina / 100))
    p = retraso_cobros / 100  # parte de las ventas que ahora se cobra un mes tarde
    cobrado = ing * (1 - p) + np.concatenate(([0.0], ing[:-1])) * p
    idx = pd.period_range(resumen.index[-1] + 1, periods=meses, freq="M")
    out = pd.DataFrame({"ingreso": cobrado, "gasto": gas}, index=idx)
    out["neto"] = out["ingreso"] - out["gasto"]
    out["saldo"] = saldo_inicial + out["neto"].cumsum()
    return out


def mes_critico(proy):
    neg = proy[proy["saldo"] < 0]
    return str(neg.index[0]) if len(neg) else None


def anomalias_gastos(df, minimo_meses=4):
    """Categorías de gasto cuyo último mes se sale de su comportamiento normal."""
    g = df[df["tipo"] == "gasto"].copy()
    g["mes"] = g["fecha"].dt.to_period("M")
    piv = g.pivot_table(index="mes", columns="categoria", values="monto", aggfunc="sum", fill_value=0.0)
    if len(piv) < minimo_meses:
        return []
    ultimo, previo = piv.iloc[-1], piv.iloc[:-1].tail(6)
    salida = []
    for cat in piv.columns:
        media, desv = previo[cat].mean(), previo[cat].std(ddof=0)
        if media > 0 and ultimo[cat] > media * 1.25 and ultimo[cat] > media + 2 * desv:
            salida.append({"categoria": cat, "ultimo": float(ultimo[cat]),
                           "media": float(media), "pct": float(ultimo[cat] / media - 1)})
    return sorted(salida, key=lambda a: a["ultimo"] - a["media"], reverse=True)


def gastos_por_categoria(df, meses=3):
    g = df[df["tipo"] == "gasto"].copy()
    g["mes"] = g["fecha"].dt.to_period("M")
    g = g[g["mes"].isin(sorted(g["mes"].unique())[-meses:])]
    return g.groupby("categoria")["monto"].sum().sort_values(ascending=False)


def cop(x):
    """Formato de pesos colombianos: 1234567 -> $1.234.567"""
    signo = "-" if x < 0 else ""
    return f"{signo}${abs(x):,.0f}".replace(",", ".")


def diagnostico(resumen, proy, saldo_inicial, df):
    """Lista de alertas {nivel, titulo, detalle, accion}. nivel: rojo/amarillo/verde."""
    items = []
    u3 = resumen.tail(3)
    ing, gas = u3["ingreso"].sum(), u3["gasto"].sum()
    margen = (ing - gas) / ing if ing > 0 else 0.0

    critico = mes_critico(proy)
    if critico:
        items.append({"nivel": "rojo", "titulo": f"La caja se agota en {critico}",
                      "detalle": f"Con el saldo actual de {cop(saldo_inicial)} y este escenario, el saldo queda negativo.",
                      "accion": "Definir desde hoy cómo cubrir ese faltante: adelantar cobros, renegociar plazos con proveedores o gestionar una línea de liquidez antes de que llegue ese mes."})
    else:
        items.append({"nivel": "verde", "titulo": "La caja alcanza durante todo el horizonte",
                      "detalle": f"El saldo proyectado final es {cop(proy['saldo'].iloc[-1])}.",
                      "accion": "Mantener una reserva y revisar esta proyección cada mes."})

    if margen < 0:
        items.append({"nivel": "rojo", "titulo": "Los gastos superan a las ventas",
                      "detalle": f"Margen de caja de los últimos 3 meses: {margen:.1%}.",
                      "accion": "Identificar los dos gastos más grandes que se puedan reducir o ajustar los precios de los productos de menor margen."})
    elif margen < 0.05:
        items.append({"nivel": "amarillo", "titulo": "Margen de caja muy estrecho",
                      "detalle": f"Solo queda {margen:.1%} de cada peso vendido en los últimos 3 meses.",
                      "accion": "Cualquier retraso en cobros o alza de costos puede dejar a la empresa sin caja. Revisar precios y costos principales."})

    h = resumen.tail(6)
    if len(h) >= 4 and h["ingreso"].iloc[0] > 0 and h["gasto"].iloc[0] > 0:
        c_ing = h["ingreso"].iloc[-3:].mean() / h["ingreso"].iloc[:3].mean() - 1
        c_gas = h["gasto"].iloc[-3:].mean() / h["gasto"].iloc[:3].mean() - 1
        if c_gas > c_ing + 0.03:
            items.append({"nivel": "amarillo", "titulo": "Los gastos crecen más rápido que las ventas",
                          "detalle": f"Gastos {c_gas:+.1%} vs. ventas {c_ing:+.1%} frente a los 3 meses anteriores.",
                          "accion": "Revisar qué categorías explican el aumento antes de que se erosione el margen."})

    cats = gastos_por_categoria(df)
    if len(cats) and cats.sum() > 0 and cats.iloc[0] / cats.sum() > 0.40:
        items.append({"nivel": "amarillo", "titulo": f"Alta concentración de gasto en '{cats.index[0]}'",
                      "detalle": f"Representa {cats.iloc[0] / cats.sum():.0%} de los gastos recientes.",
                      "accion": "Negociar condiciones con ese proveedor o rubro y buscar alternativas para no depender de uno solo."})

    for a in anomalias_gastos(df)[:2]:
        items.append({"nivel": "amarillo", "titulo": f"Gasto atípico en '{a['categoria']}'",
                      "detalle": f"El último mes fue {cop(a['ultimo'])}, {a['pct']:+.0%} sobre su promedio ({cop(a['media'])}).",
                      "accion": "Verificar si fue un pago único o un error. Si se repite, ajustar la proyección."})
    return items


def texto_para_ia(resumen, proy, saldo_inicial, df, escenario):
    """Resumen agregado para el asistente de IA (no se envían filas individuales)."""
    u3 = resumen.tail(3)
    cats = gastos_por_categoria(df)
    top = ", ".join(f"{c}: {v / cats.sum():.0%}" for c, v in cats.head(5).items()) if len(cats) else "n/d"
    anom = "; ".join(f"{a['categoria']} ({a['pct']:+.0%})" for a in anomalias_gastos(df)) or "ninguna"
    return (
        "Datos agregados de una pyme colombiana (cifras en pesos colombianos, COP):\n"
        f"- Ingresos promedio mensual (últimos 3 meses): {cop(u3['ingreso'].mean())}\n"
        f"- Gastos promedio mensual (últimos 3 meses): {cop(u3['gasto'].mean())}\n"
        f"- Saldo de caja actual: {cop(saldo_inicial)}\n"
        f"- Participación de nómina en el gasto: {porcentaje_nomina(df):.0%}\n"
        f"- Principales rubros de gasto: {top}\n"
        f"- Gastos atípicos recientes: {anom}\n"
        f"- Escenario simulado: ventas {escenario['var_ventas']:+.0f}%, gastos no laborales {escenario['var_gastos']:+.0f}%, "
        f"nómina {escenario['alza_nomina']:+.0f}%, {escenario['retraso_cobros']:.0f}% de ventas cobradas un mes tarde\n"
        f"- Saldo proyectado final ({len(proy)} meses): {cop(proy['saldo'].iloc[-1])}\n"
        f"- Mes en que la caja se agota: {mes_critico(proy) or 'no se agota en el horizonte'}\n"
    )
