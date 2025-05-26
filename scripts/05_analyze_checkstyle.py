import os
import subprocess

REPOS_DIR = "../data/repositories"
RESULTS_DIR = "../data/checkstyle_reports"
CHECKSTYLE_JAR = "CHECKSTYLE_JAR"
CHECKSTYLE_CONFIG = "../config/checkstyle-config.xml"

os.makedirs(RESULTS_DIR, exist_ok=True)

def run_checkstyle(repo_path, output_file):
    try:
        src_main_path = os.path.join(repo_path, "src", "main", "java")
        target_path = src_main_path if os.path.exists(src_main_path) else repo_path
        cmd = f"java -jar {CHECKSTYLE_JAR} -c {CHECKSTYLE_CONFIG} -f xml -o {output_file} {target_path}"
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar CheckStyle em {repo_path}: {e}")
        return False

def process_repository(repo_folder):
    repo_path = os.path.join(REPOS_DIR, repo_folder)
    print(f"Analisando {repo_folder} com CheckStyle...")

    xml_output = os.path.join(RESULTS_DIR, f"{repo_folder}_checkstyle_raw.xml")

    if run_checkstyle(repo_path, xml_output):
        print(f"Arquivo bruto salvo em {xml_output}")
        return True
    return False

def main():
    if not os.path.exists(REPOS_DIR):
        print(f"O diretório {REPOS_DIR} não existe.")
        return

    repo_folders = [name for name in os.listdir(REPOS_DIR) if os.path.isdir(os.path.join(REPOS_DIR, name))]

    if not repo_folders:
        print(f"Nenhum repositório encontrado em {REPOS_DIR}.")
        return

    print(f"Encontrados {len(repo_folders)} repositórios para análise.")

    for repo_folder in repo_folders:
        process_repository(repo_folder)

if __name__ == "__main__":
    main()
