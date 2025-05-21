import os
import json
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configurações
BUILD_RESULTS_FILE = "../data/build_logs/build_results.json"
RESULTS_DIR = "../data/results"
OUTPUT_DIR = "../data/analysis"

# Certifique-se de que o diretório de saída existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_llm_results(repo_owner, repo_name):
    """Carrega os resultados da análise com LLM."""
    file_path = os.path.join(RESULTS_DIR, "llm", f"{repo_owner}_{repo_name}_llm_results.json")
    
    if not os.path.exists(file_path):
        print(f"Resultados LLM para {repo_owner}_{repo_name} não encontrados.")
        return None
    
    with open(file_path, 'r') as f:
        return json.load(f)

def load_sonarqube_results(repo_owner, repo_name):
    """Carrega os resultados da análise com SonarQube."""
    file_path = os.path.join(RESULTS_DIR, "sonarqube", f"{repo_owner}_{repo_name}_sonar_results.json")
    
    if not os.path.exists(file_path):
        print(f"Resultados SonarQube para {repo_owner}_{repo_name} não encontrados.")
        return None
    
    with open(file_path, 'r') as f:
        return json.load(f)

def load_checkstyle_results(repo_owner, repo_name):
    """Carrega os resultados da análise com CheckStyle."""
    file_path = os.path.join(RESULTS_DIR, "checkstyle", f"{repo_owner}_{repo_name}_checkstyle_results.json")
    
    if not os.path.exists(file_path):
        print(f"Resultados CheckStyle para {repo_owner}_{repo_name} não encontrados.")
        return None
    
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_smells_from_llm(llm_results, prompt_type):
    """Extrai os code smells dos resultados do LLM."""
    smells = []
    
    for file_path, result_str in llm_results[prompt_type].items():
        try:
            # Tentar analisar o JSON
            result = json.loads(result_str)
            file_smells = result.get("smells", [])
            
            for smell in file_smells:
                smell["file"] = file_path
                smells.append(smell)
        except json.JSONDecodeError:
            print(f"Erro ao analisar JSON para {file_path} com prompt {prompt_type}")
    
    return smells

def extract_smells_from_sonarqube(sonar_results):
    """Extrai os code smells dos resultados do SonarQube."""
    smells = []
    
    # Verificar se temos a estrutura correta
    if "issues" in sonar_results:
        issues = sonar_results["issues"]
    else:
        issues = sonar_results
    
    for issue in issues:
        if issue.get("type") == "CODE_SMELL":
            # Extrair o caminho do arquivo da componente
            component = issue.get("component", "")
            file_path = component.split(":")[-1] if ":" in component else component
            
            smells.append({
                "name": issue.get("rule", ""),
                "file": file_path,
                "line": issue.get("line", ""),
                "description": issue.get("message", "")
            })
    
    return smells

def extract_smells_from_checkstyle(checkstyle_results):
    """Extrai os code smells dos resultados do CheckStyle."""
    smells = []
    
    for file_result in checkstyle_results:
        file_path = file_result.get("file", "")
        issues = file_result.get("issues", [])
        
        for issue in issues:
            smells.append({
                "name": issue.get("rule", ""),
                "file": file_path,
                "line": issue.get("line", ""),
                "description": issue.get("message", "")
            })
    
    return smells

def calculate_similarity(llm_smells, tool_smells):
    """Calcula a taxa de similaridade entre LLM e uma ferramenta."""
    if not llm_smells or not tool_smells:
        return 0
    
    # Conjunto de arquivos analisados
    llm_files = set(smell["file"] for smell in llm_smells)
    tool_files = set(smell["file"] for smell in tool_smells)
    common_files = llm_files.intersection(tool_files)
    
    if not common_files:
        return 0  # Não há arquivos em comum
    
    # Filtrar para incluir apenas arquivos comuns
    llm_filtered = [smell for smell in llm_smells if smell["file"] in common_files]
    tool_filtered = [smell for smell in tool_smells if smell["file"] in common_files]
    
    # Converte para conjuntos simplificados para comparação (arquivo + linha)
    llm_set = set((smell["file"], str(smell["line"])) for smell in llm_filtered)
    tool_set = set((smell["file"], str(smell["line"])) for smell in tool_filtered)
    
    # Calcular interseção
    intersection = llm_set.intersection(tool_set)
    union = llm_set.union(tool_set)
    
    if not union:
        return 0
    
    return len(intersection) / len(union) * 100

def calculate_divergence(llm_smells, tool_smells):
    """Calcula a taxa de divergência entre LLM e uma ferramenta."""
    if not llm_smells or not tool_smells:
        return 100
    
    # Conjunto de arquivos analisados
    llm_files = set(smell["file"] for smell in llm_smells)
    tool_files = set(smell["file"] for smell in tool_smells)
    common_files = llm_files.intersection(tool_files)
    
    if not common_files:
        return 100  # Divergência total
    
    # Filtrar para incluir apenas arquivos comuns
    llm_filtered = [smell for smell in llm_smells if smell["file"] in common_files]
    tool_filtered = [smell for smell in tool_smells if smell["file"] in common_files]
    
    # Converte para conjuntos simplificados para comparação (arquivo + linha)
    llm_set = set((smell["file"], str(smell["line"])) for smell in llm_filtered)
    tool_set = set((smell["file"], str(smell["line"])) for smell in tool_filtered)
    
    # Calcular diferença
    llm_only = llm_set - tool_set
    union = llm_set.union(tool_set)
    
    if not union:
        return 0
    
    return len(llm_only) / len(union) * 100

def analyze_repository(repo_owner, repo_name):
    """Analisa os resultados para um repositório."""
    print(f"Analisando resultados para {repo_owner}/{repo_name}...")
    
    # Carregar resultados
    llm_results = load_llm_results(repo_owner, repo_name)
    sonar_results = load_sonarqube_results(repo_owner, repo_name)
    checkstyle_results = load_checkstyle_results(repo_owner, repo_name)
    
    if not llm_results or (not sonar_results and not checkstyle_results):
        print(f"Resultados insuficientes para {repo_owner}/{repo_name}. Pulando análise.")
        return None
    
    # Extrair code smells
    zero_shot_smells = extract_smells_from_llm(llm_results, "zero_shot") if llm_results else []
    one_shot_smells = extract_smells_from_llm(llm_results, "one_shot") if llm_results else []
    calibrated_smells = extract_smells_from_llm(llm_results, "calibrated") if llm_results else []
    sonar_smells = extract_smells_from_sonarqube(sonar_results) if sonar_results else []
    checkstyle_smells = extract_smells_from_checkstyle(checkstyle_results) if checkstyle_results else []
    
    # Calcular métricas
    metrics = {
        "repository": f"{repo_owner}/{repo_name}",
        # Contagens
        "zero_shot_count": len(zero_shot_smells),
        "one_shot_count": len(one_shot_smells),
        "calibrated_count": len(calibrated_smells),
        "sonarqube_count": len(sonar_smells),
        "checkstyle_count": len(checkstyle_smells),
        
        # Diferenças
        "diff_zero_sonar": len(zero_shot_smells) - len(sonar_smells) if sonar_smells else None,
        "diff_one_sonar": len(one_shot_smells) - len(sonar_smells) if sonar_smells else None,
        "diff_calibrated_sonar": len(calibrated_smells) - len(sonar_smells) if sonar_smells else None,
        "diff_zero_checkstyle": len(zero_shot_smells) - len(checkstyle_smells) if checkstyle_smells else None,
        "diff_one_checkstyle": len(one_shot_smells) - len(checkstyle_smells) if checkstyle_smells else None,
        
        # Similaridades
        "similarity_zero_sonar": calculate_similarity(zero_shot_smells, sonar_smells) if sonar_smells else None,
        "similarity_one_sonar": calculate_similarity(one_shot_smells, sonar_smells) if sonar_smells else None,
        "similarity_calibrated_sonar": calculate_similarity(calibrated_smells, sonar_smells) if sonar_smells else None,
        "similarity_zero_checkstyle": calculate_similarity(zero_shot_smells, checkstyle_smells) if checkstyle_smells else None,
        "similarity_one_checkstyle": calculate_similarity(one_shot_smells, checkstyle_smells) if checkstyle_smells else None,
        
        # Divergências
        "divergence_zero_sonar": calculate_divergence(zero_shot_smells, sonar_smells) if sonar_smells else None,
        "divergence_one_sonar": calculate_divergence(one_shot_smells, sonar_smells) if sonar_smells else None,
        "divergence_calibrated_sonar": calculate_divergence(calibrated_smells, sonar_smells) if sonar_smells else None,
        "divergence_zero_checkstyle": calculate_divergence(zero_shot_smells, checkstyle_smells) if checkstyle_smells else None,
        "divergence_one_checkstyle": calculate_divergence(one_shot_smells, checkstyle_smells) if checkstyle_smells else None,
    }
    
    return metrics

def create_summary_charts(all_metrics):
    """Cria gráficos de resumo para os resultados."""
    # Converter dados para DataFrame
    df = pd.DataFrame(all_metrics)
    
    # Calcular médias para cada métrica
    avg_metrics = {
        "zero_shot_avg": df["zero_shot_count"].mean(),
        "one_shot_avg": df["one_shot_count"].mean(),
        "calibrated_avg": df["calibrated_count"].mean(),
        "sonarqube_avg": df["sonarqube_count"].dropna().mean() if not df["sonarqube_count"].dropna().empty else 0,
        "checkstyle_avg": df["checkstyle_count"].dropna().mean() if not df["checkstyle_count"].dropna().empty else 0,
        
        "similarity_zero_sonar_avg": df["similarity_zero_sonar"].dropna().mean() if not df["similarity_zero_sonar"].dropna().empty else 0,
        "similarity_one_sonar_avg": df["similarity_one_sonar"].dropna().mean() if not df["similarity_one_sonar"].dropna().empty else 0,
        "similarity_calibrated_sonar_avg": df["similarity_calibrated_sonar"].dropna().mean() if not df["similarity_calibrated_sonar"].dropna().empty else 0,
        
        "similarity_zero_checkstyle_avg": df["similarity_zero_checkstyle"].dropna().mean() if not df["similarity_zero_checkstyle"].dropna().empty else 0,
        "similarity_one_checkstyle_avg": df["similarity_one_checkstyle"].dropna().mean() if not df["similarity_one_checkstyle"].dropna().empty else 0,
    }
    
    # Criar figura para gráfico de barras comparando contagens
    plt.figure(figsize=(12, 8))
    bar_width = 0.15
    approaches = ['LLM Zero-Shot', 'LLM One-Shot', 'LLM Calibrado', 'SonarQube', 'CheckStyle']
    avg_counts = [
        avg_metrics["zero_shot_avg"], 
        avg_metrics["one_shot_avg"], 
        avg_metrics["calibrated_avg"], 
        avg_metrics["sonarqube_avg"], 
        avg_metrics["checkstyle_avg"]
    ]
    
    index = np.arange(len(approaches))
    plt.bar(index, avg_counts, bar_width, label='Média de Code Smells Detectados')
    
    plt.xlabel('Abordagem')
    plt.ylabel('Número Médio de Code Smells')
    plt.title('Comparação da Detecção de Code Smells por Abordagem')
    plt.xticks(index, approaches)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'detection_comparison.png'))
    
    # Criar figura para gráfico de similaridade
    plt.figure(figsize=(12, 8))
    llm_approaches = ['Zero-Shot', 'One-Shot', 'Calibrado']
    index = np.arange(len(llm_approaches))
    
    # Verificar se temos dados SonarQube
    sonar_similarities = [
        avg_metrics["similarity_zero_sonar_avg"],
        avg_metrics["similarity_one_sonar_avg"],
        avg_metrics["similarity_calibrated_sonar_avg"]
    ]
    has_sonar = any(sim > 0 for sim in sonar_similarities)
    
    # Verificar se temos dados CheckStyle
    checkstyle_similarities = [
        avg_metrics["similarity_zero_checkstyle_avg"],
        avg_metrics["similarity_one_checkstyle_avg"],
        0  # Não temos equivalente calibrado para CheckStyle
    ]
    has_checkstyle = any(sim > 0 for sim in checkstyle_similarities)
    
    if has_sonar:
        plt.bar(index - bar_width/2 if has_checkstyle else index, 
               sonar_similarities, 
               bar_width, 
               label='Similaridade com SonarQube')
    
    if has_checkstyle:
        plt.bar(index + bar_width/2 if has_sonar else index, 
               checkstyle_similarities, 
               bar_width, 
               label='Similaridade com CheckStyle')
    
    plt.xlabel('Abordagem LLM')
    plt.ylabel('Taxa de Similaridade (%)')
    plt.title('Similaridade entre LLMs e Ferramentas Tradicionais')
    plt.xticks(index, llm_approaches)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'similarity_comparison.png'))
    
    return avg_metrics

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
    
    print(f"Analisando resultados para {len(successful_repos)} repositórios compilados com sucesso...")
    
    # Analisar cada repositório
    all_metrics = []
    
    for repo in successful_repos:
        repo_owner = repo["owner"]
        repo_name = repo["name"]
        
        metrics = analyze_repository(repo_owner, repo_name)
        
        if metrics:
            all_metrics.append(metrics)
    
    # Salvar métricas individuais
    for metrics in all_metrics:
        repo_name = metrics["repository"].replace("/", "_")
        output_file = os.path.join(OUTPUT_DIR, f"{repo_name}_metrics.json")
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
    
    # Salvar métricas combinadas
    combined_output = os.path.join(OUTPUT_DIR, "combined_metrics.json")
    with open(combined_output, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    print(f"Métricas combinadas salvas em {combined_output}")
    
    # Criar gráficos de resumo
    avg_metrics = create_summary_charts(all_metrics)
    
    # Salvar métricas médias
    avg_metrics_file = os.path.join(OUTPUT_DIR, "average_metrics.json")
    with open(avg_metrics_file, 'w') as f:
        json.dump(avg_metrics, f, indent=2)
    
    print(f"Métricas médias salvas em {avg_metrics_file}")
    print("Análise concluída!")

if __name__ == "__main__":
    main()