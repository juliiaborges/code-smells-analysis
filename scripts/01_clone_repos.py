import os
import json
import time
import requests
import subprocess
import logging
from datetime import datetime

# Configurações
GITHUB_TOKEN = "github_token"  # Substitua pela sua chave API GitHub
REPOS_DIR = "../data/repositories"
LOGS_DIR = "../data/clone_logs"
NUM_REPOS_TO_CLONE = 10
START_PAGE = 1  # Modifique para clonar lotes diferentes (1=primeiros 10, 2=próximos 10, etc.)

# Configurar logging
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, f"clone_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Criar diretório para repositórios
os.makedirs(REPOS_DIR, exist_ok=True)

def get_popular_java_repos(page=1, per_page=50):
    """
    Busca os repositórios Java mais populares no GitHub.
    """
    url = "https://api.github.com/search/repositories"
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    params = {
        "q": "language:java stars:>100",
        "sort": "stars",
        "order": "desc",
        "page": page,
        "per_page": per_page
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        repos = []
        for item in data.get("items", []):
            repos.append({
                "owner": item["owner"]["login"],
                "name": item["name"],
                "stars": item["stargazers_count"],
                "url": item["html_url"]
            })
        return repos
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao buscar repositórios: {e}")
        return []

def check_uses_maven_or_gradle(owner, repo):
    """
    Verifica se o repositório usa Maven (pom.xml) ou Gradle (build.gradle ou build.gradle.kts).
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        files = response.json()
        filenames = [file["name"].lower() for file in files]
        if "pom.xml" in filenames:
            return True
        if "build.gradle" in filenames or "build.gradle.kts" in filenames:
            return True
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao verificar Maven/Gradle para {owner}/{repo}: {e}")
        return False

def get_already_cloned_repos():
    cloned_repos = set()

    results_path = os.path.join(LOGS_DIR, "clone_results.json")
    if os.path.exists(results_path):
        try:
            with open(results_path, "r") as f:
                results = json.load(f)
                for repo in results:
                    cloned_repos.add(f"{repo['owner']}_{repo['name']}")
        except json.JSONDecodeError:
            logger.warning("Erro ao ler o arquivo de resultados anteriores.")

    if os.path.exists(REPOS_DIR):
        for dirname in os.listdir(REPOS_DIR):
            if os.path.isdir(os.path.join(REPOS_DIR, dirname)):
                cloned_repos.add(dirname)

    return cloned_repos

def clone_repository(owner, name, url):
    repo_dir = os.path.join(REPOS_DIR, f"{owner}_{name}")
    if os.path.exists(repo_dir):
        return False, f"Repositório {owner}/{name} já existe."

    try:
        logger.info(f"Clonando {owner}/{name}...")
        if GITHUB_TOKEN:
            auth_url = url.replace("https://", f"https://oauth2:{GITHUB_TOKEN}@")
            cmd = ["git", "clone", auth_url, repo_dir]
        else:
            cmd = ["git", "clone", url, repo_dir]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"Erro ao clonar {owner}/{name}: {result.stderr}")
            return False, result.stderr

        logger.info(f"Repositório {owner}/{name} clonado com sucesso.")
        return True, "Clonado com sucesso."
    except Exception as e:
        logger.error(f"Exceção ao clonar {owner}/{name}: {e}")
        return False, str(e)

def main():
    clone_results = []
    cloned_count = 0
    already_cloned = get_already_cloned_repos()
    logger.info(f"Encontrados {len(already_cloned)} repositórios já clonados.")

    current_page = START_PAGE

    while cloned_count < NUM_REPOS_TO_CLONE:
        logger.info(f"Buscando repositórios populares (página {current_page})...")
        repos = get_popular_java_repos(page=current_page, per_page=50)

        if not repos:
            logger.warning(f"Nenhum repositório encontrado na página {current_page}.")
            break

        logger.info(f"Encontrados {len(repos)} repositórios na página {current_page}.")

        for repo in repos:
            if cloned_count >= NUM_REPOS_TO_CLONE:
                break

            owner = repo["owner"]
            name = repo["name"]
            repo_id = f"{owner}_{name}"

            if repo_id in already_cloned:
                logger.info(f"Pulando {owner}/{name} - já foi clonado anteriormente.")
                continue

            if not check_uses_maven_or_gradle(owner, name):
                logger.info(f"Pulando {owner}/{name} - não usa Maven nem Gradle.")
                continue

            success, message = clone_repository(owner, name, repo["url"])

            result = {
                "owner": owner,
                "name": name,
                "success": success,
                "message": message,
                "url": repo["url"],
                "stars": repo["stars"]
            }
            clone_results.append(result)

            if success:
                cloned_count += 1
                logger.info(f"Progresso: {cloned_count}/{NUM_REPOS_TO_CLONE} repositórios clonados.")

            time.sleep(1)

        current_page += 1

    results_file = os.path.join(LOGS_DIR, "clone_results.json")

    previous_results = []
    if os.path.exists(results_file):
        try:
            with open(results_file, "r") as f:
                previous_results = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Erro ao ler resultados anteriores. Criando novo arquivo.")

    all_results = previous_results + clone_results

    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Clonados {cloned_count} novos repositórios.")
    logger.info(f"Resultados salvos em {results_file}")

if __name__ == "__main__":
    main()
