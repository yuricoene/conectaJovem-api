import getpass
import json
import os
import sys
import urllib.error
import urllib.request

# a chave vem do segredo; se ele não existir, o programa pede a chave
CHAVE = (os.environ.get("AI_GATEWAY_API_KEY")
         or getpass.getpass("Cole sua chave e tecle Enter (ela não aparece na tela): ")).strip()
URL = "https://api.cloudflare.com/client/v4/accounts/47344dfa13212db01ed347b310738dae/ai/v1/chat/completions"

INSTRUCAO = """Você é um assistente de estudos.
Leia o texto do usuário e responda SOMENTE com um JSON neste formato:
{"resumo": "resumo em até 2 frases",
 "palavras_chave": ["palavra1", "palavra2", "palavra3"],
 "nivel": "básico, intermediário ou avançado"}"""

ERROS = {
    401: "Chave inválida ou expirada. Confira o segredo AI_GATEWAY_API_KEY.",
    402: "O limite de gasto da sua chave acabou. Fale com o professor.",
    429: "Muitos pedidos ou limite do dia atingido. Espere um pouco e tente de novo.",
}

texto = input("Cole um texto de estudo: ")

pedido = urllib.request.Request(
    URL,
    data=json.dumps({
        "model": "@cf/mistralai/mistral-small-3.1-24b-instruct",
        "messages": [
            {"role": "system", "content": INSTRUCAO},
            {"role": "user", "content": texto},
        ],
        "temperature": 0.2,
    }).encode(),
    headers={
        "Authorization": f"Bearer {CHAVE}",
        "Content-Type": "application/json",
    },
)
try:
    with urllib.request.urlopen(pedido, timeout=60) as resposta:
        conteudo = json.load(resposta)["choices"][0]["message"]["content"]
except urllib.error.HTTPError as erro:
    sys.exit(ERROS.get(erro.code, f"Erro {erro.code}: {erro.read().decode()[:300]}"))
except OSError as erro:
    sys.exit(f"Não consegui falar com a IA. Confira a internet. ({erro})")

conteudo = conteudo.replace("```json", "").replace("```", "").strip()

try:
    dados = json.loads(conteudo)          # texto JSON vira dicionário Python
except ValueError:
    sys.exit("A IA não respondeu em JSON. Tente de novo. Resposta recebida:\n" + conteudo)
print("Resumo:", dados["resumo"])
print("Palavras-chave:", ", ".join(dados["palavras_chave"]))
print("Nível:", dados["nivel"])
