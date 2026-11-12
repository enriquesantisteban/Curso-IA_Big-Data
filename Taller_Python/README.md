# Gestor de facturas

Aplicación web para registrar clientes y facturas, generar facturas en PDF y consultar un resumen de la facturación. Está desarrollada con Python, Streamlit y SQLite.

## Funcionalidades

- **Introducir datos:** selecciona un cliente por código para cargar su nombre y CIF, o introdúcelos manualmente. Añade fecha, número de factura y varios artículos con concepto, cantidad, precio unitario e IVA.
- **Clientes:** registra clientes con código numérico, CIF, teléfono, correo, dirección, forma de pago y observaciones. Al crear una factura puedes elegir el código para cargar automáticamente el nombre y el CIF.
- **Generar facturas:** revisa y edita los datos guardados antes de marcar cada factura como generada.
- **Informes:** consulta la facturación total, el número de facturas, los clientes distintos y el importe medio por factura. Filtra por periodo y número de factura; incluye una gráfica por cliente, descargas PDF y acciones para editar o eliminar. Las estadísticas se recalculan con los filtros y cambios aplicados.
- **Gastos:** registra compras, suministros, personal, alquiler, servicios, viajes, impuestos y otros gastos; consulta importes por periodo, categoría y estado.
- **Chatbot de facturas:** pega el texto de una factura y Qwen 2.5 extrae los datos. Si falta un campo obligatorio, lo solicita; después puedes revisar y corregir los datos antes de guardarlos.
- **PDF:** incorpora el logo de `Logo/logo.png`, los datos de cliente y empresa, la dirección, contacto y forma de pago registrados, el detalle de los artículos y los totales.
- **Persistencia:** los datos se guardan en una base de datos SQLite local y se conservan al cerrar la aplicación.

## Requisitos

- Python 3.10 o superior.
- Las dependencias indicadas en `requirements.txt`.
- Ollama con el modelo local `qwen2.5:3b` para usar el chatbot.

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

El chatbot usa Ollama en `http://127.0.0.1:11434`. Inicia Ollama y comprueba que el modelo `qwen2.5:3b` esté instalado antes de usar la pestaña Chatbot. La factura se puede guardar como pendiente o guardar y generar directamente.

## Base de datos

Al iniciar la aplicación, SQLite crea `facturas.db` en la carpeta del proyecto si todavía no existe. La app también adapta la base de datos existente para guardar los artículos de cada factura. No es necesario iniciar una base de datos manualmente.

La base de datos local puede contener información de clientes. Se excluye de Git con `.gitignore`; conserva una copia de seguridad si necesitas trasladar los datos a otro equipo.

## Estructura del proyecto

```text
app.py                      # Punto de entrada y navegación
app_pages/
  introducir_datos.py       # Registro de clientes, facturas y artículos
  clientes.py              # Registro y consulta de clientes
  generar_facturas.py       # Revisión, edición y generación
  informes.py               # Indicadores, gráfica y descargas PDF
  gastos.py                 # Registro, filtros y resumen de gastos
  chatbot.py                # Chat para extraer facturas desde texto
facturas_db.py              # Persistencia y consultas SQLite
gastos_db.py                # Persistencia SQLite de gastos
qwen_facturas.py            # Conexión local con Qwen 2.5 en Ollama
pdf_factura.py              # Diseño y generación de facturas PDF
Logo/logo.png               # Logo incluido en las facturas PDF
requirements.txt            # Dependencias
```
