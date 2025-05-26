import json
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import defaultdict

# --- Configurações Iniciais ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Assume que o script está na pasta 'scripts'
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')

PMD_REPORTS_DIR = os.path.join(DATA_DIR, 'pmd_reports', 'summaries')
CHECKSTYLE_REPORTS_DIR = os.path.join(DATA_DIR, 'checkstyle_reports', 'summaries')
LLM_RESULTS_DIR = os.path.join(DATA_DIR, 'llm_results')

OUTPUT_DIR = os.path.join(BASE_DIR, 'analysis_results')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- 1. Normalização de Nomes de Code Smells ---
def normalize_smell_name(name):
    """
    Normaliza os nomes dos code smells para comparação.
    Ex: "Too Many Fields", "too_many_fields", "TooManyFields" -> "too_many_fields"
    """
    name = name.lower()
    name = name.replace('-', '_').replace(' ', '_')
    # Adicionar mapeamentos específicos se necessário:
    # Ex: if name == "unnecessary_import_(unused_imports)": return "unused_import"
    if "empty_catch_block" in name: return "empty_catch_block"
    if "cyclomatic_complexity" in name: return "cyclomatic_complexity"
    if "god_class" in name: return "god_class"
    if "class_naming_conventions" in name: return "class_naming_conventions"
    if "too_many_fields" in name: return "too_many_fields"
    if "too_many_methods" in name: return "too_many_methods"
    if "unused_import" in name or "unnecessary_import" in name : return "unused_import" # Exemplo de mapeamento
    if "empty_control_statement" in name: return "empty_control_statement"
    if "naming_conventions" in name and "class" not in name: return "general_naming_conventions"

    return name

# --- 2. Carregamento de Dados ---
def load_json_file(file_path):
    """Carrega um único arquivo JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Aviso: Arquivo não encontrado {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Aviso: Erro ao decodificar JSON em {file_path}")
        return None

def load_tool_data(tool_summaries_path):
    """
    Carrega dados de ferramentas como PMD ou CheckStyle.
    Retorna um dicionário: {repo_name: {"code_smells": {...}, "total_smells": N}}
    """
    data = {}
    if not os.path.isdir(tool_summaries_path):
        print(f"Aviso: Diretório não encontrado {tool_summaries_path}")
        return data

    for file_path in glob.glob(os.path.join(tool_summaries_path, '*.json')):
        content = load_json_file(file_path)
        if content and 'repository' in content:
            repo_name = content['repository']
            # Normaliza os code smells ao carregar
            normalized_smells = {normalize_smell_name(k): v for k, v in content.get('code_smells', {}).items() if normalize_smell_name(k) is not None}
            data[repo_name] = {
                "code_smells": normalized_smells,
                "total_smells": content.get('total_smells', sum(normalized_smells.values()))
            }
    return data

def load_llm_data_for_prompt(llm_base_path, prompt_type):
    """
    Carrega dados da LLM para um tipo de prompt específico.
    Os arquivos são nomeados como <prompt_type>.json dentro de cada pasta de repositório.
    Retorna um dicionário: {repo_name: {"code_smells": {...}, "total_smells": N}}
    """
    data = {}
    if not os.path.isdir(llm_base_path):
        print(f"Aviso: Diretório base da LLM não encontrado {llm_base_path}")
        return data

    for repo_folder_name in os.listdir(llm_base_path):
        repo_folder_path = os.path.join(llm_base_path, repo_folder_name)
        if os.path.isdir(repo_folder_path):
            # O nome do repositório é o nome da pasta
            repo_name = repo_folder_name
            file_path = os.path.join(repo_folder_path, f"{prompt_type}.json")
            content = load_json_file(file_path)
            if content:
                 # Assume que o JSON da LLM já tem 'repository' ou podemos usar o nome da pasta
                if 'repository' not in content: # Adiciona o nome do repositório se não estiver no JSON
                    content['repository'] = repo_name

                normalized_smells = {normalize_smell_name(k): v for k, v in content.get('code_smells', {}).items() if normalize_smell_name(k) is not None}
                data[repo_name] = {
                    "code_smells": normalized_smells,
                    "total_smells": content.get('total_smells', sum(normalized_smells.values()))
                }
    return data

# --- 3. Cálculo de Métricas ---

def get_all_repositories(datasets):
    """Retorna um conjunto de todos os nomes de repositórios presentes nos datasets."""
    all_repos = set()
    for data in datasets:
        all_repos.update(data.keys())
    return sorted(list(all_repos))

def calculate_total_smells_per_tool(data_dict, tool_name, all_repositories):
    """Calcula o número total de smells para uma ferramenta/abordagem em todos os repositórios."""
    total = 0
    for repo in all_repositories:
        total += data_dict.get(repo, {}).get('total_smells', 0)
    return {tool_name: total}

def calculate_average_difference(data1, data2, name1, name2, all_repositories):
    """
    Calcula a diferença média de detecção por repositório entre duas abordagens.
    Diferença = total_smells(data1) - total_smells(data2)
    """
    differences = []
    for repo in all_repositories:
        smells1 = data1.get(repo, {}).get('total_smells', 0)
        smells2 = data2.get(repo, {}).get('total_smells', 0)
        differences.append(smells1 - smells2)
    
    if not differences:
        return 0
    return np.mean(differences)

def calculate_corpus_metrics(llm_data, tool_data, all_repositories):
    """
    Calcula Similaridade e Divergência no nível do corpus (agregando todos os repositórios).
    Retorna (similarity_rate, divergence_rate)
    """
    corpus_llm_smells = defaultdict(int)
    corpus_tool_smells = defaultdict(int)
    corpus_total_llm = 0
    corpus_total_tool = 0

    for repo in all_repositories:
        repo_llm_data = llm_data.get(repo, {"code_smells": {}, "total_smells": 0})
        repo_tool_data = tool_data.get(repo, {"code_smells": {}, "total_smells": 0})

        corpus_total_llm += repo_llm_data["total_smells"]
        corpus_total_tool += repo_tool_data["total_smells"]

        for smell, count in repo_llm_data["code_smells"].items():
            corpus_llm_smells[smell] += count
        for smell, count in repo_tool_data["code_smells"].items():
            corpus_tool_smells[smell] += count

    # Interseção: Soma das contagens mínimas para cada tipo de smell comum
    intersection_sum = 0
    common_smell_types = set(corpus_llm_smells.keys()) & set(corpus_tool_smells.keys())
    for s_type in common_smell_types:
        intersection_sum += min(corpus_llm_smells[s_type], corpus_tool_smells[s_type])

    # União: total_llm + total_tool - interseção
    # (Soma de todas as contagens de todos os tipos de smell únicos em ambas as listas)
    # total_smells_in_llm = sum(corpus_llm_smells.values())
    # total_smells_in_tool = sum(corpus_tool_smells.values())
    # union_sum = total_smells_in_llm + total_smells_in_tool - intersection_sum
    
    # União (alternativa para o denominador): Soma de max(LLM_count(s), Tool_count(s)) sobre todos os smells
    # ou, mais simples: soma de todos os smells em LLM + soma de todos os smells em Tool - soma dos que foram contados duas vezes (interseção)
    all_smell_types = set(corpus_llm_smells.keys()) | set(corpus_tool_smells.keys())
    union_sum = 0
    for s_type in all_smell_types:
        union_sum += max(corpus_llm_smells.get(s_type, 0), corpus_tool_smells.get(s_type, 0))

    if union_sum == 0: # Evita divisão por zero
        similarity_rate = 0.0
    else:
        similarity_rate = (intersection_sum / union_sum) * 100

    # Divergência (LLM - Ferramenta): Smells (e suas contagens) detectados pela LLM mas não pela Ferramenta
    llm_minus_tool_sum = 0
    for s_type in set(corpus_llm_smells.keys()) - set(corpus_tool_smells.keys()):
        llm_minus_tool_sum += corpus_llm_smells[s_type]
    
    # Adiciona a diferença para smells comuns onde LLM > Ferramenta
    # Esta interpretação é mais alinhada com "o que LLM pegou A MAIS".
    # Se for "smells que LLM pegou e Ferramenta NÃO pegou (tipo)", a linha acima já basta.
    # A formula do GQM (LLM - SonarQube) / (LLM U SonarQube) sugere a primeira interpretação.
    # Vamos usar a soma das contagens dos smells que estão em LLM e não estão na Ferramenta.

    if union_sum == 0: # Evita divisão por zero
        divergence_rate = 0.0
    else:
        divergence_rate = (llm_minus_tool_sum / union_sum) * 100
        
    return similarity_rate, divergence_rate


# --- 4. Funções de Plotagem ---
plt.style.use('seaborn-v0_8-whitegrid') # Estilo dos gráficos

def plot_bar_chart(data_dict, title, xlabel, ylabel, filename):
    """Cria um gráfico de barras."""
    names = list(data_dict.keys())
    values = list(data_dict.values())

    plt.figure(figsize=(10, 6))
    bars = plt.bar(names, values, color=sns.color_palette("viridis", len(names)))
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.05 * max(values), round(yval,2), ha='center', va='bottom')
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    # plt.show()
    plt.close()

def plot_grouped_bar_chart(df_plot, title, ylabel, filename):
    """Cria um gráfico de barras agrupado a partir de um DataFrame."""
    df_plot.plot(kind='bar', figsize=(12, 7), colormap='viridis')
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xlabel("Comparação")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Métricas")
    plt.tight_layout()
    # Adicionar valores no topo das barras
    for container in plt.gca().containers:
        plt.gca().bar_label(container, fmt='%.2f')
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    # plt.show()
    plt.close()

# --- 5. Lógica Principal do Script ---
def main():
    print("Iniciando análise de code smells...\n")

    # Carregar dados
    print("Carregando dados do PMD...")
    pmd_data = load_tool_data(PMD_REPORTS_DIR)
    print(f"PMD: {len(pmd_data)} repositórios carregados.\n")

    print("Carregando dados do CheckStyle...")
    checkstyle_data = load_tool_data(CHECKSTYLE_REPORTS_DIR)
    print(f"CheckStyle: {len(checkstyle_data)} repositórios carregados.\n")

    print("Carregando dados da LLM (zero-shot)...")
    llm_zerosho_data = load_llm_data_for_prompt(LLM_RESULTS_DIR, "zero_shot")
    print(f"LLM Zero-Shot: {len(llm_zerosho_data)} repositórios carregados.\n")

    print("Carregando dados da LLM (one-shot)...")
    llm_oneshot_data = load_llm_data_for_prompt(LLM_RESULTS_DIR, "one_shot")
    print(f"LLM One-Shot: {len(llm_oneshot_data)} repositórios carregados.\n")

    print("Carregando dados da LLM (prompt calibrado)...")
    llm_calibrated_data = load_llm_data_for_prompt(LLM_RESULTS_DIR, "prompt_calibrado")
    print(f"LLM Calibrado: {len(llm_calibrated_data)} repositórios carregados.\n")

    all_repos = get_all_repositories([pmd_data, checkstyle_data, llm_zerosho_data, llm_oneshot_data, llm_calibrated_data])
    if not all_repos:
        print("Nenhum dado de repositório encontrado. Verifique os caminhos e os arquivos.")
        return
    print(f"Total de repositórios únicos encontrados: {len(all_repos)}\n")

    # --- Question 1: LLM zero-shot vs PMD vs CheckStyle ---
    print("--- Analisando Questão 1: LLM (Zero-Shot) vs PMD vs CheckStyle ---")
    q1_totals = {}
    q1_totals.update(calculate_total_smells_per_tool(llm_zerosho_data, "LLM_Zero_Shot", all_repos))
    q1_totals.update(calculate_total_smells_per_tool(pmd_data, "PMD", all_repos))
    q1_totals.update(calculate_total_smells_per_tool(checkstyle_data, "CheckStyle", all_repos))
    print(f"Métrica 1.1: Número total de code smells detectados:\n {pd.Series(q1_totals)}\n")
    plot_bar_chart(q1_totals, "Q1: Total Code Smells Detectados", "Abordagem", "Total de Smells", "q1_metric1_1_total_smells.png")

    q1_avg_diff_llm_pmd = calculate_average_difference(llm_zerosho_data, pmd_data, "LLM_Zero_Shot", "PMD", all_repos)
    q1_avg_diff_llm_cs = calculate_average_difference(llm_zerosho_data, checkstyle_data, "LLM_Zero_Shot", "CheckStyle", all_repos)
    print(f"Métrica 1.2: Diferença média (LLM_Zero_Shot - PMD): {q1_avg_diff_llm_pmd:.2f}")
    print(f"Métrica 1.2: Diferença média (LLM_Zero_Shot - CheckStyle): {q1_avg_diff_llm_cs:.2f}\n")
    plot_bar_chart({"LLM_ZS - PMD": q1_avg_diff_llm_pmd, "LLM_ZS - CS": q1_avg_diff_llm_cs},
                   "Q1: Diferença Média de Detecção por Repositório", "Comparação", "Diferença Média", "q1_metric1_2_avg_diff.png")

    sim_llm_zs_pmd, div_llm_zs_pmd = calculate_corpus_metrics(llm_zerosho_data, pmd_data, all_repos)
    print(f"Métrica 1.3 (LLM_ZS vs PMD): Similaridade = {sim_llm_zs_pmd:.2f}%")
    print(f"Métrica 1.4 (LLM_ZS vs PMD): Divergência (LLM_ZS - PMD) = {div_llm_zs_pmd:.2f}%\n")

    sim_llm_zs_cs, div_llm_zs_cs = calculate_corpus_metrics(llm_zerosho_data, checkstyle_data, all_repos)
    print(f"Métrica 1.5 (LLM_ZS vs CheckStyle): Similaridade = {sim_llm_zs_cs:.2f}%")
    print(f"Métrica 1.6 (LLM_ZS vs CheckStyle): Divergência (LLM_ZS - CS) = {div_llm_zs_cs:.2f}%\n")
    
    q1_sim_div_data = pd.DataFrame({
        'LLM_ZS vs PMD': {"Similaridade (%)": sim_llm_zs_pmd, "Divergência (%)": div_llm_zs_pmd},
        'LLM_ZS vs CheckStyle': {"Similaridade (%)": sim_llm_zs_cs, "Divergência (%)": div_llm_zs_cs}
    })
    plot_grouped_bar_chart(q1_sim_div_data, "Q1: Similaridade e Divergência (LLM Zero-Shot)", 
                           "Taxa (%)", "q1_metrics_1_3_to_1_6_sim_div.png")


    # --- Question 2: LLM one-shot vs PMD vs CheckStyle ---
    print("--- Analisando Questão 2: LLM (One-Shot) vs PMD vs CheckStyle ---")
    q2_totals = {}
    q2_totals.update(calculate_total_smells_per_tool(llm_oneshot_data, "LLM_One_Shot", all_repos))
    q2_totals.update(calculate_total_smells_per_tool(pmd_data, "PMD", all_repos))
    q2_totals.update(calculate_total_smells_per_tool(checkstyle_data, "CheckStyle", all_repos))
    print(f"Métrica 2.1: Número total de code smells detectados:\n {pd.Series(q2_totals)}\n")
    plot_bar_chart(q2_totals, "Q2: Total Code Smells Detectados", "Abordagem", "Total de Smells", "q2_metric2_1_total_smells.png")

    q2_avg_diff_llm_pmd = calculate_average_difference(llm_oneshot_data, pmd_data, "LLM_One_Shot", "PMD", all_repos)
    q2_avg_diff_llm_cs = calculate_average_difference(llm_oneshot_data, checkstyle_data, "LLM_One_Shot", "CheckStyle", all_repos)
    print(f"Métrica 2.2: Diferença média (LLM_One_Shot - PMD): {q2_avg_diff_llm_pmd:.2f}")
    print(f"Métrica 2.2: Diferença média (LLM_One_Shot - CheckStyle): {q2_avg_diff_llm_cs:.2f}\n")
    plot_bar_chart({"LLM_OS - PMD": q2_avg_diff_llm_pmd, "LLM_OS - CS": q2_avg_diff_llm_cs},
                   "Q2: Diferença Média de Detecção por Repositório", "Comparação", "Diferença Média", "q2_metric2_2_avg_diff.png")

    sim_llm_os_pmd, div_llm_os_pmd = calculate_corpus_metrics(llm_oneshot_data, pmd_data, all_repos)
    print(f"Métrica 2.3 (LLM_OS vs PMD): Similaridade = {sim_llm_os_pmd:.2f}%")
    print(f"Métrica 2.4 (LLM_OS vs PMD): Divergência (LLM_OS - PMD) = {div_llm_os_pmd:.2f}%\n")

    sim_llm_os_cs, div_llm_os_cs = calculate_corpus_metrics(llm_oneshot_data, checkstyle_data, all_repos)
    print(f"Métrica 2.5 (LLM_OS vs CheckStyle): Similaridade = {sim_llm_os_cs:.2f}%")
    print(f"Métrica 2.6 (LLM_OS vs CheckStyle): Divergência (LLM_OS - CS) = {div_llm_os_cs:.2f}%\n")

    q2_sim_div_data = pd.DataFrame({
        'LLM_OS vs PMD': {"Similaridade (%)": sim_llm_os_pmd, "Divergência (%)": div_llm_os_pmd},
        'LLM_OS vs CheckStyle': {"Similaridade (%)": sim_llm_os_cs, "Divergência (%)": div_llm_os_cs}
    })
    plot_grouped_bar_chart(q2_sim_div_data, "Q2: Similaridade e Divergência (LLM One-Shot)",
                           "Taxa (%)", "q2_metrics_2_3_to_2_6_sim_div.png")

    # --- Question 3: LLM calibrado vs PMD ---
    print("--- Analisando Questão 3: LLM (Prompt Calibrado) vs PMD ---")
    q3_totals = {}
    q3_totals.update(calculate_total_smells_per_tool(llm_calibrated_data, "LLM_Calibrado", all_repos))
    q3_totals.update(calculate_total_smells_per_tool(pmd_data, "PMD", all_repos))
    print(f"Métrica 3.1: Número total de code smells detectados:\n {pd.Series(q3_totals)}\n")
    plot_bar_chart(q3_totals, "Q3: Total Code Smells Detectados (LLM Calibrado vs PMD)", "Abordagem", "Total de Smells", "q3_metric3_1_total_smells.png")

    q3_avg_diff_llm_pmd = calculate_average_difference(llm_calibrated_data, pmd_data, "LLM_Calibrado", "PMD", all_repos)
    print(f"Métrica 3.2: Diferença média (LLM_Calibrado - PMD): {q3_avg_diff_llm_pmd:.2f}\n")
    plot_bar_chart({"LLM_Calibrado - PMD": q3_avg_diff_llm_pmd},
                   "Q3: Diferença Média de Detecção por Repositório (LLM Calibrado vs PMD)", "Comparação", "Diferença Média", "q3_metric3_2_avg_diff.png")

    sim_llm_cal_pmd, div_llm_cal_pmd = calculate_corpus_metrics(llm_calibrated_data, pmd_data, all_repos)
    print(f"Métrica 3.3 (LLM_Calibrado vs PMD): Similaridade = {sim_llm_cal_pmd:.2f}%")
    print(f"Métrica 3.4 (LLM_Calibrado vs PMD): Divergência (LLM_Calibrado - PMD) = {div_llm_cal_pmd:.2f}%\n")

    q3_sim_div_data = pd.DataFrame({
        'LLM_Calibrado vs PMD': {"Similaridade (%)": sim_llm_cal_pmd, "Divergência (%)": div_llm_cal_pmd}
    })
    plot_grouped_bar_chart(q3_sim_div_data, "Q3: Similaridade e Divergência (LLM Calibrado vs PMD)",
                           "Taxa (%)", "q3_metrics_3_3_to_3_4_sim_div.png")

    print(f"Análise concluída. Gráficos salvos em: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == '__main__':
    main()