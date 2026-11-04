1. Estructura del Proyecto
Crea una carpeta para tu proyecto e inicialízala con los siguientes archivos:
mi-proyecto-ollama/
├── package.json
└── server.js


2. Archivo ⁠package.json⁠


{
  "name": "ollama-landing-chat",
  "version": "1.0.0",
  "type": "module",
  "main": "server.js",
  "dependencies": {
    "express": "^4.19.2",
    "ollama": "^0.5.0"
  }
}


3. Archivo ⁠server.js⁠
Este archivo contiene el servidor backend en Node.js y sirve la Landing Page con el widget de chat incrustado abajo a la derecha.


import express from 'express';
import ollama from 'ollama';

const app = express();
app.use(express.json());

// Endpoint para comunicarnos con el modelo Qwen en Ollama
app.post('/api/chat', async (req, res) => {
  try {
    const { messages } = req.body;
    const response = await ollama.chat({
      model: 'qwen', // Asegúrate de tener 'qwen' listo en Ollama
      messages: messages
    });
    res.json({ message: response.message.content });
  } catch (error) {
    res.status(500).json({ error: 'Error al conectar con Ollama.' });
  }
});

// HTML sencillo de la Landing Page + Chatbox flotante
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Landing Page + Qwen Chat</title>
      <style>
        body { font-family: sans-serif; margin: 0; padding: 40px; background: #f4f4f9; color: #333; }
        header { text-align: center; margin-bottom: 40px; }
        .content { max-width: 600px; margin: 0 auto; line-height: 1.6; }
        
        /* Estilos del Widget de Chatbox (Abajo a la derecha) */
        #chat-widget { position: fixed; bottom: 20px; right: 20px; width: 320px; height: 420px; background: #fff; border: 1px solid #ccc; border-radius: 8px; display: flex; flex-direction: column; box-shadow: 0 4px 10px rgba(0,0,0,0.15); }
        #chat-header { background: #007bff; color: white; padding: 10px; font-weight: bold; border-radius: 8px 8px 0 0; }
        #chat-messages { flex: 1; padding: 10px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; font-size: 14px; }
        .msg { padding: 8px 12px; border-radius: 12px; max-width: 80%; }
        .user { background: #007bff; color: white; align-self: flex-end; }
        .bot { background: #e9ecef; color: black; align-self: flex-start; }
        #chat-form { display: flex; border-top: 1px solid #ccc; }
        #chat-input { flex: 1; border: none; padding: 10px; outline: none; }
        #chat-form button { background: #007bff; color: white; border: none; padding: 10px 15px; cursor: pointer; }
      </style>
    </head>
    <body>

      <header>
        <h1>Bienvenido a Nuestra Plataforma</h1>
        <p>La solución perfecta para simplificar tu trabajo diario.</p>
      </header>

      <div class="content">
        <h2>¿Por qué elegirnos?</h2>
        <p>Ofrecemos herramientas eficientes y rápidas desarrolladas para optimizar tus procesos al máximo sin complicaciones.</p>
      </div>

      <!-- Chatbox Widget -->
      <div id="chat-widget">
        <div id="chat-header">Asistente Qwen</div>
        <div id="chat-messages">
          <div class="msg bot">¡Hola! Pregúntame lo que quieras sobre esta página.</div>
        </div>
        <form id="chat-form">
          <input type="text" id="chat-input" placeholder="Escribe tu mensaje..." required />
          <button type="submit">Enviar</button>
        </form>
      </div>

      <script>
        const form = document.getElementById('chat-form');
        const input = document.getElementById('chat-input');
        const messagesDiv = document.getElementById('chat-messages');

        // Contexto inicial del chat con la información de la landing page
        const history = [
          { 
            role: 'system', 
            content: 'Eres un asistente virtual servicial en una landing page. La landing page habla sobre una plataforma que simplifica el trabajo diario y optimiza procesos. Responde dudas sobre la página de forma concisa.' 
          }
        ];

        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const text = input.value.trim();
          if (!text) return;

          // Mostrar mensaje del usuario
          appendMessage(text, 'user');
          history.push({ role: 'user', content: text });
          input.value = '';

          // Solicitud al servidor Node.js
          try {
            const res = await fetch('/api/chat', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ messages: history })
            });
            const data = await res.json();
            
            if (data.message) {
              appendMessage(data.message, 'bot');
              history.push({ role: 'assistant', content: data.message });
            }
          } catch (err) {
            appendMessage('Error de conexión.', 'bot');
          }
        });

        function appendMessage(text, type) {
          const msg = document.createElement('div');
          msg.className = \`msg \${type}\`;
          msg.textContent = text;
          messagesDiv.appendChild(msg);
          messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
      </script>

    </body>
    </html>
  `);
});

app.listen(3000, () => {
  console.log('Servidor listo en http://localhost:3000');
});



4. Pasos para ejecutar y gestionar con Cursor, Ollama y Git

Asegúrate de que Ollama está ejecutándose:

ollama run qwen


Instala las dependencias:

npm install

Inicia la aplicación:


node server.js


Abre http://localhost:3000 en tu navegador para interactuar con la página y la chatbox.


Control de versiones con Git (desde la terminal de Cursor):


git init
echo "node_modules/" > .gitignore
git add .
git commit -m "Initial commit: Landing page con chatbox conectada a Ollama Qwen"


