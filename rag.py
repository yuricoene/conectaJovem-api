import getpass
import json
import math
import os
import sys
import urllib.error
import urllib.request

# a chave vem do segredo; se ele não existir, o programa pede a chave
CHAVE = (os.environ.get("AI_GATEWAY_API_KEY")
         or getpass.getpass("Cole sua chave e tecle Enter (ela não aparece na tela): ")).strip()
BASE = "https://api.cloudflare.com/client/v4/accounts/47344dfa13212db01ed347b310738dae/ai/v1"
CABECALHOS = {"Authorization": f"Bearer {CHAVE}", "Content-Type": "application/json"}

ERROS = {
    401: "Chave inválida ou expirada. Confira o segredo AI_GATEWAY_API_KEY.",
    402: "O limite de gasto da sua chave acabou. Fale com o professor.",
    429: "Muitos pedidos ou limite do dia atingido. Espere um pouco e tente de novo.",
}

# A "base de conhecimento": trechos baseados no edital do Conecta Jovem
DOCUMENTOS = [
    "A bolsa auxílio do Conecta Jovem é de R$ 500,00 por mês durante o curso.",
    "O aluno perde a bolsa se tiver 3 faltas sem justificativa, seguidas ou não.",
    "As aulas são presenciais, das 7h30 às 11h30, no Yumit Hub e na UFMT.",
    "Há vale-transporte (se necessário), auxílio alimentação e material gratuito.",
    "O programa atende jovens de 15 a 24 anos que moram na Baixada Cuiabana.",
    "No Projeto Integrador, cada aluno apresenta um MVP hospedado na nuvem.",
]


def chamar(caminho, corpo):
    pedido = urllib.request.Request(
        BASE + caminho, data=json.dumps(corpo).encode(), headers=CABECALHOS)
    try:
        with urllib.request.urlopen(pedido, timeout=60) as resposta:
            return json.load(resposta)
    except urllib.error.HTTPError as erro:
        sys.exit(ERROS.get(erro.code, f"Erro {erro.code}: {erro.read().decode()[:300]}"))
    except OSError as erro:
        sys.exit(f"Não consegui falar com a IA. Confira a internet. ({erro})")


def embeddings(textos):
    dados = chamar("/embeddings", {
        "model": "@cf/baai/bge-m3",
        "input": textos,
    })
    return [item["embedding"] for item in dados["data"]]


def similaridade(a, b):
    produto = sum(x * y for x, y in zip(a, b))
    tamanho_a = math.sqrt(sum(x * x for x in a))
    tamanho_b = math.sqrt(sum(y * y for y in b))
    return produto / (tamanho_a * tamanho_b)


vetores = embeddings(DOCUMENTOS)                 # 1. documentos viram vetores
pergunta = input("Pergunte sobre o Conecta Jovem: ")
v_pergunta = embeddings([pergunta])[0]           # 2. a pergunta vira vetor

# 3. ordena os documentos do mais parecido para o menos parecido
ranking = sorted(zip(DOCUMENTOS, vetores),
                 key=lambda par: similaridade(v_pergunta, par[1]),
                 reverse=True)
trechos = [texto for texto, _ in ranking[:2]]   # fica com os 2 melhores

# 4. monta o prompt com os trechos e pergunta ao modelo
contexto = "\n".join(f"- {t}" for t in trechos)
dados = chamar("/chat/completions", {
    "model": "@cf/mistralai/mistral-small-3.1-24b-instruct",
    "messages": [
        {"role": "system", "content":
            "Responda usando SOMENTE as informações fornecidas. Se a resposta "
            "não estiver nelas, diga: 'Não encontrei essa informação.'"},
        {"role": "user", "content": f"Informações:\n{contexto}\n\nPergunta: {pergunta}"},
    ],
    "temperature": 0.2,
})

print("\nResposta:", dados["choices"][0]["message"]["content"])
print("\nTrechos consultados:")
for t in trechos:
    print(" -", t)
