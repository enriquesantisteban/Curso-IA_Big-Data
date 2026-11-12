from datetime import date

import altair as alt
import streamlit as st

from facturas_db import inicializar_base_datos, obtener_clientes, obtener_facturas


inicializar_base_datos()
facturas = obtener_facturas()
clientes = obtener_clientes()


def total_factura(factura: dict[str, object]) -> float:
    total = 0.0
    for articulo in factura["articulos"]:
        base = round(int(articulo["cantidad"]) * float(articulo["precio"]), 2)
        impuesto = round(base * float(articulo["iva"]) / 100, 2)
        total += base + impuesto
    return round(total, 2)


def formato_euros(importe: float) -> str:
    return f"{importe:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


generadas = [factura for factura in facturas if factura["estado"] == "Generada"]
en_preparacion = [factura for factura in facturas if factura["estado"] == "Pendiente"]
pagadas = [factura for factura in generadas if factura.get("estado_pago") == "Pagado"]
pendientes_pago = [factura for factura in generadas if factura.get("estado_pago", "Pendiente") == "Pendiente"]
vencidas = [factura for factura in generadas if factura.get("estado_pago") == "Vencido"]
facturacion_total = sum(total_factura(factura) for factura in generadas)

st.title("Panel de control")
st.caption(f"LGNE PROXY · Resumen de gestión · {date.today().strftime('%d/%m/%Y')}")

metricas = st.columns(5, gap="small")
metricas[0].metric("Clientes", f"{len(clientes):,}", help="Clientes registrados.", border=True)
metricas[1].metric("Facturación", formato_euros(facturacion_total), help="Suma de las facturas generadas, con IVA.", border=True)
metricas[2].metric("Pagadas", len(pagadas), help="Facturas con estado pagado.", border=True)
metricas[3].metric("Pendientes", len(pendientes_pago), help="Facturas pendientes de pago.", border=True)
metricas[4].metric("Vencidas", len(vencidas), help="Facturas marcadas como vencidas.", border=True)
if en_preparacion:
    st.caption(f"Además, tienes {len(en_preparacion)} factura(s) en preparación, aún sin generar.")

columna_grafica, columna_estado = st.columns([1.2, 1], gap="medium")
with columna_grafica:
    with st.container(border=True):
        st.subheader("Facturación mensual")
        hoy = date.today()
        cursor = date(hoy.year, hoy.month, 1)
        meses = []
        nombres_meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        for _ in range(12):
            meses.append({"clave": cursor.strftime("%Y-%m"), "Mes": f"{nombres_meses[cursor.month - 1]} {str(cursor.year)[-2:]}", "Facturación (€)": 0.0})
            cursor = date(cursor.year - 1, 12, 1) if cursor.month == 1 else date(cursor.year, cursor.month - 1, 1)
        meses.reverse()
        importes_mes = {mes["clave"]: mes for mes in meses}
        for factura in generadas:
            clave = str(factura["fecha"])[:7]
            if clave in importes_mes:
                importes_mes[clave]["Facturación (€)"] += total_factura(factura)
        chart_meses = (
            alt.Chart(alt.Data(values=meses))
            .mark_bar(color="#3182e8", cornerRadiusTopLeft=5, cornerRadiusTopRight=5, size=24)
            .encode(
                x=alt.X("Mes:N", sort=[mes["Mes"] for mes in meses], title=None, axis=alt.Axis(labelAngle=0, labelFontSize=10, tickSize=0)),
                y=alt.Y("Facturación (€):Q", title=None, scale=alt.Scale(domainMin=0), axis=alt.Axis(grid=True, gridColor="#edf1f6", format="~s")),
                tooltip=[alt.Tooltip("Mes:N", title="Mes"), alt.Tooltip("Facturación (€):Q", title="Facturación", format=",.2f")],
            )
            .properties(height=245)
            .configure(
                background="#ffffff",
                view=alt.ViewConfig(fill="#ffffff"),
                axis=alt.AxisConfig(labelColor="#263d54", titleColor="#263d54", gridColor="#e5edf4"),
            )
        )
        st.altair_chart(chart_meses, width="stretch", alt="Facturación mensual de los últimos doce meses.")

with columna_estado:
    with st.container(border=True):
        st.subheader("Estado de documentos")
        estados = [
            {"Estado": "Pagadas", "Cantidad": len(pagadas)},
            {"Estado": "Pendientes", "Cantidad": len(pendientes_pago)},
            {"Estado": "Vencidas", "Cantidad": len(vencidas)},
        ]
        if generadas:
            chart_estado = (
                alt.Chart(alt.Data(values=estados))
                .mark_arc(innerRadius=62, outerRadius=91, cornerRadius=5)
                .encode(
                    theta=alt.Theta("Cantidad:Q"),
                    color=alt.Color("Estado:N", scale=alt.Scale(domain=["Pagadas", "Pendientes", "Vencidas"], range=["#41b883", "#3182e8", "#ef6a62"]), legend=None),
                    tooltip=[alt.Tooltip("Estado:N"), alt.Tooltip("Cantidad:Q", title="Facturas")],
                )
                .properties(width=245, height=205)
                .configure(background="#ffffff", view=alt.ViewConfig(fill="#ffffff"))
            )
            hueco_izq, centro_grafica, hueco_der = st.columns([1, 3, 1], gap="small")
            with centro_grafica:
                st.altair_chart(chart_estado, width="content", alt="Proporción de facturas pagadas, pendientes y vencidas.")
            st.markdown(
                "<div style='display:flex;justify-content:center;gap:18px;flex-wrap:wrap;"
                "font-size:14px;font-weight:650;color:#243b52'>"
                f"<span><b style='color:#218e67'>●</b> Pagadas: {len(pagadas)}</span>"
                f"<span><b style='color:#2878d0'>●</b> Pendientes: {len(pendientes_pago)}</span>"
                f"<span><b style='color:#d64f48'>●</b> Vencidas: {len(vencidas)}</span>"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("Cuando generes facturas, aquí verás su estado de pago.")

columna_clientes, columna_catalogo, columna_actividad = st.columns([1.35, 1, 1.3], gap="medium")
with columna_clientes:
    with st.container(border=True, height=370):
        st.subheader("Directorio de clientes")
        if clientes:
            for cliente in clientes[:6]:
                st.markdown(f"**{cliente['nombre']}**")
                st.caption(f"{int(cliente['codigo']):05d} · {cliente['cif']} · {cliente['ciudad'] or 'Sin ciudad'}")
                st.divider()
            if len(clientes) > 6:
                st.page_link("app_pages/clientes.py", label=f"Ver los {len(clientes)} clientes", icon=":material/groups:")
        else:
            st.info("Todavía no hay clientes registrados.")
            st.page_link("app_pages/clientes.py", label="Dar de alta un cliente", icon=":material/person_add:")

with columna_catalogo:
    with st.container(border=True, height=370):
        st.subheader("Artículos y servicios")
        conceptos = {}
        unidades_totales = 0
        for factura in facturas:
            for articulo in factura["articulos"]:
                nombre = str(articulo["concepto"])
                conceptos[nombre] = conceptos.get(nombre, 0) + int(articulo["cantidad"])
                unidades_totales += int(articulo["cantidad"])
        st.metric("Conceptos registrados", len(conceptos))
        st.metric("Unidades facturadas", unidades_totales)
        if conceptos:
            st.caption("Más recientes en tus facturas")
            for nombre, unidades in sorted(conceptos.items(), key=lambda item: item[1], reverse=True)[:4]:
                st.markdown(f"**{nombre}** · {unidades} uds.")
        else:
            st.caption("Los conceptos aparecerán aquí al guardar facturas.")
        st.page_link("app_pages/introducir_datos.py", label="Introducir datos", icon=":material/add_circle:")

with columna_actividad:
    with st.container(border=True, height=370):
        st.subheader("Actividad reciente")
        if facturas:
            for factura in facturas[:6]:
                estado = str(factura.get("estado_pago", "Pendiente")) if factura["estado"] == "Generada" else "En preparación"
                importe = total_factura(factura)
                st.markdown(f"**Factura {factura['numero_factura']}** · {factura['cliente']}")
                st.caption(f"{date.fromisoformat(str(factura['fecha'])).strftime('%d/%m/%Y')} · {estado} · {formato_euros(importe)}")
                st.divider()
            st.page_link("app_pages/informes.py", label="Ver informes y facturas", icon=":material/arrow_forward:")
        else:
            st.info("La actividad de facturación aparecerá aquí.")
            st.page_link("app_pages/introducir_datos.py", label="Crear la primera factura", icon=":material/add:")
