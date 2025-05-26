import os
import subprocess
import logging
from datetime import datetime

REPOS_DIR = "../data/repositories"   
REPORTS_DIR = "../data/pmd_reports"  
PMD_CMD = "pmd"  # Ajuste o PATH do comando PMD conforme necessário
RULESET = "rulesets/custom_ruleset.xml"
LANGUAGE = "java"
REPORT_FORMAT = "csv"  

# Configuração do logging
os.makedirs(REPORTS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(REPORTS_DIR, f"pmd_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_pmd_on_repo(repo_path, repo_name):
    report_file = os.path.join(REPORTS_DIR, f"{repo_name}_pmd_report.{REPORT_FORMAT}")

    cmd = [
        PMD_CMD,
        "check",
        "-d", repo_path,
        "-R", RULESET,
        "-f", REPORT_FORMAT,
        "--force-language=java",  
        "-r", report_file
    ]

    logger.info(f"Rodando PMD no repositório {repo_name}...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"PMD executado com sucesso no repositório {repo_name}. Relatório salvo em {report_file}")
            return True
        else:
            logger.error(f"Erro ao rodar PMD no {repo_name}: {result.stderr}")
            # Se for erro de memória, escreva mensagem no CSV
            if "OutOfMemoryError" in result.stderr:
                with open(report_file, "w", encoding="utf-8") as f:
                    f.write("PMD_ERROR: OutOfMemoryError\n")
            return False
    except Exception as e:
        logger.error(f"Exceção ao rodar PMD no {repo_name}: {e}")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"PMD_ERROR: {e}\n")
        return False

def main():
    repos = [d for d in os.listdir(REPOS_DIR) if os.path.isdir(os.path.join(REPOS_DIR, d))]

    logger.info(f"Encontrados {len(repos)} repositórios para analisar com PMD.")

    for repo_name in repos:
        repo_path = os.path.join(REPOS_DIR, repo_name)
        run_pmd_on_repo(repo_path, repo_name)

if __name__ == "__main__":
    main()