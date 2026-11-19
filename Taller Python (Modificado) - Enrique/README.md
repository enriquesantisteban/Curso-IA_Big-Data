# Gestor de facturas

Aplicación web para registrar clientes y facturas, generar facturas en PDF y consultar un resumen de la facturación. Está desarrollada con Python, Streamlit y SQLite.

## Funcionalidades

- **Introducir datos:** registra clientes con CIF, DNI o NIE; selecciona las fechas de emisión y vencimiento con calendario; y añade varios artículos con concepto, cantidad, precio unitario e IVA.
- **Clientes:** da de alta y edita fichas buscándolas por DNI, NIE o CIF. Guarda correo, teléfono, dirección fiscal, código postal, ciudad, provincia, país y notas; puedes elegir esas fichas al preparar una factura.
- **Facturas:** consulta todas las facturas en una tabla, filtra por estado y busca por cliente o número. Ordena por fecha, nombre, unidades, importe y otros campos.
- **Productos:** gestiona el catálogo de informática con descripción, foto, precio e IVA. Incluye nueve productos de demostración para editar.
- **Orden del menú:** cambia la posición de las pestañas laterales y guarda tu orden preferido.
- **Gastos:** registra proveedores, comprobantes, categorías, conceptos, importes e IVA; consulta el total, el promedio y el detalle de los gastos guardados.
- **Generar facturas:** revisa y edita los datos guardados, genera cada factura y ofrece su descarga inmediata en PDF.
- **Informes:** consulta la facturación total, el número de facturas, los clientes distintos y el importe medio por factura. Incluye una gráfica por cliente, un desplegable con el detalle completo de cada factura y una descarga PDF independiente para cada una.
- **Estado de pago:** las facturas muestran si están pendientes, pagadas o vencidas según su vencimiento. Desde el detalle de cada factura puedes marcarla como pagada o volver a pendiente.
- **Diseño de factura:** cambia logo, colores, tipografía y campos visibles; permite añadir o quitar campos adicionales de empresa.
- **PDF:** incorpora el logo configurado, los datos de cliente y empresa, los datos fiscales y de contacto disponibles, el documento identificativo, las fechas de emisión y vencimiento, el detalle de los artículos y los totales.
- **Persistencia:** los datos se guardan en una base de datos SQLite local y se conservan al cerrar la aplicación.

## Requisitos

- Python 3.10 o superior.
- Las dependencias indicadas en `requirements.txt`.

## Instalación y ejecución

Desde la carpeta del proyecto, crea y activa un entorno virtual, instala las dependencias y ejecuta Streamlit:

```bash
python -m venv .venv
```

En Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

En macOS o Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit abrirá la aplicación en `http://localhost:8501`.

## Base de datos

Al iniciar la aplicación, SQLite crea `facturas.db` en la carpeta del proyecto si todavía no existe. La app también adapta la base de datos existente para guardar los artículos de cada factura. No es necesario iniciar una base de datos manualmente.

La base de datos local puede contener información de clientes. Se excluye de Git con `.gitignore`; conserva una copia de seguridad si necesitas trasladar los datos a otro equipo. Las bases de datos existentes se actualizan al arrancar para admitir el tipo de documento, el vencimiento y el estado de pago; las facturas previas mantienen CIF y quedan sin fecha de vencimiento.

## Estructura del proyecto

```text
app.py                      # Punto de entrada y navegación
app_pages/
  introducir_datos.py       # Registro de facturas y artículos
  clientes.py              # Alta y consulta de fichas de clientes
  facturas.py              # Tabla general con filtros y ordenación
  productos.py            # Catálogo de productos con fotos y precios
  gastos.py                # Registro y resumen de gastos
  orden_menu.py            # Personalización del orden de navegación
  generar_facturas.py       # Revisión, edición y generación
  informes.py               # Indicadores, gráfica y descargas PDF
  diseno_factura.py         # Personalización de las facturas PDF
facturas_db.py              # Persistencia y consultas SQLite
pdf_factura.py              # Diseño y generación de facturas PDF
Logo/lgne_proxy.png         # Logotipo de LGNE PROXY en las facturas PDF
Logo/lgne_proxy.svg         # Fuente vectorial editable del logotipo
requirements.txt            # Dependencias
```
