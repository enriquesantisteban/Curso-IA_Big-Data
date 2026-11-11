from datetime import date

import streamlit as st

from facturas_db import (
    actualizar_datos,
    generar_factura,
    inicializar_base_datos,
    obtener_facturas,
)

inicializar_base_datos()

st.title("Generar facturas")
st.write("Revisa los datos guardados y genera las facturas cuando estén listas.")

if "confirmacion_factura_generada" in st.session_state:
    st.success(st.session_state.pop("confirmacion_factura_generada"))
if "confirmacion_datos_actualizados" in st.session_state:
    st.success(st.session_state.pop("confirmacion_datos_actualizados"))

pendientes = obtener_facturas("Pendiente")
if not pendientes:
    st.info("No hay datos pendientes. Primero guarda los datos en «Introducir datos».")

for factura in pendientes:
    articulos = factura["articulos"]
    filas_articulos = []
    for articulo in articulos:
        cantidad = int(articulo["cantidad"])
        precio = float(articulo["precio"])
        iva = float(articulo["iva"])
        subtotal_articulo = cantidad * precio
        iva_articulo = subtotal_articulo * iva / 100
        filas_articulos.append(
            {
                "Concepto": articulo["concepto"],
                "Cantidad": cantidad,
                "Precio unitario (€)": precio,
                "IVA (%)": iva,
                "Subtotal (€)": round(subtotal_articulo, 2),
                "IVA (€)": round(iva_articulo, 2),
                "Total (€)": round(subtotal_articulo + iva_articulo, 2),
            }
        )
    subtotal = sum(fila["Subtotal (€)"] for fila in filas_articulos)
    importe_iva = sum(fila["IVA (€)"] for fila in filas_articulos)
    total = subtotal + importe_iva
    cantidad_total = sum(int(articulo["cantidad"]) for articulo in articulos)

    with st.container(border=True):
        st.subheader(f"Factura {factura['numero_factura']} · {factura['cliente']}")
        cliente_col, cif_col, fecha_col = st.columns(3)
        cliente_col.write(f"**Cliente:** {factura['cliente']}")
        cif_col.write(f"**CIF:** {factura['cif']}")
        fecha_col.write(f"**Fecha:** {factura['fecha']}")

        st.dataframe(filas_articulos, hide_index=True, alt="Artículos de la factura")
        unidades_col, subtotal_col, iva_importe_col, total_col = st.columns(4)
        unidades_col.metric("Unidades", cantidad_total)
        subtotal_col.metric("Subtotal", f"{subtotal:.2f} €")
        iva_importe_col.metric("Importe de IVA", f"{importe_iva:.2f} €")
        total_col.metric("Total", f"{total:.2f} €")

        factura_id = int(factura["id"])
        if st.session_state.get("factura_en_edicion") == factura_id:
            with st.form(f"editar_factura_{factura_id}"):
                st.markdown("**Editar datos de la factura**")
                cliente_editado = st.text_input(
                    "Cliente", value=str(factura["cliente"]), key=f"cliente_{factura_id}"
                )
                cif_editado = st.text_input(
                    "CIF", value=str(factura["cif"]), key=f"cif_{factura_id}"
                )
                fecha_editada = st.date_input(
                    "Fecha",
                    value=date.fromisoformat(str(factura["fecha"])),
                    key=f"fecha_{factura_id}",
                )
                numero_editado = st.text_input(
                    "Número de factura",
                    value=str(factura["numero_factura"]),
                    key=f"numero_{factura_id}",
                )
                articulos_editados = st.data_editor(
                    [
                        {
                            "Concepto": articulo["concepto"],
                            "Cantidad": int(articulo["cantidad"]),
                            "Precio unitario (€)": float(articulo["precio"]),
                            "IVA (%)": float(articulo["iva"]),
                        }
                        for articulo in articulos
                    ],
                    column_config={
                        "Concepto": st.column_config.TextColumn(
                            "Concepto", required=True, width="large"
                        ),
                        "Cantidad": st.column_config.NumberColumn(
                            "Cantidad",
                            min_value=1,
                            step=1,
                            format="%d",
                            default=1,
                            required=True,
                        ),
                        "Precio unitario (€)": st.column_config.NumberColumn(
                            "Precio unitario (€)",
                            min_value=0.0,
                            step=0.01,
                            format="%.2f",
                            default=0.0,
                            required=True,
                        ),
                        "IVA (%)": st.column_config.NumberColumn(
                            "IVA (%)",
                            min_value=0.0,
                            max_value=100.0,
                            step=1.0,
                            format="%.2f",
                            default=21.0,
                            required=True,
                        ),
                    },
                    num_rows="dynamic",
                    hide_index=True,
                    key=f"articulos_edicion_{factura_id}",
                    alt=f"Artículos de la factura {factura['numero_factura']}",
                )
                guardar_cambios, cancelar_edicion = st.columns(2)
                with guardar_cambios:
                    guardar = st.form_submit_button("Guardar cambios", type="primary")
                with cancelar_edicion:
                    cancelar = st.form_submit_button("Cancelar")

            if guardar:
                if hasattr(articulos_editados, "to_dict"):
                    lineas_editadas = articulos_editados.to_dict(orient="records")
                else:
                    lineas_editadas = list(articulos_editados)
                lineas_guardar = []
                datos_incompletos = False
                for linea in lineas_editadas:
                    concepto = str(linea.get("Concepto") or "").strip()
                    if not concepto:
                        continue
                    try:
                        cantidad_editada = int(linea["Cantidad"])
                        precio_editado = float(linea["Precio unitario (€)"])
                        iva_editado = float(linea["IVA (%)"])
                    except (TypeError, ValueError, OverflowError):
                        datos_incompletos = True
                        break
                    if (
                        cantidad_editada < 1
                        or precio_editado < 0
                        or not 0 <= iva_editado <= 100
                    ):
                        datos_incompletos = True
                        break
                    lineas_guardar.append(
                        {
                            "concepto": concepto,
                            "cantidad": cantidad_editada,
                            "precio": precio_editado,
                            "iva": iva_editado,
                        }
                    )
                if datos_incompletos:
                    st.error("Completa cantidad, precio e IVA en cada artículo antes de guardar.")
                elif not lineas_guardar:
                    st.error("La factura debe conservar al menos un artículo.")
                else:
                    actualizar_datos(
                        factura_id=factura_id,
                        cliente=cliente_editado,
                        cif=cif_editado,
                        fecha=fecha_editada.isoformat(),
                        numero_factura=numero_editado,
                        articulos=lineas_guardar,
                    )
                    st.session_state.pop("factura_en_edicion", None)
                    st.session_state["confirmacion_datos_actualizados"] = (
                        f"Datos de la factura {numero_editado} actualizados correctamente."
                    )
                    st.rerun()
            if cancelar:
                st.session_state.pop("factura_en_edicion", None)
                st.rerun()
        else:
            editar_col, generar_col = st.columns(2)
            if editar_col.button("Editar datos", key=f"editar_{factura_id}"):
                st.session_state["factura_en_edicion"] = factura_id
                st.rerun()
            if generar_col.button(
                "Generar Factura",
                key=f"generar_factura_{factura_id}",
                type="primary",
            ):
                generar_factura(factura_id)
                st.session_state["confirmacion_factura_generada"] = (
                    f"Factura {factura['numero_factura']} generada correctamente."
                )
                st.rerun()
