from datetime import date

import streamlit as st

from facturas_db import guardar_gasto, inicializar_base_datos, obtener_gastos

inicializar_base_datos()

st.title("Gastos")
st.write("Registra y consulta los gastos de LGNE PROXY.")

with st.form("formulario_gasto"):
    proveedor = st.text_input("Proveedor o beneficiario", required=True)
    documento_col, fecha_col, numero_col = st.columns(3)
    with documento_col:
        documento = st.text_input("NIF/CIF del proveedor")
    with fecha_col:
        fecha = st.date_input("Fecha del gasto", value=date.today())
    with numero_col:
        numero_comprobante = st.text_input("Número de factura o comprobante")

    categoria_col, concepto_col = st.columns([1, 2])
    with categoria_col:
        categoria = st.selectbox(
            "Categoría",
            [
                "Alquiler",
                "Suministros",
                "Software y tecnología",
                "Transporte",
                "Material y equipo",
                "Servicios profesionales",
                "Marketing",
                "Impuestos y tasas",
                "Otros",
            ],
        )
    with concepto_col:
        concepto = st.text_input("Descripción del gasto", required=True)

    base_col, iva_col = st.columns(2)
    with base_col:
        base_imponible = st.number_input(
            "Base imponible (€)", min_value=0.0, value=0.0, step=10.0, format="%.2f"
        )
    with iva_col:
        iva = st.number_input(
            "IVA (%)", min_value=0.0, max_value=100.0, value=21.0, step=1.0, format="%.2f"
        )
    notas = st.text_area("Notas")
    guardar = st.form_submit_button("Guardar gasto", type="primary")

if guardar:
    if not proveedor.strip() or not concepto.strip():
        st.error("Indica el proveedor y la descripción del gasto.")
    else:
        guardar_gasto(
            proveedor=proveedor,
            documento=documento,
            fecha=fecha.isoformat(),
            numero_comprobante=numero_comprobante,
            categoria=categoria,
            concepto=concepto,
            base_imponible=base_imponible,
            iva=iva,
            notas=notas,
        )
        st.session_state["confirmacion_gasto"] = f"Gasto de {proveedor} guardado correctamente."
        st.rerun()

if "confirmacion_gasto" in st.session_state:
    st.success(st.session_state.pop("confirmacion_gasto"))

gastos = obtener_gastos()
st.subheader("Gastos registrados")
if gastos:
    filas = []
    total_acumulado = 0.0
    for gasto in gastos:
        importe_iva = round(float(gasto["base_imponible"]) * float(gasto["iva"]) / 100, 2)
        total = round(float(gasto["base_imponible"]) + importe_iva, 2)
        total_acumulado += total
        filas.append(
            {
                "Fecha": gasto["fecha"],
                "Proveedor": gasto["proveedor"],
                "NIF/CIF": gasto["documento"],
                "Factura / comprobante": gasto["numero_comprobante"],
                "Categoría": gasto["categoria"],
                "Descripción": gasto["concepto"],
                "Base imponible (€)": float(gasto["base_imponible"]),
                "IVA (%)": float(gasto["iva"]),
                "IVA (€)": importe_iva,
                "Total (€)": total,
                "Notas": gasto["notas"],
            }
        )
    metrica_total, metrica_cantidad, metrica_media = st.columns(3)
    metrica_total.metric("Gastos totales", f"{total_acumulado:,.2f} €", border=True)
    metrica_cantidad.metric("Número de gastos", len(gastos), border=True)
    metrica_media.metric(
        "Importe medio",
        f"{total_acumulado / len(gastos):,.2f} €",
        border=True,
    )
    st.dataframe(
        filas,
        hide_index=True,
        width="stretch",
        alt="Gastos registrados con proveedor, categoría, IVA e importe total",
    )
else:
    st.info("Todavía no hay gastos registrados.")
