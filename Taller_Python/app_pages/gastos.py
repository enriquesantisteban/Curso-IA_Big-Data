from datetime import date

import altair as alt
import streamlit as st

from gastos_db import (
    CATEGORIAS_GASTO,
    ESTADOS_GASTO,
    eliminar_gasto,
    guardar_gasto,
    inicializar_gastos,
    obtener_gastos,
)


def euros(importe: float) -> str:
    return f"{importe:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def total_gasto(gasto: dict[str, object]) -> float:
    return round(float(gasto["importe"]) * (1 + float(gasto["iva"]) / 100), 2)


inicializar_gastos()
gastos = obtener_gastos()
gastos_por_id = {int(gasto["id"]): gasto for gasto in gastos}
gasto_id_edicion = st.session_state.get("gasto_en_edicion")
gasto_edicion = gastos_por_id.get(int(gasto_id_edicion)) if gasto_id_edicion else None

st.title("Gastos de empresa")
st.caption("Registra, consulta y controla los gastos del negocio en un mismo lugar.")

if st.session_state.get("mensaje_gasto"):
    st.success(st.session_state.pop("mensaje_gasto"))

with st.expander(
    "Editar gasto" if gasto_edicion else "Registrar un gasto",
    expanded=bool(gasto_edicion) or not gastos,
):
    sufijo = str(gasto_id_edicion or "nuevo")
    with st.form(f"formulario_gasto_{sufijo}", clear_on_submit=True):
        proveedor_col, cif_col = st.columns([1.4, 1])
        with proveedor_col:
            proveedor = st.text_input(
                "Proveedor o beneficiario *",
                value=str((gasto_edicion or {}).get("proveedor", "")),
                placeholder="Nombre de empresa o profesional",
                key=f"proveedor_gasto_{sufijo}",
            )
        with cif_col:
            cif_proveedor = st.text_input(
                "CIF/NIF del proveedor",
                value=str((gasto_edicion or {}).get("cif_proveedor", "")),
                key=f"cif_proveedor_gasto_{sufijo}",
            )

        fecha_col, categoria_col, estado_col = st.columns([1, 1.6, 1])
        with fecha_col:
            fecha_gasto = st.date_input(
                "Fecha del gasto",
                value=date.fromisoformat(str(gasto_edicion["fecha"])) if gasto_edicion else date.today(),
                format="DD/MM/YYYY",
                key=f"fecha_gasto_{sufijo}",
            )
        with categoria_col:
            categoria_actual = str((gasto_edicion or {}).get("categoria", CATEGORIAS_GASTO[0]))
            categoria_gasto = st.selectbox(
                "Categoría",
                CATEGORIAS_GASTO,
                index=CATEGORIAS_GASTO.index(categoria_actual) if categoria_actual in CATEGORIAS_GASTO else 0,
                key=f"categoria_gasto_{sufijo}",
            )
        with estado_col:
            estado_actual = str((gasto_edicion or {}).get("estado_pago", "Pendiente"))
            estado_pago = st.selectbox(
                "Estado",
                ESTADOS_GASTO,
                index=ESTADOS_GASTO.index(estado_actual) if estado_actual in ESTADOS_GASTO else 0,
                key=f"estado_gasto_{sufijo}",
            )

        documento_col, concepto_col = st.columns([1, 2])
        with documento_col:
            documento = st.text_input(
                "N.º de factura o recibo",
                value=str((gasto_edicion or {}).get("numero_documento", "")),
                key=f"documento_gasto_{sufijo}",
            )
        with concepto_col:
            concepto = st.text_input(
                "Concepto o descripción *",
                value=str((gasto_edicion or {}).get("concepto", "")),
                placeholder="Ej.: cuota mensual de Internet",
                key=f"concepto_gasto_{sufijo}",
            )

        importe_col, iva_col, pago_col = st.columns([1, 1, 1.4])
        with importe_col:
            importe = st.number_input(
                "Importe antes de IVA (€)", min_value=0.0,
                value=float((gasto_edicion or {}).get("importe", 0.0)),
                step=10.0, format="%.2f", key=f"importe_gasto_{sufijo}",
            )
        with iva_col:
            iva = st.number_input(
                "IVA (%)", min_value=0.0, max_value=100.0,
                value=float((gasto_edicion or {}).get("iva", 21.0)),
                step=1.0, key=f"iva_gasto_{sufijo}",
            )
        with pago_col:
            metodos_pago = ["Transferencia", "Tarjeta", "Domiciliación", "Efectivo", "Bizum", "PayPal", "Otro"]
            metodo_actual = str((gasto_edicion or {}).get("forma_pago", ""))
            if metodo_actual and metodo_actual not in metodos_pago:
                metodos_pago.append(metodo_actual)
            forma_pago = st.selectbox(
                "Forma de pago", ["Sin especificar", *metodos_pago],
                index=metodos_pago.index(metodo_actual) + 1 if metodo_actual in metodos_pago else 0,
                key=f"forma_pago_gasto_{sufijo}",
            )

        observaciones = st.text_area(
            "Observaciones",
            value=str((gasto_edicion or {}).get("observaciones", "")),
            key=f"observaciones_gasto_{sufijo}",
        )
        guardar_col, cancelar_col = st.columns(2)
        guardar = guardar_col.form_submit_button(
            "Guardar cambios" if gasto_edicion else "Guardar gasto",
            type="primary", width="stretch",
        )
        cancelar = cancelar_col.form_submit_button("Cancelar edición", width="stretch") if gasto_edicion else False

    if guardar:
        if not proveedor.strip() or not concepto.strip():
            st.error("Completa el proveedor y el concepto del gasto.")
        elif importe <= 0:
            st.error("El importe debe ser mayor que cero.")
        else:
            try:
                id_guardado = guardar_gasto(
                    fecha=fecha_gasto.isoformat(), proveedor=proveedor,
                    cif_proveedor=cif_proveedor, numero_documento=documento,
                    categoria=categoria_gasto, concepto=concepto, importe=importe,
                    iva=iva, forma_pago="" if forma_pago == "Sin especificar" else forma_pago,
                    estado_pago=estado_pago, observaciones=observaciones,
                    gasto_id=int(gasto_id_edicion) if gasto_edicion else None,
                )
            except ValueError as error:
                st.error(str(error))
            else:
                st.session_state.pop("gasto_en_edicion", None)
                st.session_state["mensaje_gasto"] = (
                    "Gasto actualizado correctamente." if gasto_edicion
                    else f"Gasto registrado correctamente (n.º {id_guardado})."
                )
                st.rerun()
    if cancelar:
        st.session_state.pop("gasto_en_edicion", None)
        st.rerun()

if gastos:
    fechas = [date.fromisoformat(str(gasto["fecha"])) for gasto in gastos]
    fecha_minima, fecha_maxima = min(fechas), max(fechas)
    filtro_fecha_col, filtro_categoria_col, filtro_estado_col = st.columns([1.5, 1.4, 1])
    with filtro_fecha_col:
        rango = st.date_input(
            "Periodo", value=(fecha_minima, fecha_maxima),
            min_value=fecha_minima, max_value=fecha_maxima,
            format="DD/MM/YYYY", key="filtro_fechas_gastos",
        )
    with filtro_categoria_col:
        filtro_categoria = st.selectbox(
            "Categoría", ["Todas", *CATEGORIAS_GASTO], key="filtro_categoria_gastos"
        )
    with filtro_estado_col:
        filtro_estado = st.selectbox(
            "Estado de pago", ["Todos", *ESTADOS_GASTO], key="filtro_estado_gastos"
        )
    desde, hasta = (rango[0], rango[-1]) if isinstance(rango, (tuple, list)) else (rango, rango)
    gastos_filtrados = [
        gasto for gasto in gastos
        if desde <= date.fromisoformat(str(gasto["fecha"])) <= hasta
        and (filtro_categoria == "Todas" or gasto["categoria"] == filtro_categoria)
        and (filtro_estado == "Todos" or gasto["estado_pago"] == filtro_estado)
    ]
else:
    gastos_filtrados = []
    desde = hasta = date.today()
    filtro_categoria = "Todas"
    filtro_estado = "Todos"

total = sum(total_gasto(gasto) for gasto in gastos_filtrados)
pagado = sum(total_gasto(gasto) for gasto in gastos_filtrados if gasto["estado_pago"] == "Pagado")
pendiente = sum(total_gasto(gasto) for gasto in gastos_filtrados if gasto["estado_pago"] == "Pendiente")
vencido = sum(total_gasto(gasto) for gasto in gastos_filtrados if gasto["estado_pago"] == "Vencido")
tarjetas = st.columns(4, gap="medium")
tarjetas[0].metric("Gastos del periodo", euros(total), border=True)
tarjetas[1].metric("Pagados", euros(pagado), border=True)
tarjetas[2].metric("Pendientes", euros(pendiente), border=True)
tarjetas[3].metric("Vencidos", euros(vencido), border=True)

if gastos_filtrados:
    totales_categoria = {}
    for gasto in gastos_filtrados:
        categoria = str(gasto["categoria"])
        totales_categoria[categoria] = totales_categoria.get(categoria, 0.0) + total_gasto(gasto)
    datos_grafica = [
        {"Categoría": categoria, "Total (€)": round(importe, 2)}
        for categoria, importe in sorted(totales_categoria.items(), key=lambda item: item[1], reverse=True)
    ]
    grafica = (
        alt.Chart(alt.Data(values=datos_grafica))
        .mark_bar(color="#2878d0", cornerRadiusTopRight=5, cornerRadiusBottomRight=5, size=17)
        .encode(
            x=alt.X("Total (€):Q", title="Total con IVA (€)", scale=alt.Scale(domainMin=0), axis=alt.Axis(labelColor="#263d54", titleColor="#263d54", gridColor="#e5edf4")),
            y=alt.Y("Categoría:N", sort="-x", title=None, axis=alt.Axis(labelColor="#263d54", labelLimit=240)),
            tooltip=[alt.Tooltip("Categoría:N"), alt.Tooltip("Total (€):Q", format=",.2f")],
        )
        .properties(height=max(230, min(620, 28 * len(datos_grafica))))
        .configure(background="#ffffff", view=alt.ViewConfig(fill="#ffffff"))
    )
    with st.container(border=True):
        st.subheader("Gastos por categoría")
        st.altair_chart(grafica, width="stretch", alt="Importe de gastos agrupado por categoría.")

st.subheader("Registro de gastos")
if not gastos:
    st.info("Aún no hay gastos. Abre «Registrar un gasto» para añadir el primero.")
elif not gastos_filtrados:
    st.info("No hay gastos que coincidan con los filtros seleccionados.")
else:
    datos_gastos = [
        {
            "Fecha": date.fromisoformat(str(gasto["fecha"])),
            "Proveedor": str(gasto["proveedor"]),
            "Categoría": str(gasto["categoria"]),
            "Concepto": str(gasto["concepto"]),
            "Documento": str(gasto["numero_documento"]),
            "Base (€)": float(gasto["importe"]),
            "IVA (€)": round(float(gasto["importe"]) * float(gasto["iva"]) / 100, 2),
            "Total (€)": total_gasto(gasto),
            "Estado": str(gasto["estado_pago"]),
        }
        for gasto in gastos_filtrados
    ]
    evento = st.dataframe(
        datos_gastos,
        hide_index=True,
        width="stretch",
        height=min(46 * (len(datos_gastos) + 1) + 40, 680),
        on_select="rerun",
        selection_mode="single-row",
        key=(
            f"tabla_gastos_{desde}_{hasta}_{filtro_categoria}_{filtro_estado}_"
            f"{int(st.session_state.get('version_tabla_gastos', 0))}"
        ),
        column_config={
            "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY", width="small"),
            "Proveedor": st.column_config.TextColumn("Proveedor", width="medium"),
            "Categoría": st.column_config.TextColumn("Categoría", width="medium"),
            "Concepto": st.column_config.TextColumn("Concepto", width="large"),
            "Documento": st.column_config.TextColumn("N.º documento", width="small"),
            "Base (€)": st.column_config.NumberColumn("Base (€)", format="%.2f €", width="small"),
            "IVA (€)": st.column_config.NumberColumn("IVA (€)", format="%.2f €", width="small"),
            "Total (€)": st.column_config.NumberColumn("Total (€)", format="%.2f €", width="small"),
            "Estado": st.column_config.TextColumn("Estado", width="small"),
        },
    )
    filas_seleccionadas = evento.selection.rows
    if filas_seleccionadas:
        gasto = gastos_filtrados[int(filas_seleccionadas[0])]
        gasto_id = int(gasto["id"])
        with st.container(border=True):
            st.markdown(f"### {gasto['proveedor']} · {euros(total_gasto(gasto))}")
            st.caption(
                f"{gasto['categoria']} · {gasto['concepto']} · {gasto['estado_pago']} · "
                f"IVA {float(gasto['iva']):g}% · CIF/NIF {gasto['cif_proveedor'] or 'sin indicar'}"
            )
            if gasto["numero_documento"]:
                st.caption(f"Documento: {gasto['numero_documento']}")
            if gasto["observaciones"]:
                st.caption(f"Observaciones: {gasto['observaciones']}")
            editar_col, eliminar_col = st.columns(2)
            if editar_col.button("Editar gasto", key=f"editar_gasto_{gasto_id}", icon=":material/edit:", width="stretch"):
                st.session_state["gasto_en_edicion"] = gasto_id
                st.rerun()
            if eliminar_col.button("Eliminar gasto", key=f"eliminar_gasto_{gasto_id}", icon=":material/delete:", width="stretch"):
                st.session_state["confirmar_eliminar_gasto"] = gasto_id
                st.rerun()
            if st.session_state.get("confirmar_eliminar_gasto") == gasto_id:
                st.warning(f"¿Eliminar el gasto de {gasto['proveedor']} del {date.fromisoformat(str(gasto['fecha'])).strftime('%d/%m/%Y')}?")
                confirmar_col, cancelar_col = st.columns(2)
                if confirmar_col.button("Confirmar eliminación", key=f"confirmar_borrar_gasto_{gasto_id}", type="primary"):
                    eliminar_gasto(gasto_id)
                    st.session_state.pop("confirmar_eliminar_gasto", None)
                    st.session_state["mensaje_gasto"] = "Gasto eliminado correctamente."
                    st.session_state["version_tabla_gastos"] = int(st.session_state.get("version_tabla_gastos", 0)) + 1
                    st.rerun()
                if cancelar_col.button("Cancelar", key=f"cancelar_borrar_gasto_{gasto_id}"):
                    st.session_state.pop("confirmar_eliminar_gasto", None)
                    st.rerun()
