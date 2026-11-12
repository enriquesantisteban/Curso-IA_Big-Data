import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "facturas.db"


CATEGORIAS_GASTO = (
    "Alquiler y comunidad",
    "Electricidad",
    "Agua",
    "Gas y calefacción",
    "Telefonía e Internet",
    "Material de oficina",
    "Equipos informáticos",
    "Software y licencias",
    "Servicios en la nube",
    "Reparaciones y mantenimiento",
    "Limpieza",
    "Seguros",
    "Asesoría y contabilidad",
    "Servicios legales",
    "Comisiones bancarias",
    "Impuestos y tasas",
    "Nóminas y personal",
    "Formación",
    "Marketing y publicidad",
    "Web y dominio",
    "Transporte y mensajería",
    "Combustible y vehículos",
    "Viajes y alojamiento",
    "Dietas y comidas",
    "Suministros y compras",
    "Suscripciones",
    "Servicios profesionales",
    "Otros gastos",
)

ESTADOS_GASTO = ("Pendiente", "Pagado", "Vencido")


def inicializar_gastos() -> None:
    with sqlite3.connect(DATABASE_PATH) as conexion:
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS gastos_empresa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                proveedor TEXT NOT NULL,
                cif_proveedor TEXT NOT NULL DEFAULT '',
                numero_documento TEXT NOT NULL DEFAULT '',
                categoria TEXT NOT NULL,
                concepto TEXT NOT NULL,
                importe REAL NOT NULL,
                iva REAL NOT NULL DEFAULT 21,
                forma_pago TEXT NOT NULL DEFAULT '',
                estado_pago TEXT NOT NULL DEFAULT 'Pendiente',
                observaciones TEXT NOT NULL DEFAULT '',
                creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def obtener_gastos() -> list[dict[str, object]]:
    with sqlite3.connect(DATABASE_PATH) as conexion:
        conexion.row_factory = sqlite3.Row
        filas = conexion.execute(
            "SELECT * FROM gastos_empresa ORDER BY fecha DESC, id DESC"
        ).fetchall()
    return [dict(fila) for fila in filas]


def guardar_gasto(
    *,
    fecha: str,
    proveedor: str,
    cif_proveedor: str,
    numero_documento: str,
    categoria: str,
    concepto: str,
    importe: float,
    iva: float,
    forma_pago: str,
    estado_pago: str,
    observaciones: str,
    gasto_id: int | None = None,
) -> int:
    if not proveedor.strip() or not concepto.strip():
        raise ValueError("El proveedor y el concepto son obligatorios.")
    if importe <= 0:
        raise ValueError("El importe debe ser mayor que cero.")
    if not 0 <= iva <= 100:
        raise ValueError("El IVA debe estar entre 0 y 100.")
    if categoria not in CATEGORIAS_GASTO:
        raise ValueError("Selecciona una categoría de gasto válida.")
    if estado_pago not in ESTADOS_GASTO:
        raise ValueError("Selecciona un estado válido.")

    valores = (
        fecha,
        proveedor.strip(),
        cif_proveedor.strip().upper(),
        numero_documento.strip(),
        categoria,
        concepto.strip(),
        round(float(importe), 2),
        float(iva),
        forma_pago.strip(),
        estado_pago,
        observaciones.strip(),
    )
    with sqlite3.connect(DATABASE_PATH) as conexion:
        if gasto_id is None:
            cursor = conexion.execute(
                """
                INSERT INTO gastos_empresa (
                    fecha, proveedor, cif_proveedor, numero_documento, categoria,
                    concepto, importe, iva, forma_pago, estado_pago, observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                valores,
            )
            return int(cursor.lastrowid)
        conexion.execute(
            """
            UPDATE gastos_empresa SET
                fecha = ?, proveedor = ?, cif_proveedor = ?, numero_documento = ?,
                categoria = ?, concepto = ?, importe = ?, iva = ?, forma_pago = ?,
                estado_pago = ?, observaciones = ?
            WHERE id = ?
            """,
            (*valores, int(gasto_id)),
        )
    return int(gasto_id)


def eliminar_gasto(gasto_id: int) -> None:
    with sqlite3.connect(DATABASE_PATH) as conexion:
        conexion.execute("DELETE FROM gastos_empresa WHERE id = ?", (int(gasto_id),))
