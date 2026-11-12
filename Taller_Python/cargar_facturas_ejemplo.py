"""Carga 30 facturas ficticias en facturas.db sin duplicarlas al repetir el script."""

from calendar import monthrange
from datetime import date

from facturas_db import (
    actualizar_estado_pago,
    generar_factura,
    guardar_cliente,
    guardar_datos,
    inicializar_base_datos,
    obtener_clientes,
    obtener_facturas,
)


CLIENTES_EJEMPLO = [
    ("Acme Soluciones Digitales, S.L.", "B-DEMO-0001", "910 555 101", "compras@acme.example", "Madrid"),
    ("Innovate Consulting, S.L.", "B-DEMO-0002", "910 555 102", "admin@innovate.example", "Barcelona"),
    ("Logística del Norte, S.A.", "A-DEMO-0003", "944 555 103", "facturas@lognorte.example", "Bilbao"),
    ("Materiales Pro, S.L.", "B-DEMO-0004", "960 555 104", "oficina@materialespro.example", "Valencia"),
    ("Servicios Generales, S.L.", "B-DEMO-0005", "954 555 105", "gestion@serviciosgen.example", "Sevilla"),
    ("Clínica Horizonte, S.L.", "B-DEMO-0006", "981 555 106", "administracion@horizonte.example", "A Coruña"),
    ("Estudio Nube Creativa, S.L.", "B-DEMO-0007", "915 555 107", "hola@nubecreativa.example", "Madrid"),
    ("Academia Prisma, S.L.", "B-DEMO-0008", "976 555 108", "contabilidad@prisma.example", "Zaragoza"),
    ("Hotel Costa Clara, S.L.", "B-DEMO-0009", "952 555 109", "compras@costaclara.example", "Málaga"),
    ("Fundación Horizonte Abierto", "G-DEMO-0010", "928 555 110", "gestion@horizonteabierto.example", "Las Palmas"),
]

ARTICULOS_EJEMPLO = [
    {"concepto": "Portátil profesional 14 pulgadas", "cantidad": 2, "precio": 849.00, "iva": 21},
    {"concepto": "Monitor IPS 27 pulgadas", "cantidad": 3, "precio": 219.50, "iva": 21},
    {"concepto": "Puesta a punto y configuración", "cantidad": 1, "precio": 95.00, "iva": 21},
    {"concepto": "Licencia de seguridad anual", "cantidad": 5, "precio": 39.90, "iva": 21},
    {"concepto": "Router Wi-Fi 6 empresarial", "cantidad": 2, "precio": 179.00, "iva": 21},
    {"concepto": "Teclado y ratón inalámbricos", "cantidad": 4, "precio": 34.95, "iva": 21},
    {"concepto": "Ampliación de memoria RAM 16 GB", "cantidad": 2, "precio": 72.00, "iva": 21},
    {"concepto": "Mantenimiento informático trimestral", "cantidad": 1, "precio": 240.00, "iva": 21},
    {"concepto": "Disco SSD externo 1 TB", "cantidad": 3, "precio": 89.90, "iva": 21},
    {"concepto": "Instalación de red y cableado", "cantidad": 1, "precio": 385.00, "iva": 21},
]


def _ultimos_meses(cantidad: int) -> list[date]:
    hoy = date.today()
    mes = date(hoy.year, hoy.month, 1)
    resultado = []
    for _ in range(cantidad):
        resultado.append(mes)
        mes = date(mes.year - 1, 12, 1) if mes.month == 1 else date(mes.year, mes.month - 1, 1)
    return list(reversed(resultado))


def main() -> None:
    inicializar_base_datos()

    codigos_por_cif = {
        str(cliente["cif"]).strip().upper(): int(cliente["codigo"])
        for cliente in obtener_clientes()
    }
    for nombre, cif, telefono, email, ciudad in CLIENTES_EJEMPLO:
        cif = cif.upper()
        if cif in codigos_por_cif:
            continue
        codigo = guardar_cliente(
            nombre=nombre,
            cif=cif,
            telefono=telefono,
            email=email,
            direccion=f"Calle de Ejemplo, 12",
            codigo_postal="28000",
            ciudad=ciudad,
            provincia=ciudad,
            forma_pago="Transferencia",
            observaciones="Registro ficticio incluido en el dataset de demostración.",
        )
        codigos_por_cif[cif] = codigo

    numeros_existentes = {
        str(factura["numero_factura"]).upper() for factura in obtener_facturas()
    }
    meses = _ultimos_meses(12)
    creadas = 0
    ya_existian = 0
    for indice in range(30):
        numero = f"EJEMPLO-{date.today().year}-{indice + 1:03d}"
        if numero.upper() in numeros_existentes:
            ya_existian += 1
            continue

        cliente = CLIENTES_EJEMPLO[indice % len(CLIENTES_EJEMPLO)]
        nombre, cif, *_ = cliente
        mes = meses[indice % len(meses)]
        dia = min(3 + (indice * 3) % 25, monthrange(mes.year, mes.month)[1])
        fecha = date(mes.year, mes.month, dia)
        articulo_principal = ARTICULOS_EJEMPLO[(indice * 3) % len(ARTICULOS_EJEMPLO)]
        articulos = [dict(articulo_principal)]
        if indice % 3 == 0:
            articulos.append(dict(ARTICULOS_EJEMPLO[(indice * 3 + 4) % len(ARTICULOS_EJEMPLO)]))

        guardar_datos(
            cliente=nombre,
            cif=cif,
            fecha=fecha.isoformat(),
            numero_factura=numero,
            articulos=articulos,
            cliente_codigo=codigos_por_cif[cif.upper()],
        )
        factura = next(
            factura for factura in obtener_facturas()
            if str(factura["numero_factura"]) == numero
        )
        factura_id = int(factura["id"])
        generar_factura(factura_id)

        # Distribuye ejemplos de facturas pagadas, pendientes y vencidas.
        grupo = indice % 5
        estado_pago = "Pagado" if grupo in (0, 1) else "Pendiente" if grupo in (2, 3) else "Vencido"
        actualizar_estado_pago(factura_id, estado_pago, numero)
        numeros_existentes.add(numero.upper())
        creadas += 1

    print(f"Facturas de ejemplo creadas: {creadas}")
    print(f"Facturas de ejemplo que ya existían: {ya_existian}")
    print(f"Clientes de ejemplo disponibles: {len(CLIENTES_EJEMPLO)}")


if __name__ == "__main__":
    main()
