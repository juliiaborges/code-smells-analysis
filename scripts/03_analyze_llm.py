import os
import json
import glob
import time
import openai
from openai import OpenAI
import pandas as pd

# Configurações
BUILD_RESULTS_FILE = "../data/build_logs/build_results.json"
REPOS_DIR = "../data/repositories"
RESULTS_DIR = "../data/results/llm"
OPENAI_API_KEY = "SUA_CHAVE_API_OPENAI_AQUI"  # Substitua pela sua chave API OpenAI

# Certifique-se de que o diretório de resultados existe
os.makedirs(RESULTS_DIR, exist_ok=True)

# Configure a API da OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def read_java_file(file_path):
    """Lê um arquivo Java e retorna seu conteúdo."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e:
            print(f"Erro ao ler arquivo {file_path}: {e}")
            return ""

def analyze_with_zero_shot(code):
    """Analisa o código com um prompt zero-shot."""
    prompt = f"""Analise o seguinte código Java e identifique todos os code smells. 
Liste cada code smell encontrado com o nome, a linha onde ocorre e uma breve descrição do problema.
Classifique os code smells usando categorias padrão como Bloaters, Object-Orientation Abusers, 
Change Preventers, Dispensables, Couplers, etc.

Código:
```java
{code}
```
Forneça sua análise no formato JSON:
{{
"smells": [
    {{
        "name": "Nome do Code Smell",
        "category": "Categoria do Code Smell",
        "line": "Número da linha",
        "description": "Breve descrição do problema"
    }}
]
}}"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro na API da OpenAI: {e}")
        time.sleep(5)  # Esperar antes de tentar novamente
        return '{"smells": []}'

def analyze_with_one_shot(code):
    """Analisa o código com um prompt one-shot."""
    example = """{
"smells": [
    {
        "name": "Long Method",
        "category": "Bloaters",
        "line": "10-45",
        "description": "O método processData é muito longo com 35 linhas, tornando-o difícil de entender e manter"
    },
    {
        "name": "Data Class",
        "category": "Object-Orientation Abusers",
        "line": "50-60",
        "description": "A classe UserData contém apenas campos e getters/setters sem lógica de negócios"
    },
    {
        "name": "Feature Envy",
        "category": "Couplers",
        "line": "70",
        "description": "O método usa mais atributos de outras classes do que da própria classe"
    }
]
}"""
    prompt = f"""Analise o seguinte código Java e identifique todos os code smells.
Liste cada code smell encontrado com o nome, a linha onde ocorre e uma breve descrição do problema.
Classifique os code smells usando categorias padrão como Bloaters, Object-Orientation Abusers,
Change Preventers, Dispensables, Couplers, etc.
Aqui está um exemplo de como deve ser sua análise:
{example}

Código:
```java
{code}
```
Forneça sua análise no formato JSON:
{{
"smells": [
    {{
        "name": "Nome do Code Smell",
        "category": "Categoria do Code Smell",
        "line": "Número da linha",
        "description": "Breve descrição do problema"
    }}
]
}}"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro na API da OpenAI: {e}")
        time.sleep(5)  # Esperar antes de tentar novamente
        return '{"smells": []}'

def analyze_with_calibrated_prompt(code):
    """Analisa o código com um prompt calibrado baseado nas regras do SonarQube."""
    prompt = f"""Analise o seguinte código Java e identifique todos os code smells usando regras semelhantes às do SonarQube.
Foque especialmente em:

Complexidade ciclomática alta (métodos com muitos caminhos de decisão)
Métodos muito longos (> 25 linhas)
Classes muito grandes (> 500 linhas)
Duplicação de código
Nomes de variáveis ou métodos não descritivos
Comentários excessivos ou insuficientes
Muitos parâmetros em métodos (> 5)
Código morto ou não utilizado
Excesso de acoplamento entre classes
Falta de coesão em classes

Código:
```java
{code}
```
Forneça sua análise no formato JSON:
{{
"smells": [
    {{
        "name": "Nome do Code Smell (conforme regras do SonarQube)",
        "sonar_rule_id": "Possível ID da regra no SonarQube (se souber)",
        "line": "Número da linha",
        "description": "Breve descrição do problema"
    }}
]
}}"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro na API da OpenAI: {e}")
        time.sleep(5)  # Esperar antes de tentar novamente
        return '{"smells": []}'

def process_repository(repo_owner, repo_name):
    """Processa um repositório compilado."""
    repo_path = os.path.join(REPOS_DIR, f"{repo_owner}_{repo_name}")
    full_repo_name = f"{repo_owner}_{repo_name}"
    results = {
        "repository": full_repo_name,
        "zero_shot": {},
        "one_shot": {},
        "calibrated": {}
    }

    # Encontrar arquivos Java no diretório src/main
    src_main_path = os.path.join(repo_path, "src", "main", "java")
    if not os.path.exists(src_main_path):
        print(f"Diretório src/main/java não encontrado em {repo_path}")
        # Tentar encontrar arquivos Java em qualquer lugar do repositório
        java_files = glob.glob(f"{repo_path}/**/*.java", recursive=True)
    else:
        java_files = glob.glob(f"{src_main_path}/**/*.java", recursive=True)

    # Limitar a 10 arquivos para evitar custos excessivos com a API
    java_files = java_files[:10]

    print(f"Analisando {len(java_files)} arquivos Java em {full_repo_name}...")

    for file_path in java_files:
        # Obter caminho relativo para melhor legibilidade
        rel_path = os.path.relpath(file_path, repo_path)
        print(f"Analisando arquivo: {rel_path}")
        
        # Ler o código do arquivo
        code = read_java_file(file_path)
        if not code:
            continue
        
        # Executar análises com os três tipos de prompts
        print("  Executando análise Zero-Shot...")
        zero_shot_result = analyze_with_zero_shot(code)
        
        print("  Executando análise One-Shot...")
        one_shot_result = analyze_with_one_shot(code)
        
        print("  Executando análise com Prompt Calibrado...")
        calibrated_result = analyze_with_calibrated_prompt(code)
        
        # Armazenar resultados
        results["zero_shot"][rel_path] = zero_shot_result
        results["one_shot"][rel_path] = one_shot_result
        results["calibrated"][rel_path] = calibrated_result
        
        # Esperar um pouco para evitar limites de taxa na API
        time.sleep(2)

    # Salvar resultados
    output_file = os.path.join(RESULTS_DIR, f"{full_repo_name}_llm_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Resultados salvos em {output_file}")

def main():
    # Carregar informações dos repositórios compilados com sucesso
    if not os.path.exists(BUILD_RESULTS_FILE):
        print(f"Arquivo {BUILD_RESULTS_FILE} não encontrado. Execute o script de compilação primeiro.")
        return
    
    with open(BUILD_RESULTS_FILE, 'r') as f:
        build_results = json.load(f)

    # Filtrar repositórios compilados com sucesso
    successful_repos = [repo for repo in build_results if repo["success"]]

    if not successful_repos:
        print("Nenhum repositório foi compilado com sucesso. Verifique os logs de compilação.")
        return

    print(f"Analisando {len(successful_repos)} repositórios compilados com sucesso...")

    # Processar cada repositório
    for repo in successful_repos:
        repo_owner = repo["owner"]
        repo_name = repo["name"]
        
        process_repository(repo_owner, repo_name)

if __name__ == "__main__":
    main()