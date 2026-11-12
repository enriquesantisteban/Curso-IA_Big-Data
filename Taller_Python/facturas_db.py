import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path
import re

DATABASE_PATH = Path(__file__).resolve().parent / "facturas.db"


@contextmanager
def conectar() -> Iterator[sqlite3.Connection]:
    conexion = sqlite3.connect(DATABASE_PATH)
    try:
        with conexion:
            yield conexion
    finally:
        conexion.close()


def inicializar_base_datos() -> None:
    with conectar() as conexion:
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS facturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                cif TEXT NOT NULL,
                fecha TEXT NOT NULL,
                numero_factura TEXT NOT NULL,
                concepto TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                precio REAL NOT NULL,
                iva REAL NOT NULL
            )
            """
        )
        columnas = {
            fila[1] for fila in conexion.execute("PRAGMA table_info(facturas)")
        }
        if "estado" not in columnas:
            # Las facturas existentes ya se guardaban como facturas completas.
            conexion.execute(
                "ALTER TABLE facturas ADD COLUMN estado TEXT NOT NULL DEFAULT 'Generada'"
            )
        if "cliente_codigo" not in columnas:
            conexion.execute("ALTER TABLE facturas ADD COLUMN cliente_codigo INTEGER")
        if "estado_pago" not in columnas:
            conexion.execute(
                "ALTER TABLE facturas ADD COLUMN estado_pago TEXT NOT NULL DEFAULT 'Pendiente'"
            )

        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS articulos_factura (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factura_id INTEGER NOT NULL REFERENCES facturas(id),
                orden INTEGER NOT NULL,
                concepto TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                precio REAL NOT NULL,
                iva REAL NOT NULL,
                UNIQUE (factura_id, orden)
            )
            """
        )
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS clientes (
                codigo INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                cif TEXT NOT NULL DEFAULT '',
                telefono TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                direccion TEXT NOT NULL DEFAULT '',
                codigo_postal TEXT NOT NULL DEFAULT '',
                ciudad TEXT NOT NULL DEFAULT '',
                provincia TEXT NOT NULL DEFAULT '',
                forma_pago TEXT NOT NULL DEFAULT '',
                observaciones TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conexion.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_clientes_cif_unico "
            "ON clientes(cif COLLATE NOCASE) WHERE TRIM(cif) <> ''"
        )
        # Migra clientes existentes desde facturas, conservando el código de cada CIF.
        conexion.execute(
            """
            INSERT INTO clientes (nombre, cif)
            SELECT f.cliente, TRIM(f.cif)
            FROM facturas AS f
            WHERE TRIM(f.cif) <> ''
              AND NOT EXISTS (
                  SELECT 1 FROM clientes AS c
                  WHERE UPPER(TRIM(c.cif)) = UPPER(TRIM(f.cif))
              )
            GROUP BY UPPER(TRIM(f.cif))
            """
        )
        conexion.execute(
            """
            UPDATE facturas
            SET cliente_codigo = (
                SELECT c.codigo FROM clientes AS c
                WHERE UPPER(TRIM(c.cif)) = UPPER(TRIM(facturas.cif))
                LIMIT 1
            )
            WHERE cliente_codigo IS NULL AND TRIM(cif) <> ''
            """
        )
        # Convierte cada registro previo en su primera línea de artículo una sola vez.
        conexion.execute(
            """
            INSERT INTO articulos_factura (
                factura_id, orden, concepto, cantidad, precio, iva
            )
            SELECT f.id, 1, f.concepto, f.cantidad, f.precio, f.iva
            FROM facturas AS f
            WHERE NOT EXISTS (
                SELECT 1 FROM articulos_factura AS a WHERE a.factura_id = f.id
            )
            """
        )


def _guardar_articulos(
    conexion: sqlite3.Connection,
    factura_id: int,
    articulos: list[dict[str, object]],
) -> None:
    conexion.executemany(
        """
        INSERT INTO articulos_factura (
            factura_id, orden, concepto, cantidad, precio, iva
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                factura_id,
                orden,
                str(articulo["concepto"]).strip(),
                int(articulo["cantidad"]),
                float(articulo["precio"]),
                float(articulo["iva"]),
            )
            for orden, articulo in enumerate(articulos, start=1)
        ],
    )


def obtener_clientes() -> list[dict[str, object]]:
    with conectar() as conexion:
        conexion.row_factory = sqlite3.Row
        clientes = conexion.execute(
            "SELECT * FROM clientes ORDER BY nombre COLLATE NOCASE, codigo"
        ).fetchall()
    return [dict(cliente) for cliente in clientes]


def guardar_cliente(
    nombre: str,
    cif: str,
    telefono: str = "",
    email: str = "",
    direccion: str = "",
    codigo_postal: str = "",
    ciudad: str = "",
    provincia: str = "",
    forma_pago: str = "",
    observaciones: str = "",
    codigo: int | None = None,
) -> int:
    if not nombre.strip() or not cif.strip():
        raise ValueError("El nombre del cliente y el CIF son obligatorios.")
    try:
        with conectar() as conexion:
            if codigo is None:
                cursor = conexion.execute(
                    """
                    INSERT INTO clientes (
                        nombre, cif, telefono, email, direccion, codigo_postal,
                        ciudad, provincia, forma_pago, observaciones
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        nombre.strip(), cif.strip().upper(), telefono.strip(), email.strip(),
                        direccion.strip(), codigo_postal.strip(), ciudad.strip(),
                        provincia.strip(), forma_pago.strip(), observaciones.strip(),
                    ),
                )
                return int(cursor.lastrowid)
            conexion.execute(
                """
                UPDATE clientes
                SET nombre = ?, cif = ?, telefono = ?, email = ?, direccion = ?,
                    codigo_postal = ?, ciudad = ?, provincia = ?, forma_pago = ?,
                    observaciones = ?
                WHERE codigo = ?
                """,
                (
                    nombre.strip(), cif.strip().upper(), telefono.strip(), email.strip(),
                    direccion.strip(), codigo_postal.strip(), ciudad.strip(),
                    provincia.strip(), forma_pago.strip(), observaciones.strip(), codigo,
                ),
            )
            return codigo
    except sqlite3.IntegrityError as error:
        raise ValueError("Ya existe un cliente registrado con ese CIF.") from error


def invalidar_pdf_factura(numero_factura: str) -> None:
    """Quita copias locales con el nombre que usa la descarga de facturas."""
    numero_seguro = re.sub(r"[^A-Za-z0-9._-]+", "_", str(numero_factura)).strip("._")
    if not numero_seguro:
        return
    nombre_pdf = f"factura_{numero_seguro}.pdf"
    for directorio in (DATABASE_PATH.parent, DATABASE_PATH.parent / "PDF", DATABASE_PATH.parent / "facturas_pdf"):
        archivo = directorio / nombre_pdf
        if archivo.is_file():
            archivo.unlink()


def guardar_datos(
    cliente: str,
    cif: str,
    fecha: str,
    numero_factura: str,
    articulos: list[dict[str, object]],
    cliente_codigo: int | None = None,
) -> None:
    if not articulos:
        raise ValueError("La factura debe incluir al menos un artículo.")
    primero = articulos[0]
    with conectar() as conexion:
        cursor = conexion.execute(
            """
            INSERT INTO facturas (
                cliente, cif, fecha, numero_factura, concepto,
                cantidad, precio, iva, estado, cliente_codigo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', ?)
            """,
            (
                cliente,
                cif,
                fecha,
                numero_factura,
                primero["concepto"],
                primero["cantidad"],
                primero["precio"],
                primero["iva"],
                cliente_codigo,
            ),
        )
        _guardar_articulos(conexion, int(cursor.lastrowid), articulos)


def actualizar_datos(
    factura_id: int,
    cliente: str,
    cif: str,
    fecha: str,
    numero_factura: str,
    articulos: list[dict[str, object]],
    cliente_codigo: int | None = None,
) -> None:
    if not articulos:
        raise ValueError("La factura debe incluir al menos un artículo.")
    primero = articulos[0]
    with conectar() as conexion:
        conexion.execute(
            """
            UPDATE facturas
            SET cliente = ?, cif = ?, fecha = ?, numero_factura = ?,
                concepto = ?, cantidad = ?, precio = ?, iva = ?,
                cliente_codigo = COALESCE(?, cliente_codigo)
            WHERE id = ?
            """,
            (
                cliente,
                cif,
                fecha,
                numero_factura,
                primero["concepto"],
                primero["cantidad"],
                primero["precio"],
                primero["iva"],
                cliente_codigo,
                factura_id,
            ),
        )
        conexion.execute(
            "DELETE FROM articulos_factura WHERE factura_id = ?", (factura_id,)
        )
        _guardar_articulos(conexion, factura_id, articulos)


def eliminar_factura(factura_id: int, numero_factura: str | None = None) -> None:
    """Elimina una factura y sus líneas sin dejar registros huérfanos."""
    if numero_factura:
        invalidar_pdf_factura(numero_factura)
    with conectar() as conexion:
        conexion.execute("DELETE FROM articulos_factura WHERE factura_id = ?", (factura_id,))
        conexion.execute("DELETE FROM facturas WHERE id = ?", (factura_id,))


def obtener_facturas(estado: str | None = None) -> list[dict[str, object]]:
    with conectar() as conexion:
        conexion.row_factory = sqlite3.Row
        if estado is None:
            filas = conexion.execute(
                "SELECT * FROM facturas ORDER BY id DESC"
            ).fetchall()
        else:
            filas = conexion.execute(
                "SELECT * FROM facturas WHERE estado = ? ORDER BY id DESC",
                (estado,),
            ).fetchall()

        facturas = []
        for fila in filas:
            factura = dict(fila)
            cliente = conexion.execute(
                "SELECT * FROM clientes WHERE codigo = ?",
                (factura.get("cliente_codigo"),),
            ).fetchone()
            if cliente is None and factura.get("cif"):
                cliente = conexion.execute(
                    "SELECT * FROM clientes WHERE UPPER(TRIM(cif)) = UPPER(TRIM(?)) LIMIT 1",
                    (factura["cif"],),
                ).fetchone()
            factura["datos_cliente"] = dict(cliente) if cliente else {}
            lineas = conexion.execute(
                """
                SELECT concepto, cantidad, precio, iva
                FROM articulos_factura
                WHERE factura_id = ?
                ORDER BY orden, id
                """,
                (factura["id"],),
            ).fetchall()
            factura["articulos"] = [dict(linea) for linea in lineas]
            facturas.append(factura)
    return facturas


def generar_factura(factura_id: int) -> None:
    with conectar() as conexion:
        conexion.execute(
            "UPDATE facturas SET estado = 'Generada' WHERE id = ? AND estado = 'Pendiente'",
            (factura_id,),
        )


def actualizar_estado_pago(
    factura_id: int, estado_pago: str, numero_factura: str | None = None
) -> None:
    estados_validos = {"Pagado", "Pendiente", "Vencido"}
    if estado_pago not in estados_validos:
        raise ValueError("El estado debe ser Pagado, Pendiente o Vencido.")
    if numero_factura:
        invalidar_pdf_factura(numero_factura)
    with conectar() as conexion:
        conexion.execute(
            "UPDATE facturas SET estado_pago = ? WHERE id = ?",
            (estado_pago, factura_id),
        )
