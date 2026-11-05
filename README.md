# 🏋️‍♂️ Gimnasio Norte - Web & Asistente Virtual con IA

Una aplicación web completa y moderna para el **Gimnasio Norte**, desarrollada en Node.js (sin frameworks externos pesados) que incluye información general de instalaciones, cuotas, entrenadores, alquileres, un formulario de reserva de citas con calendario y un **asistente de IA flotante** impulsado por Ollama para agendar citas de forma conversacional y resolver dudas sobre el centro.

---

## 🚀 Características

* **Diseño Moderno e Integrado:**
  * Barra de navegación flotante fija (`sticky header`).
  * Cabecera principal con imagen de fondo e información superpuesta.
  * Tarjetas informativas adaptativas (*responsive grid UI*) para cuotas, entrenadores, maquinaria disponible y alquiler de pistas.
  * Formulario de agendamiento con selector de fecha tipo calendario (`<input type="date">`).

* **🤖 Chatbot Inteligente (IA Local):**
  * Conectado localmente con **Ollama** (modelo `qwen2.5:3b`).
  * **Procesamiento de lenguaje natural flexible:** Entiende fechas escritas como *"el 15 de marzo"* o días de la semana (*"el martes"*), reconociendo horas y nombres de forma conversacional.
  * Respuestas adaptativas y amables en caso de que el usuario no especifique correctamente algún dato.

* **💾 Registro de Citas:**
  * Persistencia en tiempo real: tanto las citas agendadas por la web como las solicitadas a través del chat se registran automáticamente en el archivo local `citas.txt`.

---

## 📋 Requisitos Previos

Antes de ejecutar el proyecto, asegúrate de tener instalado:

1. **[Node.js](https://nodejs.org/)** (v18 o superior).
2. **[Ollama](https://ollama.com/)** ejecutándose localmente.
3. El modelo de lenguaje descargado en Ollama. Puedes obtenerlo con:
   ```bash
   ollama run qwen2.5:3b
