import streamlit as st

from facturas_db import guardar_cliente, inicializar_base_datos, obtener_clientes

inicializar_base_datos()
clientes = obtener_clientes()
clientes_por_codigo = {int(cliente["codigo"]): cliente for cliente in clientes}

st.title("Clientes")
st.write("Registra y consulta los datos de contacto, facturación y pago de cada cliente.")

seleccionado = st.selectbox(
    "Código de cliente",
    [None, *clientes_por_codigo],
    format_func=lambda codigo: (
        "Nuevo cliente"
        if codigo is None
        else f"{codigo:05d} · {clientes_por_codigo[codigo]['nombre']} · {clientes_por_codigo[codigo]['cif']}"
    ),
    key="codigo_cliente_edicion",
)
actual = clientes_por_codigo.get(seleccionado) if seleccionado else None
sufijo = str(seleccionado or "nuevo")

with st.form("formulario_cliente"):
    st.subheader("Editar cliente" if actual else "Dar de alta cliente")
    nombre = st.text_input(
        "Nombre o razón social *",
        value=str((actual or {}).get("nombre", "")),
        key=f"cliente_nombre_{sufijo}",
    )
    cif = st.text_input(
        "CIF *",
        value=str((actual or {}).get("cif", "")),
        key=f"cliente_cif_{sufijo}",
    )
    tel_col, email_col = st.columns(2)
    with tel_col:
        telefono = st.text_input(
            "Teléfono", value=str((actual or {}).get("telefono", "")), key=f"cliente_telefono_{sufijo}"
        )
    with email_col:
        email = st.text_input(
            "Correo electrónico", value=str((actual or {}).get("email", "")), key=f"cliente_email_{sufijo}"
        )
    direccion = st.text_input(
        "Dirección fiscal", value=str((actual or {}).get("direccion", "")), key=f"cliente_direccion_{sufijo}"
    )
    postal_col, ciudad_col, provincia_col = st.columns(3)
    with postal_col:
        codigo_postal = st.text_input(
            "Código postal", value=str((actual or {}).get("codigo_postal", "")), key=f"cliente_cp_{sufijo}"
        )
    with ciudad_col:
        ciudad = st.text_input(
            "Ciudad", value=str((actual or {}).get("ciudad", "")), key=f"cliente_ciudad_{sufijo}"
        )
    with provincia_col:
        provincia = st.text_input(
            "Provincia", value=str((actual or {}).get("provincia", "")), key=f"cliente_provincia_{sufijo}"
        )
    formas_pago = ["Transferencia", "Tarjeta", "Efectivo", "Domiciliación", "PayPal", "Otro"]
    forma_actual = str((actual or {}).get("forma_pago", ""))
    if forma_actual and forma_actual not in formas_pago:
        formas_pago.append(forma_actual)
    forma_pago = st.selectbox(
        "Forma de pago",
        ["Sin especificar", *formas_pago],
        index=(formas_pago.index(forma_actual) + 1) if forma_actual in formas_pago else 0,
        key=f"cliente_pago_{sufijo}",
    )
    observaciones = st.text_area(
        "Observaciones", value=str((actual or {}).get("observaciones", "")), key=f"cliente_obs_{sufijo}"
    )
    guardar = st.form_submit_button(
        "Guardar cambios" if actual else "Dar de alta cliente", type="primary"
    )

if guardar:
    if not nombre.strip() or not cif.strip():
        st.error("El nombre o razón social y el CIF son obligatorios.")
    else:
        try:
            codigo_nuevo = guardar_cliente(
                nombre=nombre,
                cif=cif,
                telefono=telefono,
                email=email,
                direccion=direccion,
                codigo_postal=codigo_postal,
                ciudad=ciudad,
                provincia=provincia,
                forma_pago="" if forma_pago == "Sin especificar" else forma_pago,
                observaciones=observaciones,
                codigo=int(seleccionado) if seleccionado is not None else None,
            )
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state["confirmacion_cliente"] = f"Cliente {nombre} guardado con código {codigo_nuevo:05d}."
            st.rerun()

if "confirmacion_cliente" in st.session_state:
    st.success(st.session_state.pop("confirmacion_cliente"))

st.subheader("Registro de clientes")
clientes = obtener_clientes()
if clientes:
    st.dataframe(
        [
            {
                "Código": f"{int(cliente['codigo']):05d}",
                "Nombre o razón social": cliente["nombre"],
                "CIF": cliente["cif"],
                "Teléfono": cliente["telefono"],
                "Correo electrónico": cliente["email"],
                "Dirección": cliente["direccion"],
                "Código postal": cliente["codigo_postal"],
                "Ciudad": cliente["ciudad"],
                "Provincia": cliente["provincia"],
                "Forma de pago": cliente["forma_pago"],
                "Observaciones": cliente["observaciones"],
            }
            for cliente in clientes
        ],
        hide_index=True,
        width="stretch",
        alt="Registro de clientes con código, contacto, forma de pago y observaciones",
    )
else:
    st.info("Todavía no hay clientes registrados.")
