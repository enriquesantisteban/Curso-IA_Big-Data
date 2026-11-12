from datetime import date
import re

import altair as alt
import streamlit as st

from facturas_db import (
    actualizar_datos,
    actualizar_estado_pago,
    eliminar_factura,
    inicializar_base_datos,
    invalidar_pdf_factura,
    obtener_facturas,
)
from pdf_factura import generar_pdf_factura


def _formato_euros(importe: float) -> str:
    return f"{importe:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def _guardar_estado_pago(factura_id: int, numero_factura: str) -> None:
    estado = str(st.session_state[f"estado_pago_informe_{factura_id}"])
    actualizar_estado_pago(factura_id, estado, numero_factura)
    st.session_state["mensaje_estado_pago"] = (
        f"El estado de la factura {numero_factura} se actualizó a {estado.lower()}."
    )


inicializar_base_datos()

st.title("Informes")
st.write("Resumen de las facturas generadas y registradas.")
if st.session_state.get("mensaje_estado_pago"):
    st.success(st.session_state.pop("mensaje_estado_pago"))

facturas = obtener_facturas("Generada")
total_facturas_generadas = len(facturas)
if facturas:
    fechas_factura = [date.fromisoformat(str(factura["fecha"])) for factura in facturas]
    fecha_minima = min(fechas_factura)
    fecha_maxima = max(fechas_factura)
    st.subheader("Filtros de informes")
    fechas_col, numero_col, estado_col_filtro = st.columns([1.4, 1, 0.85])
    with fechas_col:
        rango_fechas = st.date_input(
            "Periodo de facturación",
            value=(fecha_minima, fecha_maxima),
            min_value=fecha_minima,
            max_value=fecha_maxima,
            format="DD/MM/YYYY",
            help="Las estadísticas, la gráfica y la tabla usarán este periodo.",
        )
    with numero_col:
        filtro_numero = st.text_input(
            "Número de factura",
            placeholder="Todas las facturas",
            help="Escribe el número completo o parte de él para filtrar.",
        ).strip().casefold()
    with estado_col_filtro:
        filtro_estado_pago = st.selectbox(
            "Estado de pago",
            ["Todos", "Pagado", "Pendiente", "Vencido"],
            key="filtro_estado_pago_informes",
        )

    if isinstance(rango_fechas, (tuple, list)):
        desde = rango_fechas[0] if rango_fechas else fecha_minima
        hasta = rango_fechas[-1] if rango_fechas else fecha_maxima
    else:
        desde = hasta = rango_fechas
    facturas = [
        factura
        for factura in facturas
        if desde <= date.fromisoformat(str(factura["fecha"])) <= hasta
        and filtro_numero in str(factura["numero_factura"]).casefold()
        and (
            filtro_estado_pago == "Todos"
            or str(factura.get("estado_pago") or "Pendiente") == filtro_estado_pago
        )
    ]

if not facturas:
    if total_facturas_generadas:
        st.info("No hay facturas generadas que coincidan con los filtros seleccionados.")
    else:
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
    meses_es = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    mes_cursor = date(desde.year, desde.month, 1)
    meses = []
    while mes_cursor <= date(hasta.year, hasta.month, 1):
        clave_mes = f"{mes_cursor.year:04d}-{mes_cursor.month:02d}"
        meses.append(
            {
                "Clave": clave_mes,
                "Mes": f"{meses_es[mes_cursor.month - 1]} {mes_cursor.year}",
                "Facturación (€)": 0.0,
            }
        )
        if mes_cursor.month == 12:
            mes_cursor = date(mes_cursor.year + 1, 1, 1)
        else:
            mes_cursor = date(mes_cursor.year, mes_cursor.month + 1, 1)
    por_mes = {mes["Clave"]: mes for mes in meses}
    for factura, fila in registros:
        clave_mes = str(factura["fecha"])[:7]
        if clave_mes in por_mes:
            por_mes[clave_mes]["Facturación (€)"] += fila["Total (€)"]

    tarjetas = st.columns(4, gap="medium")
    tarjetas[0].metric("Facturación total", _formato_euros(total_acumulado), border=True)
    tarjetas[1].metric("Número de facturas", f"{len(facturas):,}", border=True)
    tarjetas[2].metric("Clientes distintos", f"{len(identificadores_clientes):,}", border=True)
    tarjetas[3].metric("Importe medio", _formato_euros(media_por_factura), border=True)

    with st.container(border=True):
        st.subheader("Facturación por mes")
        st.caption("Importes calculados con las facturas que coinciden con los filtros seleccionados.")
        grafica_mensual = (
            alt.Chart(alt.Data(values=meses))
            .mark_bar(color="#3182e8", cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=24)
            .encode(
                x=alt.X(
                    "Mes:N",
                    title=None,
                    sort=[mes["Mes"] for mes in meses],
                    axis=alt.Axis(labelAngle=0, labelFontSize=11, labelLimit=90, tickSize=0),
                ),
                y=alt.Y(
                    "Facturación (€):Q",
                    title=None,
                    scale=alt.Scale(domainMin=0),
                    axis=alt.Axis(format="~s", labelFontSize=10, grid=True, gridColor="#eaf0f6"),
                ),
                tooltip=[
                    alt.Tooltip("Mes:N", title="Mes"),
                    alt.Tooltip("Facturación (€):Q", title="Facturado", format=",.2f"),
                ],
            )
            .properties(height=250)
            .configure(
                background="#ffffff",
                view=alt.ViewConfig(fill="#ffffff"),
                axis=alt.AxisConfig(labelColor="#263d54", titleColor="#263d54", gridColor="#e5edf4"),
            )
        )
        st.altair_chart(
            grafica_mensual,
            width="stretch",
            alt="Facturación mensual. Cada barra representa un mes y el eje comienza en cero.",
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
        .mark_bar(color="#24a27c", cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
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
        .properties(height=400)
        .configure(
            background="#ffffff",
            view=alt.ViewConfig(fill="#ffffff"),
            axis=alt.AxisConfig(labelColor="#263d54", titleColor="#263d54", gridColor="#e5edf4"),
        )
    )
    st.altair_chart(
        grafica_facturacion,
        width="stretch",
        alt="Facturación por cliente. El eje vertical comienza en cero.",
    )

    st.subheader("Facturas registradas")
    datos_tabla = []
    for factura, fila in registros:
        articulos_resumen = " · ".join(
            f"{articulo['concepto']} × {int(articulo['cantidad'])}"
            for articulo in factura["articulos"]
        )
        datos_tabla.append(
            {
                "Cliente": str(factura["cliente"]),
                "CIF": str(factura["cif"]),
                "Fecha": date.fromisoformat(str(factura["fecha"])),
                "N.º factura": str(factura["numero_factura"]),
                "Artículos": articulos_resumen,
                "Base (€)": float(fila["Subtotal (€)"]),
                "IVA (€)": float(fila["IVA (€)"]),
                "Total (€)": float(fila["Total (€)"]),
                "Estado": str(factura.get("estado_pago") or "Pendiente"),
            }
        )

    clave_tabla = (
        f"tabla_facturas_{desde.isoformat()}_{hasta.isoformat()}_"
        f"{filtro_numero}_{filtro_estado_pago}"
    )
    tabla_evento = st.dataframe(
        datos_tabla,
        hide_index=True,
        width="stretch",
        height=min(44 * (len(datos_tabla) + 1) + 45, 680),
        on_select="rerun",
        selection_mode="single-row",
        key=clave_tabla,
        column_config={
            "Cliente": st.column_config.TextColumn("Cliente", width="medium"),
            "CIF": st.column_config.TextColumn("CIF", width="small"),
            "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY", width="small"),
            "N.º factura": st.column_config.TextColumn("N.º factura", width="small"),
            "Artículos": st.column_config.TextColumn("Artículos", width="large"),
            "Base (€)": st.column_config.NumberColumn("Base (€)", format="%.2f €", width="small"),
            "IVA (€)": st.column_config.NumberColumn("IVA (€)", format="%.2f €", width="small"),
            "Total (€)": st.column_config.NumberColumn("Total (€)", format="%.2f €", width="small"),
            "Estado": st.column_config.TextColumn("Estado", width="small"),
        },
    )
    st.caption("Pulsa el encabezado «Cliente» para ordenar alfabéticamente. Selecciona una fila para ver y gestionar esa factura.")

    filas_seleccionadas = tabla_evento.selection.rows
    if not filas_seleccionadas:
        st.info("Selecciona una factura de la tabla para ver sus detalles y acciones.")
    else:
        indice = int(filas_seleccionadas[0])
        if indice < len(registros):
            factura, fila = registros[indice]
            factura_id = int(factura["id"])
            with st.container(border=True):
                st.subheader(f"Factura {factura['numero_factura']} · {factura['cliente']}")
                st.caption(
                    f"{date.fromisoformat(str(factura['fecha'])).strftime('%d/%m/%Y')}"
                    f" · CIF {factura['cif']} · Estado: {factura.get('estado_pago', 'Pendiente')}"
                )

                acciones = st.columns([1.3, 1.4, 1, 1], vertical_alignment="bottom", gap="small")
                estado_pago_actual = str(factura.get("estado_pago") or "Pendiente")
                with acciones[0]:
                    st.selectbox(
                        "Estado de pago",
                        ["Pendiente", "Pagado", "Vencido"],
                        index=["Pendiente", "Pagado", "Vencido"].index(estado_pago_actual),
                        key=f"estado_pago_informe_{factura_id}",
                        on_change=_guardar_estado_pago,
                        args=(factura_id, str(factura["numero_factura"])),
                        help="El cambio se guarda al seleccionar otro estado y actualiza el PDF descargable.",
                    )
                numero_seguro = re.sub(
                    r"[^A-Za-z0-9._-]+", "_", str(factura["numero_factura"])
                ).strip("._") or str(factura["id"])
                with acciones[1]:
                    st.download_button(
                        "Descargar PDF",
                        data=generar_pdf_factura(factura),
                        file_name=f"factura_{numero_seguro}.pdf",
                        mime="application/pdf",
                        key=f"descargar_pdf_{factura_id}",
                        icon=":material/download:",
                        help=f"Descargar factura {factura['numero_factura']} en PDF",
                        on_click="ignore",
                        width="stretch",
                    )
                if acciones[2].button(
                    "Editar", key=f"editar_informe_{factura_id}",
                    icon=":material/edit:", help="Editar los datos de esta factura", width="stretch"
                ):
                    st.session_state["factura_edicion_informe"] = factura_id
                    st.session_state.pop("confirmar_borrado_factura", None)
                    st.rerun()
                if acciones[3].button(
                    "Eliminar",
                    key=f"eliminar_informe_{factura_id}",
                    type="secondary",
                    icon=":material/delete:",
                    help="Eliminar esta factura y su PDF guardado",
                    width="stretch",
                ):
                    st.session_state["confirmar_borrado_factura"] = factura_id
                    st.session_state.pop("factura_edicion_informe", None)
                    st.rerun()

                with st.expander("Ver líneas y desglose completo", expanded=True):
                    articulos_tabla = [
                        {
                            "Descripción": articulo["concepto"],
                            "Cantidad": int(articulo["cantidad"]),
                            "Precio unitario (€)": float(articulo["precio"]),
                            "IVA (%)": float(articulo["iva"]),
                            "Importe (€)": round(
                                int(articulo["cantidad"])
                                * float(articulo["precio"])
                                * (1 + float(articulo["iva"]) / 100),
                                2,
                            ),
                        }
                        for articulo in factura["articulos"]
                    ]
                    st.dataframe(
                        articulos_tabla,
                        hide_index=True,
                        width="stretch",
                        column_config={
                            "Precio unitario (€)": st.column_config.NumberColumn(format="%.2f €"),
                            "IVA (%)": st.column_config.NumberColumn(format="%.1f%%"),
                            "Importe (€)": st.column_config.NumberColumn(format="%.2f €"),
                        },
                    )
                    subtotal_col, iva_col, total_desglose_col = st.columns(3)
                    subtotal_col.metric("Base imponible", _formato_euros(fila["Subtotal (€)"]))
                    iva_col.metric("IVA", _formato_euros(fila["IVA (€)"]))
                    total_desglose_col.metric("Total", _formato_euros(fila["Total (€)"]))

                if st.session_state.get("confirmar_borrado_factura") == factura_id:
                    st.warning(
                        f"¿Eliminar la factura {factura['numero_factura']}? También se borrarán sus artículos."
                    )
                    confirmar_col, cancelar_col = st.columns(2)
                    if confirmar_col.button(
                        "Confirmar eliminación",
                        key=f"confirmar_eliminar_{factura_id}",
                        type="primary",
                    ):
                        eliminar_factura(factura_id, str(factura["numero_factura"]))
                        st.session_state.pop("confirmar_borrado_factura", None)
                        st.session_state["mensaje_factura_eliminada"] = (
                            f"Factura {factura['numero_factura']} eliminada."
                        )
                        st.rerun()
                    if cancelar_col.button("Cancelar", key=f"cancelar_eliminar_{factura_id}"):
                        st.session_state.pop("confirmar_borrado_factura", None)
                        st.rerun()

                if st.session_state.get("factura_edicion_informe") == factura_id:
                    with st.form(f"formulario_editar_informe_{factura_id}"):
                        st.markdown(f"**Editar factura {factura['numero_factura']}**")
                        cliente_editado = st.text_input(
                            "Cliente", value=str(factura["cliente"]), key=f"editar_cliente_informe_{factura_id}"
                        )
                        cif_editado = st.text_input(
                            "CIF", value=str(factura["cif"]), key=f"editar_cif_informe_{factura_id}"
                        )
                        fecha_editada = st.date_input(
                            "Fecha", value=date.fromisoformat(str(factura["fecha"])), key=f"editar_fecha_informe_{factura_id}"
                        )
                        numero_editado = st.text_input(
                            "Número de factura", value=str(factura["numero_factura"]), key=f"editar_numero_informe_{factura_id}"
                        )
                        lineas_editadas = st.data_editor(
                            [
                                {
                                    "Concepto": articulo["concepto"],
                                    "Cantidad": int(articulo["cantidad"]),
                                    "Precio unitario (€)": float(articulo["precio"]),
                                    "IVA (%)": float(articulo["iva"]),
                                }
                                for articulo in factura["articulos"]
                            ],
                            column_config={
                                "Concepto": st.column_config.TextColumn("Concepto", required=True),
                                "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1, format="%d", required=True),
                                "Precio unitario (€)": st.column_config.NumberColumn("Precio unitario (€)", min_value=0.0, step=0.01, format="%.2f", required=True),
                                "IVA (%)": st.column_config.NumberColumn("IVA (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.2f", required=True),
                            },
                            num_rows="dynamic",
                            hide_index=True,
                            key=f"editar_articulos_informe_{factura_id}",
                            alt=f"Editar artículos de factura {factura['numero_factura']}",
                        )
                        guardar_cambios, cancelar_edicion = st.columns(2)
                        guardar = guardar_cambios.form_submit_button("Guardar cambios", type="primary")
                        cancelar = cancelar_edicion.form_submit_button("Cancelar")

                    if guardar:
                        filas_editadas = lineas_editadas.to_dict(orient="records") if hasattr(lineas_editadas, "to_dict") else list(lineas_editadas)
                        articulos_actualizados = []
                        error_datos = False
                        for linea in filas_editadas:
                            concepto = str(linea.get("Concepto") or "").strip()
                            if not concepto:
                                continue
                            try:
                                cantidad = int(linea["Cantidad"])
                                precio = float(linea["Precio unitario (€)"])
                                iva = float(linea["IVA (%)"])
                            except (TypeError, ValueError, OverflowError):
                                error_datos = True
                                break
                            if cantidad < 1 or precio < 0 or not 0 <= iva <= 100:
                                error_datos = True
                                break
                            articulos_actualizados.append({"concepto": concepto, "cantidad": cantidad, "precio": precio, "iva": iva})
                        if error_datos:
                            st.error("Revisa la cantidad, el precio y el IVA de los artículos.")
                        elif not articulos_actualizados:
                            st.error("La factura debe conservar al menos un artículo.")
                        elif not cliente_editado.strip() or not cif_editado.strip() or not numero_editado.strip():
                            st.error("Completa cliente, CIF y número de factura.")
                        else:
                            invalidar_pdf_factura(str(factura["numero_factura"]))
                            invalidar_pdf_factura(numero_editado)
                            actualizar_datos(
                                factura_id=factura_id,
                                cliente=cliente_editado,
                                cif=cif_editado,
                                fecha=fecha_editada.isoformat(),
                                numero_factura=numero_editado,
                                articulos=articulos_actualizados,
                            )
                            st.session_state.pop("factura_edicion_informe", None)
                            st.session_state["mensaje_factura_actualizada"] = (
                                f"Factura {numero_editado} actualizada; sus informes usarán los nuevos datos."
                            )
                            st.rerun()
                    if cancelar:
                        st.session_state.pop("factura_edicion_informe", None)
                        st.rerun()

if st.session_state.get("mensaje_factura_actualizada"):
    st.success(st.session_state.pop("mensaje_factura_actualizada"))
if st.session_state.get("mensaje_factura_eliminada"):
    st.success(st.session_state.pop("mensaje_factura_eliminada"))
