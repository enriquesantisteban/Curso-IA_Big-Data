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

const page = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gimnasio Norte</title>
<style>
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0;
    font-family: system-ui, sans-serif;
    line-height: 1.5;
    color: #2c2c2c;
    background: #f7f6f4;
  }
  header img {
    display: block;
    width: 100%;
    height: 280px;
    object-fit: cover;
  }
  .intro { max-width: 960px; margin: 0 auto; padding: 24px 16px 8px; }
  h1 { font-size: 1.75rem; margin: 0 0 8px; }
  h2 { font-size: 1.15rem; margin: 0 0 8px; }
  p { margin: 0 0 16px; }
  nav {
    position: sticky;
    top: 0;
    z-index: 2;
    display: flex;
    flex-wrap: wrap;
    gap: 8px 20px;
    justify-content: center;
    padding: 12px 16px;
    background: #f3f1ee;
    border-bottom: 1px solid #ddd8d2;
  }
  nav a { color: #2c2c2c; text-decoration: none; }
  nav a:hover { text-decoration: underline; }
  section { padding: 36px 16px; scroll-margin-top: 52px; }
  .wrap { max-width: 960px; margin: 0 auto; }
  #cuotas { background: #f3f1ee; }
  #entrenadores { background: #e7ece8; }
  #maquinas { background: #e8ebef; }
  #alquileres { background: #f7f6f4; }
  #cita { background: #f3f1ee; }
  #cita-form {
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-width: 420px;
  }
  #cita-form label { display: flex; flex-direction: column; gap: 4px; }
  #cita-form input,
  #cita-form select,
  #cita-form textarea {
    border: 1px solid #ccc;
    padding: 8px;
    font: inherit;
    background: #fff;
  }
  #cita-form textarea { resize: vertical; min-height: 80px; }
  #cita-form button {
    align-self: flex-start;
    border: 1px solid #222;
    background: #fff;
    padding: 8px 16px;
    font: inherit;
    cursor: pointer;
  }
  #cita-aviso { margin: 16px 0 0; }
  .cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }
  .card {
    background: #fff;
    border: 1px solid #ddd8d2;
    padding: 16px;
  }
  .card h3 { margin: 0 0 8px; font-size: 1rem; }
  .card p { margin: 0; }
  ul { margin: 0; padding-left: 20px; }
  footer {
    text-align: center;
    padding: 28px 16px 88px;
    background: #e4e1dc;
  }
  footer p { margin: 0; }
  @media (max-width: 720px) {
    .cards { grid-template-columns: 1fr; }
  }
  #toggle {
    position: fixed;
    z-index: 3;
    right: 16px;
    bottom: 16px;
    border: 1px solid #222;
    background: #fff;
    padding: 8px 16px;
    font: inherit;
    cursor: pointer;
  }
  #chat {
    position: fixed;
    z-index: 3;
    right: 16px;
    bottom: 60px;
    width: min(320px, calc(100vw - 32px));
    height: 420px;
    display: flex;
    flex-direction: column;
    border: 1px solid #222;
    background: #fff;
  }
  #chat[hidden] { display: none; }
  #log { flex: 1; overflow-y: auto; padding: 8px; }
  .row { display: flex; margin: 6px 0; }
  .user { justify-content: flex-end; }
  .bubble {
    max-width: 85%;
    padding: 8px 10px;
    border: 1px solid #ccc;
    white-space: pre-wrap;
  }
  .user .bubble { background: #f3f3f3; }
  #chat form { display: flex; gap: 6px; padding: 8px; border-top: 1px solid #ccc; }
  #chat textarea {
    flex: 1;
    resize: none;
    border: 1px solid #ccc;
    padding: 8px;
    font: inherit;
  }
  #send {
    border: 1px solid #222;
    background: #fff;
    padding: 0 12px;
    font: inherit;
    cursor: pointer;
  }
  #send:disabled { opacity: 0.5; cursor: default; }
</style>
</head>
<body>
<header>
  <img src="/gimnasio.jpg" alt="Sala de un gimnasio con máquinas y pesas">
  <div class="intro">
    <h1>Gimnasio Norte</h1>
    <p>Sala de máquinas, piscina cubierta y pistas exteriores. Elige una cuota y, si quieres, añade entrenador o alquiler de pista.</p>
  </div>
</header>
<nav>
  <a href="#cuotas">Cuotas</a>
  <a href="#entrenadores">Entrenadores</a>
  <a href="#maquinas">Máquinas</a>
  <a href="#alquileres">Alquileres</a>
  <a href="#cita">Cita</a>
</nav>
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
<section id="cita">
  <div class="wrap">
    <h2>Agenda una cita</h2>
    <form id="cita-form">
      <label>Nombre
        <input id="cita-nombre" name="nombre" type="text" required>
      </label>
      <label>Día
        <select id="cita-dia" name="dia" required>
          <option value="">Elige un día</option>
          <option>Lunes</option>
          <option>Martes</option>
          <option>Miércoles</option>
          <option>Jueves</option>
          <option>Viernes</option>
          <option>Sábado</option>
          <option>Domingo</option>
        </select>
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
        <textarea id="cita-mensaje" name="mensaje" rows="4"></textarea>
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
  return text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
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
  citaAviso.textContent = "Cita agendada para " + nombre + " el día " + dia + " a la hora " + hora;
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
