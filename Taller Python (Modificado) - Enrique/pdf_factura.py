import base64
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
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_SETTINGS = {
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


def _euros(valor: Decimal) -> str:
    valor = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def generar_pdf_factura(
    factura: dict[str, Any], ajustes: dict[str, Any] | None = None
) -> bytes:
    ajustes = {**DEFAULT_SETTINGS, **(ajustes or {})}
    accent = colors.HexColor(str(ajustes["accent_color"]))
    text_color = colors.HexColor(str(ajustes["text_color"]))
    panel_color = colors.HexColor(str(ajustes["panel_color"]))
    font_family = str(ajustes["font_family"])
    if font_family not in {"Helvetica", "Times-Roman", "Courier"}:
        font_family = "Helvetica"
    font_bold = {
        "Helvetica": "Helvetica-Bold",
        "Times-Roman": "Times-Bold",
        "Courier": "Courier-Bold",
    }[font_family]
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
            fontName=font_bold,
            fontSize=9,
            leading=12,
            textColor=accent,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            "InvoiceBody",
            parent=styles["Normal"],
            fontName=font_family,
            fontSize=10,
            leading=15,
            textColor=text_color,
        )
    )
    styles.add(
        ParagraphStyle(
            "InvoiceTitle",
            parent=styles["Normal"],
            fontName=font_bold,
            fontSize=18,
            leading=22,
            textColor=text_color,
        )
    )
    styles.add(
        ParagraphStyle(
            "InvoiceCompanyName",
            parent=styles["Normal"],
            fontName=font_bold,
            fontSize=17,
            leading=20,
            textColor=accent,
            spaceAfter=5,
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
            fontName=font_bold,
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
        author="LGNE PROXY",
    )

    customer = []
    if ajustes["show_client"]:
        customer = [
            Paragraph("CLIENTE:", styles["InvoiceLabel"]),
            body(factura["cliente"]),
        ]
        if ajustes["show_client_cif"]:
            tipo_documento = factura.get("documento_tipo") or "CIF"
            customer.append(body(f"{tipo_documento}: {factura['cif']}"))
        if ajustes["show_client_date"]:
            customer.append(body(f"Fecha de emisión: {factura['fecha']}"))
        if ajustes["show_due_date"] and factura.get("fecha_vencimiento"):
            customer.append(body(f"Fecha de vencimiento: {factura['fecha_vencimiento']}"))
        datos_cliente = factura.get("datos_cliente") or {}
        for campo, etiqueta in (
            ("direccion", "Dirección"),
            ("codigo_postal", "Código postal"),
            ("ciudad", "Ciudad"),
            ("provincia", "Provincia"),
            ("pais", "País"),
            ("email", "Correo"),
            ("telefono", "Teléfono"),
        ):
            valor = str(datos_cliente.get(campo) or "").strip()
            if valor:
                customer.append(body(f"{etiqueta}: {valor}"))

    company = []
    if ajustes["show_company"]:
        company = [
            Paragraph("EMPRESA:", styles["InvoiceLabel"]),
            body(ajustes["company_cif"]),
        ]
        if ajustes["show_company_website"] and ajustes["company_website"]:
            company.append(href(str(ajustes["company_website"])))
        for field in ajustes["additional_fields"]:
            label = str(field.get("Campo", "")).strip()
            value = str(field.get("Valor", "")).strip()
            if label and value:
                company.append(body(f"{label}: {value}"))

    logo_data = str(ajustes.get("logo_base64", ""))
    logo_bytes = base64.b64decode(logo_data) if logo_data else None
    if logo_bytes is None:
        logo_dir = PROJECT_DIR / "EOOEEOE"
        logo_candidates = (
            sorted(
                path
                for path in logo_dir.glob("*")
                if path.is_file() and path.suffix.casefold() in {".png", ".jpg", ".jpeg"}
            )
            if logo_dir.is_dir()
            else []
        )
        logo_path = next(
            (
                path
                for path in [
                    PROJECT_DIR / "Logo" / "lgne_proxy.png",
                    PROJECT_DIR / "Logo" / "logo.png",
                    *logo_candidates,
                ]
                if path.is_file()
            ),
            None,
        )
        if logo_path:
            logo_bytes = logo_path.read_bytes()

    if ajustes["show_logo"] and logo_bytes:
        logo_reader = ImageReader(BytesIO(logo_bytes))
        logo_original_width, logo_original_height = logo_reader.getSize()
        scale = min(
            71 * mm / logo_original_width,
            22 * mm / logo_original_height,
        )
        logo_width = logo_original_width * scale
        logo_height = logo_original_height * scale
        logo = Image(BytesIO(logo_bytes), width=logo_width, height=logo_height)
        if company:
            company_info = Table(
                [[element] for element in company],
                colWidths=[71 * mm],
            )
            company_info.setStyle(
                TableStyle(
                    [
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )
            company_content = Table(
                [[logo], [company_info]],
                colWidths=[71 * mm],
            )
            company_content.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (0, 0), 5),
                    ]
                )
            )
        else:
            company_content = logo
    else:
        if company:
            company.insert(
                1,
                Paragraph(escape(str(ajustes["company_name"])), styles["InvoiceCompanyName"]),
            )
        company_content = company

    party_cells = []
    if customer:
        party_cells.append(customer)
    if company_content:
        party_cells.append(company_content)
    if len(party_cells) == 2:
        parties = Table([[party_cells[0], party_cells[1]]], colWidths=[87 * mm, 87 * mm])
    elif party_cells:
        parties = Table([[party_cells[0]]], colWidths=[174 * mm])
    else:
        parties = None
    if parties:
        parties.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), panel_color),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D9E2E8")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#D9E2E8")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
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
                ("BACKGROUND", (0, 0), (-1, 0), accent),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, panel_color]),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D9E2E8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9E2E8")),
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
                ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.HexColor("#D9E2E8")),
                ("LINEABOVE", (0, 5), (-1, 5), 1.2, accent),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story = []
    if parties:
        story.extend([parties, Spacer(1, 12 * mm)])
    if ajustes["show_invoice_number"]:
        story.extend(
            [
                Paragraph(
                    f"Factura {escape(str(factura['numero_factura']))}",
                    styles["InvoiceTitle"],
                ),
                Spacer(1, 7 * mm),
            ]
        )
    if ajustes["show_items"]:
        story.extend([detail, Spacer(1, 10 * mm)])
    if ajustes["show_totals"]:
        story.append(totals)
    if ajustes["show_footer"] and ajustes["footer_text"]:
        story.extend(
            [
                Spacer(1, 12 * mm),
                Paragraph(
                    escape(str(ajustes["footer_text"])),
                    ParagraphStyle(
                        "InvoiceFooter",
                        parent=styles["InvoiceBody"],
                        fontSize=8,
                        textColor=colors.HexColor("#64748B"),
                        alignment=TA_CENTER,
                    ),
                ),
            ]
        )
    document.build(story)
    return buffer.getvalue()
