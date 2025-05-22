import os
import json
import tiktoken
import time
from openai import OpenAI

client = OpenAI(api_key="COLOCA_O_TOKEN_ARROMBADO")

REPO_NAME = "TheAlgorithms_Java"
REPO_PATH = "C:\\Users\\GUILHERME\\PycharmProjects\\code-smells-analysis\\data\\repositories\\TheAlgorithms_Java"
TIPOS_CODE_SMELLS = [
    "God Class", "Long Method", "Feature Envy", "Data Class", "Duplicated Code",
    "Primitive Obsession", "Long Parameter List", "Shotgun Surgery", "Speculative Generality"
]

MODEL = "gpt-3.5-turbo"
MAX_TOKENS_POR_CHAMADA = 12000
tokenizer = tiktoken.encoding_for_model(MODEL)

def contar_tokens(texto):
    return len(tokenizer.encode(texto))

def carregar_arquivos_java(caminho):
    arquivos = []
    for root, _, files in os.walk(caminho):
        for file in files:
            if file.endswith(".java"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    arquivos.append(f.read())
    return arquivos

def construir_prompt(codigo):
    return f"""
Você é um especialista em detectar code smells em código Java. Analise o código abaixo e conte quantos code smells de cada tipo você encontra. Tipos a considerar: God Class, Long Method, Feature Envy, Data Class, Duplicated Code, Primitive Obsession, Long Parameter List, Shotgun Surgery, Speculative Generality.

Retorne APENAS um JSON no formato:

{{
  "repository": "{REPO_NAME}",
  "code_smells": {{
    "God Class": 0,
    "Long Method": 0,
    "Feature Envy": 0,
    "Data Class": 0,
    "Duplicated Code": 0,
    "Primitive Obsession": 0,
    "Long Parameter List": 0,
    "Shotgun Surgery": 0,
    "Speculative Generality": 0
  }},
  "total_smells": 0
}}

Código:
{codigo}
"""

def agrupar_por_token_limite(arquivos, limite_tokens):
    lotes = []
    lote_atual = []
    tokens_atual = 0

    for arquivo in arquivos:
        tokens = contar_tokens(arquivo)
        if tokens > limite_tokens:
            continue

        if tokens_atual + tokens > limite_tokens:
            lotes.append(lote_atual)
            lote_atual = [arquivo]
            tokens_atual = tokens
        else:
            lote_atual.append(arquivo)
            tokens_atual += tokens

    if lote_atual:
        lotes.append(lote_atual)
    return lotes

def analisar_code_smells(arquivos_java):
    lotes = agrupar_por_token_limite(arquivos_java, MAX_TOKENS_POR_CHAMADA)
    resultado_total = {smell: 0 for smell in TIPOS_CODE_SMELLS}
    total_geral = 0

    for i, lote in enumerate(lotes):
        print(f"Analisando lote {i+1} com {len(lote)} arquivos...")

        codigo = "\n\n".join(lote)
        prompt = construir_prompt(codigo)

        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            resposta = json.loads(response.choices[0].message.content)
            smells_lote = resposta["code_smells"]

            for smell, qtd in smells_lote.items():
                resultado_total[smell] += qtd

            total_geral += resposta["total_smells"]

        except Exception as e:
            print(f"Erro no lote {i+1}: {e}")
            continue

        time.sleep(1.5)

    return {
        "repository": REPO_NAME,
        "code_smells": resultado_total,
        "total_smells": total_geral
    }

if __name__ == "__main__":
    print(f"Procurando arquivos .java em: {REPO_PATH}")
    arquivos_java = carregar_arquivos_java(REPO_PATH)
    print(f"{len(arquivos_java)} arquivos Java encontrados.")

    if arquivos_java:
        resultado = analisar_code_smells(arquivos_java)
        print("\n--- Resultado da análise ---\n")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))

        # Salvando o resultado em arquivo JSON
        output_dir = "C:\\Users\\GUILHERME\\PycharmProjects\\code-smells-analysis\\data\\llm_results"
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f"{REPO_NAME}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)

        print(f"\nResultado salvo em: {output_path}")
    else:
        print("Nenhum arquivo Java encontrado.")
