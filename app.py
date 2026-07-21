import os
import requests
import re
from flask import Flask, request

app = Flask(__name__)

# Token atualizado conforme solicitado
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
                chat_id, 
                "Olá! Escolha uma consulta:\n\n"
                "/cep [número] - Consulta de Endereço\n"
                "/cnpj [número] - Consulta de Empresa\n"
                "/cpf [número] - Validação e Status (Algorítmico)\n"
                "/tel [número] - Info de Linha (DDD/Região)"
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

        # 3. Validação REAL de CPF (Algorítmica)
        elif text.startswith("/cpf"):
            numero_cpf = text.replace("/cpf", "").strip()
            # Remove formatação
            numero_cpf = re.sub(r'[^0-9]', '', numero_cpf)
            
            if len(numero_cpf) != 11 or not numero_cpf.isdigit():
                enviar_mensagem(chat_id, "❌ Formato incorreto. Digite os 11 números. Ex: /cpf 12345678900")
            else:
                if validar_cpf_algoritmo(numero_cpf):
                    # Nota: Não é possível obter nome/dados reais sem API paga/ilegal.
                    # Aqui retornamos a validade matemática e uma máscara segura.
                    mensagem = "✅ *CPF Válido (Matematicamente)*\n\n"
                    mensagem += f"CPF: {formatar_cpf(numero_cpf)}\n"
                    mensagem += "_Nota: Dados cadastrais (Nome/Endereço) são protegidos pela LGPD e não acessíveis via API pública._"
                else:
                    mensagem = "❌ *CPF Inválido*\n\n"
                    mensagem += f"CPF: {formatar_cpf(numero_cpf)}\n"
                    mensagem += "Os dígitos verificadores não conferem."
                
                enviar_mensagem(chat_id, mensagem)

        # 4. Consulta de Telefone (DDD/Região)
        elif text.startswith("/tel"):
            numero_tel = text.replace("/tel", "").strip()
            numero_tel = re.sub(r'[^0-9]', '', numero_tel)
            
            # Remove DDI se houver (ex: 5511999999999 -> 11999999999)
            if numero_tel.startswith("55") and len(numero_tel) > 10:
                numero_tel = numero_tel[2:]
            
            if len(numero_tel) < 10 or len(numero_tel) > 11 or not numero_tel.isdigit():
                enviar_mensagem(chat_id, "❌ Formato inválido. Use DDD + Número. Ex: /tel 11999998888")
            else:
                resultado = buscar_info_telefone(numero_tel)
                enviar_mensagem(chat_id, resultado)

        # Comando /sobre
        elif text == "/sobre":
            enviar_mensagem(chat_id, "ℹ️ Bot de consultas técnicas. Criado com foco em privacidade e dados públicos.")

        # Resposta padrão
        else:
            enviar_mensagem(chat_id, "Não entendi. Digite /start para ver as opções.")

    return "OK", 200


def enviar_mensagem(chat_id, texto):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": texto,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")


def buscar_cep_real(cep):
    cep = re.sub(r'[^0-9]', '', cep)
    if len(cep) != 8:
        return "❌ CEP inválido. 8 dígitos."
  
    try:
        link = f"https://viacep.com.br/ws/{cep}/json/"
        resposta = requests.get(link, timeout=5)
        dados = resposta.json()
        
        if "erro" in dados:
            return "❌ CEP não encontrado."
        
        mensagem = "📍 *Endereço:*\n\n"
        mensagem += f"*Rua:* {dados.get('logradouro')}\n"
        mensagem += f"*Bairro:* {dados.get('bairro')}\n"
        mensagem += f"*Cidade:* {dados.get('localidade')} - {dados.get('uf')}\n"
        mensagem += f"*IBGE:* {dados.get('ibge')}"
        return mensagem
    except Exception:
        return "❌ Erro ao buscar o CEP."


def buscar_cnpj_real(cnpj):
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj) != 14:
        return "❌ CNPJ inválido. 14 dígitos."
  
    try:
        link = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
        resposta = requests.get(link, timeout=5)
        
        if resposta.status_code != 200:
            return "❌ CNPJ não encontrado ou erro na API."
            
        dados = resposta.json()
        
        mensagem = "🏢 *Empresa:*\n\n"
        mensagem += f"*Razão Social:* {dados.get('razao_social')}\n"
        nome_fantasia = dados.get('nome_fantasia')
        if nome_fantasia:
            mensagem += f"*Fantasia:* {nome_fantasia}\n"
        mensagem += f"*Situação:* {dados.get('descricao_situacao_cadastral')}\n"
        mensagem += f"*Abertura:* {dados.get('data_inicio_atividade')}\n"
        mensagem += f"*Cidade:* {dados.get('municipio')} - {dados.get('uf')}"
        return mensagem
    except Exception:
        return "❌ Erro ao buscar o CNPJ."


def validar_cpf_algoritmo(cpf):
    """Valida CPF usando o algoritmo oficial dos dígitos verificadores."""
    if cpf == cpf[::-1]: # Evita CPFs repetidos como 111.111.111-11
        return False
        
    def calcular_digito(cpf_parcial):
        soma = 0
        peso = len(cpf_parcial) + 1
        for i in range(len(cpf_parcial)):
            soma += int(cpf_parcial[i]) * peso
            peso -= 1
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    # Primeiro dígito
    d1 = calcular_digito(cpf[:9])
    if int(cpf[9]) != d1:
        return False
    
    # Segundo dígito
    d2 = calcular_digito(cpf[:10])
    if int(cpf[10]) != d2:
        return False
        
    return True


def formatar_cpf(cpf):
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def buscar_info_telefone(telefone):
    """
    Consulta informações públicas baseadas no DDD (ANATEL).
    Não retorna nome do titular (dados privados).
    """
    ddd = telefone[:2]
    numero = telefone[2:]
    
    # Mapeamento simples de DDD para Estado (Base ANATEL)
    ddd_map = {
        "11": "São Paulo (SP)", "12": "São José dos Campos (SP)", "13": "Santos (SP)",
        "14": "Bauru (SP)", "15": "Sorocaba (SP)", "16": "Ribeirão Preto (SP)",
        "17": "São José do Rio Preto (SP)", "18": "Pres. Prudente (SP)", "19": "Campinas (SP)",
        "21": "Rio de Janeiro (RJ)", "22": "Campos dos Goytacazes (RJ)", "24": "Petrópolis (RJ)",
        "27": "Vitória (ES)", "28": "Cachoeiro de Itapemirim (ES)",
        "31": "Belo Horizonte (MG)", "32": "Juiz de Fora (MG)", "33": "Divinópolis (MG)",
        "34": "Uberlândia (MG)", "35": "Poços de Caldas (MG)", "37": "Muriaé (MG)",
        "38": "Montes Claros (MG)",
        "41": "Curitiba (PR)", "42": "Ponta Grossa (PR)", "43": "Londrina (PR)",
        "44": "Maringá (PR)", "45": "Foz do Iguaçu (PR)", "46": "Francisco Beltrão (PR)",
        "47": "Joinville (SC)", "48": "Florianópolis (SC)", "49": "Chapecó (SC)",
        "51": "Porto Alegre (RS)", "53": "Pelotas (RS)", "54": "Caxias do Sul (RS)",
        "55": "Santa Maria (RS)",
        "61": "Brasília (DF)", "62": "Goiânia (GO)", "63": "Palmas (TO)",
        "64": "Rio Verde (GO)", "65": "Cuiabá (MT)", "66": "Rondonópolis (MT)",
        "67": "Campo Grande (MS)", "68": "Rio Branco (AC)", "69": "Porto Velho (RO)",
        "71": "Salvador (BA)", "73": "Ilhéus (BA)", "74": "Juazeiro (BA)",
        "75": "Alagoinhas (BA)", "77": "Vitória da Conquista (BA)", "79": "Aracaju (SE)",
        "81": "Recife (PE)", "82": "Maceió (AL)", "83": "João Pessoa (PB)",
        "84": "Natal (RN)", "85": "Fortaleza (CE)", "86": "Teresina (PI)",
        "87": "Petrolina (PE)", "88": "Juazeiro do Norte (CE)", "89": "Picos (PI)",
        "91": "Belém (PA)", "92": "Manaus (AM)", "93": "Santarém (PA)",
        "94": "Marabá (PA)", "95": "Boa Vista (RR)", "96": "Macapá (AP)",
        "97": "Coari (AM)", "98": "São Luís (MA)", "99": "Imperatriz (MA)"
    }
    
    localizacao = ddd_map.get(ddd, "Região não identificada ou DDD inexistente")
    
    # Identifica se é celular (8 ou 9 dígitos após DDD) ou fixo
    tipo = "Celular" if len(numero) == 9 else "Fixo" if len(numero) == 8 else "Inválido"
    
    mensagem = "📱 *Info da Linha:*\n\n"
    mensagem += f"*Número:* ({ddd}) {numero}\n"
    mensagem += f"*Tipo:* {tipo}\n"
    mensagem += f"*Região (Anatel):* {localizacao}\n"
    mensagem += "_Nota: Dados do titular são privados e não acessíveis._"
    
    return mensagem


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
