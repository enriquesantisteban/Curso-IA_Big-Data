import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

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


def guardar_datos(
    cliente: str,
    cif: str,
    fecha: str,
    numero_factura: str,
    articulos: list[dict[str, object]],
) -> None:
    if not articulos:
        raise ValueError("La factura debe incluir al menos un artículo.")
    primero = articulos[0]
    with conectar() as conexion:
        cursor = conexion.execute(
            """
            INSERT INTO facturas (
                cliente, cif, fecha, numero_factura, concepto,
                cantidad, precio, iva, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente')
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
) -> None:
    if not articulos:
        raise ValueError("La factura debe incluir al menos un artículo.")
    primero = articulos[0]
    with conectar() as conexion:
        conexion.execute(
            """
            UPDATE facturas
            SET cliente = ?, cif = ?, fecha = ?, numero_factura = ?,
                concepto = ?, cantidad = ?, precio = ?, iva = ?
            WHERE id = ? AND estado = 'Pendiente'
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
                factura_id,
            ),
        )
        conexion.execute(
            "DELETE FROM articulos_factura WHERE factura_id = ?", (factura_id,)
        )
        _guardar_articulos(conexion, factura_id, articulos)


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
