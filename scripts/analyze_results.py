import json
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# --- Configurações Iniciais ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')

PMD_REPORTS_DIR = os.path.join(DATA_DIR, 'pmd_reports', 'summaries')
CHECKSTYLE_REPORTS_DIR = os.path.join(DATA_DIR, 'checkstyle_reports', 'summaries')
LLM_RESULTS_DIR = os.path.join(DATA_DIR, 'llm_results')

OUTPUT_DIR = os.path.join(BASE_DIR, 'analysis_results')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Configurações de estilo para gráficos
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# --- Code Smells Comuns entre PMD e CheckStyle ---
COMMON_CODE_SMELLS = {
    "empty_catch_block",
    "unused_import",
    "cyclomatic_complexity",
    "god_class",
    "naming_conventions",
    "class_naming_conventions",
    "empty_control_statement",
    "too_many_fields"
}

# --- 1. Normalização de Nomes de Code Smells ---
def normalize_smell_name(name):
    """
    Normaliza os nomes dos code smells para comparação.
    """
    name = name.lower()
    name = name.replace('-', '_').replace(' ', '_')
    
    # Mapeamentos específicos
    mappings = {
        "empty_catch_block": ["empty_catch_block", "emptycatchblock"],
        "cyclomatic_complexity": ["cyclomatic_complexity", "cyclomaticcomplexity"],
        "god_class": ["god_class", "godclass", "classfanoutcomplexity"],
        "class_naming_conventions": ["class_naming_conventions", "classnamingconventions", "typename"],
        "too_many_fields": ["too_many_fields", "toomanyfields", "classdataabstractioncoupling"],
        "too_many_methods": ["too_many_methods", "toomanymethods"],
        "unused_import": ["unused_import", "unnecessary_import", "unnecessaryimport", "unusedimports"],
        "empty_control_statement": ["empty_control_statement", "emptycontrolstatement", "emptystatement"],
        "naming_conventions": ["naming_conventions", "namingconventions", "typename"],
        "unused_local_variable": ["unused_local_variable", "unnecessarylocalbeforereturn"]
    }
    
    for normalized, variations in mappings.items():
        if any(var in name for var in variations):
            return normalized
    
    return name

# --- 2. Carregamento de Dados ---
def load_json_file(file_path):
    """Carrega um único arquivo JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Aviso: Erro ao carregar {file_path}: {e}")
        return None

def load_tool_data(tool_summaries_path, filter_common=True):
    """
    Carrega dados de ferramentas como PMD ou CheckStyle.
    """
    data = {}
    if not os.path.isdir(tool_summaries_path):
        print(f"Aviso: Diretório não encontrado {tool_summaries_path}")
        return data

    for file_path in glob.glob(os.path.join(tool_summaries_path, '*.json')):
        content = load_json_file(file_path)
        if content and 'repository' in content:
            repo_name = content['repository']
            normalized_smells = {}
            
            for k, v in content.get('code_smells', {}).items():
                normalized_name = normalize_smell_name(k)
                if normalized_name and (not filter_common or normalized_name in COMMON_CODE_SMELLS):
                    normalized_smells[normalized_name] = normalized_smells.get(normalized_name, 0) + v
            
            data[repo_name] = {
                "code_smells": normalized_smells,
                "total_smells": sum(normalized_smells.values())
            }
    return data

def load_llm_data_for_prompt(llm_base_path, prompt_type, filter_common=True):
    """
    Carrega dados da LLM para um tipo de prompt específico.
    """
    data = {}
    if not os.path.isdir(llm_base_path):
        print(f"Aviso: Diretório base da LLM não encontrado {llm_base_path}")
        return data

    for repo_folder_name in os.listdir(llm_base_path):
        repo_folder_path = os.path.join(llm_base_path, repo_folder_name)
        if os.path.isdir(repo_folder_path):
            repo_name = repo_folder_name
            file_path = os.path.join(repo_folder_path, f"{prompt_type}.json")
            content = load_json_file(file_path)
            
            if content:
                if 'repository' not in content:
                    content['repository'] = repo_name

                normalized_smells = {}
                for k, v in content.get('code_smells', {}).items():
                    normalized_name = normalize_smell_name(k)
                    if normalized_name and (not filter_common or normalized_name in COMMON_CODE_SMELLS):
                        normalized_smells[normalized_name] = normalized_smells.get(normalized_name, 0) + v
                
                data[repo_name] = {
                    "code_smells": normalized_smells,
                    "total_smells": sum(normalized_smells.values())
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
    """Calcula o número total de smells para uma ferramenta/abordagem."""
    total = 0
    for repo in all_repositories:
        total += data_dict.get(repo, {}).get('total_smells', 0)
    return {tool_name: total}

def calculate_average_difference(data1, data2, name1, name2, all_repositories):
    """Calcula a diferença média de detecção por repositório."""
    differences = []
    for repo in all_repositories:
        smells1 = data1.get(repo, {}).get('total_smells', 0)
        smells2 = data2.get(repo, {}).get('total_smells', 0)
        differences.append(smells1 - smells2)
    
    return np.mean(differences) if differences else 0

def calculate_corpus_metrics(llm_data, tool_data, all_repositories):
    """
    Calcula Similaridade e Divergência usando a fórmula de Jaccard.
    """
    corpus_llm_smells = defaultdict(int)
    corpus_tool_smells = defaultdict(int)

    for repo in all_repositories:
        repo_llm_data = llm_data.get(repo, {"code_smells": {}})
        repo_tool_data = tool_data.get(repo, {"code_smells": {}})

        for smell, count in repo_llm_data["code_smells"].items():
            corpus_llm_smells[smell] += count
        for smell, count in repo_tool_data["code_smells"].items():
            corpus_tool_smells[smell] += count

    # Interseção e União
    intersection_sum = 0
    all_smell_types = set(corpus_llm_smells.keys()) | set(corpus_tool_smells.keys())
    
    for s_type in all_smell_types:
        llm_count = corpus_llm_smells.get(s_type, 0)
        tool_count = corpus_tool_smells.get(s_type, 0)
        intersection_sum += min(llm_count, tool_count)
    
    # União
    union_sum = sum(corpus_llm_smells.values()) + sum(corpus_tool_smells.values()) - intersection_sum
    
    if union_sum == 0:
        similarity_rate = 0.0
        divergence_rate = 0.0
    else:
        similarity_rate = (intersection_sum / union_sum) * 100
        
        # Divergência: LLM - Ferramenta
        llm_minus_tool = sum(corpus_llm_smells.values()) - intersection_sum
        divergence_rate = (llm_minus_tool / union_sum) * 100
        
    return similarity_rate, divergence_rate

def prepare_detailed_comparison_data(llm_data, tool_data, all_repositories):
    """Prepara dados detalhados para visualizações avançadas."""
    comparison_data = []
    
    for repo in all_repositories:
        llm_smells = llm_data.get(repo, {"code_smells": {}})["code_smells"]
        tool_smells = tool_data.get(repo, {"code_smells": {}})["code_smells"]
        
        all_smells_in_repo = set(llm_smells.keys()) | set(tool_smells.keys())
        
        for smell in all_smells_in_repo:
            comparison_data.append({
                'repository': repo,
                'code_smell': smell,
                'llm_count': llm_smells.get(smell, 0),
                'tool_count': tool_smells.get(smell, 0)
            })
    
    return pd.DataFrame(comparison_data)

# --- 4. Funções de Plotagem Aprimoradas ---
def plot_enhanced_bar_chart(data_dict, title, xlabel, ylabel, filename):
    """Gráfico de barras aprimorado com gradientes."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    names = list(data_dict.keys())
    values = list(data_dict.values())
    
    # Cores com gradiente
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(names)))
    
    bars = ax.bar(names, values, color=colors, edgecolor='black', linewidth=1.5)
    
    # Adicionar valores nas barras
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.01,
                f'{int(val)}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax.set_xlabel(xlabel, fontsize=14)
    ax.set_ylabel(ylabel, fontsize=14)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300, bbox_inches='tight')
    plt.close()

def plot_scatter_comparison(df, llm_name, tool_name, filename):
    """Cria scatter plot melhorado para comparação entre LLM e ferramenta."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    
    # Preparar dados - duas agregações diferentes
    # 1. Por code smell (soma total)
    smell_summary = df.groupby('code_smell').agg({
        'llm_count': 'sum',
        'tool_count': 'sum'
    }).reset_index()
    
    # 2. Por repositório (soma total)
    repo_summary = df.groupby('repository').agg({
        'llm_count': 'sum',
        'tool_count': 'sum'
    }).reset_index()
    
    # --- Subplot 1: Por Code Smell ---
    # Cores baseadas na diferença percentual
    smell_summary['diff_percent'] = ((smell_summary['llm_count'] - smell_summary['tool_count']) / 
                                     (smell_summary['tool_count'] + 1)) * 100
    
    # Tamanho dos pontos baseado no total de detecções
    smell_summary['total'] = smell_summary['llm_count'] + smell_summary['tool_count']
    sizes = 100 + (smell_summary['total'] / smell_summary['total'].max()) * 400
    
    scatter1 = ax1.scatter(smell_summary['tool_count'], 
                          smell_summary['llm_count'],
                          s=sizes, 
                          c=smell_summary['diff_percent'],
                          cmap='RdYlBu', 
                          alpha=0.7,
                          edgecolors='black', 
                          linewidth=1.5)
    
    # Linha de referência (y=x)
    max_val1 = max(smell_summary['tool_count'].max(), smell_summary['llm_count'].max()) * 1.1
    ax1.plot([0, max_val1], [0, max_val1], 'k--', alpha=0.5, linewidth=2, label='Linha de igualdade')
    
    # Adicionar anotações para pontos significativos
    for idx, row in smell_summary.iterrows():
        # Anotar apenas pontos com diferença significativa ou total alto
        if abs(row['diff_percent']) > 50 or row['total'] > smell_summary['total'].median():
            ax1.annotate(row['code_smell'].replace('_', ' ').title(), 
                        (row['tool_count'], row['llm_count']),
                        xytext=(10, 10), 
                        textcoords='offset points',
                        fontsize=10, 
                        alpha=0.9,
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3', alpha=0.5))
    
    # Configurações do subplot 1
    ax1.set_xlabel(f'{tool_name} - Total de Detecções', fontsize=14, fontweight='bold')
    ax1.set_ylabel(f'{llm_name} - Total de Detecções', fontsize=14, fontweight='bold')
    ax1.set_title(f'Comparação por Tipo de Code Smell', fontsize=16, fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_axisbelow(True)
    
    # Adicionar zonas de interpretação
    ax1.fill_between([0, max_val1], [0, 0], [0, max_val1], 
                     where=[True, True], alpha=0.1, color='red', 
                     label=f'{tool_name} detecta mais')
    ax1.fill_between([0, max_val1], [0, max_val1], [max_val1, max_val1], 
                     where=[True, True], alpha=0.1, color='blue', 
                     label=f'{llm_name} detecta mais')
    
    # Colorbar para o subplot 1
    cbar1 = plt.colorbar(scatter1, ax=ax1)
    cbar1.set_label('Diferença % (LLM - Ferramenta)', fontsize=12)
    
    ax1.legend(loc='upper left', fontsize=11)
    
    # --- Subplot 2: Por Repositório ---
    # Calcular métricas para coloração
    repo_summary['diff_percent'] = ((repo_summary['llm_count'] - repo_summary['tool_count']) / 
                                    (repo_summary['tool_count'] + 1)) * 100
    
    scatter2 = ax2.scatter(repo_summary['tool_count'], 
                          repo_summary['llm_count'],
                          s=150, 
                          c=repo_summary['diff_percent'],
                          cmap='RdYlBu', 
                          alpha=0.7,
                          edgecolors='black', 
                          linewidth=1.5,
                          marker='D')  # Diamante para diferenciar
    
    # Linha de referência
    max_val2 = max(repo_summary['tool_count'].max(), repo_summary['llm_count'].max()) * 1.1
    ax2.plot([0, max_val2], [0, max_val2], 'k--', alpha=0.5, linewidth=2)
    
    # Adicionar estatísticas no gráfico
    correlation = repo_summary[['tool_count', 'llm_count']].corr().iloc[0, 1]
    textstr = f'Correlação: {correlation:.3f}\n'
    textstr += f'Repositórios: {len(repo_summary)}\n'
    textstr += f'{llm_name} > {tool_name}: {(repo_summary["llm_count"] > repo_summary["tool_count"]).sum()}\n'
    textstr += f'{tool_name} > {llm_name}: {(repo_summary["tool_count"] > repo_summary["llm_count"]).sum()}'
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax2.text(0.05, 0.95, textstr, transform=ax2.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)
    
    # Configurações do subplot 2
    ax2.set_xlabel(f'{tool_name} - Total de Detecções', fontsize=14, fontweight='bold')
    ax2.set_ylabel(f'{llm_name} - Total de Detecções', fontsize=14, fontweight='bold')
    ax2.set_title(f'Comparação por Repositório', fontsize=16, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_axisbelow(True)
    
    # Colorbar para o subplot 2
    cbar2 = plt.colorbar(scatter2, ax=ax2)
    cbar2.set_label('Diferença % (LLM - Ferramenta)', fontsize=12)
    
    # Título geral
    fig.suptitle(f'Análise Comparativa: {llm_name} vs {tool_name}', 
                 fontsize=18, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300, bbox_inches='tight')
    plt.close()
    
    # --- Gráfico adicional: Violin Plot ---
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Preparar dados para violin plot
    violin_data = []
    for _, row in df.iterrows():
        if row['llm_count'] > 0:
            violin_data.extend([llm_name] * int(row['llm_count']))
        if row['tool_count'] > 0:
            violin_data.extend([tool_name] * int(row['tool_count']))
    
    # Criar DataFrame para violin plot
    if violin_data:  # Apenas se houver dados
        violin_df = pd.DataFrame({'Tool': violin_data})
        violin_df['Count'] = 1
        
        # Agregar por repositório e ferramenta
        plot_data = []
        for repo in df['repository'].unique():
            repo_data = df[df['repository'] == repo]
            plot_data.append({
                'Tool': llm_name,
                'Count': repo_data['llm_count'].sum(),
                'Repository': repo
            })
            plot_data.append({
                'Tool': tool_name,
                'Count': repo_data['tool_count'].sum(),
                'Repository': repo
            })
        
        plot_df = pd.DataFrame(plot_data)
        
        # Criar violin plot
        sns.violinplot(data=plot_df, x='Tool', y='Count', ax=ax, inner='box', palette='Set2')
        
        # Adicionar pontos individuais
        sns.stripplot(data=plot_df, x='Tool', y='Count', ax=ax, 
                     size=4, color='black', alpha=0.3)
        
        ax.set_title(f'Distribuição de Detecções por Repositório\n{llm_name} vs {tool_name}', 
                    fontsize=16, fontweight='bold')
        ax.set_ylabel('Total de Code Smells por Repositório', fontsize=14)
        ax.set_xlabel('Ferramenta', fontsize=14)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Adicionar médias
        means = plot_df.groupby('Tool')['Count'].mean()
        for i, (tool, mean) in enumerate(means.items()):
            ax.hlines(mean, i-0.4, i+0.4, colors='red', linestyles='dashed', linewidth=2)
            ax.text(i, mean + plot_df['Count'].max()*0.02, f'Média: {mean:.1f}', 
                   ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, filename.replace('.png', '_violin.png')), 
                   dpi=300, bbox_inches='tight')
        plt.close()

def plot_heatmap_comparison(llm_data, tool_data, all_repositories, llm_name, tool_name, filename):
    """Cria heatmap para comparação entre repositórios e code smells."""
    # Preparar matriz de dados
    all_smells = set()
    for repo in all_repositories:
        all_smells.update(llm_data.get(repo, {"code_smells": {}})["code_smells"].keys())
        all_smells.update(tool_data.get(repo, {"code_smells": {}})["code_smells"].keys())
    
    all_smells = sorted(list(all_smells))
    
    # Criar matriz de diferença
    diff_matrix = np.zeros((len(all_repositories), len(all_smells)))
    
    for i, repo in enumerate(all_repositories):
        for j, smell in enumerate(all_smells):
            llm_count = llm_data.get(repo, {"code_smells": {}})["code_smells"].get(smell, 0)
            tool_count = tool_data.get(repo, {"code_smells": {}})["code_smells"].get(smell, 0)
            diff_matrix[i, j] = llm_count - tool_count
    
    # Criar heatmap
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Criar máscaras para valores zero
    mask = diff_matrix == 0
    
    sns.heatmap(diff_matrix, 
                xticklabels=all_smells,
                yticklabels=all_repositories,
                cmap='RdBu_r',
                center=0,
                annot=True,
                fmt='.0f',
                mask=mask,
                cbar_kws={'label': f'Diferença ({llm_name} - {tool_name})'},
                ax=ax)
    
    ax.set_title(f'Heatmap de Diferenças: {llm_name} - {tool_name}', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Code Smells', fontsize=14)
    ax.set_ylabel('Repositórios', fontsize=14)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300, bbox_inches='tight')
    plt.close()

def plot_grouped_bar_enhanced(data_dict, title, filename):
    """Gráfico de barras agrupadas aprimorado."""
    df = pd.DataFrame(data_dict)
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    x = np.arange(len(df.columns))
    width = 0.35
    
    # Cores distintas para cada métrica
    colors = ['#3498db', '#e74c3c']
    
    for i, (metric, row) in enumerate(df.iterrows()):
        offset = width * (i - len(df) / 2 + 0.5)
        bars = ax.bar(x + offset, row, width, label=metric, color=colors[i], alpha=0.8, edgecolor='black')
        
        # Adicionar valores nas barras
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=10)
    
    ax.set_xlabel('Comparações', fontsize=14)
    ax.set_ylabel('Taxa (%)', fontsize=14)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(df.columns, rotation=45, ha='right')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300, bbox_inches='tight')
    plt.close()

def create_summary_report(results_dict, filename):
    """Cria um relatório resumido em formato de tabela."""
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.axis('tight')
    ax.axis('off')
    
    # Preparar dados para tabela
    table_data = []
    headers = ['Questão', 'Métrica', 'Valor', 'Interpretação']
    
    for question, metrics in results_dict.items():
        for metric_name, value in metrics.items():
            interpretation = ""
            if "similaridade" in metric_name.lower():
                interpretation = "Alta" if value > 70 else "Média" if value > 40 else "Baixa"
            elif "divergência" in metric_name.lower():
                interpretation = "Alta" if value > 30 else "Média" if value > 15 else "Baixa"
            elif "diferença" in metric_name.lower():
                interpretation = "LLM detecta mais" if value > 0 else "Ferramenta detecta mais"
            
            table_data.append([question, metric_name, f"{value:.2f}", interpretation])
    
    # Criar tabela
    table = ax.table(cellText=table_data,
                     colLabels=headers,
                     cellLoc='center',
                     loc='center',
                     colWidths=[0.15, 0.45, 0.15, 0.25])
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    
    # Estilizar cabeçalho
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#3498db')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Estilizar linhas alternadas
    for i in range(1, len(table_data) + 1):
        for j in range(len(headers)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#ecf0f1')
    
    ax.set_title('Relatório Resumido - Análise de Code Smells', fontsize=18, fontweight='bold', pad=20)
    
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300, bbox_inches='tight')
    plt.close()

# --- 5. Lógica Principal do Script ---
def main():
    print("=" * 80)
    print("ANÁLISE APRIMORADA DE CODE SMELLS - LLM vs FERRAMENTAS")
    print("=" * 80)
    print()
    
    # Opção para filtrar apenas code smells comuns
    filter_common = True
    print(f"Filtro de code smells comuns: {'ATIVADO' if filter_common else 'DESATIVADO'}")
    print(f"Code smells considerados: {', '.join(sorted(COMMON_CODE_SMELLS))}")
    print()
    
    # Carregar dados
    print("📊 Carregando dados...")
    pmd_data = load_tool_data(PMD_REPORTS_DIR, filter_common)
    print(f"✓ PMD: {len(pmd_data)} repositórios carregados")
    
    checkstyle_data = load_tool_data(CHECKSTYLE_REPORTS_DIR, filter_common)
    print(f"✓ CheckStyle: {len(checkstyle_data)} repositórios carregados")
    
    llm_zeroshot_data = load_llm_data_for_prompt(LLM_RESULTS_DIR, "zero_shot", filter_common)
    print(f"✓ LLM Zero-Shot: {len(llm_zeroshot_data)} repositórios carregados")
    
    llm_oneshot_data = load_llm_data_for_prompt(LLM_RESULTS_DIR, "one_shot", filter_common)
    print(f"✓ LLM One-Shot: {len(llm_oneshot_data)} repositórios carregados")
    
    llm_calibrated_data = load_llm_data_for_prompt(LLM_RESULTS_DIR, "prompt_calibrado", filter_common)
    print(f"✓ LLM Calibrado: {len(llm_calibrated_data)} repositórios carregados")
    print()
    
    all_repos = get_all_repositories([pmd_data, checkstyle_data, llm_zeroshot_data, llm_oneshot_data, llm_calibrated_data])
    
    if not all_repos:
        print("❌ Nenhum dado de repositório encontrado. Verifique os caminhos e os arquivos.")
        return
    
    print(f"📁 Total de repositórios únicos: {len(all_repos)}")
    print("-" * 80)
    
    # Dicionário para armazenar todos os resultados
    all_results = {}
    
    # --- Question 1: LLM zero-shot vs PMD vs CheckStyle ---
    print("\n🔍 QUESTÃO 1: LLM (Zero-Shot) vs PMD vs CheckStyle")
    print("-" * 80)
    
    q1_results = {}
    
    # Métrica 1.1
    q1_totals = {}
    q1_totals.update(calculate_total_smells_per_tool(llm_zeroshot_data, "LLM Zero-Shot", all_repos))
    q1_totals.update(calculate_total_smells_per_tool(pmd_data, "PMD", all_repos))
    q1_totals.update(calculate_total_smells_per_tool(checkstyle_data, "CheckStyle", all_repos))
    
    print("📈 Métrica 1.1 - Total de code smells detectados:")
    for tool, total in q1_totals.items():
        print(f"   • {tool}: {total}")
        q1_results[f"1.1 - Total {tool}"] = total
    
    plot_enhanced_bar_chart(q1_totals, "Q1: Total de Code Smells Detectados", 
                           "Abordagem", "Total de Smells", "q1_metric1_1_total_smells.png")
    
    # Métrica 1.2
    q1_avg_diff_llm_pmd = calculate_average_difference(llm_zeroshot_data, pmd_data, "LLM_Zero_Shot", "PMD", all_repos)
    q1_avg_diff_llm_cs = calculate_average_difference(llm_zeroshot_data, checkstyle_data, "LLM_Zero_Shot", "CheckStyle", all_repos)
    
    print(f"\n📊 Métrica 1.2 - Diferença média por repositório:")
    print(f"   • LLM Zero-Shot - PMD: {q1_avg_diff_llm_pmd:.2f}")
    print(f"   • LLM Zero-Shot - CheckStyle: {q1_avg_diff_llm_cs:.2f}")
    
    q1_results["1.2 - Dif. Média LLM_ZS-PMD"] = q1_avg_diff_llm_pmd
    q1_results["1.2 - Dif. Média LLM_ZS-CS"] = q1_avg_diff_llm_cs
    
    plot_enhanced_bar_chart({"LLM ZS - PMD": q1_avg_diff_llm_pmd, "LLM ZS - CheckStyle": q1_avg_diff_llm_cs},
                           "Q1: Diferença Média de Detecção por Repositório", 
                           "Comparação", "Diferença Média", "q1_metric1_2_avg_diff.png")
    
    # Métricas 1.3-1.6
    sim_llm_zs_pmd, div_llm_zs_pmd = calculate_corpus_metrics(llm_zeroshot_data, pmd_data, all_repos)
    sim_llm_zs_cs, div_llm_zs_cs = calculate_corpus_metrics(llm_zeroshot_data, checkstyle_data, all_repos)
    
    print(f"\n🔄 Métricas 1.3-1.6 - Similaridade e Divergência:")
    print(f"   • LLM ZS vs PMD:")
    print(f"     - Similaridade: {sim_llm_zs_pmd:.2f}%")
    print(f"     - Divergência: {div_llm_zs_pmd:.2f}%")
    print(f"   • LLM ZS vs CheckStyle:")
    print(f"     - Similaridade: {sim_llm_zs_cs:.2f}%")
    print(f"     - Divergência: {div_llm_zs_cs:.2f}%")
    
    q1_results["1.3 - Similaridade LLM_ZS vs PMD"] = sim_llm_zs_pmd
    q1_results["1.4 - Divergência LLM_ZS vs PMD"] = div_llm_zs_pmd
    q1_results["1.5 - Similaridade LLM_ZS vs CS"] = sim_llm_zs_cs
    q1_results["1.6 - Divergência LLM_ZS vs CS"] = div_llm_zs_cs
    
    all_results["Questão 1"] = q1_results
    
    q1_sim_div_data = {
        'LLM ZS vs PMD': {"Similaridade (%)": sim_llm_zs_pmd, "Divergência (%)": div_llm_zs_pmd},
        'LLM ZS vs CheckStyle': {"Similaridade (%)": sim_llm_zs_cs, "Divergência (%)": div_llm_zs_cs}
    }
    plot_grouped_bar_enhanced(q1_sim_div_data, "Q1: Similaridade e Divergência - LLM Zero-Shot", 
                             "q1_metrics_1_3_to_1_6_sim_div.png")
    
    # Visualizações adicionais Q1
    df_comparison_zs_pmd = prepare_detailed_comparison_data(llm_zeroshot_data, pmd_data, all_repos)
    plot_scatter_comparison(df_comparison_zs_pmd, "LLM Zero-Shot", "PMD", "q1_scatter_llm_zs_vs_pmd.png")
    
    df_comparison_zs_cs = prepare_detailed_comparison_data(llm_zeroshot_data, checkstyle_data, all_repos)
    plot_scatter_comparison(df_comparison_zs_cs, "LLM Zero-Shot", "CheckStyle", "q1_scatter_llm_zs_vs_checkstyle.png")
    
    plot_heatmap_comparison(llm_zeroshot_data, pmd_data, all_repos[:10], "LLM Zero-Shot", "PMD", "q1_heatmap_llm_zs_vs_pmd.png")
    
    # --- Question 2: LLM one-shot vs PMD vs CheckStyle ---
    print("\n" + "=" * 80)
    print("🔍 QUESTÃO 2: LLM (One-Shot) vs PMD vs CheckStyle")
    print("-" * 80)
    
    q2_results = {}
    
    # Métrica 2.1
    q2_totals = {}
    q2_totals.update(calculate_total_smells_per_tool(llm_oneshot_data, "LLM One-Shot", all_repos))
    q2_totals.update(calculate_total_smells_per_tool(pmd_data, "PMD", all_repos))
    q2_totals.update(calculate_total_smells_per_tool(checkstyle_data, "CheckStyle", all_repos))
    
    print("📈 Métrica 2.1 - Total de code smells detectados:")
    for tool, total in q2_totals.items():
        print(f"   • {tool}: {total}")
        q2_results[f"2.1 - Total {tool}"] = total
    
    plot_enhanced_bar_chart(q2_totals, "Q2: Total de Code Smells Detectados", 
                           "Abordagem", "Total de Smells", "q2_metric2_1_total_smells.png")
    
    # Métrica 2.2
    q2_avg_diff_llm_pmd = calculate_average_difference(llm_oneshot_data, pmd_data, "LLM_One_Shot", "PMD", all_repos)
    q2_avg_diff_llm_cs = calculate_average_difference(llm_oneshot_data, checkstyle_data, "LLM_One_Shot", "CheckStyle", all_repos)
    
    print(f"\n📊 Métrica 2.2 - Diferença média por repositório:")
    print(f"   • LLM One-Shot - PMD: {q2_avg_diff_llm_pmd:.2f}")
    print(f"   • LLM One-Shot - CheckStyle: {q2_avg_diff_llm_cs:.2f}")
    
    q2_results["2.2 - Dif. Média LLM_OS-PMD"] = q2_avg_diff_llm_pmd
    q2_results["2.2 - Dif. Média LLM_OS-CS"] = q2_avg_diff_llm_cs
    
    plot_enhanced_bar_chart({"LLM OS - PMD": q2_avg_diff_llm_pmd, "LLM OS - CheckStyle": q2_avg_diff_llm_cs},
                           "Q2: Diferença Média de Detecção por Repositório", 
                           "Comparação", "Diferença Média", "q2_metric2_2_avg_diff.png")
    
    # Métricas 2.3-2.6
    sim_llm_os_pmd, div_llm_os_pmd = calculate_corpus_metrics(llm_oneshot_data, pmd_data, all_repos)
    sim_llm_os_cs, div_llm_os_cs = calculate_corpus_metrics(llm_oneshot_data, checkstyle_data, all_repos)
    
    print(f"\n🔄 Métricas 2.3-2.6 - Similaridade e Divergência:")
    print(f"   • LLM OS vs PMD:")
    print(f"     - Similaridade: {sim_llm_os_pmd:.2f}%")
    print(f"     - Divergência: {div_llm_os_pmd:.2f}%")
    print(f"   • LLM OS vs CheckStyle:")
    print(f"     - Similaridade: {sim_llm_os_cs:.2f}%")
    print(f"     - Divergência: {div_llm_os_cs:.2f}%")
    
    q2_results["2.3 - Similaridade LLM_OS vs PMD"] = sim_llm_os_pmd
    q2_results["2.4 - Divergência LLM_OS vs PMD"] = div_llm_os_pmd
    q2_results["2.5 - Similaridade LLM_OS vs CS"] = sim_llm_os_cs
    q2_results["2.6 - Divergência LLM_OS vs CS"] = div_llm_os_cs
    
    all_results["Questão 2"] = q2_results
    
    q2_sim_div_data = {
        'LLM OS vs PMD': {"Similaridade (%)": sim_llm_os_pmd, "Divergência (%)": div_llm_os_pmd},
        'LLM OS vs CheckStyle': {"Similaridade (%)": sim_llm_os_cs, "Divergência (%)": div_llm_os_cs}
    }
    plot_grouped_bar_enhanced(q2_sim_div_data, "Q2: Similaridade e Divergência - LLM One-Shot", 
                             "q2_metrics_2_3_to_2_6_sim_div.png")
    
    # Visualizações adicionais Q2
    df_comparison_os_pmd = prepare_detailed_comparison_data(llm_oneshot_data, pmd_data, all_repos)
    plot_scatter_comparison(df_comparison_os_pmd, "LLM One-Shot", "PMD", "q2_scatter_llm_os_vs_pmd.png")
    
    df_comparison_os_cs = prepare_detailed_comparison_data(llm_oneshot_data, checkstyle_data, all_repos)
    plot_scatter_comparison(df_comparison_os_cs, "LLM One-Shot", "CheckStyle", "q2_scatter_llm_os_vs_checkstyle.png")
    
    plot_heatmap_comparison(llm_oneshot_data, pmd_data, all_repos[:10], "LLM One-Shot", "PMD", "q2_heatmap_llm_os_vs_pmd.png")
    
    # --- Question 3: LLM calibrado vs PMD ---
    print("\n" + "=" * 80)
    print("🔍 QUESTÃO 3: LLM (Prompt Calibrado) vs PMD")
    print("-" * 80)
    
    q3_results = {}
    
    # Métrica 3.1
    q3_totals = {}
    q3_totals.update(calculate_total_smells_per_tool(llm_calibrated_data, "LLM Calibrado", all_repos))
    q3_totals.update(calculate_total_smells_per_tool(pmd_data, "PMD", all_repos))
    
    print("📈 Métrica 3.1 - Total de code smells detectados:")
    for tool, total in q3_totals.items():
        print(f"   • {tool}: {total}")
        q3_results[f"3.1 - Total {tool}"] = total
    
    plot_enhanced_bar_chart(q3_totals, "Q3: Total de Code Smells Detectados", 
                           "Abordagem", "Total de Smells", "q3_metric3_1_total_smells.png")
    
    # Métrica 3.2
    q3_avg_diff_llm_pmd = calculate_average_difference(llm_calibrated_data, pmd_data, "LLM_Calibrado", "PMD", all_repos)
    
    print(f"\n📊 Métrica 3.2 - Diferença média por repositório:")
    print(f"   • LLM Calibrado - PMD: {q3_avg_diff_llm_pmd:.2f}")
    
    q3_results["3.2 - Dif. Média LLM_Cal-PMD"] = q3_avg_diff_llm_pmd
    
    plot_enhanced_bar_chart({"LLM Calibrado - PMD": q3_avg_diff_llm_pmd},
                           "Q3: Diferença Média de Detecção por Repositório", 
                           "Comparação", "Diferença Média", "q3_metric3_2_avg_diff.png")
    
    # Métricas 3.3-3.4
    sim_llm_cal_pmd, div_llm_cal_pmd = calculate_corpus_metrics(llm_calibrated_data, pmd_data, all_repos)
    
    print(f"\n🔄 Métricas 3.3-3.4 - Similaridade e Divergência:")
    print(f"   • LLM Calibrado vs PMD:")
    print(f"     - Similaridade: {sim_llm_cal_pmd:.2f}%")
    print(f"     - Divergência: {div_llm_cal_pmd:.2f}%")
    
    q3_results["3.3 - Similaridade LLM_Cal vs PMD"] = sim_llm_cal_pmd
    q3_results["3.4 - Divergência LLM_Cal vs PMD"] = div_llm_cal_pmd
    
    all_results["Questão 3"] = q3_results
    
    q3_sim_div_data = {
        'LLM Calibrado vs PMD': {"Similaridade (%)": sim_llm_cal_pmd, "Divergência (%)": div_llm_cal_pmd}
    }
    plot_grouped_bar_enhanced(q3_sim_div_data, "Q3: Similaridade e Divergência - LLM Calibrado vs PMD", 
                             "q3_metrics_3_3_to_3_4_sim_div.png")
    
    # Visualizações adicionais Q3
    df_comparison_cal_pmd = prepare_detailed_comparison_data(llm_calibrated_data, pmd_data, all_repos)
    plot_scatter_comparison(df_comparison_cal_pmd, "LLM Calibrado", "PMD", "q3_scatter_llm_cal_vs_pmd.png")
    
    plot_heatmap_comparison(llm_calibrated_data, pmd_data, all_repos[:10], "LLM Calibrado", "PMD", "q3_heatmap_llm_cal_vs_pmd.png")
    
    # --- Análises Adicionais ---
    print("\n" + "=" * 80)
    print("📊 ANÁLISES ADICIONAIS")
    print("-" * 80)
    
    # Comparação entre todos os prompts LLM
    llm_comparison = {
        "LLM Zero-Shot": calculate_total_smells_per_tool(llm_zeroshot_data, "LLM Zero-Shot", all_repos)["LLM Zero-Shot"],
        "LLM One-Shot": calculate_total_smells_per_tool(llm_oneshot_data, "LLM One-Shot", all_repos)["LLM One-Shot"],
        "LLM Calibrado": calculate_total_smells_per_tool(llm_calibrated_data, "LLM Calibrado", all_repos)["LLM Calibrado"]
    }
    
    print("\n📈 Comparação entre prompts LLM:")
    for prompt, total in llm_comparison.items():
        print(f"   • {prompt}: {total}")
    
    plot_enhanced_bar_chart(llm_comparison, "Comparação entre Prompts LLM", 
                           "Tipo de Prompt", "Total de Smells", "comparison_llm_prompts.png")
    
    # Análise por tipo de code smell
    print("\n🔍 Análise por tipo de code smell (top 5 mais detectados):")
    
    all_smell_counts = defaultdict(int)
    for data_source in [pmd_data, checkstyle_data, llm_zeroshot_data, llm_oneshot_data, llm_calibrated_data]:
        for repo_data in data_source.values():
            for smell, count in repo_data["code_smells"].items():
                all_smell_counts[smell] += count
    
    top_smells = sorted(all_smell_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    print("   Top 5 code smells mais detectados:")
    for smell, count in top_smells:
        print(f"   • {smell}: {count}")
    
    # Criar gráfico de distribuição por tipo de smell
    smell_distribution = {}
    tools = [
        ("LLM Zero-Shot", llm_zeroshot_data),
        ("LLM One-Shot", llm_oneshot_data),
        ("LLM Calibrado", llm_calibrated_data),
        ("PMD", pmd_data),
        ("CheckStyle", checkstyle_data)
    ]
    
    for smell, _ in top_smells:
        smell_distribution[smell] = {}
        for tool_name, tool_data in tools:
            total = sum(repo_data["code_smells"].get(smell, 0) for repo_data in tool_data.values())
            smell_distribution[smell][tool_name] = total
    
    # Criar DataFrame para visualização
    smell_df = pd.DataFrame(smell_distribution).T
    
    # Gráfico de barras empilhadas
    fig, ax = plt.subplots(figsize=(14, 8))
    smell_df.plot(kind='bar', ax=ax, width=0.8)
    ax.set_title("Distribuição dos Top 5 Code Smells por Ferramenta", fontsize=16, fontweight='bold')
    ax.set_xlabel("Tipo de Code Smell", fontsize=14)
    ax.set_ylabel("Total de Detecções", fontsize=14)
    ax.legend(title="Ferramenta", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "distribution_top_smells_by_tool.png"), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Criar relatório resumido
    print("\n📄 Gerando relatório resumido...")
    create_summary_report(all_results, "summary_report.png")
    
    # Análise de correlação
    print("\n🔗 Análise de correlação entre ferramentas:")
    
    # Preparar dados para correlação
    correlation_data = []
    for repo in all_repos:
        row = {
            'Repository': repo,
            'LLM_ZS': llm_zeroshot_data.get(repo, {}).get('total_smells', 0),
            'LLM_OS': llm_oneshot_data.get(repo, {}).get('total_smells', 0),
            'LLM_Cal': llm_calibrated_data.get(repo, {}).get('total_smells', 0),
            'PMD': pmd_data.get(repo, {}).get('total_smells', 0),
            'CheckStyle': checkstyle_data.get(repo, {}).get('total_smells', 0)
        }
        correlation_data.append(row)
    
    corr_df = pd.DataFrame(correlation_data)
    corr_matrix = corr_df[['LLM_ZS', 'LLM_OS', 'LLM_Cal', 'PMD', 'CheckStyle']].corr()
    
    # Heatmap de correlação
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, 
                square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                fmt='.3f', ax=ax)
    ax.set_title("Matriz de Correlação entre Ferramentas", fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "correlation_matrix_tools.png"), dpi=300, bbox_inches='tight')
    plt.close()
    
    print("   Correlações mais fortes:")
    # Encontrar correlações mais fortes (excluindo diagonal)
    corr_values = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr_values.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_matrix.iloc[i, j]))
    
    corr_values.sort(key=lambda x: abs(x[2]), reverse=True)
    for tool1, tool2, corr in corr_values[:3]:
        print(f"   • {tool1} vs {tool2}: {corr:.3f}")
    
    # Salvar dados resumidos em CSV
    print("\n💾 Salvando dados resumidos...")
    
    # Resumo geral
    summary_data = []
    for question, metrics in all_results.items():
        for metric, value in metrics.items():
            summary_data.append({
                'Questão': question,
                'Métrica': metric,
                'Valor': value
            })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(os.path.join(OUTPUT_DIR, 'summary_metrics.csv'), index=False)
    
    # Dados detalhados por repositório
    detailed_data = []
    for repo in all_repos:
        row = {
            'Repository': repo,
            'LLM_ZeroShot': llm_zeroshot_data.get(repo, {}).get('total_smells', 0),
            'LLM_OneShot': llm_oneshot_data.get(repo, {}).get('total_smells', 0),
            'LLM_Calibrated': llm_calibrated_data.get(repo, {}).get('total_smells', 0),
            'PMD': pmd_data.get(repo, {}).get('total_smells', 0),
            'CheckStyle': checkstyle_data.get(repo, {}).get('total_smells', 0)
        }
        detailed_data.append(row)
    
    detailed_df = pd.DataFrame(detailed_data)
    detailed_df.to_csv(os.path.join(OUTPUT_DIR, 'detailed_by_repository.csv'), index=False)
    
    print("\n" + "=" * 80)
    print("✅ ANÁLISE CONCLUÍDA!")
    print("=" * 80)
    print(f"\n📁 Resultados salvos em: {os.path.abspath(OUTPUT_DIR)}")
    print("\n📊 Arquivos gerados:")
    print("   • Gráficos de barras para cada questão")
    print("   • Scatter plots comparativos")
    print("   • Heatmaps de diferenças")
    print("   • Matriz de correlação")
    print("   • Distribuição de code smells")
    print("   • Relatório resumido visual")
    print("   • Arquivos CSV com dados detalhados")
    print("\n🎯 Total de visualizações criadas: 20+")

if __name__ == '__main__':
    main()