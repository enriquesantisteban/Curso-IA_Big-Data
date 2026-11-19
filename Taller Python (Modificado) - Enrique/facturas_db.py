import base64
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "facturas.db"
AJUSTES_FACTURA_DEFAULT = {
    "accent_color": "#176B5B",
    "text_color": "#1F2937",
    "panel_color": "#EEF5F3",
    "font_family": "Helvetica",
    "company_name": "LGNE PROXY",
    "company_cif": "A123456",
    "company_website": "enriquesantisteban.github.io/portfolio",
    "show_logo": True,
    "show_client": True,
    "show_client_cif": True,
    "show_client_date": True,
    "show_due_date": True,
    "show_company": True,
    "show_invoice_number": True,
    "show_items": True,
    "show_totals": True,
    "show_company_website": True,
    "show_footer": True,
    "footer_text": "Gracias por confiar en nuestros servicios.",
    "additional_fields": [],
    "logo_base64": "",
}
ORDEN_NAVEGACION_DEFAULT = [
    "introducir_datos",
    "clientes",
    "facturas",
    "productos",
    "gastos",
    "generar_facturas",
    "informes",
    "diseno_factura",
]


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
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS ajustes_factura (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                configuracion TEXT NOT NULL
            )
            """
        )
        columnas = {
            fila[1] for fila in conexion.execute("PRAGMA table_info(facturas)")
        }
        if "documento_tipo" not in columnas:
            conexion.execute(
                "ALTER TABLE facturas ADD COLUMN documento_tipo TEXT NOT NULL DEFAULT 'CIF'"
            )
        if "fecha_vencimiento" not in columnas:
            conexion.execute("ALTER TABLE facturas ADD COLUMN fecha_vencimiento TEXT")
        columnas = {
            fila[1] for fila in conexion.execute("PRAGMA table_info(facturas)")
        }
        if "estado" not in columnas:
            # Las facturas existentes ya se guardaban como facturas completas.
            conexion.execute(
                "ALTER TABLE facturas ADD COLUMN estado TEXT NOT NULL DEFAULT 'Generada'"
            )
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                documento_tipo TEXT NOT NULL,
                documento_numero TEXT NOT NULL,
                nombre TEXT NOT NULL,
                email TEXT NOT NULL DEFAULT '',
                telefono TEXT NOT NULL DEFAULT '',
                direccion TEXT NOT NULL DEFAULT '',
                codigo_postal TEXT NOT NULL DEFAULT '',
                ciudad TEXT NOT NULL DEFAULT '',
                provincia TEXT NOT NULL DEFAULT '',
                pais TEXT NOT NULL DEFAULT 'España',
                notas TEXT NOT NULL DEFAULT '',
                UNIQUE(documento_tipo, documento_numero)
            )
            """
        )
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor TEXT NOT NULL,
                documento TEXT NOT NULL DEFAULT '',
                fecha TEXT NOT NULL,
                numero_comprobante TEXT NOT NULL DEFAULT '',
                categoria TEXT NOT NULL,
                concepto TEXT NOT NULL,
                base_imponible REAL NOT NULL,
                iva REAL NOT NULL,
                notas TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE COLLATE NOCASE,
                categoria TEXT NOT NULL,
                descripcion TEXT NOT NULL DEFAULT '',
                precio REAL NOT NULL,
                iva REAL NOT NULL,
                foto BLOB,
                fecha_alta TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS preferencias_aplicacion (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                orden_navegacion TEXT NOT NULL,
                catalogo_demo_cargado INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        columnas_preferencias = {
            fila[1]
            for fila in conexion.execute("PRAGMA table_info(preferencias_aplicacion)")
        }
        if "catalogo_demo_cargado" not in columnas_preferencias:
            conexion.execute(
                "ALTER TABLE preferencias_aplicacion ADD COLUMN catalogo_demo_cargado INTEGER NOT NULL DEFAULT 0"
            )
        # Crea una ficha básica para los clientes de facturas anteriores.
        conexion.execute(
            """
            INSERT OR IGNORE INTO clientes (
                documento_tipo, documento_numero, nombre
            )
            SELECT COALESCE(NULLIF(documento_tipo, ''), 'CIF'), cif, cliente
            FROM facturas
            WHERE TRIM(cif) <> ''
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


def _guardar_cliente_basico(
    conexion: sqlite3.Connection,
    cliente: str,
    documento_tipo: str,
    documento_numero: str,
) -> None:
    conexion.execute(
        """
        INSERT OR IGNORE INTO clientes (documento_tipo, documento_numero, nombre)
        VALUES (?, ?, ?)
        """,
        (documento_tipo.strip().upper(), documento_numero.strip().upper(), cliente.strip()),
    )


def guardar_cliente(
    documento_tipo: str,
    documento_numero: str,
    nombre: str,
    email: str = "",
    telefono: str = "",
    direccion: str = "",
    codigo_postal: str = "",
    ciudad: str = "",
    provincia: str = "",
    pais: str = "España",
    notas: str = "",
) -> None:
    with conectar() as conexion:
        conexion.execute(
            """
            INSERT INTO clientes (
                documento_tipo, documento_numero, nombre, email, telefono,
                direccion, codigo_postal, ciudad, provincia, pais, notas
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(documento_tipo, documento_numero) DO UPDATE SET
                nombre = excluded.nombre, email = excluded.email,
                telefono = excluded.telefono, direccion = excluded.direccion,
                codigo_postal = excluded.codigo_postal, ciudad = excluded.ciudad,
                provincia = excluded.provincia, pais = excluded.pais,
                notas = excluded.notas
            """,
            (
                documento_tipo.strip().upper(), documento_numero.strip().upper(),
                nombre.strip(), email.strip(), telefono.strip(), direccion.strip(),
                codigo_postal.strip(), ciudad.strip(), provincia.strip(), pais.strip(),
                notas.strip(),
            ),
        )


def obtener_clientes() -> list[dict[str, object]]:
    with conectar() as conexion:
        conexion.row_factory = sqlite3.Row
        filas = conexion.execute(
            "SELECT * FROM clientes ORDER BY nombre COLLATE NOCASE, documento_numero"
        ).fetchall()
    return [dict(fila) for fila in filas]


def guardar_gasto(
    proveedor: str,
    documento: str,
    fecha: str,
    numero_comprobante: str,
    categoria: str,
    concepto: str,
    base_imponible: float,
    iva: float,
    notas: str = "",
) -> None:
    if base_imponible < 0 or not 0 <= iva <= 100:
        raise ValueError("El importe y el porcentaje de IVA no son válidos.")
    with conectar() as conexion:
        conexion.execute(
            """
            INSERT INTO gastos (
                proveedor, documento, fecha, numero_comprobante, categoria,
                concepto, base_imponible, iva, notas
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proveedor.strip(), documento.strip().upper(), fecha,
                numero_comprobante.strip(), categoria.strip(), concepto.strip(),
                float(base_imponible), float(iva), notas.strip(),
            ),
        )


def obtener_gastos() -> list[dict[str, object]]:
    with conectar() as conexion:
        conexion.row_factory = sqlite3.Row
        filas = conexion.execute(
            "SELECT * FROM gastos ORDER BY fecha DESC, id DESC"
        ).fetchall()
    return [dict(fila) for fila in filas]


def cargar_productos_demo_si_vacio() -> None:
    productos_demo = [
        ("LGNE NovaBook 15", "Equipos", "Portátil de 15,6 pulgadas, 16 GB de RAM y SSD de 512 GB.", 699.00, 21.0),
        ("LGNE Vision 27", "Monitores", "Monitor IPS de 27 pulgadas con resolución QHD.", 229.00, 21.0),
        ("LGNE Pulse Mechanical", "Periféricos", "Teclado mecánico retroiluminado con conexión USB-C.", 79.90, 21.0),
        ("LGNE Flow Wireless", "Periféricos", "Ratón inalámbrico ergonómico con sensor de precisión.", 34.90, 21.0),
        ("LGNE Echo Headset", "Audio", "Auriculares estéreo con micrófono abatible y cancelación de ruido.", 59.00, 21.0),
        ("LGNE Speed NVMe 1 TB", "Almacenamiento", "Unidad SSD NVMe de 1 TB para equipos compatibles.", 89.90, 21.0),
        ("LGNE Link AX3000", "Redes", "Router Wi-Fi 6 de doble banda con cuatro puertos Ethernet.", 99.00, 21.0),
        ("LGNE Focus HD", "Cámaras", "Webcam Full HD con enfoque automático y tapa de privacidad.", 49.90, 21.0),
        ("LGNE Bridge 8-in-1", "Accesorios", "Adaptador USB-C con HDMI, USB-A, Ethernet y lector de tarjetas.", 69.90, 21.0),
    ]
    with conectar() as conexion:
        total = conexion.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
        catalogo_demo_cargado = conexion.execute(
            "SELECT catalogo_demo_cargado FROM preferencias_aplicacion WHERE id = 1"
        ).fetchone()
        if total == 0 and not (catalogo_demo_cargado and catalogo_demo_cargado[0]):
            conexion.executemany(
                """
                INSERT INTO productos (nombre, categoria, descripcion, precio, iva)
                VALUES (?, ?, ?, ?, ?)
                """,
                productos_demo,
            )
        conexion.execute(
            """
            INSERT INTO preferencias_aplicacion (id, orden_navegacion, catalogo_demo_cargado)
            VALUES (1, ?, 1)
            ON CONFLICT(id) DO UPDATE SET catalogo_demo_cargado = 1
            """,
            (json.dumps(ORDEN_NAVEGACION_DEFAULT),),
        )


def guardar_producto(
    nombre: str,
    categoria: str,
    descripcion: str,
    precio: float,
    iva: float,
    foto: bytes | None = None,
    producto_id: int | None = None,
) -> None:
    if not nombre.strip() or precio < 0 or not 0 <= iva <= 100:
        raise ValueError("Revisa el nombre, el precio y el IVA del producto.")
    try:
        with conectar() as conexion:
            if producto_id is None:
                conexion.execute(
                    """
                    INSERT INTO productos (nombre, categoria, descripcion, precio, iva, foto)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (nombre.strip(), categoria.strip(), descripcion.strip(), precio, iva, foto),
                )
            else:
                conexion.execute(
                    """
                    UPDATE productos
                    SET nombre = ?, categoria = ?, descripcion = ?, precio = ?, iva = ?,
                        foto = COALESCE(?, foto)
                    WHERE id = ?
                    """,
                    (
                        nombre.strip(), categoria.strip(), descripcion.strip(), precio,
                        iva, foto, producto_id,
                    ),
                )
    except sqlite3.IntegrityError as error:
        raise ValueError("Ya existe un producto con ese nombre.") from error


def obtener_productos() -> list[dict[str, object]]:
    with conectar() as conexion:
        conexion.row_factory = sqlite3.Row
        filas = conexion.execute(
            "SELECT * FROM productos ORDER BY categoria COLLATE NOCASE, nombre COLLATE NOCASE"
        ).fetchall()
    return [dict(fila) for fila in filas]


def eliminar_producto(producto_id: int) -> None:
    with conectar() as conexion:
        conexion.execute("DELETE FROM productos WHERE id = ?", (producto_id,))


def obtener_orden_navegacion() -> list[str]:
    with conectar() as conexion:
        fila = conexion.execute(
            "SELECT orden_navegacion FROM preferencias_aplicacion WHERE id = 1"
        ).fetchone()
    if not fila:
        return ORDEN_NAVEGACION_DEFAULT.copy()
    try:
        guardado = json.loads(fila[0])
    except (TypeError, json.JSONDecodeError):
        return ORDEN_NAVEGACION_DEFAULT.copy()
    orden = [
        pagina
        for pagina in guardado
        if pagina in ORDEN_NAVEGACION_DEFAULT
    ] if isinstance(guardado, list) else []
    orden.extend(pagina for pagina in ORDEN_NAVEGACION_DEFAULT if pagina not in orden)
    return orden


def guardar_orden_navegacion(orden: list[str]) -> None:
    if len(orden) != len(ORDEN_NAVEGACION_DEFAULT) or set(orden) != set(ORDEN_NAVEGACION_DEFAULT):
        raise ValueError("El orden debe incluir todas las pestañas una sola vez.")
    with conectar() as conexion:
        conexion.execute(
            """
            INSERT INTO preferencias_aplicacion (id, orden_navegacion)
            VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET orden_navegacion = excluded.orden_navegacion
            """,
            (json.dumps(orden, ensure_ascii=False),),
        )


def guardar_datos(
    cliente: str,
    documento_tipo: str,
    cif: str,
    fecha: str,
    fecha_vencimiento: str | None,
    numero_factura: str,
    articulos: list[dict[str, object]],
) -> None:
    if not articulos:
        raise ValueError("La factura debe incluir al menos un artículo.")
    primero = articulos[0]
    with conectar() as conexion:
        _guardar_cliente_basico(conexion, cliente, documento_tipo, cif)
        cursor = conexion.execute(
            """
            INSERT INTO facturas (
                cliente, documento_tipo, cif, fecha, fecha_vencimiento,
                numero_factura, concepto,
                cantidad, precio, iva, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente')
            """,
            (
                cliente,
                documento_tipo,
                cif,
                fecha,
                fecha_vencimiento,
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
    documento_tipo: str,
    cif: str,
    fecha: str,
    fecha_vencimiento: str | None,
    numero_factura: str,
    articulos: list[dict[str, object]],
) -> None:
    if not articulos:
        raise ValueError("La factura debe incluir al menos un artículo.")
    primero = articulos[0]
    with conectar() as conexion:
        _guardar_cliente_basico(conexion, cliente, documento_tipo, cif)
        conexion.execute(
            """
            UPDATE facturas
            SET cliente = ?, documento_tipo = ?, cif = ?, fecha = ?,
                fecha_vencimiento = ?, numero_factura = ?,
                concepto = ?, cantidad = ?, precio = ?, iva = ?
            WHERE id = ? AND estado = 'Pendiente'
            """,
            (
                cliente,
                documento_tipo,
                cif,
                fecha,
                fecha_vencimiento,
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
        hoy = date.today().isoformat()
        conexion.execute(
            """
            UPDATE facturas
            SET estado_pago = CASE
                WHEN fecha_vencimiento IS NOT NULL AND fecha_vencimiento < ?
                    THEN 'Vencida'
                ELSE 'Pendiente'
            END
            WHERE estado_pago <> 'Pagada'
            """,
            (hoy,),
        )
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
                """
                SELECT email, telefono, direccion, codigo_postal, ciudad, provincia, pais
                FROM clientes
                WHERE documento_tipo = ? AND documento_numero = ?
                """,
                (
                    str(factura.get("documento_tipo") or "CIF").strip().upper(),
                    str(factura["cif"]).strip().upper(),
                ),
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


def actualizar_estado_pago(factura_id: int, estado_pago: str) -> None:
    if estado_pago not in {"Pendiente", "Pagada"}:
        raise ValueError("El estado de pago debe ser Pendiente o Pagada.")
    with conectar() as conexion:
        conexion.execute(
            "UPDATE facturas SET estado_pago = ? WHERE id = ?",
            (estado_pago, factura_id),
        )


def obtener_ajustes_factura() -> dict[str, object]:
    with conectar() as conexion:
        fila = conexion.execute(
            "SELECT configuracion FROM ajustes_factura WHERE id = 1"
        ).fetchone()
    ajustes = AJUSTES_FACTURA_DEFAULT.copy()
    if fila:
        ajustes.update(json.loads(fila[0]))
    return ajustes


def guardar_ajustes_factura(ajustes: dict[str, object]) -> None:
    permitidos = AJUSTES_FACTURA_DEFAULT.keys()
    configuracion = {
        clave: valor for clave, valor in ajustes.items() if clave in permitidos
    }
    # Validar logo guardado antes de persistirlo.
    logo = configuracion.get("logo_base64", "")
    if logo:
        base64.b64decode(str(logo), validate=True)
    with conectar() as conexion:
        conexion.execute(
            """
            INSERT INTO ajustes_factura (id, configuracion) VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET configuracion = excluded.configuracion
            """,
            (json.dumps(configuracion, ensure_ascii=False),),
        )
