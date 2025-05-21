import os
import json
import subprocess
import glob
import xml.etree.ElementTree as ET

# Configurações
BUILD_RESULTS_FILE = "../data/build_logs/build_results.json"
REPOS_DIR = "../data/repositories"
RESULTS_DIR = "../data/results/checkstyle"
CHECKSTYLE_JAR = "../config/checkstyle-10.3-all.jar"
CHECKSTYLE_CONFIG = "../config/checkstyle-config.xml"

# Certifique-se de que o diretório de resultados existe
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_checkstyle(repo_path, output_file):
    """Executa o CheckStyle no repositório."""
    try:
        # Encontrar diretório src/main/java
        src_main_path = os.path.join(repo_path, "src", "main", "java")
        if not os.path.exists(src_main_path):
            print(f"Diretório src/main/java não encontrado em {repo_path}")
            # Tentar encontrar arquivos Java em qualquer lugar do repositório
            java_files = glob.glob(f"{repo_path}/**/*.java", recursive=True)
        else:
            java_files = glob.glob(f"{src_main_path}/**/*.java", recursive=True)
        
        if not java_files:
            print(f"Nenhum arquivo Java encontrado em {repo_path}")
            return False
        
        # Limitar a 100 arquivos para evitar problemas com linhas de comando muito longas
        java_files = java_files[:100]
        
        # Formatar a lista de arquivos para o comando
        files_list = " ".join(java_files)
        
        # Preparar o comando
        cmd = f"java -jar {CHECKSTYLE_JAR} -c {CHECKSTYLE_CONFIG} -f xml -o {output_file} {files_list}"
        
        # Executar o CheckStyle
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar CheckStyle: {e}")
        return False

def parse_checkstyle_results(xml_file):
    """Analisa o arquivo XML de resultados do CheckStyle."""
    results = []
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        for file_element in root.findall('.//file'):
            file_path = file_element.get('name')
            file_results = []
            
            for error in file_element.findall('.//error'):
                line = error.get('line')
                column = error.get('column', '0')
                severity = error.get('severity')
                message = error.get('message')
                source = error.get('source', '').split('.')[-1]  # Último componente do nome da regra
                
                file_results.append({
                    "line": line,
                    "column": column,
                    "severity": severity,
                    "message": message,
                    "rule": source
                })
            
            if file_results:
                results.append({
                    "file": file_path,
                    "issues": file_results
                })
    except Exception as e:
        print(f"Erro ao analisar resultados do CheckStyle: {e}")
    
    return results

def process_repository(repo_owner, repo_name):
    """Processa um repositório com CheckStyle."""
    repo_path = os.path.join(REPOS_DIR, f"{repo_owner}_{repo_name}")
    full_repo_name = f"{repo_owner}_{repo_name}"
    
    print(f"Analisando {full_repo_name} com CheckStyle...")
    
    # Definir arquivo de saída para os resultados XML brutos
    xml_output = os.path.join(RESULTS_DIR, f"{full_repo_name}_checkstyle_raw.xml")
    
    # Executar o CheckStyle
    if run_checkstyle(repo_path, xml_output):
        print(f"Análise com CheckStyle concluída para {full_repo_name}")
        
        # Analisar os resultados
        results = parse_checkstyle_results(xml_output)
        
        # Salvar resultados em formato JSON
        json_output = os.path.join(RESULTS_DIR, f"{full_repo_name}_checkstyle_results.json")
        with open(json_output, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Resultados salvos em {json_output}")
        return True
    
    return False

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