import os
import json
import subprocess
import glob
import time

# Configurações
REPOS_INFO_FILE = "../data/repositories_info.json"
REPOS_DIR = "../data/repositories"
BUILD_LOG_DIR = "../data/build_logs"

# Certifique-se de que o diretório de logs existe
os.makedirs(BUILD_LOG_DIR, exist_ok=True)

def build_maven_project(repo_path, repo_name):
    """Compila um projeto Maven."""
    print(f"Compilando {repo_name}...")
    
    log_file = os.path.join(BUILD_LOG_DIR, f"{repo_name}_build.log")
    
    try:
        # Verificar se o pom.xml existe
        pom_file = os.path.join(repo_path, "pom.xml")
        if not os.path.exists(pom_file):
            print(f"Arquivo pom.xml não encontrado em {repo_path}")
            return False
        
        # Executar o Maven para compilar o projeto e pular os testes
        # -DskipTests para pular a execução de testes, mas compilar as classes de teste
        # -Dmaven.test.skip=true para pular a compilação e execução de testes
        with open(log_file, 'w') as f:
            process = subprocess.run(
                ["mvn", "clean", "compile", "-DskipTests", "-Dmaven.test.skip=true"],
                cwd=repo_path,
                stdout=f,
                stderr=subprocess.STDOUT,
                check=False
            )
        
        if process.returncode != 0:
            print(f"Erro ao compilar {repo_name}. Veja o log para detalhes: {log_file}")
            return False
        
        # Verificar se foram gerados arquivos .class
        target_dir = os.path.join(repo_path, "target", "classes")
        if not os.path.exists(target_dir):
            print(f"Diretório target/classes não encontrado em {repo_path}")
            return False
        
        class_files = glob.glob(f"{target_dir}/**/*.class", recursive=True)
        if not class_files:
            print(f"Nenhum arquivo .class gerado em {repo_path}")
            return False
        
        print(f"Projeto {repo_name} compilado com sucesso! Gerados {len(class_files)} arquivos .class")
        return True
    
    except Exception as e:
        print(f"Erro ao compilar {repo_name}: {e}")
        return False

def main():
    # Carregar informações dos repositórios
    if not os.path.exists(REPOS_INFO_FILE):
        print(f"Arquivo {REPOS_INFO_FILE} não encontrado. Execute o script de clonagem primeiro.")
        return
    
    with open(REPOS_INFO_FILE, 'r') as f:
        repos_info = json.load(f)
    
    # Compilar cada repositório
    build_results = []
    
    for repo in repos_info:
        repo_owner = repo["owner"]
        repo_name = repo["name"]
        repo_path = os.path.join(REPOS_DIR, f"{repo_owner}_{repo_name}")
        
        if not os.path.exists(repo_path):
            print(f"Repositório {repo_owner}/{repo_name} não encontrado em {REPOS_DIR}. Pulando...")
            continue
        
        success = build_maven_project(repo_path, f"{repo_owner}_{repo_name}")
        
        build_results.append({
            "owner": repo_owner,
            "name": repo_name,
            "success": success
        })
    
    # Salvar resultados da compilação
    with open(os.path.join(BUILD_LOG_DIR, "build_results.json"), 'w') as f:
        json.dump(build_results, f, indent=2)
    
    # Resumo
    successful_builds = sum(1 for result in build_results if result["success"])
    print(f"\nResumo da compilação:")
    print(f"- Total de repositórios: {len(build_results)}")
    print(f"- Compilados com sucesso: {successful_builds}")
    print(f"- Falhas na compilação: {len(build_results) - successful_builds}")
    
    print("\nRepositórios compilados com sucesso:")
    for result in build_results:
        if result["success"]:
            print(f"- {result['owner']}/{result['name']}")
    
    print("\nRepositórios com falha na compilação:")
    for result in build_results:
        if not result["success"]:
            print(f"- {result['owner']}/{result['name']}")

if __name__ == "__main__":
    main()