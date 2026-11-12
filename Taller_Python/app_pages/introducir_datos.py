import streamlit as st

from facturas_db import guardar_datos, inicializar_base_datos, obtener_clientes

inicializar_base_datos()

st.title("Introducir datos")
st.write("Registra los datos del cliente y añade uno o varios artículos a la factura.")

clientes = obtener_clientes()
clientes_por_codigo = {int(cliente["codigo"]): cliente for cliente in clientes}
codigo_seleccionado = st.selectbox(
    "Cliente por código (opcional)",
    [None, *clientes_por_codigo],
    format_func=lambda codigo: (
        "Introducir cliente manualmente"
        if codigo is None
        else f"{codigo:05d} · {clientes_por_codigo[codigo]['nombre']} · {clientes_por_codigo[codigo]['cif']}"
    ),
    key="cliente_codigo_factura",
    help="Al elegir un código se cargan el nombre y el CIF del registro.",
)
cliente_elegido = clientes_por_codigo.get(codigo_seleccionado) if codigo_seleccionado else None

with st.form("formulario_factura"):
    cliente = st.text_input(
        "Cliente",
        value=str((cliente_elegido or {}).get("nombre", "")),
        placeholder="Nombre o razón social",
        required=True,
        key=f"nombre_cliente_factura_{codigo_seleccionado or 'manual'}",
    )
    cif = st.text_input(
        "CIF",
        value=str((cliente_elegido or {}).get("cif", "")),
        placeholder="CIF del cliente",
        required=True,
        key=f"cif_cliente_factura_{codigo_seleccionado or 'manual'}",
    )
    if cliente_elegido:
        datos_contacto = [
            str(cliente_elegido.get(campo) or "").strip()
            for campo in ("telefono", "email", "direccion", "codigo_postal", "ciudad", "provincia", "forma_pago")
            if str(cliente_elegido.get(campo) or "").strip()
        ]
        if datos_contacto:
            st.caption(" · ".join(datos_contacto))
    fecha = st.date_input("Fecha")
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
            cif=cif,
            fecha=fecha.isoformat(),
            numero_factura=numero_factura,
            articulos=articulos,
            cliente_codigo=int(codigo_seleccionado) if codigo_seleccionado is not None else None,
        )
        st.success(f"Datos de la factura {numero_factura} guardados correctamente.")
