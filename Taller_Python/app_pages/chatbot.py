from datetime import date, datetime
import math
import re

import streamlit as st

from facturas_db import (
    generar_factura,
    guardar_datos,
    inicializar_base_datos,
    obtener_clientes,
    obtener_facturas,
)
from qwen_facturas import ErrorQwen, extraer_datos_factura


ETIQUETAS = {
    "cliente": "el nombre del cliente",
    "cif": "el CIF/NIF del cliente",
    "fecha": "la fecha de la factura",
    "numero_factura": "el número de factura",
}


def _numero(valor: object) -> float | None:
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        numero = float(valor)
        return numero if math.isfinite(numero) else None
    texto = str(valor).strip().replace("€", "").replace(" ", "")
    if not texto:
        return None
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")
    elif re.fullmatch(r"[+-]?\d{1,3}(?:\.\d{3})+", texto):
        texto = texto.replace(".", "")
    try:
        numero = float(texto)
        return numero if math.isfinite(numero) else None
    except ValueError:
        return None


def _fecha_iso(valor: object) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(texto, formato).date().isoformat()
        except ValueError:
            pass
    try:
        return date.fromisoformat(texto[:10]).isoformat()
    except ValueError:
        return None


def _valor_o_anterior(nuevo: object, anterior: object) -> object:
    return nuevo if nuevo not in (None, "") else anterior


def _normalizar_borrador(
    extraido: dict[str, object], anterior: dict[str, object] | None
) -> dict[str, object]:
    anterior = anterior or {}
    borrador: dict[str, object] = {}
    for campo in ("cliente", "cif", "numero_factura"):
        valor = _valor_o_anterior(extraido.get(campo), anterior.get(campo))
        borrador[campo] = str(valor).strip() if valor not in (None, "") else None
    borrador["fecha"] = _fecha_iso(extraido.get("fecha")) or _fecha_iso(anterior.get("fecha"))

    anteriores = anterior.get("articulos", [])
    if not isinstance(anteriores, list):
        anteriores = []
    nuevos = extraido.get("articulos", [])
    if isinstance(nuevos, dict):
        nuevos = [nuevos]
    if not isinstance(nuevos, list):
        nuevos = []

    articulos_anteriores = [
        item if isinstance(item, dict) else {} for item in anteriores
    ]
    usados: set[int] = set()
    articulos = []
    for indice, articulo_nuevo in enumerate(nuevos):
        if not isinstance(articulo_nuevo, dict):
            continue
        concepto_nuevo = str(articulo_nuevo.get("concepto") or "").strip()
        coincidencia = None
        if concepto_nuevo:
            for i, item in enumerate(articulos_anteriores):
                if i not in usados and str(item.get("concepto") or "").strip().casefold() == concepto_nuevo.casefold():
                    coincidencia = i
                    break
        elif len(nuevos) == 1 and len(articulos_anteriores) == 1:
            coincidencia = 0
        elif indice < len(articulos_anteriores) and indice not in usados:
            coincidencia = indice
        previo = articulos_anteriores[coincidencia] if coincidencia is not None else {}
        if coincidencia is not None:
            usados.add(coincidencia)
        item = {"concepto": None, "cantidad": None, "precio": None, "iva": None}
        item["concepto"] = _valor_o_anterior(articulo_nuevo.get("concepto"), previo.get("concepto"))
        cantidad_nueva = _numero(articulo_nuevo.get("cantidad"))
        cantidad = cantidad_nueva if cantidad_nueva is not None else _numero(previo.get("cantidad"))
        precio_nuevo = _numero(articulo_nuevo.get("precio"))
        precio = precio_nuevo if precio_nuevo is not None else _numero(previo.get("precio"))
        iva_nuevo = _numero(articulo_nuevo.get("iva"))
        iva = iva_nuevo if iva_nuevo is not None else _numero(previo.get("iva"))
        if cantidad is None or cantidad < 1 or not cantidad.is_integer():
            cantidad = _numero(previo.get("cantidad"))
        if precio is None or precio < 0:
            precio = _numero(previo.get("precio"))
        if iva is None or not 0 <= iva <= 100:
            iva = _numero(previo.get("iva"))
        item["cantidad"] = int(cantidad) if cantidad is not None and cantidad >= 1 and cantidad.is_integer() else None
        item["precio"] = precio if precio is not None and precio >= 0 else None
        item["iva"] = iva if iva is not None and 0 <= iva <= 100 else None
        if item["concepto"] not in (None, "") or any(item[k] is not None for k in ("cantidad", "precio", "iva")):
            articulos.append(item)

    if not articulos and articulos_anteriores:
        articulos = articulos_anteriores
    else:
        for indice, item in enumerate(articulos_anteriores):
            if indice not in usados:
                articulos.append(item)
    borrador["articulos"] = articulos
    return borrador


def _faltantes(borrador: dict[str, object]) -> list[str]:
    faltantes = [ETIQUETAS[campo] for campo in ETIQUETAS if not borrador.get(campo)]
    articulos = borrador.get("articulos")
    if not isinstance(articulos, list) or not articulos:
        faltantes.append("al menos un artículo con concepto, cantidad, precio unitario e IVA")
        return faltantes
    for indice, articulo in enumerate(articulos, start=1):
        articulo = articulo if isinstance(articulo, dict) else {}
        prefijo = f"el artículo {indice}: "
        if not str(articulo.get("concepto") or "").strip():
            faltantes.append(prefijo + "su concepto")
        if articulo.get("cantidad") is None:
            faltantes.append(prefijo + "la cantidad (unidades enteras)")
        if articulo.get("precio") is None:
            faltantes.append(prefijo + "el precio unitario antes de IVA")
        if articulo.get("iva") is None:
            faltantes.append(prefijo + "el porcentaje de IVA")
    return faltantes


def _respuesta_faltantes(faltantes: list[str]) -> str:
    if not faltantes:
        return "He completado los datos. Revísalos en el resumen antes de guardar."
    lista = "\n".join(f"- {dato[0].upper() + dato[1:]}" for dato in faltantes)
    return "Para completar la factura, dime por favor:\n\n" + lista


inicializar_base_datos()
st.title("Chatbot de facturas")
st.caption("Pega la factura como texto. Qwen 2.5 extraerá los datos y te preguntará lo que falte.")
st.info("Qwen 2.5 se ejecuta en Ollama en este equipo. Revisa los importes antes de guardar.", icon=":material/lock:")

if st.session_state.get("confirmacion_chat_factura"):
    st.success(st.session_state.pop("confirmacion_chat_factura"))

mensajes = st.session_state.setdefault("chat_factura_mensajes", [])
borrador = st.session_state.get("chat_factura_borrador")
faltantes = _faltantes(borrador) if isinstance(borrador, dict) else ["el texto de la factura"]

if not mensajes:
    with st.chat_message("assistant"):
        st.markdown(
            "Hola. Pega el texto de una factura y extraeré cliente, CIF, fecha, "
            "número e importe de cada artículo. Si algo no aparece, te preguntaré."
        )
for mensaje in mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

if faltantes:
    with st.form("formulario_texto_chat_factura", clear_on_submit=True):
        texto_nuevo = st.text_area(
            "Texto de la factura o respuesta a los datos pendientes",
            height=170,
            max_chars=50000,
            placeholder=(
                "Ejemplo: Factura F-2026-104 del 12/11/2026. Cliente Acme S.L., CIF B12345678. "
                "Dos monitores de 27 pulgadas a 180 € cada uno, IVA 21 %."
            ),
            label_visibility="collapsed",
        )
        enviar = st.form_submit_button("Enviar a Qwen 2.5", type="primary", icon=":material/auto_awesome:")
    if enviar:
        if not texto_nuevo.strip():
            st.warning("Pega el texto de la factura o responde a los datos que faltan.")
        else:
            mensajes.append({"role": "user", "content": texto_nuevo.strip()})
            try:
                with st.spinner("Qwen 2.5 está leyendo la factura…"):
                    extraido = extraer_datos_factura(texto_nuevo, borrador)
                borrador = _normalizar_borrador(extraido, borrador)
                st.session_state["chat_factura_borrador"] = borrador
                st.session_state["chat_factura_revision"] = int(
                    st.session_state.get("chat_factura_revision", 0)
                ) + 1
                faltantes = _faltantes(borrador)
                mensajes.append({"role": "assistant", "content": _respuesta_faltantes(faltantes)})
            except ErrorQwen as error:
                mensajes.append({"role": "assistant", "content": f"No he podido analizar el texto. {error}"})
            st.rerun()
else:
    st.divider()
    st.subheader("Revisa los datos extraídos")
    st.caption("Puedes corregir cualquier campo antes de guardar. La factura no se guardará hasta que pulses uno de los botones.")
    revision = int(st.session_state.get("chat_factura_revision", 1))
    with st.form(f"formulario_revision_factura_{revision}"):
        cliente_col, cif_col = st.columns(2)
        with cliente_col:
            cliente = st.text_input("Cliente", value=str(borrador["cliente"]), key=f"chat_cliente_{revision}")
        with cif_col:
            cif = st.text_input("CIF/NIF", value=str(borrador["cif"]), key=f"chat_cif_{revision}")
        fecha_col, numero_col = st.columns(2)
        with fecha_col:
            fecha_factura = st.date_input(
                "Fecha", value=date.fromisoformat(str(borrador["fecha"])),
                format="DD/MM/YYYY", key=f"chat_fecha_{revision}",
            )
        with numero_col:
            numero_factura = st.text_input(
                "Número de factura", value=str(borrador["numero_factura"]),
                key=f"chat_numero_{revision}",
            )
        articulos_editados = st.data_editor(
            [
                {
                    "Concepto": str(articulo["concepto"]),
                    "Cantidad": int(articulo["cantidad"]),
                    "Precio unitario (€)": float(articulo["precio"]),
                    "IVA (%)": float(articulo["iva"]),
                }
                for articulo in borrador["articulos"]
            ],
            column_config={
                "Concepto": st.column_config.TextColumn("Concepto", required=True, width="large"),
                "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1, format="%d", required=True),
                "Precio unitario (€)": st.column_config.NumberColumn("Precio unitario (€)", min_value=0.0, step=0.01, format="%.2f", required=True),
                "IVA (%)": st.column_config.NumberColumn("IVA (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.2f", required=True),
            },
            num_rows="dynamic",
            hide_index=True,
            key=f"chat_articulos_{revision}",
            alt="Revisa los artículos extraídos de la factura",
        )
        st.caption("Guardar como pendiente permite revisar y generar la factura después. La otra opción la genera directamente.")
        guardar_col, generar_col = st.columns(2)
        guardar_pendiente = guardar_col.form_submit_button("Guardar como pendiente", width="stretch")
        guardar_generar = generar_col.form_submit_button("Guardar y generar factura", type="primary", width="stretch")

    if guardar_pendiente or guardar_generar:
        if not cliente.strip() or not cif.strip() or not numero_factura.strip():
            st.error("Completa el cliente, CIF/NIF y número de factura.")
        else:
            filas = articulos_editados.to_dict(orient="records") if hasattr(articulos_editados, "to_dict") else list(articulos_editados)
            articulos = []
            error_articulos = False
            for linea in filas:
                concepto = str(linea.get("Concepto") or "").strip()
                if not concepto:
                    continue
                try:
                    cantidad = int(linea["Cantidad"])
                    precio = float(linea["Precio unitario (€)"])
                    iva = float(linea["IVA (%)"])
                except (TypeError, ValueError, OverflowError):
                    error_articulos = True
                    break
                if cantidad < 1 or precio < 0 or not 0 <= iva <= 100:
                    error_articulos = True
                    break
                articulos.append({"concepto": concepto, "cantidad": cantidad, "precio": precio, "iva": iva})
            if error_articulos or not articulos:
                st.error("Revisa los artículos. Cada línea necesita concepto, cantidad, precio e IVA válidos.")
            else:
                numero_normalizado = numero_factura.strip().casefold()
                repetida = any(
                    str(factura["numero_factura"]).strip().casefold() == numero_normalizado
                    for factura in obtener_facturas()
                )
                if repetida:
                    st.error("Ya existe una factura con ese número. Corrígelo antes de guardar.")
                else:
                    cliente_registrado = next(
                        (c for c in obtener_clientes() if str(c["cif"]).strip().casefold() == cif.strip().casefold()),
                        None,
                    )
                    guardar_datos(
                        cliente=cliente.strip(),
                        cif=cif.strip(),
                        fecha=fecha_factura.isoformat(),
                        numero_factura=numero_factura.strip(),
                        articulos=articulos,
                        cliente_codigo=int(cliente_registrado["codigo"]) if cliente_registrado else None,
                    )
                    if guardar_generar:
                        factura_guardada = next(
                            f for f in obtener_facturas()
                            if str(f["numero_factura"]).strip().casefold() == numero_normalizado
                        )
                        generar_factura(int(factura_guardada["id"]))
                        confirmacion = f"Factura {numero_factura.strip()} guardada y generada correctamente. Ya aparece en Informes."
                    else:
                        confirmacion = f"Factura {numero_factura.strip()} guardada como pendiente. Puedes terminarla en «Generar facturas»."
                    st.session_state["confirmacion_chat_factura"] = confirmacion
                    st.session_state["chat_factura_revision"] = revision + 1
                    for clave in (
                        "chat_factura_mensajes", "chat_factura_borrador"
                    ):
                        st.session_state.pop(clave, None)
                    st.rerun()

    if st.button("Empezar otra factura", icon=":material/add:"):
        st.session_state["chat_factura_revision"] = revision + 1
        for clave in ("chat_factura_mensajes", "chat_factura_borrador"):
            st.session_state.pop(clave, None)
        st.rerun()
