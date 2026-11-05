const http = require("http");
const fs = require("fs");
const path = require("path");

const OLLAMA = "http://127.0.0.1:11434/api/chat";
const MODEL = "qwen2.5:3b";
const PORT = 3000;
const CITAS_FILE = path.join(__dirname, "citas.txt");

const SYSTEM = `Eres el asistente de la página del Gimnasio Norte. Responde en español, solo con la información de esta página. Si preguntan algo que no está aquí, dilo.

Cuotas (acceso a la sala de máquinas y a la piscina cubierta):
- Mensual: 35 €
- Trimestral: 90 €
- Anual: 320 €

Entrenadores personales. El servicio es aparte de la cuota. Cada uno ofrece plan Básico, Intermedio y Premium. Precios por sesión:
- Ana Ruiz: Básico 25 €, Intermedio 45 €, Premium 70 €
- Luis Ortega: Básico 30 €, Intermedio 50 €, Premium 80 €
- Marta Gil: Básico 28 €, Intermedio 48 €, Premium 75 €

Máquinas incluidas en la cuota:
- Tren superior: press banca, jalón al pecho, press militar, remo
- Tren inferior: prensa, extensión de cuádriceps, femoral tumbado, gemelos

Alquileres aparte de la cuota, por hora:
- Piscina cubierta: 8 €
- Fútbol sala: 40 €
- Tenis: 18 €
- Baloncesto: 30 €
- Pádel: 22 €`;

const page = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gimnasio Norte</title>
<style>
  :root {
    --bg-main: #f8fafc;
    --bg-card: #ffffff;
    --accent: #0f172a;
    --accent-hover: #1e293b;
    --primary: #2563eb;
    --text: #334155;
    --text-heading: #0f172a;
    --border: #e2e8f0;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.05);
    --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.05);
    --radius: 12px;
  }

  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: var(--text);
    background: var(--bg-main);
  }

  nav {
    position: sticky;
    top: 0;
    z-index: 100;
    display: flex;
    flex-wrap: wrap;
    gap: 12px 24px;
    justify-content: center;
    padding: 14px 20px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--border);
  }

  nav a {
    color: var(--text);
    text-decoration: none;
    font-weight: 500;
    font-size: 0.95rem;
    transition: color 0.2s;
  }

  nav a:hover { color: var(--primary); }

  header {
    position: relative;
    width: 100%;
    height: 380px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: #fff;
    overflow: hidden;
  }

  header img {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    z-index: 1;
  }

  header::after {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(15, 23, 42, 0.6);
    z-index: 2;
  }

  .intro {
    position: relative;
    z-index: 3;
    max-width: 800px;
    padding: 0 20px;
  }

  h1 { font-size: 2.5rem; margin: 0 0 12px; color: #fff; font-weight: 700; }
  .intro p { font-size: 1.15rem; margin: 0; color: #e2e8f0; }

  h2 { font-size: 1.5rem; margin: 0 0 12px; color: var(--text-heading); font-weight: 600; text-align: center; }
  .section-subtitle { text-align: center; max-width: 600px; margin: 0 auto 28px; color: #64748b; }

  section { padding: 56px 20px; scroll-margin-top: 60px; }
  .wrap { max-width: 1000px; margin: 0 auto; }

  #cuotas { background: #f1f5f9; }
  #entrenadores { background: #ffffff; }
  #maquinas { background: #f8fafc; }
  #alquileres { background: #ffffff; }
  #cita { background: #f1f5f9; }

  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 20px;
  }

  .card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    box-shadow: var(--shadow-sm);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  .card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-md);
  }

  .card h3 {
    margin: 0 0 12px;
    font-size: 1.15rem;
    color: var(--text-heading);
    border-bottom: 2px solid #f1f5f9;
    padding-bottom: 8px;
  }

  .card .price {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary);
    margin-top: 8px;
  }

  .card p { margin: 6px 0; }
  .card ul { margin: 0; padding-left: 18px; color: var(--text); }
  .card ul li { margin-bottom: 6px; }

  #cita .wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  #cita-form {
    display: flex;
    flex-direction: column;
    gap: 16px;
    width: 100%;
    max-width: 480px;
    background: var(--bg-card);
    padding: 32px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-md);
  }

  #cita-form label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-weight: 500;
    font-size: 0.9rem;
    color: var(--text-heading);
  }

  #cita-form input,
  #cita-form select,
  #cita-form textarea {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
    font: inherit;
    background: #fff;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  .date-picker { position: relative; }
  .date-picker-control { display: flex; gap: 8px; }
  .date-picker-control input { min-width: 0; flex: 1; }
  #calendar-toggle {
    width: auto;
    padding: 10px 14px;
    background: #fff;
    color: var(--text-heading);
    border: 1px solid var(--border);
  }
  #calendar-toggle:hover { background: #f1f5f9; }
  #calendar {
    margin-top: 8px;
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: #fff;
  }
  #calendar[hidden] { display: none; }
  .calendar-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
  }
  .calendar-heading button {
    width: 36px;
    height: 36px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: #fff;
    font: inherit;
    cursor: pointer;
  }
  .calendar-heading button:hover,
  .calendar-day:hover { background: #eff6ff; }
  #calendar-month { font-weight: 600; text-transform: capitalize; }
  .calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, minmax(0, 1fr));
    gap: 4px;
    text-align: center;
  }
  .calendar-weekday {
    padding: 4px 0;
    color: var(--text);
    font-size: 0.75rem;
    font-weight: 600;
  }
  .calendar-day {
    min-width: 0;
    padding: 7px 0;
    border: 0;
    border-radius: 6px;
    background: #fff;
    color: var(--text-heading);
    font: inherit;
    cursor: pointer;
  }
  .calendar-day[aria-pressed="true"] {
    background: var(--primary);
    color: #fff;
  }

  #cita-form input:focus,
  #cita-form select:focus,
  #cita-form textarea:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
  }

  #cita-form textarea { resize: vertical; min-height: 90px; }

  #cita-form > button {
    width: 100%;
    border: none;
    background: var(--accent);
    color: #fff;
    padding: 12px 20px;
    font: inherit;
    font-weight: 600;
    border-radius: 8px;
    cursor: pointer;
    transition: background-color 0.2s ease;
  }

  #cita-form > button:hover { background: var(--accent-hover); }

  #cita-aviso {
    margin: 16px 0 0;
    font-weight: 500;
    color: #16a34a;
    text-align: center;
  }

  footer {
    text-align: center;
    padding: 32px 20px;
    background: var(--accent);
    color: #94a3b8;
    font-size: 0.9rem;
  }

  footer p { margin: 0; }

  #toggle {
    position: fixed;
    z-index: 30;
    right: 20px;
    bottom: 20px;
    border: none;
    background: var(--primary);
    color: #fff;
    padding: 12px 20px;
    font: inherit;
    font-weight: 600;
    border-radius: 30px;
    box-shadow: var(--shadow-lg);
    cursor: pointer;
    transition: transform 0.2s;
  }

  #toggle:hover { transform: scale(1.05); }

  #chat {
    position: fixed;
    z-index: 30;
    right: 20px;
    bottom: 76px;
    width: min(360px, calc(100vw - 40px));
    height: 460px;
    display: flex;
    flex-direction: column;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: #fff;
    box-shadow: var(--shadow-lg);
    overflow: hidden;
  }

  #chat[hidden] { display: none; }
  #log { flex: 1; overflow-y: auto; padding: 12px; background: #f8fafc; }
  .row { display: flex; margin: 8px 0; }
  .user { justify-content: flex-end; }
  
  .bubble {
    max-width: 85%;
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 0.9rem;
    line-height: 1.4;
    white-space: pre-wrap;
  }

  .bot .bubble { background: #fff; border: 1px solid var(--border); color: var(--text); }
  .user .bubble { background: var(--primary); color: #fff; }

  #chat form {
    display: flex;
    gap: 8px;
    padding: 10px;
    background: #fff;
    border-top: 1px solid var(--border);
  }

  #chat textarea {
    flex: 1;
    resize: none;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 10px;
    font: inherit;
    font-size: 0.9rem;
  }

  #chat textarea:focus { outline: none; border-color: var(--primary); }

  #send {
    border: none;
    background: var(--accent);
    color: #fff;
    padding: 0 16px;
    border-radius: 8px;
    font: inherit;
    font-weight: 500;
    cursor: pointer;
  }

  #send:disabled { opacity: 0.5; cursor: default; }
</style>
</head>
<body>

<nav>
  <a href="#cuotas">Cuotas</a>
  <a href="#entrenadores">Entrenadores</a>
  <a href="#maquinas">Máquinas</a>
  <a href="#alquileres">Alquileres</a>
  <a href="#cita">Cita</a>
</nav>

<header>
  <img src="/gimnasio.jpg" alt="Sala de un gimnasio con máquinas y pesas">
  <div class="intro">
    <h1>Gimnasio Norte</h1>
    <p>Sala de máquinas, piscina cubierta y pistas exteriores. Elige una cuota y, si quieres, añade entrenador o alquiler de pista.</p>
  </div>
</header>

<section id="cuotas">
  <div class="wrap">
    <h2>Cuotas</h2>
    <p class="section-subtitle">La cuota incluye el acceso a la sala de máquinas y a la piscina cubierta.</p>
    <div class="cards">
      <article class="card">
        <h3>Mensual</h3>
        <div class="price">35 €</div>
      </article>
      <article class="card">
        <h3>Trimestral</h3>
        <div class="price">90 €</div>
      </article>
      <article class="card">
        <h3>Anual</h3>
        <div class="price">320 €</div>
      </article>
    </div>
  </div>
</section>

<section id="entrenadores">
  <div class="wrap">
    <h2>Entrenadores personales</h2>
    <p class="section-subtitle">Servicio aparte de la cuota. Cada entrenador ofrece plan Básico, Intermedio y Premium. Precio por sesión.</p>
    <div class="cards">
      <article class="card">
        <h3>Ana Ruiz</h3>
        <p><strong>Básico:</strong> 25 €</p>
        <p><strong>Intermedio:</strong> 45 €</p>
        <p><strong>Premium:</strong> 70 €</p>
      </article>
      <article class="card">
        <h3>Luis Ortega</h3>
        <p><strong>Básico:</strong> 30 €</p>
        <p><strong>Intermedio:</strong> 50 €</p>
        <p><strong>Premium:</strong> 80 €</p>
      </article>
      <article class="card">
        <h3>Marta Gil</h3>
        <p><strong>Básico:</strong> 28 €</p>
        <p><strong>Intermedio:</strong> 48 €</p>
        <p><strong>Premium:</strong> 75 €</p>
      </article>
    </div>
  </div>
</section>

<section id="maquinas">
  <div class="wrap">
    <h2>Máquinas</h2>
    <p class="section-subtitle">Todas las máquinas están incluidas en tu cuota habitual.</p>
    <div class="cards">
      <article class="card">
        <h3>Tren superior</h3>
        <ul>
          <li>Press banca</li>
          <li>Jalón al pecho</li>
          <li>Press militar</li>
          <li>Remo</li>
        </ul>
      </article>
      <article class="card">
        <h3>Tren inferior</h3>
        <ul>
          <li>Prensa</li>
          <li>Extensión de cuádriceps</li>
          <li>Femoral tumbado</li>
          <li>Gemelos</li>
        </ul>
      </article>
    </div>
  </div>
</section>

<section id="alquileres">
  <div class="wrap">
    <h2>Alquileres</h2>
    <p class="section-subtitle">Aparte de la cuota. Tarifas de reserva por hora.</p>
    <div class="cards">
      <article class="card">
        <h3>Piscina cubierta</h3>
        <div class="price">8 € / h</div>
      </article>
      <article class="card">
        <h3>Fútbol sala</h3>
        <div class="price">40 € / h</div>
      </article>
      <article class="card">
        <h3>Tenis</h3>
        <div class="price">18 € / h</div>
      </article>
      <article class="card">
        <h3>Baloncesto</h3>
        <div class="price">30 € / h</div>
      </article>
      <article class="card">
        <h3>Pádel</h3>
        <div class="price">22 € / h</div>
      </article>
    </div>
  </div>
</section>

<section id="cita">
  <div class="wrap">
    <h2>Agenda una cita</h2>
    <p class="section-subtitle">Rellena el formulario y ven a conocer nuestras instalaciones.</p>
    <form id="cita-form">
      <label>Nombre
        <input id="cita-nombre" name="nombre" type="text" placeholder="Tu nombre completo" required>
      </label>
      <label>Fecha
        <div class="date-picker">
          <div class="date-picker-control">
            <input id="cita-fecha" name="fecha" type="text" inputmode="numeric" placeholder="dd/mm/aaaa" pattern="[0-9]{2}/[0-9]{2}/[0-9]{4}" title="Usa el formato dd/mm/aaaa" autocomplete="off" required>
            <button id="calendar-toggle" type="button" aria-expanded="false" aria-controls="calendar" aria-label="Abrir calendario">▦</button>
          </div>
          <div id="calendar" hidden>
            <div class="calendar-heading">
              <button id="calendar-prev" type="button" aria-label="Mes anterior">‹</button>
              <span id="calendar-month" aria-live="polite"></span>
              <button id="calendar-next" type="button" aria-label="Mes siguiente">›</button>
            </div>
            <div id="calendar-grid" class="calendar-grid" role="group" aria-label="Días del mes"></div>
          </div>
        </div>
      </label>
      <label>Hora
        <select id="cita-hora" name="hora" required>
          <option value="">Elige una hora</option>
          <option>09:00</option>
          <option>10:00</option>
          <option>11:00</option>
          <option>12:00</option>
          <option>13:00</option>
          <option>14:00</option>
          <option>15:00</option>
          <option>16:00</option>
          <option>17:00</option>
          <option>18:00</option>
          <option>19:00</option>
          <option>20:00</option>
        </select>
      </label>
      <label>Mensaje
        <textarea id="cita-mensaje" name="mensaje" rows="4" placeholder="¿Quieres añadir alguna observación?"></textarea>
      </label>
      <button type="submit">Agendar cita</button>
    </form>
    <p id="cita-aviso"></p>
  </div>
</section>

<footer>
  <p>© 2026 · Enrique Santisteban. Todos los derechos reservados.</p>
</footer>

<button id="toggle" type="button">Chat</button>
<div id="chat" hidden>
  <div id="log"></div>
  <form id="form">
    <textarea id="input" rows="1" placeholder="Pregunta sobre el gimnasio..."></textarea>
    <button id="send" type="submit">Enviar</button>
  </form>
</div>

<script>
const log = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("input");
const send = document.getElementById("send");
const toggle = document.getElementById("toggle");
const chat = document.getElementById("chat");
const messages = [];

let citaEnProceso = null;

const MESES = {
  "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
  "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
  "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
};

function sinTilde(text) {
  return text.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
}

function extraerFecha(text) {
  const limpio = sinTilde(text);
  const match = limpio.match(/(\\d{1,2})\\s*(?:de)?\\s*([a-z]+)/);
  
  if (match) {
    const diaNum = match[1].padStart(2, '0');
    const mesPalabra = match[2];
    if (MESES[mesPalabra]) {
      const anioActual = new Date().getFullYear();
      return anioActual + "-" + MESES[mesPalabra] + "-" + diaNum;
    }
  }

  const matchIso = text.match(/(\\d{4}-\\d{2}-\\d{2})/);
  if (matchIso) return matchIso[1];

  return null;
}

function extraerHora(text) {
  const match = text.match(/(\\d{1,2})[:h](\\d{2})?|(\\d{1,2})/);
  if (!match) return null;
  const hour = Number(match[1] || match[3]);
  if (!Number.isInteger(hour) || hour < 9 || hour > 20) return null;
  return hour + ":00";
}

function replyLocal(userText, answer) {
  messages.push({ role: "user", content: userText });
  add("user", userText);
  messages.push({ role: "assistant", content: answer });
  add("assistant", answer);
}

toggle.addEventListener("click", () => {
  chat.hidden = !chat.hidden;
  toggle.textContent = chat.hidden ? "Chat" : "Cerrar";
  if (!chat.hidden) input.focus();
});

function add(role, text) {
  const row = document.createElement("div");
  row.className = "row " + (role === "user" ? "user" : "bot");
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  row.appendChild(bubble);
  log.appendChild(row);
  log.scrollTop = log.scrollHeight;
  return bubble;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text || send.disabled) return;
  input.value = "";

  const textLower = sinTilde(text);

  if (citaEnProceso || textLower.includes("cita") || textLower.includes("reservar") || textLower.includes("apuntar")) {
    if (!citaEnProceso) {
      citaEnProceso = { nombre: null, dia: null, hora: null, esperando: "nombre" };
    }

    const posibleFecha = extraerFecha(text);
    const posibleHora = extraerHora(text);

    if (citaEnProceso.esperando === "nombre") {
      if (!posibleFecha && !posibleHora && text.length > 2) {
        citaEnProceso.nombre = text;
      } else if (!citaEnProceso.nombre) {
        replyLocal(text, "Perdona, no te he entendido bien. ¿Me podrías decir tu nombre completo para la reserva?");
        input.focus();
        return;
      }
      citaEnProceso.esperando = "dia";
    }

    if (posibleFecha) {
      citaEnProceso.dia = posibleFecha;
    }

    if (posibleHora) {
      citaEnProceso.hora = posibleHora;
    }

    if (!citaEnProceso.dia) {
      citaEnProceso.esperando = "dia";
      const mensajeError = (textLower !== "cita" && textLower !== "reservar") 
        ? "Vaya, no te he entendido con la fecha. Por favor, dime el día y el mes (ej: 15 de marzo)." 
        : "¡Claro! ¿Para qué día te gustaría agendar la cita?";
      replyLocal(text, mensajeError);
      input.focus();
      return;
    }

    if (!citaEnProceso.hora) {
      citaEnProceso.esperando = "hora";
      replyLocal(text, "Perfecto, fecha " + citaEnProceso.dia + ". ¿A qué hora te va bien? Atendemos desde las 9:00 hasta las 20:00.");
      input.focus();
      return;
    }

    const datosCita = { 
      nombre: citaEnProceso.nombre || "Anónimo", 
      dia: citaEnProceso.dia, 
      hora: citaEnProceso.hora, 
      mensaje: "Agendado vía chat inteligente" 
    };

    try {
      const resp = await fetch("/api/citas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datosCita)
      });
      if (!resp.ok) throw new Error("Error en servidor");
    } catch(err) {
      console.error("Error al guardar la cita:", err);
    }

    replyLocal(text, "¡Listo! Ya te he guardado la cita a nombre de " + datosCita.nombre + " para el día " + datosCita.dia + " a las " + datosCita.hora + ". ¡Te esperamos en el Gimnasio Norte!");
    
    citaEnProceso = null;
    input.focus();
    return;
  }

  messages.push({ role: "user", content: text });
  add("user", text);
  send.disabled = true;
  const bubble = add("assistant", "");
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
    });
    if (!res.ok) throw new Error(await res.text());
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let full = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      full += decoder.decode(value, { stream: true });
      bubble.textContent = full;
      log.scrollTop = log.scrollHeight;
    }
    messages.push({ role: "assistant", content: full });
  } catch (err) {
    bubble.textContent = "Error: " + err.message;
  }
  send.disabled = false;
  input.focus();
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

const citaForm = document.getElementById("cita-form");
const citaAviso = document.getElementById("cita-aviso");
const citaFecha = document.getElementById("cita-fecha");
const calendar = document.getElementById("calendar");
const calendarToggle = document.getElementById("calendar-toggle");
const calendarMonth = document.getElementById("calendar-month");
const calendarGrid = document.getElementById("calendar-grid");
const calendarWeekdays = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];
let visibleMonth = new Date();
visibleMonth.setDate(1);

function renderCalendar() {
  calendarMonth.textContent = visibleMonth.toLocaleDateString("es-ES", {
    month: "long",
    year: "numeric"
  });
  calendarGrid.replaceChildren();

  calendarWeekdays.forEach((day) => {
    const weekday = document.createElement("span");
    weekday.className = "calendar-weekday";
    weekday.textContent = day;
    calendarGrid.appendChild(weekday);
  });

  const year = visibleMonth.getFullYear();
  const month = visibleMonth.getMonth();
  const firstWeekday = (new Date(year, month, 1).getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const selectedDate = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(citaFecha.value);

  for (let i = 0; i < firstWeekday; i++) {
    calendarGrid.appendChild(document.createElement("span"));
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const button = document.createElement("button");
    const date = new Date(year, month, day);
    const dayText = String(day).padStart(2, "0");
    const monthText = String(month + 1).padStart(2, "0");
    const dateValue = dayText + "/" + monthText + "/" + year;
    button.type = "button";
    button.className = "calendar-day";
    button.textContent = String(day);
    button.setAttribute("aria-label", date.toLocaleDateString("es-ES", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric"
    }));
    button.setAttribute("aria-pressed", String(Boolean(
      selectedDate &&
      Number(selectedDate[1]) === day &&
      Number(selectedDate[2]) === month + 1 &&
      Number(selectedDate[3]) === year
    )));
    button.addEventListener("click", () => {
      citaFecha.value = dateValue;
      calendar.hidden = true;
      calendarToggle.setAttribute("aria-expanded", "false");
      citaFecha.focus();
    });
    calendarGrid.appendChild(button);
  }
}

calendarToggle.addEventListener("click", () => {
  calendar.hidden = !calendar.hidden;
  calendarToggle.setAttribute("aria-expanded", String(!calendar.hidden));
  if (!calendar.hidden) {
    const selectedDate = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(citaFecha.value);
    if (selectedDate) visibleMonth = new Date(Number(selectedDate[3]), Number(selectedDate[2]) - 1, 1);
    renderCalendar();
  }
});

document.getElementById("calendar-prev").addEventListener("click", () => {
  visibleMonth.setMonth(visibleMonth.getMonth() - 1);
  renderCalendar();
});

document.getElementById("calendar-next").addEventListener("click", () => {
  visibleMonth.setMonth(visibleMonth.getMonth() + 1);
  renderCalendar();
});

citaForm.addEventListener("reset", () => {
  calendar.hidden = true;
  calendarToggle.setAttribute("aria-expanded", "false");
});

citaForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const nombre = document.getElementById("cita-nombre").value.trim();
  const fecha = citaFecha.value.trim();
  const hora = document.getElementById("cita-hora").value;
  const submitButton = citaForm.querySelector('button[type="submit"]');
  submitButton.disabled = true;

  try {
    const response = await fetch("/api/citas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre, fecha, hora })
    });
    if (!response.ok) throw new Error(await response.text());
    citaAviso.textContent = "Cita agendada y guardada para " + nombre + " el " + fecha + " a las " + hora + ".";
    citaForm.reset();
  } catch (err) {
    citaAviso.textContent = "No se pudo guardar la cita: " + err.message;
  } finally {
    submitButton.disabled = false;
  }
});
</script>
</body>
</html>`;

const server = http.createServer(async (req, res) => {
  if (req.method === "GET" && req.url === "/") {
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(page);
    return;
  }

  if (req.method === "GET" && req.url === "/gimnasio.jpg") {
    res.writeHead(200, { "Content-Type": "image/jpeg" });
    const imgPath = path.join(__dirname, "gimnasio.jpg");
    if (fs.existsSync(imgPath)) {
      fs.createReadStream(imgPath).pipe(res);
    } else {
      res.writeHead(404);
      res.end();
    }
    return;
  }

  if (req.method === "POST" && req.url === "/api/citas") {
    let body = "";
    req.on("data", chunk => { body += chunk; });
    req.on("end", () => {
      try {
        const data = JSON.parse(body);
        const nombre = typeof data.nombre === "string" ? data.nombre.trim().replace(/[\r\n]+/g, " ") : "";
        const fecha = typeof data.fecha === "string" ? data.fecha.trim() : "";
        const hora = typeof data.hora === "string" ? data.hora : "";
        const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(fecha);
        const dia = match ? Number(match[1]) : 0;
        const mes = match ? Number(match[2]) : 0;
        const anio = match ? Number(match[3]) : 0;
        const diasEnMes = mes >= 1 && mes <= 12 && anio >= 1000
          ? new Date(Date.UTC(anio, mes, 0)).getUTCDate()
          : 0;

        if (!nombre || !match || dia < 1 || dia > diasEnMes || !/^(?:09|1\d|20):00$/.test(hora)) {
          res.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
          res.end("Introduce nombre, fecha válida en formato dd/mm/aaaa y hora.");
          return;
        }

        const lineaCita = `Nombre: ${nombre}\nFecha: ${fecha}\nHora: ${hora}\n\n`;
        fs.appendFile(CITAS_FILE, lineaCita, "utf8", (err) => {
          if (err) {
            console.error("Error al guardar la cita:", err);
            res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
            res.end("Error al guardar la cita en citas.txt.");
          } else {
            res.writeHead(201, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ success: true }));
          }
        });
      } catch (err) {
        res.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
        res.end("Datos incorrectos.");
      }
    });
    return;
  }

  if (req.method === "POST" && req.url === "/api/chat") {
    let body = "";
    req.on("data", chunk => { body += chunk; });
    req.on("end", async () => {
      try {
        const { messages } = JSON.parse(body);
        let ollama;
        try {
          ollama = await fetch(OLLAMA, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              model: MODEL,
              messages: [{ role: "system", content: SYSTEM }, ...messages],
              stream: true,
            }),
          });
        } catch {
          res.writeHead(502, { "Content-Type": "text/plain; charset=utf-8" });
          res.end("No se pudo conectar con Ollama. ¿Está en marcha?");
          return;
        }

        if (!ollama.ok) {
          res.writeHead(502, { "Content-Type": "text/plain; charset=utf-8" });
          res.end(await ollama.text());
          return;
        }

        res.writeHead(200, {
          "Content-Type": "text/plain; charset=utf-8",
          "Cache-Control": "no-cache",
        });

        const reader = ollama.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const lines = buf.split("\n");
          buf = lines.pop();
          for (const line of lines) {
            if (!line.trim()) continue;
            const piece = JSON.parse(line).message?.content || "";
            if (piece) res.write(piece);
          }
        }
        res.end();
      } catch (err) {
        res.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
        res.end("Error al procesar la solicitud del chat");
      }
    });
    return;
  }

  res.writeHead(404);
  res.end();
});

server.listen(PORT, () => {
  console.log("Servidor y chat con calendario en http://localhost:" + PORT);
});