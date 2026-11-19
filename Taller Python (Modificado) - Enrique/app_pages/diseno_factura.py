import base64
from pathlib import Path

import streamlit as st

from facturas_db import (
    guardar_ajustes_factura,
    inicializar_base_datos,
    obtener_ajustes_factura,
)
from pdf_factura import generar_pdf_factura

inicializar_base_datos()
ajustes = obtener_ajustes_factura()
logo_por_defecto = next(
    (
        ruta
        for ruta in [
            Path(__file__).resolve().parent.parent / "Logo" / "lgne_proxy.png",
            Path(__file__).resolve().parent.parent / "Logo" / "logo.png",
            *sorted(
                candidate
                for candidate in (Path(__file__).resolve().parent.parent / "EOOEEOE").glob("*")
                if candidate.is_file()
                and candidate.suffix.casefold() in {".png", ".jpg", ".jpeg"}
            ),
        ]
        if ruta.is_file()
    ),
    None,
)

st.title("Diseño de factura")
st.write(
    "Personaliza el diseño de todos los PDF descargables. Los cambios se guardan "
    "en SQLite y se aplican también a las facturas ya generadas."
)

with st.form("ajustes_diseno_factura"):
    col_color, col_fuente = st.columns(2)
    with col_color:
        accent_color = st.color_picker("Color principal", str(ajustes["accent_color"]))
        text_color = st.color_picker("Color del texto", str(ajustes["text_color"]))
        panel_color = st.color_picker("Color de los paneles", str(ajustes["panel_color"]))
    with col_fuente:
        fuentes = ["Helvetica", "Times-Roman", "Courier"]
        font_family = st.selectbox(
            "Tipografía",
            fuentes,
            index=fuentes.index(str(ajustes["font_family"]))
            if ajustes["font_family"] in fuentes
            else 0,
        )
        st.caption("La tipografía elegida se aplica al contenido y a los títulos del PDF.")

    st.subheader("Datos de empresa")
    nombre_empresa = st.text_input("Nombre de empresa", value=str(ajustes["company_name"]))
    cif_empresa = st.text_input("CIF de empresa", value=str(ajustes["company_cif"]))
    web_empresa = st.text_input(
        "Web o contacto", value=str(ajustes["company_website"])
    )
    texto_pie = st.text_input("Texto al pie de factura", value=str(ajustes["footer_text"]))

    st.subheader("Elementos de la factura")
    col_elementos_a, col_elementos_b = st.columns(2)
    with col_elementos_a:
        mostrar_logo = st.checkbox("Mostrar logo", value=bool(ajustes["show_logo"]))
        mostrar_cliente = st.checkbox(
            "Bloque de cliente", value=bool(ajustes["show_client"])
        )
        mostrar_cif = st.checkbox(
            "CIF del cliente", value=bool(ajustes["show_client_cif"])
        )
        mostrar_fecha = st.checkbox(
            "Fecha de factura", value=bool(ajustes["show_client_date"])
        )
        mostrar_vencimiento = st.checkbox(
            "Fecha de vencimiento", value=bool(ajustes["show_due_date"])
        )
        mostrar_empresa = st.checkbox(
            "Bloque de empresa", value=bool(ajustes["show_company"])
        )
        mostrar_numero = st.checkbox(
            "Número de factura", value=bool(ajustes["show_invoice_number"])
        )
    with col_elementos_b:
        mostrar_articulos = st.checkbox(
            "Tabla de artículos", value=bool(ajustes["show_items"])
        )
        mostrar_totales = st.checkbox("Recuento y totales", value=bool(ajustes["show_totals"]))
        mostrar_web = st.checkbox(
            "Web o contacto", value=bool(ajustes["show_company_website"])
        )
        mostrar_pie = st.checkbox("Texto al pie", value=bool(ajustes["show_footer"]))

    st.caption("Puedes añadir y eliminar campos opcionales en el bloque de empresa.")
    campos_adicionales = st.data_editor(
        list(ajustes.get("additional_fields", [])) or [{"Campo": "", "Valor": ""}],
        column_config={
            "Campo": st.column_config.TextColumn("Campo", required=True),
            "Valor": st.column_config.TextColumn("Valor", required=True),
        },
        num_rows="dynamic",
        hide_index=True,
        key="campos_adicionales_factura",
        alt="Campos adicionales de la factura",
    )

    st.subheader("Logo")
    if ajustes.get("logo_base64"):
        st.caption("Se está usando el logo personalizado guardado.")
        st.image(
            base64.b64decode(str(ajustes["logo_base64"])),
            width=180,
            alt="Logo personalizado de la empresa",
        )
    elif logo_por_defecto and logo_por_defecto.is_file():
        st.caption(f"Logo detectado: {logo_por_defecto.parent.name}/{logo_por_defecto.name}")
        st.image(str(logo_por_defecto), width=180, alt="Logo actual de la empresa")
    else:
        st.info("No se ha encontrado el logo de LGNE PROXY ni un logo alternativo.")
    logo_subido = st.file_uploader(
        "Cambiar logo (PNG o JPEG)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=False,
    )
    guardar = st.form_submit_button("Guardar diseño", type="primary")

if guardar:
    if hasattr(campos_adicionales, "to_dict"):
        filas_campos = campos_adicionales.to_dict(orient="records")
    else:
        filas_campos = list(campos_adicionales)
    campos_guardados = [
        {"Campo": str(fila.get("Campo", "")).strip(), "Valor": str(fila.get("Valor", "")).strip()}
        for fila in filas_campos
        if str(fila.get("Campo", "")).strip() and str(fila.get("Valor", "")).strip()
    ]

    logo_base64 = str(ajustes.get("logo_base64", ""))
    if logo_subido is not None:
        logo_base64 = base64.b64encode(logo_subido.getvalue()).decode("ascii")

    ajustes_actualizados = {
        **ajustes,
        "accent_color": accent_color,
        "text_color": text_color,
        "panel_color": panel_color,
        "font_family": font_family,
        "company_name": nombre_empresa.strip(),
        "company_cif": cif_empresa.strip(),
        "company_website": web_empresa.strip(),
        "footer_text": texto_pie.strip(),
        "show_logo": mostrar_logo,
        "show_client": mostrar_cliente,
        "show_client_cif": mostrar_cif,
        "show_client_date": mostrar_fecha,
        "show_due_date": mostrar_vencimiento,
        "show_company": mostrar_empresa,
        "show_invoice_number": mostrar_numero,
        "show_items": mostrar_articulos,
        "show_totals": mostrar_totales,
        "show_company_website": mostrar_web,
        "show_footer": mostrar_pie,
        "additional_fields": campos_guardados,
        "logo_base64": logo_base64,
    }
    guardar_ajustes_factura(ajustes_actualizados)
    st.success("Diseño guardado. Ya se aplicará a las facturas descargables.")

with st.expander("Vista previa del PDF"):
    vista_previa = {
        "id": 0,
        "cliente": "Cliente de ejemplo",
        "cif": "B12345678",
        "fecha": "2026-11-12",
        "numero_factura": "DEMO-001",
        "articulos": [
            {"concepto": "Servicio de ejemplo", "cantidad": 2, "precio": 50, "iva": 21},
            {"concepto": "Artículo adicional", "cantidad": 1, "precio": 15, "iva": 10},
        ],
    }
    st.download_button(
        "Descargar vista previa en PDF",
        data=generar_pdf_factura(vista_previa, ajustes),
        file_name="vista_previa_factura.pdf",
        mime="application/pdf",
        key="descargar_vista_previa_factura",
        icon=":material/preview:",
        on_click="ignore",
    )
