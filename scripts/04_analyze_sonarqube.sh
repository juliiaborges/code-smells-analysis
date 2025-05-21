#!/bin/bash

# Configurações
REPOS_DIR="../data/repositories"
BUILD_LOG_DIR="../data/build_logs"
RESULTS_DIR="../data/results/sonarqube"
SONAR_URL="http://localhost:9000"
SONAR_TOKEN="SEU_TOKEN_AQUI"  # Substitua pelo seu token do SonarQube

# Certifique-se de que o diretório de resultados existe
mkdir -p $RESULTS_DIR

# Carregar informações dos repositórios compilados com sucesso
BUILD_RESULTS="$BUILD_LOG_DIR/build_results.json"

if [ ! -f "$BUILD_RESULTS" ]; then
    echo "Arquivo $BUILD_RESULTS não encontrado. Execute o script de compilação primeiro."
    exit 1
fi

# Função para verificar se o SonarQube está em execução
check_sonarqube() {
    echo "Verificando se o SonarQube está em execução..."
    if curl -s -f -u "$SONAR_TOKEN:" "$SONAR_URL/api/system/status" > /dev/null; then
        echo "SonarQube está em execução!"
        return 0
    else
        echo "SonarQube não está acessível. Verifique se está em execução em $SONAR_URL"
        return 1
    fi
}

# Função para analisar um repositório com SonarQube
analyze_repo() {
    local repo_owner=$1
    local repo_name=$2
    local repo_path="$REPOS_DIR/${repo_owner}_${repo_name}"
    local project_key="${repo_owner}_${repo_name}"
    
    echo "Analisando $repo_owner/$repo_name com SonarQube..."
    
    # Criar arquivo sonar-project.properties
    cat > "$repo_path/sonar-project.properties" << EOF
sonar.projectKey=$project_key
sonar.projectName=$repo_name
sonar.projectVersion=1.0
sonar.sources=src/main
sonar.java.binaries=target/classes
sonar.sourceEncoding=UTF-8
sonar.java.source=8
EOF
    
    # Executar SonarQube Scanner
    cd "$repo_path" && \
    sonar-scanner \
        -Dsonar.host.url=$SONAR_URL \
        -Dsonar.login=$SONAR_TOKEN
    
    local status=$?
    
    if [ $status -eq 0 ]; then
        echo "Análise com SonarQube concluída para $repo_owner/$repo_name"
        
        # Extrair resultados da API do SonarQube
        echo "Extraindo resultados da API do SonarQube..."
        curl -s -u "$SONAR_TOKEN:" "$SONAR_URL/api/issues/search?componentKeys=$project_key&types=CODE_SMELL&ps=500" \
            > "$RESULTS_DIR/${repo_owner}_${repo_name}_sonar_results.json"
        
        echo "Resultados salvos em $RESULTS_DIR/${repo_owner}_${repo_name}_sonar_results.json"
        return 0
    else
        echo "Erro na análise com SonarQube para $repo_owner/$repo_name"
        return 1
    fi
}

# Verificar se o SonarQube está em execução
check_sonarqube || exit 1

# Processar cada repositório compilado com sucesso
jq -c '.[] | select(.success == true)' "$BUILD_RESULTS" | while read -r repo; do
    owner=$(echo $repo | jq -r '.owner')
    name=$(echo $repo | jq -r '.name')
    
    analyze_repo "$owner" "$name"
    
    # Pausa para não sobrecarregar o SonarQube
    sleep 5
done

echo "Análise com SonarQube concluída para todos os repositórios compilados com sucesso!"