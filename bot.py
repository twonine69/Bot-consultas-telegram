import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Token do seu bot
TOKEN = "8965654492:AAHG05JuRJeVm7ovQSe3vXH01k4bZgVOfjl"
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
  update = request.get_json()

  if update and "message" in update:
    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")

    # Resposta de teste para o comando /start
    if text == "/start":
      enviar_mensagem(
          chat_id, "Olá, Caio! Seu bot Python no Render está rodando com sucesso! 🚀"
      )

  return "OK", 200


def enviar_mensagem(chat_id, texto):
  url = f"{TELEGRAM_API}/sendMessage"
  payload = {"chat_id": chat_id, "text": texto}
  requests.post(url, json=payload)


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
