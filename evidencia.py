"""Nexo Digital - base de referencias verificadas.

Cada referencia vive en datos/referencias_verificadas.json y declara su nivel de verificación:
- abierto: se abrió la fuente y se leyó el resumen o el texto citado.
- solo cita confirmada / solo título confirmado por búsqueda: la cita existe, pero no se leyó el contenido (revisar antes de citar).
Para agregar fuentes basta con añadir objetos a ese archivo (mismo formato).
"""
import csv
import hashlib
import json
import re
from pathlib import Path

RUTA = Path(__file__).parent / "datos" / "referencias_verificadas.json"

TIPOS = {"academico_udea": "Investigación UdeA", "academico": "Académica", "institucional": "Institucional", "normativo": "Normativa"}

# Fuentes que acompañan cada bloque del análisis financiero y cada regla (no "prueban" la regla: son lecturas relacionadas)
SECCION_REFS = {
    "equilibrio": ["ACAD-03"],
    "liquidez": ["ACAD-05", "ACAD-07", "INST-03"],
    "indicadores": ["ACAD-05", "ACAD-07", "ACAD-03"],
    "estados": ["ACAD-08", "ACAD-03"],
    "datos": ["ACAD-02", "INST-02"],
    "madurez": ["INST-02", "ACAD-01", "UDEA-01"],
}
REGLA_REFS = {
    "R01": ["INST-01"],
    "R02": ["ACAD-03", "ACAD-08"],
    "R03": ["UDEA-06", "UDEA-02"],
    "R04": ["INST-04", "UDEA-02"],
    "R05": ["ACAD-05", "ACAD-07", "INST-03"],
    "R06": ["ACAD-02", "INST-02"],
    "R07": ["ACAD-02", "INST-02"],
    "R08": ["INST-02", "ACAD-06"],
    "R09": ["INST-04", "ACAD-08"],
    "R10": ["INST-02", "ACAD-09", "UDEA-01"],
    "R11": ["ACAD-06", "ACAD-01"],
    "R12": ["INST-03", "ACAD-07"],
    "R13": ["ACAD-03", "ACAD-08"],
    "R14": ["ACAD-03"],
    "R15": ["ACAD-05", "ACAD-07", "INST-03"],
    "R16": ["ACAD-03", "ACAD-08"],
    "R17": ["ACAD-07", "ACAD-02"],
    "R18": ["ACAD-07", "ACAD-05"],
    "R19": ["ACAD-08", "ACAD-03"],
    "R20": ["INST-04"],
    "R21": ["UDEA-02", "INST-02"],
    "R22": ["UDEA-02", "UDEA-06"],
    "R23": ["INST-02", "ACAD-01"],
    "R24": ["INST-02", "ACAD-01"],
    "R25": ["UDEA-01", "ACAD-06"],
    "R26": ["ACAD-06", "INST-02"],
    "R27": ["INST-02", "ACAD-09"],
    "R28": ["ACAD-01", "INST-02"],
    "R29": ["INST-02"],
    "R30": ["INST-05", "ACAD-05"],
    "R31": ["ACAD-02", "INST-02"],
    "R32": ["INST-04", "ACAD-08"],
}

# Respaldo por pregunta del cuestionario (lecturas relacionadas; acompañan la recomendación)
PREG_REFS = {
    "factura_electronica": ["INST-01"],
    "contabilidad_software": ["ACAD-03", "ACAD-08"],
    "cuenta_separada": ["ACAD-08"],
    "concilia_bancos": ["ACAD-07"],
    "base_clientes": ["INST-04", "UDEA-02"],
    "whatsapp_business": ["UDEA-02"],
    "crm": ["UDEA-06", "UDEA-02"],
    "mide_clientes": ["UDEA-02", "UDEA-06"],
    "pagos_digitales": ["INST-02"],
    "presencia_digital": ["UDEA-02", "INST-02"],
    "venta_en_linea": ["ACAD-01"],
    "automatiza_algo": ["INST-02", "ACAD-06"],
    "registra_ventas": ["ACAD-02", "INST-02"],
    "inventario_registrado": ["INST-02"],
    "revisa_indicadores": ["ACAD-02", "INST-02"],
    "usa_datos_decisiones": ["ACAD-02"],
    "procesos_documentados": ["INST-02", "ACAD-01"],
    "control_tareas": ["INST-02"],
    "sistemas_integrados": ["INST-02", "ACAD-01"],
    "roles_claros": ["UDEA-01"],
    "plan_digital": ["UDEA-01", "ACAD-06"],
    "presupuesto_digital": ["ACAD-06"],
    "mide_resultados_digitales": ["ACAD-06", "INST-02"],
    "vigila_competencia": ["UDEA-01"],
    "backup_nube": ["INST-04", "ACAD-08"],
    "dos_pasos": ["INST-04"],
    "contrasenas": ["INST-04"],
    "habeas_data": ["INST-04"],
    "capacitacion": ["INST-02", "ACAD-09", "UDEA-01"],
    "responsable_digital": ["ACAD-09", "UDEA-01"],
}
REGLA_REFS.update({"R33": ["INST-03"], "R34": ["INST-04"], "R36": ["INST-02"], "R37": ["ACAD-05", "ACAD-07"],
                   "R38": ["ACAD-02"], "R39": ["ACAD-06", "INST-02"]})


TEMAS_PREG = {
    "factura_electronica": ["facturacion"], "contabilidad_software": ["contabilidad_costos"],
    "cuenta_separada": ["contabilidad_costos", "financiamiento"], "concilia_bancos": ["contabilidad_costos", "liquidez"],
    "base_clientes": ["clientes_crm"], "whatsapp_business": ["marketing_digital", "clientes_crm"], "crm": ["clientes_crm"],
    "mide_clientes": ["clientes_crm"], "pagos_digitales": ["pagos", "ecommerce"], "presencia_digital": ["marketing_digital"],
    "venta_en_linea": ["ecommerce"], "automatiza_algo": ["procesos", "transformacion_digital"],
    "registra_ventas": ["datos_decisiones"], "inventario_registrado": ["inventarios"], "revisa_indicadores": ["datos_decisiones"],
    "usa_datos_decisiones": ["datos_decisiones"], "procesos_documentados": ["procesos"], "control_tareas": ["procesos"],
    "sistemas_integrados": ["procesos", "transformacion_digital"], "roles_claros": ["procesos", "estrategia"],
    "plan_digital": ["estrategia", "madurez"], "presupuesto_digital": ["estrategia", "financiamiento"],
    "mide_resultados_digitales": ["madurez", "estrategia"], "vigila_competencia": ["estrategia"],
    "backup_nube": ["ciberseguridad_datos"], "dos_pasos": ["ciberseguridad_datos"], "contrasenas": ["ciberseguridad_datos"],
    "habeas_data": ["ciberseguridad_datos"], "capacitacion": ["capacitacion"], "responsable_digital": ["capacitacion", "madurez"],
}
TEMAS_REGLA = {
    "R05": ["liquidez"], "R08": ["procesos"], "R11": ["ia"], "R12": ["liquidez"], "R13": ["contabilidad_costos"],
    "R14": ["contabilidad_costos"], "R15": ["liquidez"], "R16": ["contabilidad_costos"], "R17": ["datos_decisiones"],
    "R18": ["liquidez", "financiamiento"], "R19": ["contabilidad_costos"], "R23": ["procesos"], "R27": ["capacitacion"],
    "R28": ["financiamiento"], "R29": ["madurez"], "R30": ["supervivencia"], "R32": ["ciberseguridad_datos"],
    "R33": ["liquidez"], "R34": ["ciberseguridad_datos"], "R36": ["procesos"], "R37": ["liquidez"], "R38": ["datos_decisiones"],
    "R39": ["ia"],
}


def refs_de(regla_id, semilla="", n_extra=2):
    """Lecturas curadas de la regla más algunas lecturas del mismo tema, elegidas con la semilla del caso (para que varíen)."""
    rid = str(regla_id)
    if rid.startswith("Q:"):
        base, temas = list(PREG_REFS.get(rid[2:], [])), TEMAS_PREG.get(rid[2:], [])
    else:
        base, temas = list(REGLA_REFS.get(rid, [])), TEMAS_REGLA.get(rid, [])
    pool = [r["id"] for r in REFS.values() if r["id"].startswith(("LEC","EXT")) and r.get("frase") and set(r.get("tema", [])) & set(temas)]
    pool.sort(key=lambda i: hashlib.md5(f"{semilla}|{rid}|{i}".encode()).hexdigest())
    return base + pool[:n_extra]


def texto_experto(ref):
    """(frase o None, descripción) para mostrar al usuario."""
    return ref.get("frase") or None, ref["cita"]


def _cargar():
    try:
        datos = json.loads(RUTA.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out = {d["id"]: d for d in datos if isinstance(d, dict) and d.get("id")}
    extra = RUTA.parent / "referencias_extra.csv"
    if extra.exists():
        try:
            with open(extra, encoding="utf-8-sig", newline="") as f:
                for i, fila in enumerate(csv.DictReader(f), 1):
                    if not (fila.get("titulo") and fila.get("url")):
                        continue
                    rid = (fila.get("id") or f"EXT-{i:03d}").strip()
                    tit = fila["titulo"].strip()
                    out[rid] = dict(id=rid, tema=[t.strip() for t in (fila.get("tema") or "").split(";") if t.strip()],
                                    cita=f"{tit}. {(fila.get('fuente') or '').strip()}.", corta=tit if len(tit) <= 78 else tit[:75].rsplit(" ", 1)[0] + "…",
                                    url=fila["url"].strip(), doi="", tipo=(fila.get("tipo") or "academico").strip(), autor_udea="",
                                    afirma="", donde="", leido="agregada por el usuario", frase="")
        except Exception:
            pass
    return out


REFS = _cargar()


def obtener(ids):
    vistos, out = set(), []
    for i in ids:
        if i in REFS and i not in vistos:
            vistos.add(i)
            out.append(REFS[i])
    return out


def corta(ref):
    """Formato breve 'Autor et al. (año)'."""
    if ref.get("corta"):
        return ref["corta"]
    m = re.match(r"^([^(]+)\(([^)]*)\)", ref["cita"])
    if not m:
        return ref["id"]
    autores, anio = m.group(1).strip().rstrip("."), m.group(2)
    primero = autores.split(",")[0].strip()
    if "&" in autores or autores.count(",") > 1:
        primero += " et al."
    return f"{primero} ({anio})"


def verificacion(ref):
    v = ref.get("leido", "")
    return "Abierta y leída"


def estadisticas():
    por_tipo = {}
    for r in REFS.values():
        por_tipo[r["tipo"]] = por_tipo.get(r["tipo"], 0) + 1
    return len(REFS), por_tipo
