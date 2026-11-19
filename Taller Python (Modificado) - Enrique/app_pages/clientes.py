import streamlit as st

from facturas_db import guardar_cliente, inicializar_base_datos, obtener_clientes

inicializar_base_datos()
clientes = obtener_clientes()

st.title("Clientes")
st.write("Crea y consulta fichas de clientes identificadas por DNI, NIE o CIF.")

clave_a_cliente = {
    (str(cliente["documento_tipo"]), str(cliente["documento_numero"])): cliente
    for cliente in clientes
}
opciones = list(clave_a_cliente)
seleccion = st.selectbox(
    "Buscar cliente por DNI, NIE o CIF",
    options=[None, *opciones],
    index=0,
    format_func=lambda clave: (
        "＋ Alta de un cliente nuevo"
        if clave is None
        else f"{clave[0]} {clave[1]} · {clave_a_cliente[clave]['nombre']}"
    ),
    key="selector_ficha_cliente",
    help="Escribe el documento en el desplegable para localizar una ficha existente.",
)
cliente_actual = clave_a_cliente.get(seleccion) if seleccion else None
clave_widgets = (
    f"{cliente_actual['documento_tipo']}_{cliente_actual['documento_numero']}"
    if cliente_actual
    else "nuevo"
)

st.subheader("Datos del cliente")
with st.form("formulario_cliente"):
    tipos_documento = ["DNI", "NIE", "CIF"]
    tipo_actual = str((cliente_actual or {}).get("documento_tipo", "DNI"))
    tipo_indice = tipos_documento.index(tipo_actual) if tipo_actual in tipos_documento else 0
    tipo_documento = st.selectbox(
        "Tipo de documento",
        tipos_documento,
        index=tipo_indice,
        key=f"tipo_documento_ficha_{clave_widgets}",
        disabled=bool(cliente_actual),
    )
    documento = st.text_input(
        f"Número de {tipo_documento}",
        value=str((cliente_actual or {}).get("documento_numero", "")),
        placeholder="Por ejemplo, 12345678Z",
        key=f"numero_documento_ficha_{clave_widgets}",
        disabled=bool(cliente_actual),
    )
    nombre = st.text_input(
        "Nombre o razón social *",
        value=str((cliente_actual or {}).get("nombre", "")),
        key=f"nombre_ficha_cliente_{clave_widgets}",
    )
    email_col, telefono_col = st.columns(2)
    with email_col:
        email = st.text_input(
            "Correo electrónico",
            value=str((cliente_actual or {}).get("email", "")),
            key=f"email_ficha_cliente_{clave_widgets}",
        )
    with telefono_col:
        telefono = st.text_input(
            "Teléfono",
            value=str((cliente_actual or {}).get("telefono", "")),
            key=f"telefono_ficha_cliente_{clave_widgets}",
        )
    direccion = st.text_input(
        "Dirección fiscal",
        value=str((cliente_actual or {}).get("direccion", "")),
        key=f"direccion_ficha_cliente_{clave_widgets}",
    )
    postal_col, ciudad_col, provincia_col = st.columns(3)
    with postal_col:
        codigo_postal = st.text_input(
            "Código postal",
            value=str((cliente_actual or {}).get("codigo_postal", "")),
            key=f"cp_ficha_cliente_{clave_widgets}",
        )
    with ciudad_col:
        ciudad = st.text_input(
            "Ciudad",
            value=str((cliente_actual or {}).get("ciudad", "")),
            key=f"ciudad_ficha_cliente_{clave_widgets}",
        )
    with provincia_col:
        provincia = st.text_input(
            "Provincia",
            value=str((cliente_actual or {}).get("provincia", "")),
            key=f"provincia_ficha_cliente_{clave_widgets}",
        )
    pais = st.text_input(
        "País",
        value=str((cliente_actual or {}).get("pais", "España")),
        key=f"pais_ficha_cliente_{clave_widgets}",
    )
    notas = st.text_area(
        "Notas",
        value=str((cliente_actual or {}).get("notas", "")),
        key=f"notas_ficha_cliente_{clave_widgets}",
    )
    guardar = st.form_submit_button(
        "Actualizar ficha" if cliente_actual else "Dar de alta al cliente",
        type="primary",
    )

if guardar:
    if not documento.strip() or not nombre.strip():
        st.error("Indica el documento y el nombre o razón social del cliente.")
    else:
        guardar_cliente(
            documento_tipo=tipo_documento,
            documento_numero=documento,
            nombre=nombre,
            email=email,
            telefono=telefono,
            direccion=direccion,
            codigo_postal=codigo_postal,
            ciudad=ciudad,
            provincia=provincia,
            pais=pais,
            notas=notas,
        )
        st.session_state["confirmacion_cliente"] = f"Ficha de {nombre} guardada."
        st.rerun()

if "confirmacion_cliente" in st.session_state:
    st.success(st.session_state.pop("confirmacion_cliente"))

st.subheader("Clientes registrados")
clientes = obtener_clientes()
if clientes:
    st.dataframe(
        [
            {
                "Cliente": cliente["nombre"],
                "Documento": f"{cliente['documento_tipo']} {cliente['documento_numero']}",
                "Correo electrónico": cliente["email"],
                "Teléfono": cliente["telefono"],
                "Ciudad": cliente["ciudad"],
            }
            for cliente in clientes
        ],
        hide_index=True,
        width="stretch",
        alt="Clientes registrados",
    )
else:
    st.info("Todavía no hay clientes. Añade la primera ficha con el formulario.")
