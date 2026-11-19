from datetime import date

import streamlit as st

from facturas_db import inicializar_base_datos, obtener_facturas

inicializar_base_datos()
facturas = obtener_facturas()

st.title("Facturas")
st.write("Consulta, filtra y ordena las facturas registradas.")

if not facturas:
    st.info("Todavía no hay facturas. Añade una desde «Introducir datos».")
else:
    filas = []
    for factura in facturas:
        articulos = factura["articulos"]
        subtotal = sum(
            round(int(articulo["cantidad"]) * float(articulo["precio"]), 2)
            for articulo in articulos
        )
        iva = sum(
            round(
                round(int(articulo["cantidad"]) * float(articulo["precio"]), 2)
                * float(articulo["iva"])
                / 100,
                2,
            )
            for articulo in articulos
        )
        conceptos = ", ".join(str(articulo["concepto"]) for articulo in articulos)
        filas.append(
            {
                "Número de factura": str(factura["numero_factura"]),
                "Cliente": str(factura["cliente"]),
                "Documento": f"{factura.get('documento_tipo') or 'CIF'} {factura['cif']}",
                "Fecha de emisión": str(factura["fecha"]),
                "Fecha de vencimiento": str(factura.get("fecha_vencimiento") or ""),
                "Conceptos": conceptos,
                "Unidades": sum(int(articulo["cantidad"]) for articulo in articulos),
                "Subtotal (€)": round(subtotal, 2),
                "IVA (€)": round(iva, 2),
                "Importe total (€)": round(subtotal + iva, 2),
                "Estado de generación": str(factura.get("estado") or "Generada"),
                "Estado de pago": str(factura.get("estado_pago") or "Pendiente"),
            }
        )

    filtro_col, pago_col, busqueda_col = st.columns([1, 1, 2])
    with filtro_col:
        filtro_generacion = st.selectbox(
            "Estado de generación",
            ["Todas", "Pendientes de generar", "Generadas"],
        )
    with pago_col:
        filtro_pago = st.selectbox(
            "Estado de pago",
            ["Todos", "Pendiente", "Pagada", "Vencida"],
        )
    with busqueda_col:
        busqueda = st.text_input(
            "Buscar cliente, documento o número de factura",
            placeholder="Escribe para filtrar…",
        ).strip().casefold()

    orden_col, direccion_col = st.columns([2, 1])
    with orden_col:
        ordenar_por = st.selectbox(
            "Ordenar por",
            [
                "Fecha de emisión",
                "Nombre del cliente",
                "Número de unidades",
                "Importe total",
                "Fecha de vencimiento",
                "Número de factura",
                "Estado de pago",
            ],
            index=0,
        )
    with direccion_col:
        direccion = st.selectbox("Orden", ["Más reciente / mayor primero", "Más antiguo / menor primero"])

    visibles = filas
    if filtro_generacion != "Todas":
        estado_objetivo = "Pendiente" if filtro_generacion == "Pendientes de generar" else "Generada"
        visibles = [fila for fila in visibles if fila["Estado de generación"] == estado_objetivo]
    if filtro_pago != "Todos":
        visibles = [fila for fila in visibles if fila["Estado de pago"] == filtro_pago]
    if busqueda:
        visibles = [
            fila
            for fila in visibles
            if busqueda
            in " ".join(
                str(fila[campo])
                for campo in ("Cliente", "Documento", "Número de factura")
            ).casefold()
        ]

    ascendente = direccion == "Más antiguo / menor primero"
    campo_orden = {
        "Fecha de emisión": "Fecha de emisión",
        "Nombre del cliente": "Cliente",
        "Número de unidades": "Unidades",
        "Importe total": "Importe total (€)",
        "Fecha de vencimiento": "Fecha de vencimiento",
        "Número de factura": "Número de factura",
        "Estado de pago": "Estado de pago",
    }[ordenar_por]
    if campo_orden == "Fecha de vencimiento":
        con_vencimiento = [fila for fila in visibles if fila[campo_orden]]
        sin_vencimiento = [fila for fila in visibles if not fila[campo_orden]]
        con_vencimiento.sort(key=lambda fila: fila[campo_orden], reverse=not ascendente)
        visibles = con_vencimiento + sin_vencimiento
    elif campo_orden == "Fecha de emisión":
        visibles.sort(key=lambda fila: date.fromisoformat(fila[campo_orden]), reverse=not ascendente)
    elif campo_orden in {"Unidades", "Importe total (€)"}:
        visibles.sort(key=lambda fila: float(fila[campo_orden]), reverse=not ascendente)
    else:
        visibles.sort(key=lambda fila: str(fila[campo_orden]).casefold(), reverse=not ascendente)

    st.caption(f"Mostrando {len(visibles)} de {len(facturas)} facturas. Puedes pulsar cualquier encabezado para ordenar directamente la tabla.")
    st.dataframe(
        visibles,
        hide_index=True,
        width="stretch",
        height=560,
        column_config={
            "Unidades": st.column_config.NumberColumn("Unidades", format="%d"),
            "Subtotal (€)": st.column_config.NumberColumn("Subtotal (€)", format="%.2f"),
            "IVA (€)": st.column_config.NumberColumn("IVA (€)", format="%.2f"),
            "Importe total (€)": st.column_config.NumberColumn("Importe total (€)", format="%.2f"),
        },
        alt="Facturas con cliente, fechas, artículos, importes y estados",
    )
