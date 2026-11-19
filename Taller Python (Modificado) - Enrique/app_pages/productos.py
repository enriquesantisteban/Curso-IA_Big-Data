import streamlit as st
import hashlib

from facturas_db import (
    cargar_productos_demo_si_vacio,
    eliminar_producto,
    guardar_producto,
    inicializar_base_datos,
    obtener_productos,
)

inicializar_base_datos()
cargar_productos_demo_si_vacio()
productos = obtener_productos()
producto_por_id = {int(producto["id"]): producto for producto in productos}

st.title("Productos")
st.write("Administra el catálogo de informática de LGNE PROXY con sus fotos, precios e IVA.")

opciones_producto = [None, *producto_por_id]
producto_seleccionado_id = st.selectbox(
    "Producto para editar",
    opciones_producto,
    format_func=lambda producto_id: (
        "Añadir producto nuevo"
        if producto_id is None
        else producto_por_id[producto_id]["nombre"]
    ),
    key="producto_a_editar",
)
producto_actual = producto_por_id.get(producto_seleccionado_id)
widget_sufijo = str(producto_seleccionado_id or "nuevo")

if producto_actual and producto_actual.get("foto"):
    st.image(
        producto_actual["foto"],
        caption=f"Foto actual · {producto_actual['nombre']}",
        width=260,
    )

st.subheader("Alta de producto" if producto_actual is None else "Editar producto")
with st.form("formulario_producto"):
    categorias = [
        "Equipos",
        "Monitores",
        "Periféricos",
        "Audio",
        "Almacenamiento",
        "Redes",
        "Cámaras",
        "Accesorios",
        "Otros",
    ]
    categoria_actual = str((producto_actual or {}).get("categoria", categorias[0]))
    if categoria_actual not in categorias:
        categorias.append(categoria_actual)
    nombre = st.text_input(
        "Nombre del producto *",
        value=str((producto_actual or {}).get("nombre", "")),
        key=f"nombre_producto_{widget_sufijo}",
    )
    categoria = st.selectbox(
        "Categoría",
        categorias,
        index=categorias.index(categoria_actual),
        key=f"categoria_producto_{widget_sufijo}",
    )
    descripcion = st.text_area(
        "Descripción",
        value=str((producto_actual or {}).get("descripcion", "")),
        key=f"descripcion_producto_{widget_sufijo}",
    )
    precio_col, iva_col = st.columns(2)
    with precio_col:
        precio = st.number_input(
            "Precio unitario (€)",
            min_value=0.0,
            value=float((producto_actual or {}).get("precio", 0.0)),
            step=1.0,
            format="%.2f",
            key=f"precio_producto_{widget_sufijo}",
        )
    with iva_col:
        iva = st.number_input(
            "IVA (%)",
            min_value=0.0,
            max_value=100.0,
            value=float((producto_actual or {}).get("iva", 21.0)),
            step=1.0,
            format="%.2f",
            key=f"iva_producto_{widget_sufijo}",
        )
    foto_subida = st.file_uploader(
        "Foto del producto (PNG, JPG o WEBP)",
        type=["png", "jpg", "jpeg", "webp"],
        key=f"foto_producto_{widget_sufijo}",
    )
    guardar = st.form_submit_button(
        "Guardar cambios" if producto_actual else "Dar de alta producto",
        type="primary",
    )

if guardar:
    if not nombre.strip():
        st.error("Escribe el nombre del producto.")
    else:
        try:
            guardar_producto(
                nombre=nombre,
                categoria=categoria,
                descripcion=descripcion,
                precio=precio,
                iva=iva,
                foto=foto_subida.getvalue() if foto_subida else None,
                producto_id=int(producto_seleccionado_id) if producto_seleccionado_id else None,
            )
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state["confirmacion_producto"] = f"Producto «{nombre}» guardado correctamente."
            st.rerun()

if "confirmacion_producto" in st.session_state:
    st.success(st.session_state.pop("confirmacion_producto"))
if "confirmacion_foto_producto" in st.session_state:
    st.success(st.session_state.pop("confirmacion_foto_producto"))

productos = obtener_productos()
st.subheader(f"Catálogo · {len(productos)} productos")
if productos:
    columnas = st.columns(3)
    for indice, producto in enumerate(productos):
        with columnas[indice % 3]:
            with st.container(border=True):
                if producto.get("foto"):
                    st.image(producto["foto"], width="stretch", alt=f"Foto de {producto['nombre']}")
                else:
                    foto_directa = st.file_uploader(
                        "Foto pendiente de añadir · pulsa para elegir",
                        type=["png", "jpg", "jpeg", "webp"],
                        key=f"foto_directa_producto_{producto['id']}",
                        help="La foto se guarda en este producto al seleccionarla.",
                    )
                    if foto_directa is not None:
                        bytes_foto = foto_directa.getvalue()
                        hash_foto = hashlib.sha256(bytes_foto).hexdigest()
                        clave_hash = f"foto_guardada_hash_{producto['id']}"
                        if st.session_state.get(clave_hash) != hash_foto:
                            guardar_producto(
                                nombre=str(producto["nombre"]),
                                categoria=str(producto["categoria"]),
                                descripcion=str(producto["descripcion"]),
                                precio=float(producto["precio"]),
                                iva=float(producto["iva"]),
                                foto=bytes_foto,
                                producto_id=int(producto["id"]),
                            )
                            st.session_state[clave_hash] = hash_foto
                            st.session_state["confirmacion_foto_producto"] = (
                                f"Foto de «{producto['nombre']}» guardada."
                            )
                            st.rerun()
                st.markdown(f"**{producto['nombre']}**")
                st.caption(str(producto["categoria"]))
                st.write(str(producto["descripcion"]))
                st.metric("Precio", f"{float(producto['precio']):,.2f} €")
                st.caption(f"IVA: {float(producto['iva']):g}%")
else:
    st.info("Todavía no hay productos en el catálogo.")
