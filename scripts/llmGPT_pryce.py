import os
import tiktoken

# Caminho para o diretório com seus arquivos .java
CAMINHO_REPOSITORIO = "C:\\Users\\GUILHERME\\PycharmProjects\\code-smells-analysis\\data\\repositories\\TheAlgorithms_Java"

# Preço por 1000 tokens para cada modelo
PRECOS = {
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
}

# Escolha seu modelo
MODELO = "gpt-3.5-turbo"  # ou "gpt-4o", "gpt-4-turbo"

def contar_tokens(texto, tokenizer):
    return len(tokenizer.encode(texto))

def estimar_custo(tokens_input, tokens_output, modelo):
    preco = PRECOS[modelo]
    custo_input = (tokens_input / 1000) * preco["input"]
    custo_output = (tokens_output / 1000) * preco["output"]
    return custo_input + custo_output

def main():
    # Inicializa o tokenizador
    tokenizer = tiktoken.encoding_for_model(MODELO)

    total_tokens_input = 0

    print(f"Procurando arquivos .java em: {CAMINHO_REPOSITORIO}")
    for root, _, files in os.walk(CAMINHO_REPOSITORIO):
        for file in files:
            if file.endswith(".java"):
                caminho_arquivo = os.path.join(root, file)
                try:
                    with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as f:
                        conteudo = f.read()
                        tokens = contar_tokens(conteudo, tokenizer)
                        total_tokens_input += tokens
                        print(f"{file}: {tokens} tokens")
                except Exception as e:
                    print(f"Erro ao ler {file}: {e}")

    # Suposição: a saída da IA é 25% do total de tokens de entrada
    total_tokens_output = int(total_tokens_input * 0.25)

    # Cálculo do custo
    custo_total = estimar_custo(total_tokens_input, total_tokens_output, MODELO)

    print(f"\nTotal de tokens (entrada): {total_tokens_input}")
    print(f"Tokens estimados de saída: {total_tokens_output}")
    print(f"Custo estimado usando {MODELO}: U${custo_total:.4f}")

if __name__ == "__main__":
    main()
