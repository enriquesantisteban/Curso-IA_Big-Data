import streamlit as st
from facturas_db import inicializar_base_datos, obtener_orden_navegacion

st.set_page_config(page_title="Gestor de facturas", page_icon=":material/receipt_long:")
inicializar_base_datos()

paginas_por_id = {
    "introducir_datos": st.Page(
        "app_pages/introducir_datos.py",
        title="Introducir datos",
        icon=":material/edit_note:",
        help="Apartado para introducir los datos de clientes y facturas.",
    ),
    "clientes": st.Page(
        "app_pages/clientes.py",
        title="Clientes",
        icon=":material/group:",
        help="Alta y consulta de fichas de clientes.",
    ),
    "facturas": st.Page(
        "app_pages/facturas.py",
        title="Facturas",
        icon=":material/receipt_long:",
        help="Consulta y ordena todas las facturas registradas.",
    ),
    "productos": st.Page(
        "app_pages/productos.py",
        title="Productos",
        icon=":material/inventory_2:",
        help="Gestiona el catálogo de productos, fotos, precios e IVA.",
    ),
    "gastos": st.Page(
        "app_pages/gastos.py",
        title="Gastos",
        icon=":material/payments:",
        help="Registra y consulta los gastos de la empresa.",
    ),
    "generar_facturas": st.Page(
        "app_pages/generar_facturas.py",
        title="Generar facturas",
        icon=":material/description:",
        help="Apartado para preparar y generar facturas.",
    ),
    "informes": st.Page(
        "app_pages/informes.py",
        title="Informes",
        icon=":material/analytics:",
        help="Apartado para consultar informes sobre las facturas.",
    ),
    "diseno_factura": st.Page(
        "app_pages/diseno_factura.py",
        title="Diseño de factura",
        icon=":material/palette:",
        help="Personaliza los campos, colores, tipografía y logo de las facturas PDF.",
    ),
}
paginas = [paginas_por_id[page_id] for page_id in obtener_orden_navegacion()]
pagina_orden = st.Page(
    "app_pages/orden_menu.py",
    title="Orden del menú",
    icon=":material/reorder:",
    help="Personaliza el orden de las pestañas del menú lateral.",
)
paginas_con_ajustes = [*paginas, pagina_orden]
page = st.navigation(paginas_con_ajustes, position="hidden")

with st.sidebar:
    st.markdown("## LGNE PROXY")
    st.caption("Gestor de facturas")
    st.divider()
    for pagina in paginas_con_ajustes:
        st.page_link(pagina, label=pagina.title, icon=pagina.icon)

page.run()
