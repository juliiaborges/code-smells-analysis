import os
import json
import subprocess
import requests
import time

# Configurações
OUTPUT_DIR = "../data/repositories"
GITHUB_TOKEN = "SEU_TOKEN_AQUI"  # Substitua pelo seu token GitHub
REPOS_INFO_FILE = "../data/repositories_info.json"
NUM_REPOS = 10  # Número de repositórios a serem clonados

# Certifique-se de que o diretório de saída existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

def search_maven_repositories():
    """Busca os repositórios Java que usam Maven mais populares no GitHub."""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Consulta para encontrar repositórios Java populares, não-forks, com Maven
    query = "language:java stars:>500 fork:false filename:pom.xml"
    
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={NUM_REPOS}"
    
    print(f"Buscando repositórios com a query: {query}")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Erro na API do GitHub: {response.status_code}")
        print(response.json())
        return []
    
    repositories = response.json()["items"]
    
    filtered_repos = []
    for repo in repositories:
        repo_name = repo["name"]
        repo_owner = repo["owner"]["login"]
        repo_url = repo["html_url"]
        
        # Verificar conteúdo do repositório para confirmar pom.xml
        contents_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
        contents_response = requests.get(contents_url, headers=headers)
        
        if contents_response.status_code != 200:
            print(f"Erro ao buscar conteúdo de {repo_name}: {contents_response.status_code}")
            continue
        
        contents = contents_response.json()
        file_names = [item["name"] for item in contents if item["type"] == "file"]
        
        if "pom.xml" in file_names:
            filtered_repos.append({
                "name": repo_name,
                "owner": repo_owner,
                "url": repo_url,
                "stars": repo["stargazers_count"],
                "clone_url": repo["clone_url"],
                "description": repo["description"]
            })
            print(f"Repositório qualificado: {repo_owner}/{repo_name} com {repo['stargazers_count']} estrelas")
        
    print(f"Total de repositórios qualificados: {len(filtered_repos)}")
    return filtered_repos[:NUM_REPOS]  # Limitar aos primeiros NUM_REPOS repositórios

def clone_repositories(repositories):
    """Clona os repositórios para o diretório local."""
    for repo in repositories:
        repo_name = repo["name"]
        repo_owner = repo["owner"]
        clone_url = repo["clone_url"]
        output_path = os.path.join(OUTPUT_DIR, f"{repo_owner}_{repo_name}")
        
        # Pular se o repositório já foi clonado
        if os.path.exists(output_path):
            print(f"Repositório {repo_owner}/{repo_name} já existe. Pulando...")
            continue
        
        print(f"Clonando {repo_owner}/{repo_name}...")
        
        try:
            subprocess.run(["git", "clone", clone_url, output_path], check=True)
            print(f"Repositório {repo_owner}/{repo_name} clonado com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao clonar {repo_owner}/{repo_name}: {e}")

def main():
    print("Buscando repositórios Java com Maven populares no GitHub...")
    repositories = search_maven_repositories()
    
    if not repositories:
        print("Nenhum repositório encontrado. Verifique o token do GitHub e tente novamente.")
        return
    
    print(f"Encontrados {len(repositories)} repositórios qualificados.")
    
    # Salvar informações dos repositórios para uso posterior
    with open(REPOS_INFO_FILE, "w") as f:
        json.dump(repositories, f, indent=2)
    
    print(f"Informações dos repositórios salvas em {REPOS_INFO_FILE}")
    
    # Clonar os repositórios
    clone_repositories(repositories)
    
    print("Processo de clonagem concluído!")

if __name__ == "__main__":
    main()