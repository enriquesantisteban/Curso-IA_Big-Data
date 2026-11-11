import re

import altair as alt
import streamlit as st

from facturas_db import inicializar_base_datos, obtener_facturas
from pdf_factura import generar_pdf_factura

inicializar_base_datos()

st.title("Informes")
st.write("Resumen de las facturas generadas y registradas.")

facturas = obtener_facturas("Generada")
if not facturas:
    st.info("Todavía no hay facturas generadas.")
else:
    registros = []
    total_acumulado = 0.0
    facturacion_por_cliente = {}
    for factura in facturas:
        articulos = factura["articulos"]
        unidades = sum(int(articulo["cantidad"]) for articulo in articulos)
        subtotal = sum(
            round(int(articulo["cantidad"]) * float(articulo["precio"]), 2)
            for articulo in articulos
        )
        importe_iva = sum(
            round(
                round(int(articulo["cantidad"]) * float(articulo["precio"]), 2)
                * float(articulo["iva"])
                / 100,
                2,
            )
            for articulo in articulos
        )
        total = subtotal + importe_iva
        identificador_cliente = (
            str(factura["cif"]).strip().casefold()
            or str(factura["cliente"]).strip().casefold()
        )
        if identificador_cliente not in facturacion_por_cliente:
            facturacion_por_cliente[identificador_cliente] = {
                "Cliente": str(factura["cliente"]),
                "CIF": str(factura["cif"]).strip(),
                "Facturación (€)": 0.0,
            }
        facturacion_por_cliente[identificador_cliente]["Facturación (€)"] += total
        resumen_articulos = "; ".join(
            f"{articulo['concepto']} ({int(articulo['cantidad'])} x "
            f"{float(articulo['precio']):.2f} €; IVA {float(articulo['iva']):g}%)"
            for articulo in articulos
        )
        total_acumulado += total
        registros.append(
            (
                factura,
                {
                    "Cliente": factura["cliente"],
                    "CIF": factura["cif"],
                    "Fecha": factura["fecha"],
                    "Número de factura": factura["numero_factura"],
                    "Artículos": resumen_articulos,
                    "Unidades": unidades,
                    "Subtotal (€)": round(subtotal, 2),
                    "IVA (€)": round(importe_iva, 2),
                    "Total (€)": round(total, 2),
                },
            )
        )

    identificadores_clientes = {
        str(factura["cif"]).strip().casefold()
        or str(factura["cliente"]).strip().casefold()
        for factura in facturas
    }
    media_por_factura = total_acumulado / len(facturas)
    primera_fila = st.columns(2)
    primera_fila[0].metric(
        "Facturación total", f"{total_acumulado:,.2f} €", border=True, height="stretch"
    )
    primera_fila[1].metric(
        "Número de facturas", len(facturas), border=True, height="stretch"
    )
    segunda_fila = st.columns(2)
    segunda_fila[0].metric(
        "Número de clientes", len(identificadores_clientes), border=True, height="stretch"
    )
    segunda_fila[1].metric(
        "Importe medio por factura",
        f"{media_por_factura:,.2f} €",
        border=True,
        height="stretch",
    )

    st.subheader("Facturación por cliente")
    recuento_nombres = {}
    for cliente in facturacion_por_cliente.values():
        nombre_normalizado = cliente["Cliente"].strip().casefold()
        recuento_nombres[nombre_normalizado] = (
            recuento_nombres.get(nombre_normalizado, 0) + 1
        )

    datos_grafica = []
    for cliente in facturacion_por_cliente.values():
        nombre = cliente["Cliente"]
        if recuento_nombres[nombre.strip().casefold()] > 1:
            nombre = f"{nombre} ({cliente['CIF']})"
        datos_grafica.append(
            {
                "Cliente": nombre,
                "Facturación (€)": cliente["Facturación (€)"],
            }
        )
    datos_grafica = sorted(
        datos_grafica,
        key=lambda cliente: cliente["Facturación (€)"],
        reverse=True,
    )
    if any(cantidad > 1 for cantidad in recuento_nombres.values()):
        st.caption("Se muestra el CIF junto al nombre cuando hay clientes homónimos.")
    grafica_facturacion = (
        alt.Chart(alt.Data(values=datos_grafica))
        .mark_bar(color="#176B5B", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(
                "Cliente:N",
                title="Clientes",
                sort=None,
                axis=alt.Axis(labelAngle=-30, labelLimit=220),
            ),
            y=alt.Y(
                "Facturación (€):Q",
                title="Facturación (€)",
                scale=alt.Scale(domainMin=0),
                axis=alt.Axis(format=",.2f"),
            ),
            tooltip=[
                alt.Tooltip("Cliente:N", title="Cliente"),
                alt.Tooltip("Facturación (€):Q", title="Facturación", format=",.2f"),
            ],
        )
        .properties(height=400)
    )
    st.altair_chart(
        grafica_facturacion,
        width="stretch",
        alt="Facturación por cliente. El eje vertical comienza en cero.",
    )

    for factura, fila in registros:
        with st.container(border=True):
            datos_col, descarga_col = st.columns([10, 2], vertical_alignment="center")
            with datos_col:
                st.dataframe([fila], hide_index=True, height=82)
            with descarga_col:
                numero_seguro = re.sub(
                    r"[^A-Za-z0-9._-]+", "_", str(factura["numero_factura"])
                ).strip("._") or str(factura["id"])
                st.download_button(
                    "Descargar PDF",
                    data=generar_pdf_factura(factura),
                    file_name=f"factura_{numero_seguro}.pdf",
                    mime="application/pdf",
                    key=f"descargar_pdf_{factura['id']}",
                    icon=":material/download:",
                    help=f"Descargar factura {factura['numero_factura']} en PDF",
                    on_click="ignore",
                    width="stretch",
                )
