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
          chat_id, "Olá, Caio! Escolha uma consulta:\n\n/cep [número] - Consulta de Endereço\n/cnpj [número] - Consulta de Empresa\n/cpf [número] - Simulação de Consulta"
      )
    
    # 1. Consulta REAL de CEP
    elif text.startswith("/cep"):
      numero_cep = text.replace("/cep", "").strip()
      if numero_cep == "":
        enviar_mensagem(chat_id, "Você esqueceu de digitar o CEP! Tente assim: /cep 01001000")
      else:
        resultado = buscar_cep_real(numero_cep)
        enviar_mensagem(chat_id, resultado)

    # 2. Consulta REAL de CNPJ
    elif text.startswith("/cnpj"):
      numero_cnpj = text.replace("/cnpj", "").strip()
      if numero_cnpj == "":
        enviar_mensagem(chat_id, "Você esqueceu de digitar o CNPJ! Tente assim: /cnpj 00000000000191")
      else:
        resultado = buscar_cnpj_real(numero_cnpj)
        enviar_mensagem(chat_id, resultado)

    # 3. Consulta SIMULADA de CPF
    elif text.startswith("/cpf"):
      numero_cpf = text.replace("/cpf", "").strip()
      if len(numero_cpf) == 11 and numero_cpf.isdigit():
        mensagem = "🔎 *Resultado da Consulta (SIMULAÇÃO)*\n\n"
        mensagem += f"CPF Consultado: {numero_cpf[:3]}.***.***-{numero_cpf[-2:]}\n"
        mensagem += "Nome: Fulano de Tal Silva (Dado Fictício)\n"
        mensagem += "Nascimento: 01/01/1990\n"
        mensagem += "Situação na Receita: REGULAR"
        enviar_mensagem(chat_id, mensagem)
      else:
        enviar_mensagem(chat_id, "❌ Formato incorreto. Digite apenas os 11 números. Exemplo: /cpf 12345678900")

    # Comando /sobre
    elif text == "/sobre":
      enviar_mensagem(chat_id, "ℹ️ Bot de consultas em Python criado pelo Caio.")

    # Resposta padrão para erros
    else:
      enviar_mensagem(chat_id, "Não entendi o comando. Digite /start para ver as opções.")

  return "OK", 200


def enviar_mensagem(chat_id, texto):
  url = f"{TELEGRAM_API}/sendMessage"
  payload = {"chat_id": chat_id, "text": texto}
  requests.post(url, json=payload)


def buscar_cep_real(cep):
  cep = cep.replace("-", "").replace(".", "").replace(" ", "")
  if len(cep) != 8 or not cep.isdigit():
    return "❌ CEP inválido. Por favor, digite apenas os 8 números."
  
  try:
    link = f"https://viacep.com.br/ws/{cep}/json/"
    resposta = requests.get(link)
    dados = resposta.json()
    
    if "erro" in dados:
      return "❌ CEP não encontrado."
    
    mensagem = "📍 *Resultado do CEP:*\n\n"
    mensagem += f"Rua: {dados.get('logradouro')}\n"
    mensagem += f"Bairro: {dados.get('bairro')}\n"
    mensagem += f"Cidade: {dados.get('localidade')} - {dados.get('uf')}"
    return mensagem
  except Exception:
    return "❌ Erro ao buscar o CEP."


def buscar_cnpj_real(cnpj):
  cnpj = cnpj.replace(".", "").replace("-", "").replace("/", "").replace(" ", "")
  if len(cnpj) != 14 or not cnpj.isdigit():
    return "❌ CNPJ inválido. Digite apenas os 14 números."
  
  try:
    link = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
    resposta = requests.get(link)
    
    if resposta.status_code != 200:
        return "❌ CNPJ não encontrado ou erro na Receita Federal."
        
    dados = resposta.json()
    
    mensagem = "🏢 *Resultado do CNPJ:*\n\n"
    mensagem += f"Empresa: {dados.get('razao_social')}\n"
    nome_fantasia = dados.get('nome_fantasia')
    if nome_fantasia:
      mensagem += f"Fantasia: {nome_fantasia}\n"
    mensagem += f"Situação: {dados.get('descricao_situacao_cadastral')}\n"
    mensagem += f"Abertura: {dados.get('data_inicio_atividade')}\n"
    mensagem += f"Cidade: {dados.get('municipio')} - {dados.get('uf')}"
    return mensagem
  except Exception:
    return "❌ Erro ao buscar o CNPJ."


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
