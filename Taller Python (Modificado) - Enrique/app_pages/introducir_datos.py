from datetime import date, timedelta

import streamlit as st

from facturas_db import guardar_datos, inicializar_base_datos, obtener_clientes

inicializar_base_datos()
clientes = obtener_clientes()

st.title("Introducir datos")
st.write("Registra los datos del cliente y añade uno o varios artículos a la factura.")

cliente_por_documento = {
    (str(registro["documento_tipo"]), str(registro["documento_numero"])): registro
    for registro in clientes
}
seleccion_cliente = st.selectbox(
    "Usar ficha de cliente (opcional)",
    options=[None, *cliente_por_documento],
    index=0,
    format_func=lambda clave: (
        "Introducir un cliente manualmente"
        if clave is None
        else f"{clave[0]} {clave[1]} · {cliente_por_documento[clave]['nombre']}"
    ),
    key="cliente_para_factura",
    help="Escribe el DNI, NIE o CIF para buscar un cliente registrado.",
)
cliente_prefill = cliente_por_documento.get(seleccion_cliente) if seleccion_cliente else None

with st.form("formulario_factura"):
    if cliente_prefill:
        cliente = str(cliente_prefill["nombre"])
        documento_tipo = str(cliente_prefill["documento_tipo"])
        cif = str(cliente_prefill["documento_numero"])
        st.info(f"Cliente seleccionado: **{cliente}** · **{documento_tipo} {cif}**")
        datos_contacto = [
            str(cliente_prefill.get(campo) or "").strip()
            for campo in ("direccion", "codigo_postal", "ciudad", "provincia", "email", "telefono")
            if str(cliente_prefill.get(campo) or "").strip()
        ]
        if datos_contacto:
            st.caption(" · ".join(datos_contacto))
    else:
        cliente = st.text_input("Cliente", placeholder="Nombre o razón social", required=True)
        tipo_documento_col, documento_col = st.columns([1, 2])
        with tipo_documento_col:
            documento_tipo = st.selectbox("Identificación", ["CIF", "DNI", "NIE"])
        with documento_col:
            cif = st.text_input(
                f"Número de {documento_tipo}",
                placeholder="Documento del cliente",
                required=True,
                key="documento_cliente",
            )
    fecha_col, vencimiento_col = st.columns(2)
    with fecha_col:
        fecha = st.date_input("Fecha de emisión (calendario)", value=date.today())
    with vencimiento_col:
        fecha_vencimiento = st.date_input(
            "Fecha de vencimiento (calendario)",
            value=date.today() + timedelta(days=30),
        )
    numero_factura = st.text_input("Número de factura", required=True)
    st.markdown("**Artículos de la factura**")
    st.caption("Añade filas en la tabla para incluir más artículos.")
    articulos_editados = st.data_editor(
        [
            {
                "Concepto": "",
                "Cantidad": 1,
                "Precio unitario (€)": 0.0,
                "IVA (%)": 21.0,
            }
        ],
        column_config={
            "Concepto": st.column_config.TextColumn(
                "Concepto", required=True, width="large"
            ),
            "Cantidad": st.column_config.NumberColumn(
                "Cantidad", min_value=1, step=1, format="%d", default=1, required=True
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
        key="articulos_nueva_factura",
        alt="Artículos de la factura",
    )

    guardar = st.form_submit_button("Guardar Datos", type="primary")

if guardar:
    if hasattr(articulos_editados, "to_dict"):
        filas_articulos = articulos_editados.to_dict(orient="records")
    else:
        filas_articulos = list(articulos_editados)

    articulos = []
    datos_incompletos = False
    for fila in filas_articulos:
        concepto = str(fila.get("Concepto") or "").strip()
        if not concepto:
            continue
        try:
            cantidad = int(fila["Cantidad"])
            precio = float(fila["Precio unitario (€)"])
            iva = float(fila["IVA (%)"])
        except (TypeError, ValueError, OverflowError):
            datos_incompletos = True
            break
        if cantidad < 1 or precio < 0 or not 0 <= iva <= 100:
            datos_incompletos = True
            break
        articulos.append(
            {
                "concepto": concepto,
                "cantidad": cantidad,
                "precio": precio,
                "iva": iva,
            }
        )

    if datos_incompletos:
        st.error("Completa cantidad, precio e IVA en cada artículo antes de guardar.")
    elif not articulos:
        st.error("Añade al menos un artículo con su concepto antes de guardar.")
    else:
        guardar_datos(
            cliente=cliente,
            documento_tipo=documento_tipo,
            cif=cif,
            fecha=fecha.isoformat(),
            fecha_vencimiento=fecha_vencimiento.isoformat(),
            numero_factura=numero_factura,
            articulos=articulos,
        )
        st.success(f"Datos de la factura {numero_factura} guardados correctamente.")
