import streamlit as st

from facturas_db import (
    ORDEN_NAVEGACION_DEFAULT,
    guardar_orden_navegacion,
    inicializar_base_datos,
    obtener_orden_navegacion,
)

inicializar_base_datos()

NOMBRES_PAGINAS = {
    "introducir_datos": "Introducir datos",
    "clientes": "Clientes",
    "facturas": "Facturas",
    "productos": "Productos",
    "gastos": "Gastos",
    "generar_facturas": "Generar facturas",
    "informes": "Informes",
    "diseno_factura": "Diseño de factura",
}

st.title("Orden del menú")
st.write("Elige una pestaña y la posición en la que quieres verla en la barra lateral.")

orden_actual = obtener_orden_navegacion()
st.subheader("Orden actual")
for posicion, pagina_id in enumerate(orden_actual, start=1):
    st.write(f"**{posicion}.** {NOMBRES_PAGINAS[pagina_id]}")

pagina_a_mover = st.selectbox(
    "Pestaña que quieres mover",
    orden_actual,
    format_func=lambda pagina_id: NOMBRES_PAGINAS[pagina_id],
)
posicion_actual = orden_actual.index(pagina_a_mover)
nueva_posicion = st.selectbox(
    "Nueva posición",
    options=list(range(1, len(orden_actual) + 1)),
    index=posicion_actual,
    format_func=lambda posicion: f"{posicion}. {NOMBRES_PAGINAS[orden_actual[posicion - 1]]}",
)

guardar_col, restablecer_col = st.columns(2)
if guardar_col.button("Guardar orden", type="primary", width="stretch"):
    nuevo_orden = orden_actual.copy()
    nuevo_orden.remove(pagina_a_mover)
    nuevo_orden.insert(nueva_posicion - 1, pagina_a_mover)
    guardar_orden_navegacion(nuevo_orden)
    st.session_state["confirmacion_orden_menu"] = "El orden del menú se ha guardado."
    st.rerun()

if restablecer_col.button("Restaurar orden inicial", width="stretch"):
    guardar_orden_navegacion(ORDEN_NAVEGACION_DEFAULT)
    st.session_state["confirmacion_orden_menu"] = "Se ha restaurado el orden inicial del menú."
    st.rerun()

if "confirmacion_orden_menu" in st.session_state:
    st.success(st.session_state.pop("confirmacion_orden_menu"))
