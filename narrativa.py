"""Nexo Digital - redacción del análisis a partir de los resultados de cada empresa.

Todo el texto depende de los datos y las respuestas del caso: dos empresas distintas obtienen
informes distintos. No depende de Streamlit.
"""
import core
import nexo
import preguntas

# ------------------------------------------------------------------ Contenido por necesidad
NEC_INFO = {
    "FAC": dict(objetivo="Facturar electrónicamente el 100 % de las ventas obligadas.",
                indicador="Porcentaje de ventas con factura electrónica", meta="100 % al día 30",
                error="Habilitarse tarde y emitir facturas manuales mientras tanto."),
    "CON": dict(objetivo="Conocer el costo y la rentabilidad reales con registros ordenados y separados del dinero personal.",
                indicador="Cierre contable mensual completado", meta="Primer cierre mensual al día 45",
                error="Comprar un software contable sin haber ordenado antes los registros."),
    "CLI": dict(objetivo="Tener una base de clientes viva, con seguimiento y medición de recompra.",
                indicador="Porcentaje de clientes que compra de nuevo en 90 días", meta="Línea base al día 30 y mejora de 5 puntos al día 90",
                error="Adquirir un CRM antes de tener una base ordenada."),
    "CAJ": dict(objetivo="Proteger la caja: cobrar a tiempo, conciliar y anticipar faltantes.",
                indicador="Días de cartera y cobertura de caja en meses", meta="Cobertura de caja de al menos un mes de gastos",
                error="Asumir cuotas recurrentes sin saber cuántos meses de gastos cubre la caja."),
    "DAT": dict(objetivo="Registrar ventas e inventario y usar tres o cuatro indicadores para decidir.",
                indicador="Número de decisiones al mes apoyadas en un dato", meta="Una decisión mensual con dato desde el día 60",
                error="Construir tableros sofisticados con datos incompletos."),
    "AUT": dict(objetivo="Liberar horas de trabajo repetitivo sin sacrificar control.",
                indicador="Horas semanales en tareas administrativas repetitivas", meta="Reducción de 20 % en 90 días",
                error="Automatizar un proceso que todavía no está definido."),
    "SEG": dict(objetivo="Evitar la pérdida de información y cumplir con el tratamiento de datos personales.",
                indicador="Cuentas críticas con verificación en dos pasos y copia de seguridad vigente", meta="100 % de cuentas críticas al día 30",
                error="Guardar datos de clientes sin autorización ni respaldo."),
    "FOR": dict(objetivo="Contar con una persona responsable y con formación mínima en herramientas digitales.",
                indicador="Horas de formación por persona al trimestre", meta="Responsable designado al día 15",
                error="Comprar herramientas sin que nadie las adopte."),
    "IA": dict(objetivo="Probar la inteligencia artificial en tareas de bajo riesgo.",
               indicador="Horas ahorradas por semana con IA", meta="Una tarea piloto al día 30",
               error="Pagar un plan antes de tener casos de uso claros."),
    "PRO": dict(objetivo="Documentar los procesos principales y organizar el seguimiento del trabajo.",
                indicador="Procesos documentados y tareas con responsable y fecha", meta="Tres procesos documentados al día 45",
                error="Intentar integrar sistemas sin procesos definidos."),
    "EST": dict(objetivo="Dirigir lo digital con un plan, un presupuesto y una medida de éxito.",
                indicador="Plan digital de una página aprobado y revisado cada trimestre", meta="Plan escrito al día 30",
                error="Tomar decisiones de tecnología una a una, sin criterio común."),
    "CAN": dict(objetivo="Ser fácil de encontrar, contactar y pagar.",
                indicador="Consultas y pedidos recibidos por canal digital al mes", meta="Línea base al día 30 y crecimiento sostenido",
                error="Abrir una tienda en línea sin haber validado la demanda por mensajería."),
}

TXT_TAM = {
    "1-3": "Un equipo de 1 a 3 personas permite decidir rápido, pero cada hora de gestión compite con el tiempo comercial. Conviene priorizar soluciones gratuitas, simples y de implementación inmediata.",
    "4-10": "Un equipo de 4 a 10 personas necesita coordinación explícita: roles claros, tareas visibles y una persona responsable de lo digital marcan la diferencia.",
    "11-50": "Con 11 a 50 personas, la informalidad se vuelve costosa: procesos documentados, integración de sistemas y control de accesos pasan a ser condiciones de crecimiento ordenado.",
}
TXT_ANT = {
    "<2": "Al ser una empresa joven, la prioridad es proteger la caja y ordenar la información desde el inicio; cada compra recurrente debe justificarse con un resultado esperado.",
    "2-5": "Con entre 2 y 5 años de operación, la empresa suele estar en el punto en que la informalidad inicial empieza a frenar el crecimiento; es buen momento para formalizar procesos y datos.",
    ">5": "Con más de 5 años de operación, la empresa tiene historia suficiente para analizar tendencias y estacionalidad, y la oportunidad principal está en modernizar procesos que se hacen igual desde el inicio.",
}
TXT_CANAL = {
    "presencial": "La venta principalmente presencial hace que la presencia en internet y el pago digital sean los primeros pasos de bajo costo para captar clientes nuevos.",
    "redes": "La venta por WhatsApp y redes sociales exige orden en el catálogo, tiempos de respuesta y registro de pedidos; además implica recoger datos personales que requieren autorización.",
    "en_linea": "La venta en línea hace que la disponibilidad, la seguridad de los datos y la integración entre pedidos, inventario y contabilidad sean críticas.",
    "b2b": "La venta a otras empresas hace que la facturación oportuna, los plazos de pago y el seguimiento de cartera determinen la caja.",
    "mixto": "Al combinar varios canales, el riesgo principal es la dispersión de la información: ventas, clientes e inventario deben consolidarse en un solo lugar.",
}
TXT_BARRERA = {
    "dinero": "La falta de recursos económicos hace que la escalera de gasto comience en cero: se priorizan procesos sin tecnología y herramientas gratuitas.",
    "tiempo": "La falta de tiempo recomienda acciones cortas y de alto impacto, y asignar bloques fijos semanales (por ejemplo, dos horas) a lo digital.",
    "conocimiento": "La falta de conocimiento se atiende con formación gratuita y acompañamiento externo antes de cualquier compra.",
    "seguridad": "La preocupación por la seguridad es una razón válida para activar primero las medidas básicas gratuitas y revisar las condiciones de cada herramienta.",
    "no_se": "La dificultad para elegir herramientas se reduce con un criterio común: elegir la opción gratuita que cubra la necesidad y evaluar pagos solo después de un uso real.",
    "resistencia": "La resistencia del equipo se trabaja involucrando a las personas desde el diseño, comenzando con una sola herramienta y comunicando resultados tempranos.",
}
TXT_PROBLEMA = {
    "No tengo claro por dónde empezar": "Al no existir un problema dominante, el orden de prioridades se define únicamente por las brechas y por la situación financiera.",
}


def _cop(x):
    return core.cop(x)


# ------------------------------------------------------------------ Perfil de la empresa
def perfil_empresa(r):
    c = r.get("contexto") or {}
    P = []
    partes = []
    if c.get("tam"):
        partes.append(nexo.TAMANOS[c["tam"]].lower())
    if c.get("antig"):
        partes.append(nexo.ANTIGUEDAD[c["antig"]].lower() + " de antigüedad")
    if c.get("canal"):
        cn = nexo.CANALES[c["canal"]]
        partes.append("canal de venta: " + cn[0].lower() + cn[1:])
    if partes:
        P.append(("Caracterización", "La empresa cuenta con " + ", ".join(partes) + "."))
    for k, d in (("tam", TXT_TAM), ("antig", TXT_ANT), ("canal", TXT_CANAL)):
        if c.get(k) in d:
            P.append(("Implicación", d[c[k]]))
    for b in c.get("barreras", []):
        if b in TXT_BARRERA:
            P.append((nexo.BARRERAS[b], TXT_BARRERA[b]))
    pr = r.get("problema", "")
    if pr in TXT_PROBLEMA:
        P.append(("Problema principal", TXT_PROBLEMA[pr]))
    elif pr:
        nec = [nexo.NECESIDADES[n] for n in nexo.PROBLEMAS.get(pr, [])]
        P.append(("Problema principal", f"El problema señalado ('{pr}') eleva la prioridad de: {', '.join(nec)}."))
    return P


# ------------------------------------------------------------------ Lectura financiera
def lectura_financiera(fin, saldo):
    """Lista de (título, texto) con las cifras de la empresa."""
    L = []
    mov, eq, est, cat = fin["mov"], fin["equilibrio"], fin["estados"], fin["categorias"]
    if mov:
        ing, gas, neto = mov["ingreso_prom"], mov["gasto_prom"], mov["neto_prom"]
        t = (f"En los últimos tres meses analizados, la empresa registró ingresos promedio de {_cop(ing)} y gastos promedio de {_cop(gas)} por mes, "
             f"lo que deja un resultado de caja de {_cop(neto)} mensuales y un margen de {mov['margen']:.1%}. ")
        if mov["margen"] < 0:
            t += "El negocio está gastando más de lo que ingresa; mientras esto ocurra, cada compra de tecnología se financia con caja acumulada."
        elif mov["margen"] < 0.05:
            t += "El margen es muy estrecho: un retraso de cobros o un alza de costos puede eliminarlo."
        elif mov["margen"] < 0.15:
            t += "El margen es positivo pero moderado; hay espacio para mejorar con control de costos y precios."
        else:
            t += "El margen es holgado, lo que da espacio para invertir con método."
        L.append(("Resultado de caja", t))
        cob = mov["cobertura_meses"]
        if cob is not None:
            tt = f"El saldo de caja ({_cop(saldo)}) cubre {cob:.1f} meses de gastos. "
            tt += ("Está por debajo del colchón mínimo de un mes, por lo que se recomienda aplazar compromisos recurrentes." if cob < nexo.MESES_COLCHON_MIN
                   else "Cumple el colchón mínimo de un mes." if cob < 3
                   else "Supera tres meses de gastos, una posición cómoda para absorber imprevistos.")
            L.append(("Colchón de caja", tt))
        if mov["meses_en_rojo"]:
            L.append(("Regularidad", f"En {mov['meses_en_rojo']} de los últimos {mov['meses_considerados']} meses los gastos superaron a los ingresos."))
        else:
            L.append(("Regularidad", f"En ninguno de los últimos {mov['meses_considerados']} meses los gastos superaron a los ingresos."))
        if mov.get("volatilidad") is not None:
            v = mov["volatilidad"]
            L.append(("Estabilidad de los ingresos", f"La variación mensual de los ingresos es de {v:.0%} respecto a su promedio. "
                      + ("Es alta: conviene planear caja por temporada." if v > 0.30 else "Es moderada." if v > 0.15 else "Es baja: los ingresos son estables.")))
        if mov.get("crec_ingresos") is not None and mov.get("crec_gastos") is not None:
            L.append(("Tendencia reciente", f"Frente al trimestre anterior, los ingresos varían {mov['crec_ingresos']:+.1%} y los gastos {mov['crec_gastos']:+.1%}. "
                      + ("Los gastos crecen más rápido que las ventas." if mov["crec_gastos"] > mov["crec_ingresos"] + 0.03
                         else "Las ventas crecen al menos al ritmo de los gastos.")))
    if eq and eq.get("ventas_equilibrio"):
        h = eq["holgura"]
        t = (f"Con los gastos fijos estimados ({_cop(eq['fijos'])}) y un margen de contribución de {eq['margen_contribucion']:.1%}, "
             f"el punto de equilibrio está en ventas de {_cop(eq['ventas_equilibrio'])} al mes. ")
        if h is not None:
            t += (f"Las ventas actuales superan ese punto en {h:.1%}: ese es el margen de seguridad frente a una caída de ventas." if h >= 0
                  else f"Las ventas actuales están {abs(h):.1%} por debajo del punto de equilibrio.")
        L.append(("Punto de equilibrio", t))
    if cat is not None and len(cat) and fin["concentracion"]:
        cn = fin["concentracion"]
        t = (f"El rubro principal de gasto es '{cn['top1_nombre']}', con {cn['top1']:.0%} del total; las tres categorías mayores suman {cn['top3']:.0%}. ")
        t += ("Esta concentración es alta y hace que un solo proveedor o rubro condicione la rentabilidad." if cn["top1"] > 0.40
              else "La concentración es moderada.")
        L.append(("Estructura de gastos", t))
    esc = fin["escenarios"]
    if esc:
        tab = esc["tabla"]
        crit = tab[tab["mes_critico"] != "No se agota"]
        if crit.empty:
            t = "En ninguno de los escenarios evaluados la caja se agota durante los seis meses proyectados. "
        else:
            nombres = "; ".join(f"{str(x['escenario']).split(' (')[0]} (mes {x['mes_critico']})" for _, x in crit.iterrows())
            t = f"La caja se agotaría en los siguientes escenarios: {nombres}. "
        sens = esc["sensibilidad"]
        peor = sens.iloc[0]
        t += f"El choque que más afecta el saldo final es '{str(peor['factor']).split(' (')[0]}', con un efecto de {_cop(peor['impacto'])}."
        L.append(("Resistencia de la caja", t))
    est_s = fin["estacionalidad"]
    if est_s:
        L.append(("Estacionalidad", f"Los meses de ingresos más altos son {', '.join(est_s['pico'])} y los más bajos {', '.join(est_s['valle'])}; "
                  f"la diferencia entre el mejor y el peor mes es de {est_s['amplitud']:.0%} del promedio."
                  + (" Con menos de 24 meses de datos la lectura es preliminar." if est_s["preliminar"] else "")))
    if est:
        ind = est["indicadores"]
        partes = []
        if "margen_neto" in ind:
            partes.append(f"margen neto de {ind['margen_neto']:.1f} %")
        if "razon_corriente" in ind:
            partes.append(f"razón corriente de {ind['razon_corriente']:.2f}")
        if "endeudamiento" in ind:
            partes.append(f"endeudamiento de {ind['endeudamiento']:.0f} %")
        if "rotacion_deudores_dias" in ind:
            partes.append(f"rotación de deudores de {ind['rotacion_deudores_dias']:.0f} días")
        rojos = [i["nombre"] for i in est["items"] if i["nivel"] == "rojo"]
        amar = [i["nombre"] for i in est["items"] if i["nivel"] == "amarillo"]
        t = "Los estados financieros muestran " + ", ".join(partes) + ". "
        if rojos:
            t += "Indicadores en zona de riesgo: " + ", ".join(rojos) + ". "
        if amar:
            t += "Indicadores en zona de atención: " + ", ".join(amar) + ". "
        if not rojos and not amar:
            t += "Ningún indicador está en zona de riesgo o de atención."
        L.append(("Estados financieros", t.strip()))
        dp = est.get("dupont")
        if dp:
            motor = max([("margen", dp["margen_neto"] / 10), ("rotación de activos", dp["rotacion_activos"]), ("apalancamiento", dp["multiplicador"] / 2)], key=lambda x: x[1])[0]
            L.append(("Origen de la rentabilidad (DuPont)", f"El ROE de {dp['roe']:.1f} % resulta de un margen neto de {dp['margen_neto']:.1f} %, "
                      f"una rotación de activos de {dp['rotacion_activos']:.2f} veces y un multiplicador de capital de {dp['multiplicador']:.2f}. "
                      f"Los tres factores se pueden mejorar de forma distinta: precios y costos (margen), uso de los activos (rotación) y estructura de deuda (apalancamiento)."))
    con = fin["consistencia"]
    if con:
        L.append(("Consistencia entre fuentes", f"Los ingresos de los últimos 12 meses en los movimientos ({_cop(con['ingresos_mov'])}) frente a los del estado de resultados "
                  f"({_cop(con['ingresos_estados'])}) difieren en {con['diferencia']:+.1%}. "
                  + ("La coincidencia es razonable." if con["coincide"] else "La diferencia es grande: conviene revisar qué fuente está incompleta.")))
    if not L:
        L.append(("Sin datos financieros", "No se cargaron movimientos ni estados financieros. El diagnóstico se basa únicamente en las respuestas del cuestionario; "
                  "al cargar datos se habilitan el semáforo financiero, el punto de equilibrio, los escenarios de caja y el presupuesto prudente."))
    return L


def palancas(fin):
    """Mejoras cuantificadas con las cifras de la empresa (ejercicios de sensibilidad, no promesas)."""
    out = []
    mov, cat = fin["mov"], fin["categorias"]
    if mov and mov["ingreso_prom"] > 0:
        ing, gas = mov["ingreso_prom"], mov["gasto_prom"]
        if cat is not None and len(cat):
            top = cat.iloc[0]
            ahorro = float(top["monto_mensual"]) * 0.10
            out.append(dict(nombre=f"Reducir 10 % el gasto en '{top['categoria']}'", mensual=ahorro, anual=ahorro * 12,
                            lectura=f"Equivale a {ahorro / ing:.1%} de los ingresos mensuales."))
        pr = ing * 0.03
        out.append(dict(nombre="Aumentar 3 % los precios sin perder clientes", mensual=pr, anual=pr * 12,
                        lectura=f"Aumenta el margen de caja en cerca de {pr / ing:.1%} de los ingresos, si el volumen se mantiene."))
        if gas > 0:
            red = gas * 0.05
            out.append(dict(nombre="Reducir 5 % el total de gastos", mensual=red, anual=red * 12,
                            lectura=f"Equivale a {red / ing:.1%} de los ingresos mensuales."))
    return out


def liberacion_cartera(estados):
    """Caja liberada por cada 10 días menos de cartera (usa los estados financieros)."""
    if not estados or estados.get("ingresos", 0) <= 0:
        return None
    return estados["ingresos"] / 365 * 10


# ------------------------------------------------------------------ Lectura de las dimensiones y de las preguntas
def lectura_dimensiones(r):
    resp = r["resp"]
    out = []
    por = preguntas.por_seccion()
    for sec, d in r["indice"]["detalle"].items():
        info = preguntas.SECCIONES[sec]
        pct = d["pct"]
        texto = info["bajo"] if pct < 34 else info["medio"] if pct < 67 else info["alto"]
        fort = [p["si"] for p in por[sec] if int(resp.get(p["key"], 0)) == 2]
        brechas = [preguntas.lectura(p, int(resp.get(p["key"], 0))) for p in por[sec] if int(resp.get(p["key"], 0)) < 2]
        out.append(dict(seccion=sec, pct=pct, banda=d["banda"], puntos=d["puntos"], maximo=d["maximo"], texto=texto,
                        fortalezas=fort, brechas=brechas))
    return out


def lectura_preguntas(r):
    out = []
    resp = r["resp"]
    for p in preguntas.PREGUNTAS:
        v = int(resp.get(p["key"], 0))
        out.append(dict(seccion=p["sec"], pregunta=p["texto"], respuesta=preguntas.RESP[v], lectura=preguntas.lectura(p, v)))
    return out


# ------------------------------------------------------------------ Seguimiento y agenda
def seguimiento(r, n=5):
    out = []
    for nec in r["orden"][:n]:
        i = NEC_INFO.get(nec)
        if i:
            out.append(dict(necesidad=nexo.NECESIDADES[nec], **i))
    return out


def agenda(r):
    """Agenda de 90 días construida con las prioridades del caso."""
    orden = r["orden"]
    disp = r["disparadas"]

    def acc(nec, k=2):
        rs = [x for x in disp if x["nec"] == nec and x["id"].startswith("Q:")]
        return [x["por_que"].split(". ")[-1].strip().rstrip(".") for x in rs[:k]]

    ag = []
    if orden:
        ag.append(("Semanas 1 y 2", f"Frente prioritario: {nexo.NECESIDADES[orden[0]]}.", acc(orden[0], 3)))
    if len(orden) > 1:
        ag.append(("Semanas 3 y 4", f"Segundo frente: {nexo.NECESIDADES[orden[1]]}.", acc(orden[1], 2)))
    if len(orden) > 2:
        ag.append(("Mes 2", f"Tercer frente: {nexo.NECESIDADES[orden[2]]}.", acc(orden[2], 2)))
    ag.append(("Mes 3", "Revisión y decisión sobre inversiones.",
               ["Medir los indicadores de seguimiento de cada frente.", "Decidir si alguna herramienta de pago se justifica con los resultados obtenidos.",
                "Repetir este diagnóstico y comparar el índice de preparación."]))
    return ag


# ------------------------------------------------------------------ Conclusión del caso
def conclusion(r):
    """Párrafo de cierre que combina semáforo, índice, matriz, prioridades y presupuesto."""
    fin, ind, mat, sem = r["fin"], r["indice"], r["matriz"], r["fin"]["semaforo"]
    P = []
    s = f"{r['caso']} obtiene un índice de preparación digital de {ind['valor']:.0f} sobre 100 (nivel {ind['banda'].lower()})"
    mejor = max(ind["detalle"].items(), key=lambda kv: kv[1]["pct"])
    peor = min(ind["detalle"].items(), key=lambda kv: kv[1]["pct"])
    if abs(mejor[1]["pct"] - peor[1]["pct"]) < 1:
        s += f". Todas las secciones se encuentran en un nivel similar ({mejor[1]['pct']:.0f} %)."
    else:
        s += f". Su sección más fuerte es {mejor[0].lower()} ({mejor[1]['pct']:.0f} %) y la más débil, {peor[0].lower()} ({peor[1]['pct']:.0f} %)."
    P.append(s)
    if sem:
        P.append(f"La situación financiera se clasifica como '{sem['etiqueta']}'. " + sem["razones"][0][1])
    if mat:
        P.append(f"El cruce entre capacidad financiera y preparación digital sugiere la estrategia '{mat['nombre']}'. {mat['texto']}")
    if r["orden"]:
        P.append("Las prioridades, en orden, son: " + "; ".join(nexo.NECESIDADES[n] for n in r["orden"][:3]) + ".")
    if r["cap"] is None:
        P.append("Al no contar con datos financieros, no se estimó un presupuesto digital; hasta tenerlo se recomienda limitar las acciones a las que no tienen costo.")
    elif r["presupuesto"] <= 0:
        P.append("La caja y el margen actuales no permiten asumir gastos digitales nuevos: la ruta recomendada es de costo cero.")
    else:
        P.append(f"El presupuesto digital prudente es de {_cop(r['presupuesto'])} al mes, con la regla de comprometer como máximo "
                 f"{nexo.PRUDENCIA_EXCEDENTE:.0%} del excedente mensual.")
    return P
