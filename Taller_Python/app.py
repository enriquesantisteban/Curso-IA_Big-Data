import streamlit as st

st.set_page_config(page_title="Gestor de facturas", page_icon=":material/receipt_long:")

page = st.navigation(
    [
        st.Page(
            "app_pages/introducir_datos.py",
            title="Introducir datos",
            icon=":material/edit_note:",
            help="Apartado para introducir los datos de clientes y facturas.",
        ),
        st.Page(
            "app_pages/generar_facturas.py",
            title="Generar facturas",
            icon=":material/description:",
            help="Apartado para preparar y generar facturas.",
        ),
        st.Page(
            "app_pages/informes.py",
            title="Informes",
            icon=":material/analytics:",
            help="Apartado para consultar informes sobre las facturas.",
        ),
    ],
    position="sidebar",
)

page.run()
