import re

import altair as alt
import streamlit as st

from facturas_db import (
    actualizar_estado_pago,
    inicializar_base_datos,
    obtener_ajustes_factura,
    obtener_facturas,
)
from pdf_factura import generar_pdf_factura

inicializar_base_datos()
ajustes_factura = obtener_ajustes_factura()

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
        tipo_documento = str(factura.get("documento_tipo") or "CIF")
        numero_documento = str(factura["cif"]).strip()
        identificador_cliente = (
            f"{tipo_documento.casefold()}:{numero_documento.casefold()}"
            if numero_documento
            else str(factura["cliente"]).strip().casefold()
        )
        if identificador_cliente not in facturacion_por_cliente:
            facturacion_por_cliente[identificador_cliente] = {
                "Cliente": str(factura["cliente"]),
                "Documento": f"{tipo_documento} {numero_documento}".strip(),
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
                    "Documento": f"{tipo_documento} {numero_documento}".strip(),
                    "Fecha de emisión": factura["fecha"],
                    "Vencimiento": factura.get("fecha_vencimiento") or "Sin fecha",
                    "Estado de pago": factura.get("estado_pago", "Pendiente"),
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
        (
            f"{str(factura.get('documento_tipo') or 'CIF').casefold()}:{str(factura['cif']).strip().casefold()}"
            if str(factura["cif"]).strip()
            else str(factura["cliente"]).strip().casefold()
        )
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
            nombre = f"{nombre} ({cliente['Documento']})"
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
        st.caption("Se muestra el DNI, NIE o CIF junto al nombre de clientes homónimos.")
    grafica_facturacion = (
        alt.Chart(alt.Data(values=datos_grafica))
        .mark_bar(color="#176B5B", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(
                "Cliente:N",
                title="Clientes",
                sort=None,
                axis=alt.Axis(
                    labelAngle=-45,
                    labelOverlap=False,
                    labelLimit=0,
                    labelFontSize=11,
                ),
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
        .properties(height=440)
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
                    data=generar_pdf_factura(factura, ajustes_factura),
                    file_name=f"factura_{numero_seguro}.pdf",
                    mime="application/pdf",
                    key=f"descargar_pdf_{factura['id']}",
                    icon=":material/download:",
                    help=f"Descargar factura {factura['numero_factura']} en PDF",
                    on_click="ignore",
                    width="stretch",
                )
            tipo_documento = str(factura.get("documento_tipo") or "CIF")
            with st.expander(
                f"Ver datos completos · {factura['numero_factura']}",
                icon=":material/receipt_long:",
            ):
                estado_pago = str(factura.get("estado_pago") or "Pendiente")
                st.write(f"**Estado de pago:** {estado_pago}")
                nuevo_estado = "Pendiente" if estado_pago == "Pagada" else "Pagada"
                etiqueta_boton = (
                    "Marcar como pendiente"
                    if estado_pago == "Pagada"
                    else "Marcar como pagada"
                )
                if st.button(
                    etiqueta_boton,
                    key=f"estado_pago_{factura['id']}",
                    type="primary" if nuevo_estado == "Pagada" else "secondary",
                ):
                    actualizar_estado_pago(int(factura["id"]), nuevo_estado)
                    st.rerun()
                cliente_col, documento_col = st.columns(2)
                cliente_col.write(f"**Cliente:** {factura['cliente']}")
                documento_col.write(
                    f"**{tipo_documento}:** {factura['cif']}"
                )
                datos_cliente = factura.get("datos_cliente") or {}
                direccion_cliente = ", ".join(
                    str(datos_cliente.get(campo) or "").strip()
                    for campo in ("direccion", "codigo_postal", "ciudad", "provincia", "pais")
                    if str(datos_cliente.get(campo) or "").strip()
                )
                if direccion_cliente:
                    st.write(f"**Dirección fiscal:** {direccion_cliente}")
                contacto_col, telefono_col = st.columns(2)
                if datos_cliente.get("email"):
                    contacto_col.write(f"**Correo:** {datos_cliente['email']}")
                if datos_cliente.get("telefono"):
                    telefono_col.write(f"**Teléfono:** {datos_cliente['telefono']}")
                numero_col, emision_col, vencimiento_col = st.columns(3)
                numero_col.write(f"**Número de factura:** {factura['numero_factura']}")
                emision_col.write(f"**Fecha de emisión:** {factura['fecha']}")
                vencimiento_col.write(
                    f"**Fecha de vencimiento:** {factura.get('fecha_vencimiento') or 'Sin fecha'}"
                )
                st.markdown("**Artículos**")
                st.dataframe(
                    [
                        {
                            "Descripción": articulo["concepto"],
                            "Cantidad": int(articulo["cantidad"]),
                            "Precio unitario (€)": float(articulo["precio"]),
                            "IVA (%)": float(articulo["iva"]),
                            "Total (€)": round(
                                int(articulo["cantidad"])
                                * float(articulo["precio"])
                                * (1 + float(articulo["iva"]) / 100),
                                2,
                            ),
                        }
                        for articulo in factura["articulos"]
                    ],
                    hide_index=True,
                    alt=f"Detalle de la factura {factura['numero_factura']}",
                )
                resumen_col, iva_col, total_col = st.columns(3)
                resumen_col.metric("Subtotal", f"{fila['Subtotal (€)']:.2f} €")
                iva_col.metric("IVA", f"{fila['IVA (€)']:.2f} €")
                total_col.metric("Total", f"{fila['Total (€)']:.2f} €")
