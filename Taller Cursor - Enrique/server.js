const http = require("http");
const fs = require("fs");
const path = require("path");

const OLLAMA = "http://127.0.0.1:11434/api/chat";
const MODEL = "qwen2.5:3b";
const PORT = 3000;

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

const server = http.createServer(async (req, res) => {
  if (req.method === "GET" && req.url === "/") {
    // Leemos el JSON de elementos para pasárselo a la página dinámicamente
    let elementos = [];
    try {
      const data = fs.readFileSync(path.join(__dirname, "elementos.json"), "utf8");
      elementos = JSON.parse(data);
    } catch (err) {
      console.error("No se pudo leer elementos.json", err);
    }

    // Generamos las tarjetas HTML a partir del JSON
    const elementosHtml = elementos.map(el => `
      <article class="card">
        <h3>${el.titulo}</h3>
        <p>${el.descripcion}</p>
      </article>
    `).join("");

    const page = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gimnasio Norte</title>
<style>

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  font-family: system-ui, sans-serif;
  line-height: 1.6;
  color: #252a27;
  background: #f7f8f6;
}

/* NAVEGACIÓN SUPERIOR */
nav {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px 30px;
  padding: 17px 20px;
  background: #172c24;
  box-shadow: 0 3px 12px rgba(0,0,0,.15);
}

nav a {
  color: white;
  text-decoration: none;
  font-size: .95rem;
  font-weight: 600;
  transition: color .2s;
}

nav a:hover {
  color: #9bd5a9;
}

/* IMAGEN PRINCIPAL */
header {
  position: relative;
  height: 480px;
  overflow: hidden;
  display: flex;
  align-items: center;
}

header img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

header::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    rgba(0,0,0,.78),
    rgba(0,0,0,.25)
  );
}

.intro {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: 30px;
  color: white;
}

h1 {
  font-size: clamp(2.5rem, 6vw, 4.5rem);
  line-height: 1.1;
  margin: 0 0 18px;
  font-weight: 800;
}

.intro p {
  max-width: 620px;
  font-size: 1.15rem;
  color: #f0f0f0;
}

/* SECCIONES */
section {
  padding: 55px 20px;
  scroll-margin-top: 75px;
}

.wrap {
  max-width: 1100px;
  margin: 0 auto;
}

h2 {
  font-size: 1.8rem;
  margin: 0 0 12px;
  color: #203c2e;
}

section .wrap > p {
  color: #666;
  margin-bottom: 25px;
}

/* FONDOS */
#cuotas {
  background: #f1f5f1;
}

#entrenadores {
  background: #e6eee8;
}

#maquinas {
  background: #edf0f4;
}

#alquileres {
  background: #f7f8f6;
}

#elementos-dinamicos {
  background: #edf3ed;
}

/* TARJETAS */
.cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.card {
  background: white;
  border: 1px solid #e2e7e2;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 14px rgba(0,0,0,.045);
  transition: transform .2s, box-shadow .2s;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 9px 22px rgba(0,0,0,.09);
}

.card h3 {
  margin: 0 0 12px;
  font-size: 1.1rem;
  color: #24563b;
}

.card p {
  margin: 0 0 8px;
}

/* FORMULARIO DE CITAS */
#cita {
  background: #e8eee9;
  display: flex;
  justify-content: center;
}

#cita .wrap {
  width: 100%;
  max-width: 550px;
  background: white;
  padding: 35px;
  border-radius: 14px;
  box-shadow: 0 5px 20px rgba(0,0,0,.07);
}

#cita h2 {
  text-align: center;
  margin-bottom: 25px;
}

#cita-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

#cita-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 600;
}

#cita-form input,
#cita-form select,
#cita-form textarea {
  width: 100%;
  border: 1px solid #d4dcd5;
  padding: 12px;
  font: inherit;
  background: #f9faf9;
  border-radius: 7px;
}

#cita-form input:focus,
#cita-form select:focus,
#cita-form textarea:focus {
  outline: none;
  border-color: #39734e;
}

#cita-form textarea {
  resize: vertical;
  min-height: 90px;
}

#cita-form button {
  border: none;
  background: #24563b;
  color: white;
  padding: 14px;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  border-radius: 7px;
  transition: background .2s;
}

#cita-form button:hover {
  background: #173d29;
}

#cita-aviso {
  margin-top: 16px;
  text-align: center;
  color: #2e7d32;
  font-weight: 600;
}

/* PIE DE PÁGINA */
footer {
  text-align: center;
  padding: 30px 16px 100px;
  background: #172c24;
  color: white;
}

/* CHAT */
#toggle {
  position: fixed;
  z-index: 12;
  right: 20px;
  bottom: 20px;
  border: none;
  background: #24563b;
  color: white;
  padding: 12px 22px;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  border-radius: 25px;
  box-shadow: 0 4px 12px rgba(0,0,0,.2);
}

#chat {
  position: fixed;
  z-index: 12;
  right: 20px;
  bottom: 75px;
  width: min(350px, calc(100vw - 40px));
  height: 420px;
  display: flex;
  flex-direction: column;
  border: 1px solid #ddd;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 5px 25px rgba(0,0,0,.18);
}

#chat[hidden] {
  display: none;
}

#log {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.row {
  display: flex;
  margin: 8px 0;
}

.user {
  justify-content: flex-end;
}

.bubble {
  max-width: 85%;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f0f2f0;
  white-space: pre-wrap;
}

.user .bubble {
  background: #e1eee4;
}

#chat form {
  display: flex;
  gap: 6px;
  padding: 10px;
  border-top: 1px solid #ddd;
}

#chat textarea {
  flex: 1;
  resize: none;
  border: 1px solid #ccc;
  border-radius: 6px;
  padding: 8px;
  font: inherit;
}

#send {
  border: none;
  background: #24563b;
  color: white;
  padding: 0 14px;
  border-radius: 6px;
  cursor: pointer;
}

#send:disabled {
  opacity: .5;
  cursor: default;
}

/* ADAPTACIÓN A MÓVILES */
@media (max-width: 720px) {
  nav {
    gap: 10px 16px;
    padding: 13px 10px;
  }

  nav a {
    font-size: .85rem;
  }

  header {
    height: 390px;
  }

  .intro {
    padding: 22px;
  }

  .cards {
    grid-template-columns: 1fr;
  }

  section {
    padding: 40px 16px;
  }

  #cita .wrap {
    padding: 24px;
  }
}

</style>
</head>

<body>

<nav>
  <a href="#cuotas">Cuotas</a>
  <a href="#entrenadores">Entrenadores</a>
  <a href="#maquinas">Máquinas</a>
  <a href="#alquileres">Alquileres</a>
  <a href="#elementos-dinamicos">Servicios Destacados</a>
  <a href="#cita">Cita</a>
</nav>

<header>
  <img src="/gimnasio.jpg" alt="Sala de un gimnasio con máquinas y pesas">

  <div class="intro">
    <h1>Gimnasio Norte</h1>
    <p>
      Sala de máquinas, piscina cubierta y pistas exteriores.
      Elige una cuota y, si quieres, añade entrenador o alquiler de pista.
    </p>
  </div>
</header>

<section id="cuotas">
  <div class="wrap">
    <h2>Cuotas</h2>
    <p>La cuota incluye el acceso a la sala de máquinas y a la piscina cubierta.</p>
    <div class="cards">
      <article class="card">
        <h3>Mensual</h3>
        <p>35 €</p>
      </article>
      <article class="card">
        <h3>Trimestral</h3>
        <p>90 €</p>
      </article>
      <article class="card">
        <h3>Anual</h3>
        <p>320 €</p>
      </article>
    </div>
  </div>
</section>

<section id="entrenadores">
  <div class="wrap">
    <h2>Entrenadores personales</h2>
    <p>Servicio aparte de la cuota. Cada entrenador ofrece plan Básico, Intermedio y Premium. Precio por sesión.</p>
    <div class="cards">
      <article class="card">
        <h3>Ana Ruiz</h3>
        <p>Básico --> 25 €</p>
        <p>Intermedio --> 45 €</p>
        <p>Premium --> 70 €</p>
      </article>
      <article class="card">
        <h3>Luis Ortega</h3>
        <p>Básico --> 30 €</p>
        <p>Intermedio --> 50 €</p>
        <p>Premium --> 80 €</p>
      </article>
      <article class="card">
        <h3>Marta Gil</h3>
        <p>Básico --> 28 €</p>
        <p>Intermedio --> 48 €</p>
        <p>Premium --> 75 €</p>
      </article>
    </div>
  </div>
</section>

<section id="maquinas">
  <div class="wrap">
    <h2>Máquinas</h2>
    <p>Incluidas en la cuota.</p>
    <div class="cards">
      <article class="card">
        <h3>Tren superior</h3>
        <p>Press banca, jalón al pecho, press militar, remo</p>
      </article>
      <article class="card">
        <h3>Tren inferior</h3>
        <p>Prensa, extensión de cuádriceps, femoral tumbado, gemelos</p>
      </article>
    </div>
  </div>
</section>

<section id="alquileres">
  <div class="wrap">
    <h2>Alquileres</h2>
    <p>Aparte de la cuota. Precio por hora.</p>
    <div class="cards">
      <article class="card">
        <h3>Piscina cubierta</h3>
        <p>8 €</p>
      </article>
      <article class="card">
        <h3>Fútbol sala</h3>
        <p>40 €</p>
      </article>
      <article class="card">
        <h3>Tenis</h3>
        <p>18 €</p>
      </article>
      <article class="card">
        <h3>Baloncesto</h3>
        <p>30 €</p>
      </article>
      <article class="card">
        <h3>Pádel</h3>
        <p>22 €</p>
      </article>
    </div>
  </div>
</section>

<!-- SECCIÓN NUEVA CARGADA DESDE EL JSON -->
<section id="elementos-dinamicos">
  <div class="wrap">
    <h2>Servicios e Instalaciones Destacadas</h2>
    <p>Listado obtenido directamente desde nuestra base de datos en JSON.</p>
    <div class="cards">
      ${elementosHtml}
    </div>
  </div>
</section>

<section id="cita">
  <div class="wrap">
    <h2>Agenda una cita</h2>
    <form id="cita-form">
      <label>Nombre
        <input id="cita-nombre" name="nombre" type="text" placeholder="Tu nombre completo" required>
      </label>
      <label>Fecha de la cita
  <input
    id="cita-dia"
    name="dia"
    type="date"
    required
  >
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
      <label>Mensaje (Opcional)
        <textarea id="cita-mensaje" name="mensaje" placeholder="¿Alguna duda o comentario adicional?"></textarea>
      </label>
      <button type="submit">Agendar una cita</button>
    </form>
    <p id="cita-aviso"></p>
  </div>
</section>

<footer>
  <p>2026 · Enrique Santisteban</p>
</footer>

<button id="toggle" type="button">Chat</button>
<div id="chat" hidden>
  <div id="log"></div>
  <form id="form">
    <textarea id="input" rows="2" placeholder="Pregunta sobre el gimnasio"></textarea>
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
let cita = null;

const DIAS = [
  ["lunes", "Lunes"],
  ["martes", "Martes"],
  ["miercoles", "Miércoles"],
  ["jueves", "Jueves"],
  ["viernes", "Viernes"],
  ["sabado", "Sábado"],
  ["domingo", "Domingo"],
];

function sinTilde(text) {
  return text.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
}

function diaValido(text) {
  const key = sinTilde(text).trim();
  const found = DIAS.find(([plain]) => plain === key);
  return found ? found[1] : null;
}

function horaValida(text) {
  const match = text.match(/(\\d{1,2})/);
  if (!match) return null;
  const hour = Number(match[1]);
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

  if (cita || sinTilde(text).includes("agendar una cita")) {
    if (!cita) {
      cita = { step: "nombre" };
      replyLocal(text, "¡Genial! ¿Cuál es tu nombre?");
      input.focus();
      return;
    }
    if (cita.step === "nombre") {
      cita.nombre = text;
      cita.step = "dia";
      replyLocal(text, "¿Qué día de la semana quieres agendar la cita? Recuerda que estamos disponibles de lunes a domingo");
      input.focus();
      return;
    }
    if (cita.step === "dia") {
      const dia = diaValido(text);
      if (!dia) {
        replyLocal(text, "¿Qué día de la semana quieres agendar la cita? Recuerda que estamos disponibles de lunes a domingo");
        input.focus();
        return;
      }
      cita.dia = dia;
      cita.step = "hora";
      replyLocal(text, "Perfecto, y por último. ¿A qué hora quieres venir? Tenemos citas cada hora, desde las 9:00 hasta las 20:00");
      input.focus();
      return;
    }
    const hora = horaValida(text);
    if (!hora) {
      replyLocal(text, "Perfecto, y por último. ¿A qué hora quieres venir? Tenemos citas cada hora, desde las 9:00 hasta las 20:00");
      input.focus();
      return;
    }
    replyLocal(text, "¡Perfecto! Se ha agendado una cita para " + cita.nombre + ", el día " + cita.dia + " a las " + hora);
    cita = null;
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
citaForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const nombre = document.getElementById("cita-nombre").value.trim();
const dia = document.getElementById("cita-dia").value;
const hora = document.getElementById("cita-hora").value;

// Convertimos la fecha a formato español
const fecha = new Date(dia + "T12:00:00");
const fechaFormateada = fecha.toLocaleDateString("es-ES", {
  day: "numeric",
  month: "long",
  year: "numeric"
});

citaAviso.textContent =
  "¡Cita agendada para " + nombre +
  " el día " + fechaFormateada +
  " a las " + hora;
  });
</script>
</body>
</html>`;

    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(page);
    return;
  }

  if (req.method === "GET" && req.url === "/gimnasio.jpg") {
    res.writeHead(200, { "Content-Type": "image/jpeg" });
    fs.createReadStream(path.join(__dirname, "gimnasio.jpg")).pipe(res);
    return;
  }

  if (req.method === "POST" && req.url === "/api/chat") {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const { messages } = JSON.parse(Buffer.concat(chunks).toString());

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
    return;
  }

  res.writeHead(404);
  res.end();
});

server.listen(PORT, () => {
  console.log("Chat en http://localhost:" + PORT);
});