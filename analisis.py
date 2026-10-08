"""Nexo Digital - orquestador: une el análisis financiero con las reglas de transformación digital."""
from datetime import date

import core
import evidencia
import finanzas
import narrativa
import herramientas
import nexo


def analizar(caso, df, saldo, estados, resp, problema, ia, horas, catalogo, ref=None, sector="", contexto=None):
    """Devuelve un diccionario único con todo lo que muestran la pantalla y los informes.

    resp: {clave de pregunta: 0 (No) | 1 (En parte) | 2 (Sí)}; estados: dict de 9 campos o None; df: movimientos limpios o None.
    """
    contexto = contexto or {}
    resp = {k: int(resp.get(k, 0)) for k in nexo.HECHOS}
    fin = finanzas.analizar_financiero(df, saldo, estados, ref)
    h = nexo.hechos_desde_respuestas(resp)
    hx = nexo.hechos_extendidos(h, ia)
    cap = fin["cap"]
    ctx = dict(semilla=str(caso), h=hx, resp=resp, cap=cap, horas=horas, ia=ia, problema=problema, fin=fin, tam=contexto.get("tam", ""),
               antig=contexto.get("antig", ""), canal=contexto.get("canal", ""), barreras=list(contexto.get("barreras", [])))
    orden, puntaje, disparadas = nexo.evaluar(ctx)
    presupuesto = cap["presupuesto"] if cap else 0.0
    sw = nexo.detectar_software(df)
    notas = nexo.verificar(h, df, sw)
    d30, d90 = nexo.ruta(orden, catalogo, hx, presupuesto)
    nct = nexo.no_compres_todavia(orden, catalogo, hx, presupuesto)
    ops = {n: nexo.opciones(n, catalogo, hx, presupuesto) for n in orden[:6]}
    if cap and df is not None:
        confianza = "Media: hay movimientos financieros que contrastan las respuestas."
    elif cap:
        confianza = "Media-baja: solo estados financieros, sin movimientos."
    else:
        confianza = "Baja: sin datos financieros; el análisis se basa solo en las respuestas."
    r = dict(caso=caso or "Empresa sin nombre", fecha=date.today().isoformat(), sector=sector, saldo=saldo,
             problema=problema, ia=ia, horas=horas, resp=resp, h=h, fin=fin, perfil=nexo.perfil(resp),
             orden=orden, puntaje=puntaje, disparadas=disparadas, presupuesto=presupuesto, notas=notas,
             d30=d30, d90=d90, nct=nct, ops=ops, confianza=confianza, cap=cap, df_reporte=None, contexto=contexto)
    r["herramientas"] = herramientas.herramientas_para(orden, presupuesto, hx)
    r["indice"] = nexo.indice_preparacion(resp)
    r["matriz"] = nexo.matriz_estrategica(fin["semaforo"], r["indice"])
    r["resumen_ejecutivo"] = resumen_ejecutivo(r)
    r["lectura_fin"] = narrativa.lectura_financiera(fin, saldo)
    r["palancas"] = narrativa.palancas(fin)
    r["cartera_10"] = narrativa.liberacion_cartera(estados)
    r["perfil_empresa"] = narrativa.perfil_empresa(r)
    r["dimensiones"] = narrativa.lectura_dimensiones(r)
    r["lectura_preguntas"] = narrativa.lectura_preguntas(r)
    r["seguimiento"] = narrativa.seguimiento(r)
    r["agenda"] = narrativa.agenda(r)
    r["conclusion"] = narrativa.conclusion(r)
    return r


def resumen_ejecutivo(r):
    """Mensajes que una persona ocupada debe leer: semáforo, prioridades, presupuesto, primer paso y alerta."""
    fin, sem = r["fin"], r["fin"]["semaforo"]
    top = []
    for n in r["orden"][:3]:
        rs = [x for x in r["disparadas"] if x["nec"] == n]
        top.append((nexo.NECESIDADES[n], (rs[0]["por_que"] + " " + rs[0].get("detalle", "")).strip() if rs else ""))
    primer = ""
    for nec, ops in r["d30"]:
        if ops:
            primer = f"{nec}: {ops[0]['nombre']} ({ops[0]['costo']})."
            break
    alerta = ""
    graves = [a for a in fin["alertas"] if a["nivel"] != "verde"]
    if graves:
        a = graves[0]
        alerta = f"{a['titulo']}. {a['accion']}"
    elif sem and sem["razones"] and sem["nivel"] > 0:
        alerta = sem["razones"][0][1]
    if r["cap"] is None:
        pres = "No es posible estimarlo sin datos financieros; se asume cero."
    elif r["presupuesto"] <= 0:
        pres = "$0: la caja o el margen todavía no permiten asumir gastos nuevos."
    else:
        pres = core.cop(r["presupuesto"]) + " al mes (regla prudente)."
    return dict(indice=r["indice"], matriz=r["matriz"], semaforo=sem, prioridades=top, presupuesto=pres,
                primer_paso=primer, alerta=alerta)
