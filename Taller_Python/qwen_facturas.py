import json
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"
MODELO_QWEN = "qwen2.5:3b"


class ErrorQwen(RuntimeError):
    pass


def extraer_datos_factura(
    texto_nuevo: str,
    borrador_actual: dict[str, object] | None = None,
) -> dict[str, object]:
    """Actualiza un borrador de factura a partir de texto usando Qwen local."""
    system = """Eres un extractor cuidadoso de facturas en español.
Devuelve exclusivamente un objeto JSON válido. No inventes ningún dato ni calcules
campos que no aparezcan en el texto. Usa null para los campos ausentes. Conserva
los datos del borrador salvo que el texto nuevo los corrija expresamente. No
 dupliques artículos: actualiza una línea existente si el nuevo texto la aclara y
añade solo líneas de conceptos nuevos. Cada artículo debe tener concepto,
cantidad entera, precio unitario antes de IVA e IVA
porcentual. Convierte las fechas conocidas a AAAA-MM-DD y los importes a números
decimales, sin símbolos de moneda. No confundas el total de línea con el precio
unitario. Si solo aparece un total sin cantidad o precio unitario, deja esos
campos en null.

Esquema obligatorio:
{"cliente":null,"cif":null,"fecha":null,"numero_factura":null,
 "articulos":[{"concepto":null,"cantidad":null,"precio":null,"iva":null}]}"""
    user = (
        "BORRADOR ACTUAL (puede estar incompleto):\n"
        + json.dumps(borrador_actual or {}, ensure_ascii=False)
        + "\n\nTEXTO NUEVO DEL USUARIO:\n"
        + texto_nuevo.strip()
    )
    body = json.dumps(
        {
            "model": MODELO_QWEN,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0, "num_ctx": 8192},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        OLLAMA_CHAT_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(request, timeout=180) as response:
            resultado = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detalle = error.read().decode("utf-8", errors="replace")[:500]
        if error.code == 404:
            raise ErrorQwen(
                f"Ollama no encuentra {MODELO_QWEN}. Comprueba que el modelo esté instalado."
            ) from error
        raise ErrorQwen(f"Ollama respondió con error ({error.code}): {detalle}") from error
    except (URLError, TimeoutError, OSError) as error:
        raise ErrorQwen(
            "No se pudo conectar con Ollama en 127.0.0.1:11434. Inicia Ollama e inténtalo de nuevo."
        ) from error
    except json.JSONDecodeError as error:
        raise ErrorQwen("Ollama devolvió una respuesta que no se pudo leer.") from error

    contenido = (resultado.get("message") or {}).get("content", "")
    try:
        datos = json.loads(contenido)
    except (TypeError, json.JSONDecodeError) as error:
        raise ErrorQwen("Qwen no devolvió los datos de la factura en formato JSON.") from error
    if not isinstance(datos, dict):
        raise ErrorQwen("Qwen devolvió un formato de factura inesperado.")
    return datos
