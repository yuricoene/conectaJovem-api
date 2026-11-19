import getpass
import json
import os
import urllib.error
import urllib.request

# a chave vem do segredo; se ele não existir, o programa pede a chave
CHAVE = (os.environ.get("AI_GATEWAY_API_KEY")
         or getpass.getpass("Cole sua chave e tecle Enter (ela não aparece na tela): ")).strip()
URL = "https://api.cloudflare.com/client/v4/accounts/47344dfa13212db01ed347b310738dae/ai/v1/chat/completions"
MODELO = "@cf/mistralai/mistral-small-3.1-24b-instruct"

ERROS = {
    401: "Chave inválida ou expirada. Confira o segredo AI_GATEWAY_API_KEY.",
    402: "O limite de gasto da sua chave acabou. Fale com o professor.",
    429: "Muitos pedidos ou limite do dia atingido. Espere um pouco e tente de novo.",
}


def perguntar(sistema, pergunta, temperatura):
    pedido = urllib.request.Request(
        URL,
        data=json.dumps({
            "model": MODELO,
            "temperature": temperatura,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": pergunta},
            ],
        }).encode(),
        headers={
            "Authorization": f"Bearer {CHAVE}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(pedido, timeout=60) as resposta:
            dados = json.load(resposta)
    except urllib.error.HTTPError as erro:
        return ERROS.get(erro.code, f"Erro {erro.code}: {erro.read().decode()[:300]}")
    except OSError as erro:
        return f"Não consegui falar com a IA. Confira a internet. ({erro})"
    return dados["choices"][0]["message"]["content"]


print("=== Meu playground de IA ===")
sistema = input("Instrução de sistema (quem a IA deve ser): ")
try:
    temperatura = float(input("Temperatura (de 0 a 1): ").replace(",", "."))
except ValueError:
    temperatura = 0.7

while True:
    pergunta = input("\nVocê (ou 'sair'): ")
    if pergunta.strip().lower() == "sair":
        break
    print("IA:", perguntar(sistema, pergunta, temperatura))
