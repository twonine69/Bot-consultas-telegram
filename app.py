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
          chat_id, "Olá, Caio! Para consultar um endereço, digite /cep seguido do número.\n\nExemplo: /cep 01001000"
      )
    
    # Novo comando real de CEP
    elif text.startswith("/cep"):
      # Pega apenas o número que o usuário digitou depois de "/cep "
      numero_cep = text.replace("/cep", "").strip()
      
      if numero_cep == "":
        enviar_mensagem(chat_id, "Você esqueceu de digitar o CEP! Tente assim: /cep 01001000")
      else:
        # Chama a função que vai na internet buscar o CEP
        resultado = buscar_cep_real(numero_cep)
        enviar_mensagem(chat_id, resultado)

    # Comando /sobre
    elif text == "/sobre":
      enviar_mensagem(chat_id, "ℹ️ Bot de consultas em Python criado pelo Caio.")

    # Resposta padrão para erros
    else:
      enviar_mensagem(chat_id, "Não entendi. Tente usar o comando /cep seguido de um número.")

  return "OK", 200

# Função para enviar a mensagem de volta pro Telegram
def enviar_mensagem(chat_id, texto):
  url = f"{TELEGRAM_API}/sendMessage"
  payload = {"chat_id": chat_id, "text": texto}
  requests.post(url, json=payload)

# Função nova que conecta na internet e busca o CEP real
def buscar_cep_real(cep):
  # Limpa o CEP tirando traços ou pontos
  cep = cep.replace("-", "").replace(".", "").replace(" ", "")
  
  if len(cep) != 8 or not cep.isdigit():
    return "❌ CEP inválido. Por favor, digite apenas os 8 números."
  
  try:
    # Consulta a API gratuita do ViaCEP
    link = f"https://viacep.com.br/ws/{cep}/json/"
    resposta = requests.get(link)
    dados = resposta.json()
    
    # Se o CEP não existir no sistema
    if "erro" in dados:
      return "❌ CEP não encontrado."
    
    # Monta a mensagem bonitinha com os dados reais
    mensagem = "📍 *Resultado da Consulta:*\n\n"
    mensagem += f"CEP: {dados.get('cep')}\n"
    mensagem += f"Rua: {dados.get('logradouro')}\n"
    mensagem += f"Bairro: {dados.get('bairro')}\n"
    mensagem += f"Cidade: {dados.get('localidade')} - {dados.get('uf')}"
    
    return mensagem

  except Exception as e:
    return "❌ Ocorreu um erro no servidor ao buscar o CEP."

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
