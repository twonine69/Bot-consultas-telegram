import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Token do seu bot
TOKEN = "8965654492:AAE4BrpoPMoe8AFd0sIsuH2MrZyaEJgpxgw"
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
  update = request.get_json()

  if update and "message" in update:
    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")

    # Comando /start
    if text == "/start":
      enviar_mensagem(
          chat_id, "Olá, Caio! Escolha uma opção:\n\n/consulta - Fazer uma nova consulta\n/sobre - Informações do bot"
      )
    
    # Novo comando /consulta
    elif text == "/consulta":
      enviar_mensagem(
          chat_id, "🔍 Você escolheu Consultar!\n\nPor favor, digite o que você deseja buscar..."
      )

    # Novo comando /sobre
    elif text == "/sobre":
      enviar_mensagem(
          chat_id, "ℹ️ Este é um bot de consultas criado em Python pelo Caio."
      )

    # O que ele responde se a pessoa digitar qualquer outra coisa
    else:
      enviar_mensagem(
          chat_id, f"Você digitou: {text}\nEm breve vou conseguir consultar essa informação para você!"
      )

  return "OK", 200


def enviar_mensagem(chat_id, texto):
  url = f"{TELEGRAM_API}/sendMessage"
  payload = {"chat_id": chat_id, "text": texto}
  requests.post(url, json=payload)


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
