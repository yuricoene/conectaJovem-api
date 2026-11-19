import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date

# a chave vem do segredo; se ele não existir, o programa pede a chave
CHAVE = (os.environ.get("AI_GATEWAY_API_KEY")
         or getpass.getpass("Cole sua chave e tecle Enter (ela não aparece na tela): ")).strip()
URL = "https://api.cloudflare.com/client/v4/accounts/47344dfa13212db01ed347b310738dae/ai/v1/chat/completions"
MODELO = "@cf/mistralai/mistral-small-3.1-24b-instruct"

ERROS = {
    401: "Chave inválida ou expirada. Confira o segredo AI_GATEWAY_API_KEY.",
    429: "Muitos pedidos ou limite do dia atingido. Espere um pouco e tente de novo.",
}


# 1. As ferramentas são funções Python comuns
def calcular_media(notas):
    return round(sum(notas) / len(notas), 2)


def dias_ate(data):
    alvo = date.fromisoformat(data)      # data no formato AAAA-MM-DD
    return (alvo - date.today()).days


FUNCOES = {"calcular_media": calcular_media, "dias_ate": dias_ate}

# 2. A descrição das ferramentas, para o modelo saber o que existe
FERRAMENTAS = [
    {"type": "function", "function": {
        "name": "calcular_media",
        "description": "Calcula a média de uma lista de notas.",
        "parameters": {"type": "object",
                       "properties": {"notas": {"type": "array",
                                                "items": {"type": "number"}}},
                       "required": ["notas"]}}},
    {"type": "function", "function": {
        "name": "dias_ate",
        "description": "Conta quantos dias faltam até uma data (AAAA-MM-DD).",
        "parameters": {"type": "object",
                       "properties": {"data": {"type": "string"}},
                       "required": ["data"]}}},
]


def chamar(mensagens):
    pedido = urllib.request.Request(
        URL,
        data=json.dumps({"model": MODELO, "messages": mensagens,
                         "tools": FERRAMENTAS}).encode(),
        headers={"Authorization": f"Bearer {CHAVE}",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(pedido, timeout=60) as resposta:
            return json.load(resposta)["choices"][0]["message"]
    except urllib.error.HTTPError as erro:
        sys.exit(ERROS.get(erro.code, f"Erro {erro.code}: {erro.read().decode()[:300]}"))
    except OSError as erro:
        sys.exit(f"Não consegui falar com a IA. Confira a internet. ({erro})")


mensagens = [
    {"role": "system", "content": f"Você é um assistente escolar. Hoje é "
     f"{date.today()}. Use as ferramentas para fazer contas e contar dias."},
    {"role": "user", "content": input("Peça algo ao agente: ")},
]

# 3. O ciclo do agente: pensar, usar ferramenta, observar (no máximo 5 voltas)
for rodada in range(5):
    mensagem = chamar(mensagens)
    mensagens.append(mensagem)

    if not mensagem.get("tool_calls"):           # sem pedido de ferramenta:
        print("\nAgente:", mensagem["content"])  # é a resposta final
        break

    for chamada in mensagem["tool_calls"]:       # executa cada ferramenta pedida
        nome = chamada["function"]["name"]
        argumentos = json.loads(chamada["function"]["arguments"])
        resultado = FUNCOES[nome](**argumentos)
        print(f"[ferramenta] {nome}({argumentos}) = {resultado}")
        mensagens.append({"role": "tool", "tool_call_id": chamada["id"],
                          "content": json.dumps(resultado)})
