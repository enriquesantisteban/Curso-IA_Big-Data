# Gestor de facturas

Aplicación web para registrar clientes y facturas, generar facturas en PDF y consultar un resumen de la facturación. Está desarrollada con Python, Streamlit y SQLite.

## Funcionalidades

- **Introducir datos:** registra cliente, CIF, fecha y número de factura. Añade varios artículos con concepto, cantidad, precio unitario e IVA.
- **Generar facturas:** revisa y edita los datos guardados antes de marcar cada factura como generada.
- **Informes:** consulta la facturación total, el número de facturas, los clientes distintos y el importe medio por factura. Incluye una gráfica de facturación por cliente y una descarga PDF para cada factura.
- **PDF:** incorpora el logo de `Logo/logo.png`, los datos de cliente y empresa, el detalle de los artículos y los totales.
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

La base de datos local puede contener información de clientes. Se excluye de Git con `.gitignore`; conserva una copia de seguridad si necesitas trasladar los datos a otro equipo.

## Estructura del proyecto

```text
app.py                      # Punto de entrada y navegación
app_pages/
  introducir_datos.py       # Registro de clientes, facturas y artículos
  generar_facturas.py       # Revisión, edición y generación
  informes.py               # Indicadores, gráfica y descargas PDF
facturas_db.py              # Persistencia y consultas SQLite
pdf_factura.py              # Diseño y generación de facturas PDF
Logo/logo.png               # Logo incluido en las facturas PDF
requirements.txt            # Dependencias
```
