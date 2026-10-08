"""Nexo Digital - herramientas concretas por necesidad (programas, páginas y servicios que resuelven cada frente).

tipo: gratuito | gratuito con límites | por transacción | de pago. Las condiciones cambian: se recomienda confirmarlas en el sitio oficial.
"""
G, L, T, P = "Gratuito", "Gratuito con límites", "Comisión por transacción", "De pago"

HERRAMIENTAS = {
    "FAC": [
        ("Facturación electrónica gratuita de la DIAN", G, "Expedir factura electrónica válida sin costo, con límites de volumen.", "https://www.dian.gov.co"),
        ("Alegra", P, "Facturación y contabilidad en la nube, pensada para pymes de Colombia.", "https://www.alegra.com/colombia/"),
        ("Siigo", P, "Facturación, contabilidad, nómina y punto de venta en un mismo programa.", "https://www.siigo.com"),
    ],
    "CON": [
        ("Google Sheets o Excel con plantilla de ingresos y gastos", G, "Primer registro ordenado, sin gasto nuevo.", "https://sheets.google.com"),
        ("Odoo Community", G, "Programa de código abierto con módulo contable; requiere apoyo técnico para instalarlo.", "https://www.odoo.com"),
        ("ERPNext", G, "Programa de código abierto de gestión con contabilidad e inventario.", "https://erpnext.com"),
        ("Alegra", P, "Contabilidad en la nube con informes y conciliación bancaria.", "https://www.alegra.com/colombia/"),
        ("Siigo", P, "Contabilidad completa con nómina y punto de venta.", "https://www.siigo.com"),
    ],
    "CLI": [
        ("WhatsApp Business", G, "Catálogo, respuestas rápidas y etiquetas para ordenar a los clientes.", "https://business.whatsapp.com"),
        ("HubSpot CRM", L, "Registro de clientes y seguimiento de ventas con plan gratuito.", "https://www.hubspot.com/products/crm"),
        ("Zoho CRM", L, "Gestión de clientes y oportunidades; tiene edición gratuita para pocos usuarios.", "https://www.zoho.com/crm/"),
        ("Google Forms", G, "Encuesta breve de satisfacción y recompra.", "https://forms.google.com"),
    ],
    "CAJ": [
        ("Google Sheets o Excel (hoja de caja semanal)", G, "Saldo proyectado a ocho semanas y fechas de cobro.", "https://sheets.google.com"),
        ("Proyección de caja de Nexo", G, "Escenarios de caja a seis meses con los movimientos de la empresa.", ""),
        ("Alegra", P, "Cuentas por cobrar y por pagar con recordatorios.", "https://www.alegra.com/colombia/"),
    ],
    "DAT": [
        ("Google Sheets o Excel con tablas dinámicas", G, "Registro de ventas e inventario y un panel simple.", "https://sheets.google.com"),
        ("Looker Studio", G, "Paneles de indicadores conectados a hojas de cálculo.", "https://lookerstudio.google.com"),
        ("Power BI Desktop", G, "Análisis y paneles en el computador; requiere Windows.", "https://powerbi.microsoft.com"),
    ],
    "AUT": [
        ("Formularios, plantillas y recordatorios de Sheets, Excel o correo", G, "Automatizar lo repetitivo sin programas nuevos.", "https://workspace.google.com"),
        ("Make", L, "Conecta aplicaciones y automatiza tareas sin programar.", "https://www.make.com"),
        ("Zapier", L, "Automatiza tareas entre aplicaciones sin programar.", "https://zapier.com"),
        ("n8n", G, "Automatización de código abierto que puede alojarse en servidor propio.", "https://n8n.io"),
        ("Tidio", L, "Chatbot y chat en vivo para sitio web y redes, con plan gratuito.", "https://www.tidio.com"),
        ("ManyChat", L, "Chatbots para Instagram, Messenger y WhatsApp con plan gratuito.", "https://manychat.com"),
        ("Botpress", L, "Creación de agentes conversacionales con inteligencia artificial.", "https://botpress.com"),
    ],
    "SEG": [
        ("Bitwarden", G, "Gestor de contraseñas con plan gratuito.", "https://bitwarden.com"),
        ("Verificación en dos pasos de Google o Microsoft", G, "Protege correo y cuentas con un segundo paso.", "https://myaccount.google.com/security"),
        ("Google Drive o OneDrive", L, "Copia de seguridad en la nube de los archivos clave.", "https://drive.google.com"),
        ("Superintendencia de Industria y Comercio (datos personales)", G, "Guías y formatos del tratamiento de datos personales, Ley 1581 de 2012.", "https://www.sic.gov.co"),
    ],
    "FOR": [
        ("Chequeo Digital de MinTIC", G, "Autodiagnóstico gratuito de madurez digital de la empresa.", "https://www.mintic.gov.co"),
        ("HubSpot Academy", G, "Cursos gratuitos de marketing, ventas y servicio al cliente.", "https://academy.hubspot.com"),
        ("Google Skillshop y Actívate", G, "Cursos gratuitos de herramientas digitales y publicidad.", "https://skillshop.withgoogle.com"),
        ("Laboratorio Financiero de la Universidad de Antioquia", G, "Acompañamiento universitario a empresas que se acercan a la Facultad.", ""),
    ],
    "IA": [
        ("ChatGPT, Gemini o Claude (versión gratuita)", L, "Redactar mensajes, resumir documentos y preparar ideas con revisión humana.", "https://claude.ai"),
        ("Microsoft Copilot", L, "Asistente de inteligencia artificial integrado con Office y el navegador.", "https://copilot.microsoft.com"),
        ("NotebookLM", L, "Consulta y resume documentos propios con citas a la fuente.", "https://notebooklm.google"),
    ],
    "PRO": [
        ("Trello", L, "Tablero de tareas por proceso y responsable.", "https://trello.com"),
        ("Notion", L, "Documentar procesos y organizar tareas en un solo lugar.", "https://www.notion.com"),
        ("Google Tasks y Calendar", G, "Tareas y recordatorios con fecha para el equipo.", "https://calendar.google.com"),
        ("Odoo o ERPNext", G, "Integrar ventas, inventario y contabilidad cuando el equipo ya tenga procesos definidos.", "https://www.odoo.com"),
    ],
    "EST": [
        ("Chequeo Digital de MinTIC", G, "Punto de partida para el plan digital.", "https://www.mintic.gov.co"),
        ("Centros de Transformación Digital Empresarial", G, "Programas públicos de acompañamiento a pymes (MinTIC e iNNpulsa).", "https://innpulsacolombia.com"),
        ("Google Sheets o Notion", G, "Plan digital de una página y tablero de tres a cinco indicadores.", "https://sheets.google.com"),
    ],
    "CAN": [
        ("Google Business Profile", G, "Ficha gratuita en Google Maps con horarios, fotos y catálogo.", "https://www.google.com/business/"),
        ("Instagram o Facebook (perfil comercial)", G, "Vitrina con catálogo y mensajes directos.", "https://business.facebook.com"),
        ("Wompi", T, "Enlace y botón de pago con tarjeta, PSE y otros medios; cobra comisión por venta.", "https://wompi.com"),
        ("Bold", T, "Datáfono y link de pago; cobra comisión por venta.", "https://bold.co"),
        ("ePayco", T, "Pasarela de pagos en línea para tiendas y cobros recurrentes.", "https://www.epayco.com"),
        ("WooCommerce", G, "Tienda en línea de código abierto sobre WordPress; el alojamiento tiene costo.", "https://woocommerce.com"),
        ("Tiendanube o Shopify", P, "Tienda en línea lista para usar con mensualidad.", "https://www.tiendanube.com"),
    ],
}


def herramientas_para(orden, presupuesto, h=None, n=6, semilla=""):
    """Herramientas concretas de los n frentes prioritarios. Sin presupuesto prudente solo se ofrecen gratuitas o con plan gratuito."""
    h = h or {}
    filas = []
    for nec in orden[:n]:
        for nombre, tipo, para, url in HERRAMIENTAS.get(nec, []):
            if presupuesto <= 0 and tipo in (P,):
                continue
            filas.append(dict(nec=nec, nombre=nombre, tipo=tipo, para=para, url=url))
    return filas
