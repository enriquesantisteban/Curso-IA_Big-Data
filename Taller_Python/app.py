from pathlib import Path

import streamlit as st
from tema import aplicar_tema

st.set_page_config(
    page_title="LGNE PROXY · Gestor de facturas",
    page_icon=":material/receipt_long:",
    layout="wide",
)
aplicar_tema()

logo_path = Path(__file__).resolve().parent / "Logo" / "logo.png"
if logo_path.is_file():
    st.logo(str(logo_path), size="large")

page = st.navigation(
    {
        "": [
            st.Page(
                "app_pages/inicio.py",
                title="Inicio",
                icon=":material/dashboard:",
                help="Resumen visual del estado del gestor.",
            ),
            st.Page(
                "app_pages/introducir_datos.py",
                title="Introducir datos",
                icon=":material/edit_note:",
                help="Registra facturas y sus artículos.",
            ),
            st.Page(
                "app_pages/generar_facturas.py",
                title="Generar facturas",
                icon=":material/description:",
                help="Revisa los datos y genera facturas listas para descargar.",
            ),
            st.Page(
                "app_pages/informes.py",
                title="Informes",
                icon=":material/analytics:",
                help="Consulta indicadores, evolución mensual y facturas generadas.",
            ),
            st.Page(
                "app_pages/gastos.py",
                title="Gastos",
                icon=":material/payments:",
                help="Registra y controla los gastos de la empresa.",
            ),
            st.Page(
                "app_pages/chatbot.py",
                title="Chatbot",
                icon=":material/auto_awesome:",
                help="Crea una factura pegando su texto a Qwen 2.5.",
            ),
        ],
        "Gestión": [
            st.Page(
                "app_pages/clientes.py",
                title="Clientes",
                icon=":material/group:",
                help="Consulta y actualiza el registro de clientes.",
            ),
        ],
    },
    position="top",
)

page.run()
