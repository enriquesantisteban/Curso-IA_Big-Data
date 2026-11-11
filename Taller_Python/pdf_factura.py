from decimal import Decimal, ROUND_HALF_UP
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


INK = colors.HexColor("#1F2937")
ACCENT = colors.HexColor("#176B5B")
PALE = colors.HexColor("#EEF5F3")
LINE = colors.HexColor("#D9E2E8")
LOGO_PATH = Path(__file__).resolve().parent / "Logo" / "logo.png"


def _euros(valor: Decimal) -> str:
    valor = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def generar_pdf_factura(factura: dict[str, Any]) -> bytes:
    articulos = factura.get("articulos") or [
        {
            "concepto": factura["concepto"],
            "cantidad": factura["cantidad"],
            "precio": factura["precio"],
            "iva": factura["iva"],
        }
    ]
    cantidad_total = 0
    subtotal_total = Decimal("0.00")
    iva_total = Decimal("0.00")
    lineas_calculadas = []
    precios_unitarios = []
    for articulo in articulos:
        cantidad = int(articulo["cantidad"])
        precio = Decimal(str(articulo["precio"]))
        iva = Decimal(str(articulo["iva"]))
        subtotal_linea = (Decimal(cantidad) * precio).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        iva_linea = (subtotal_linea * iva / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total_linea = subtotal_linea + iva_linea
        cantidad_total += cantidad
        subtotal_total += subtotal_linea
        iva_total += iva_linea
        precios_unitarios.append(_euros(precio))
        lineas_calculadas.append(
            {
                "concepto": articulo["concepto"],
                "cantidad": cantidad,
                "precio": precio,
                "iva": iva,
                "total": total_linea,
            }
        )
    total = subtotal_total + iva_total

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "InvoiceLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=ACCENT,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            "InvoiceBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            textColor=INK,
        )
    )
    styles.add(
        ParagraphStyle(
            "InvoiceTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=INK,
        )
    )
    styles.add(
        ParagraphStyle(
            "InvoiceRight",
            parent=styles["InvoiceBody"],
            alignment=TA_RIGHT,
        )
    )
    styles.add(
        ParagraphStyle(
            "InvoiceHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=TA_CENTER,
        )
    )

    def body(text: object) -> Paragraph:
        return Paragraph(escape(str(text)).replace("\n", "<br/>"), styles["InvoiceBody"])

    def href(url: str) -> Paragraph:
        target = url if url.startswith(("http://", "https://")) else f"https://{url}"
        return Paragraph(
            f'<link href="{escape(target, quote=True)}"><u>{escape(url)}</u></link>',
            styles["InvoiceBody"],
        )

    filas_detalle = [
        [
            body(linea["concepto"]),
            Paragraph(str(linea["cantidad"]), styles["InvoiceRight"]),
            Paragraph(_euros(linea["precio"]), styles["InvoiceRight"]),
            Paragraph(f"{linea['iva']:g}%", styles["InvoiceRight"]),
            Paragraph(_euros(linea["total"]), styles["InvoiceRight"]),
        ]
        for linea in lineas_calculadas
    ]

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Factura {factura['numero_factura']}",
        author="Enrique Santisteban",
    )

    customer = [
        Paragraph("CLIENTE:", styles["InvoiceLabel"]),
        body(factura["cliente"]),
        body(factura["cif"]),
        body(factura["fecha"]),
    ]
    company_details = [
        Paragraph("EMPRESA:", styles["InvoiceLabel"]),
        body("Enrique Santisteban"),
        body("A123456"),
        href("enriquesantisteban.github.io/portfolio"),
        website := href("enriquesantisteban.github.io"),
    ]
    if LOGO_PATH.is_file():
        logo = Image(str(LOGO_PATH), width=21 * mm, height=21 * mm)
        company = Table(
            [[company_details, logo]],
            colWidths=[39 * mm, 22 * mm],
        )
        company.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
    else:
        company = company_details
    parties = Table([[customer, company]], colWidths=[87 * mm, 87 * mm])
    parties.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )

    description_header = [
        Paragraph("DESCRIPCIÓN", styles["InvoiceHeader"]),
        Paragraph("CANTIDAD", styles["InvoiceHeader"]),
        Paragraph("PRECIO<br/>UNITARIO", styles["InvoiceHeader"]),
        Paragraph("IVA", styles["InvoiceHeader"]),
        Paragraph("TOTAL", styles["InvoiceHeader"]),
    ]
    detail = Table(
        [description_header, *filas_detalle],
        colWidths=[67 * mm, 22 * mm, 32 * mm, 19 * mm, 34 * mm],
        repeatRows=1,
    )
    detail.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("BACKGROUND", (0, 1), (-1, 1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )

    totals = Table(
        [
            [Paragraph("RECUENTO", styles["InvoiceLabel"]), "", ""],
            [body("Cantidad total"), Paragraph(str(cantidad_total), styles["InvoiceRight"]), ""],
            [body("Precios unitarios (por artículo)"), body(" · ".join(precios_unitarios)), ""],
            [body("Subtotal"), Paragraph(_euros(subtotal_total), styles["InvoiceRight"]), ""],
            [body("IVA total"), Paragraph(_euros(iva_total), styles["InvoiceRight"]), ""],
            [Paragraph("TOTAL", styles["InvoiceLabel"]), "", Paragraph(_euros(total), styles["InvoiceTitle"])],
        ],
        colWidths=[80 * mm, 35 * mm, 35 * mm],
        hAlign="RIGHT",
    )
    totals.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (2, 0)),
                ("SPAN", (1, 1), (2, 1)),
                ("SPAN", (1, 2), (2, 2)),
                ("SPAN", (1, 3), (2, 3)),
                ("SPAN", (1, 4), (2, 4)),
                ("SPAN", (0, 5), (1, 5)),
                ("LINEABOVE", (0, 0), (-1, 0), 0.8, LINE),
                ("LINEABOVE", (0, 5), (-1, 5), 1.2, ACCENT),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story = [
        parties,
        Spacer(1, 18 * mm),
        Paragraph(f"Factura {escape(str(factura['numero_factura']))}", styles["InvoiceTitle"]),
        Spacer(1, 7 * mm),
        detail,
        Spacer(1, 12 * mm),
        totals,
    ]
    document.build(story)
    return buffer.getvalue()
