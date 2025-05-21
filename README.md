## Detalhes dos Scripts

Para ajudar novos desenvolvedores a entender melhor o projeto, aqui está uma explicação detalhada de cada script:

### Script 1: `01_clone_repos.py`

Este script é responsável por clonar automaticamente os repositórios Java mais populares do GitHub.

**O que faz**:
- Busca automaticamente os repositórios Java mais populares no GitHub
- Verifica se o repositório usa Maven (possui arquivo pom.xml)
- Clona os 10 repositórios mais populares que ainda não foram clonados
- Permite clonar em lotes (primeiros 10, próximos 10, etc.)
- Registra o sucesso ou falha de cada clonagem

**Como funciona a clonagem automática**:
- O script usa a API do GitHub para buscar repositórios Java ordenados por número de estrelas
- Filtra apenas os que usam Maven (contém arquivo pom.xml)
- Verifica quais repositórios já foram clonados anteriormente para evitar duplicatas
- Clona os próximos 10 repositórios mais populares que ainda não foram analisados

**Como configurar**:
```python
# Definir o número de repositórios a clonar por execução
NUM_REPOS_TO_CLONE = 10

# Definir seu token do GitHub (necessário para API)
GITHUB_TOKEN = "ghp_seu_token_aqui"

# Para pular para o próximo lote de repositórios, você pode modificar:
START_PAGE = 1  # Aumente este valor para pular repositórios já processados
```

**Exemplo de execução para clonar diferentes lotes**:
```bash
# Primeira execução - clona os 10 primeiros repositórios mais populares
python 01_clone_repos.py

# Segunda execução - modifique START_PAGE para 2 no script e execute novamente
# Isso clonará os próximos 10 repositórios (11-20 mais populares)
python 01_clone_repos.py

# Terceira execução - modifique START_PAGE para 3
# Isso clonará os próximos 10 repositórios (21-30 mais populares)
python 01_clone_repos.py
```

### Script 2: `02_build_repos.py`

Este script é responsável por compilar todos os repositórios clonados.

**O que faz**:
- Tenta compilar cada repositório usando Maven
- Salva os logs de compilação
- Cria um resumo dos resultados da compilação

**Configurações importantes a verificar**:

```python
# Tempo máximo para compilação (em segundos)
# Aumente este valor se tiver repositórios grandes ou uma máquina lenta
COMPILE_TIMEOUT = 1800  # 30 minutos

# Comando de compilação
# Este é o comando padrão, mas alguns repositórios podem precisar de comandos específicos
MAVEN_COMMAND = ["mvn", "clean", "install", "-DskipTests"]
```

**Dicas para compilação bem-sucedida**:
1. Certifique-se de que a versão do Java seja compatível com os repositórios (JDK 11 é geralmente uma boa escolha)
2. Alguns repositórios podem precisar de variáveis de ambiente específicas (JAVA_HOME, etc.)
3. Se um repositório falhar na compilação, você pode tentar executar o comando Maven manualmente para depurar:
   ```bash
   cd data/repositories/dono_repo
   mvn clean install -DskipTests
   ```

### Script 3: `03_analyze_llm.py`

Este script é responsável por analisar code smells em **TODOS** os arquivos Java dos repositórios compilados com sucesso.

**O que faz**:
- Carrega a lista de repositórios compilados com sucesso
- Encontra todos os arquivos Java em cada repositório
-# Projeto de Análise de Code Smells em Repositórios Java

Este projeto realiza uma análise automatizada de code smells em repositórios Java utilizando LLM (Large Language Models). O pipeline completo inclui clonagem de novos repositórios, compilação e análise completa de todos os arquivos Java usando diferentes abordagens de prompting.

## Fluxo de Trabalho Completo

1. **Clone de 10 novos repositórios Java** - Selecione e clone 10 repositórios diferentes dos já existentes
2. **Compilação de todos os repositórios** - Compile cada repositório usando Maven
3. **Verificação dos resultados de compilação** - Confirme quais repositórios foram compilados com sucesso
4. **Análise completa com LLM** - Analise TODOS os arquivos Java de cada repositório (não apenas 10)
5. **Verificação dos resultados** - Examine os relatórios de code smells gerados

## Estrutura do Projeto

```
projeto/
│
├── data/
│   ├── build_logs/          # Logs do processo de compilação
│   │   └── build_results.json   # Resultados da compilação
│   │
│   ├── repositories/        # Repositórios clonados
│   │   └── owner_name/      # Repositórios organizados por owner_name
│   │
│   └── results/            
│       └── llm/             # Resultados das análises de LLM
│           └── owner_name_llm_results.json
│
├── scripts/
│   ├── 01_clone_repos.py    # Script para clonar repositórios
│   ├── 02_build_repos.py    # Script para compilar repositórios
│   └── 03_analyze_llm.py    # Script para análise de code smells com LLM
│
└── requirements.txt         # Dependências do projeto
```

## Requisitos de Sistema

- Python 3.7 ou superior
- Java Development Kit (JDK) 11 ou superior
- Maven para compilação de projetos Java
- Git para clonagem de repositórios
- Espaço em disco suficiente para repositórios e dados de análise (~10GB recomendado)
- Acesso à API da OpenAI com créditos suficientes (para análise de múltiplos repositórios)

## Instalação e Configuração

### Passo 1: Clonar o Projeto

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

### Passo 2: Configurar o Ambiente Virtual (recomendado)

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate
```

### Passo 3: Instalar Dependências

```bash
pip install -r requirements.txt
```

### Passo 4: Configurar Credenciais

1. **Configurar token do GitHub** (para clonar repositórios):
   - Crie um token de acesso pessoal em: https://github.com/settings/tokens
   - Selecione ao menos as permissões: `repo`, `read:packages`
   - Abra o script `01_clone_repos.py` e atualize a variável:
     ```python
     GITHUB_TOKEN = "seu-token-github-aqui"
     ```

2. **Configurar chave da API OpenAI** (para análise LLM):
   - Obtenha uma chave em: https://platform.openai.com/api-keys
   - Abra o script `03_analyze_llm.py` e atualize a variável:
     ```python
     OPENAI_API_KEY = "sua-chave-openai-aqui"
     ```

## Guia de Execução Passo a Passo

### Fase 1: Clonar Automaticamente Repositórios do GitHub

Este passo envolve clonar automaticamente os repositórios Java mais populares do GitHub que usam Maven.

1. **Configure seu token de acesso do GitHub**:
   - Crie um token de acesso pessoal em: https://github.com/settings/tokens
   - Selecione ao menos as permissões: `repo`, `read:packages`
   - Abra o script `01_clone_repos.py` e atualize a variável:
   ```python
   GITHUB_TOKEN = "seu-token-github-aqui"
   ```

2. **Execute o script de clonagem**:
   ```bash
   # Certifique-se de estar na pasta principal do projeto
   cd scripts
   python 01_clone_repos.py
   ```

3. **O que acontece durante a execução**:
   - O script busca automaticamente os repositórios Java mais populares (com mais estrelas)
   - Verifica se cada repositório usa Maven (tem arquivo pom.xml)
   - Clona os 10 primeiros repositórios elegíveis que ainda não foram clonados
   - Os resultados são registrados em `data/clone_logs/clone_results.json`

4. **Para clonar MAIS 10 repositórios**:
   - Quando quiser clonar o próximo lote de 10 repositórios:
   - Edite o script e aumente o valor de `START_PAGE`:
   ```python
   START_PAGE = 2  # Mude para 2 na segunda execução, 3 na terceira, etc.
   ```
   - Execute o script novamente:
   ```bash
   python 01_clone_repos.py
   ```
   - Isso clonará o próximo lote de 10 repositórios elegíveis

5. **Verificação obrigatória**:
   - Confirme que os repositórios foram clonados para `data/repositories/`
   - Cada repositório deve estar em uma pasta com nome `owner_name`
   - Verifique o arquivo de log em `data/clone_logs/clone_results.json`

### Fase 2: Compilar TODOS os Repositórios

Nesta fase, você compilará cada repositório clonado usando Maven.

1. **Instale o Maven (se ainda não estiver instalado)**:
   ```bash
   # Para Ubuntu/Debian
   sudo apt install maven
   
   # Para macOS via Homebrew
   brew install maven
   
   # Para Windows, baixe do site oficial e adicione ao PATH
   # Verifique a instalação com:
   mvn --version
   ```

2. **Execute o script de compilação para todos os repositórios**:
   ```bash
   # Na pasta scripts
   python 02_build_repos.py
   ```

3. **O processo de compilação**:
   - O script executa `mvn clean install -DskipTests` para cada repositório
   - O progresso é exibido no console durante a execução
   - Tempo estimado: 10-30 minutos dependendo do tamanho dos repositórios

4. **Verificação obrigatória dos resultados da compilação**:
   - Abra o arquivo `data/build_logs/build_results.json`
   - Verifique quais repositórios foram compilados com sucesso (`"success": true`)
   - Caso menos de 5 repositórios tenham sido compilados com sucesso:
     1. Verifique os logs de erro em `data/build_logs/`
     2. Tente resolver os problemas (versão do Java, dependências)
     3. Ou substitua os repositórios por outros mais simples
   
   **Exemplo de resultado de compilação bem-sucedida**:
   ```json
   [
     {
       "owner": "primeiro-autor",
       "name": "primeiro-repo",
       "success": true,
       "time_taken": 45.21,
       "log_file": "primeiro-autor_primeiro-repo_build.log"
     },
     // Outros repositórios...
   ]
   ```

### Fase 3: Analisar TODOS os Arquivos Java com LLM

Este passo envolve analisar **TODOS** os arquivos Java de cada repositório compilado com sucesso.

1. **Importante: Modifique o script para analisar todos os arquivos**:
   - Abra `03_analyze_llm.py`
   - Encontre e **REMOVA ou COMENTE** a linha que limita a análise a 10 arquivos:
   ```python
   # REMOVA OU COMENTE esta linha:
   # java_files = java_files[:10]
   ```

2. **Configure sua chave da API OpenAI**:
   - Substitua `"SUA_CHAVE_API_OPENAI_AQUI"` pela sua chave real:
   ```python
   OPENAI_API_KEY = "sk-sua-chave-real-aqui"
   ```
   - **IMPORTANTE**: Certifique-se de ter créditos suficientes na sua conta OpenAI

3. **Execute o script de análise**:
   ```bash
   python 03_analyze_llm.py
   ```

4. **Acompanhamento durante a execução**:
   - O script mostrará o progresso para cada repositório e arquivo
   - O processo é demorado devido ao número de arquivos e chamadas à API
   - Tempo estimado: 1-5 horas dependendo do número de arquivos Java
   - **ATENÇÃO**: O processo pode consumir créditos significativos da API OpenAI

5. **Verificação de resultados**:
   - Para cada repositório compilado com sucesso, você terá um arquivo:
   - `data/results/llm/owner_name_llm_results.json`
   - Cada arquivo contém análises de todos os arquivos Java no repositório
   - A análise inclui os três tipos de prompts: zero-shot, one-shot e calibrado
   
6. **Importante: Estratégia para grandes repositórios**:
   Se tiver muitos arquivos Java e estiver preocupado com o custo da API, você pode:
   - Processar um repositório por vez modificando a função `main()` para selecionar um repositório específico
   - Implementar uma lógica de salvamento incremental para continuar de onde parou em caso de interrupção
   - Usar um modelo mais econômico (como GPT-3.5) para análise preliminar

## Análise Detalhada dos Resultados

Após concluir a análise de todos os repositórios, você terá um conjunto completo de dados sobre code smells. Aqui está como entender e trabalhar com esses resultados:

### Estrutura dos Resultados

Para cada repositório, você terá um arquivo JSON com a seguinte estrutura:

```json
{
  "repository": "autor_repositorio",
  "zero_shot": {
    "caminho/para/Arquivo1.java": "{ \"smells\": [ ... ] }",
    "caminho/para/Arquivo2.java": "{ \"smells\": [ ... ] }",
    "caminho/para/ArquivoN.java": "{ \"smells\": [ ... ] }"
  },
  "one_shot": {
    // Mesma estrutura que zero_shot, com resultados da abordagem one-shot
  },
  "calibrated": {
    // Mesma estrutura que zero_shot, com resultados da abordagem calibrada
  }
}
```

### Como Interpretar os Resultados

Para cada arquivo Java, você terá três análises diferentes (uma para cada tipo de prompt). Cada análise identifica uma lista de code smells com:

- **Nome do code smell** (ex: "Long Method", "God Class")
- **Categoria** (ex: "Bloaters", "Object-Orientation Abusers")
- **Linha ou intervalo de linhas** onde o code smell ocorre
- **Descrição** explicando o problema

### Comparação Entre Abordagens

Um dos objetivos deste projeto é comparar a eficácia das diferentes abordagens de prompt:

1. **Zero-Shot**: Como o LLM performa sem exemplos ou contexto específico?
2. **One-Shot**: Um único exemplo melhora a qualidade da análise?
3. **Calibrado**: Instruções específicas baseadas no SonarQube produzem resultados melhores?

Ao analisar, observe:
- Quais abordagens identificam mais code smells?
- Quais abordagens produzem descrições mais úteis e acionáveis?
- Há diferenças nos tipos de code smells identificados por cada abordagem?

## Solução de Problemas Comuns

### Problemas com o GitHub

**Erro**: "API rate limit exceeded"
- **Solução**: Verifique se seu token tem permissões suficientes ou aguarde uma hora

**Erro**: "Authentication failed"
- **Solução**: Verifique se o token está correto e não expirou

### Problemas de Compilação

**Erro**: "Could not resolve dependencies"
- **Solução**: 
  1. Verifique se o Maven está configurado corretamente
  2. Tente executar manualmente `mvn clean install -DskipTests` no repositório
  3. Alguns repositórios podem precisar de uma versão específica do Java

**Erro**: "Unsupported class file major version"
- **Solução**: O repositório foi compilado com uma versão diferente do Java. Instale a versão correta do JDK.

### Problemas com a API da OpenAI

**Erro**: "Incorrect API key provided"
- **Solução**: Verifique se a chave foi copiada corretamente

**Erro**: "You exceeded your current quota"
- **Solução**: Adicione créditos à sua conta OpenAI ou use uma chave diferente

**Erro**: "Rate limit reached"
- **Solução**: 
  1. Modifique o script para aumentar o tempo de espera entre chamadas:
  ```python
  time.sleep(5)  # Aumente para 5 segundos ou mais
  ```
  2. Ou implemente uma lógica de retry com backoff exponencial

## Exemplos de Comandos Completos

Aqui está o fluxo completo de comandos para executar o projeto do início ao fim:

```bash
# 1. Clone o repositório do projeto
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio

# 2. Configure o ambiente virtual
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as credenciais nos scripts
# Edite 01_clone_repos.py e 03_analyze_llm.py para adicionar tokens/chaves

# 5. Adicione 10 novos repositórios em 01_clone_repos.py
# Edite a lista REPOSITORIES no arquivo

# 6. Execute o script de clonagem
cd scripts
python 01_clone_repos.py

# 7. Verifique se os repositórios foram clonados
ls -la ../data/repositories

# 8. Compile os repositórios
python 02_build_repos.py

# 9. Verifique os resultados da compilação
cat ../data/build_logs/build_results.json

# 10. Modifique 03_analyze_llm.py para analisar TODOS os arquivos
# Comente ou remova a linha: java_files = java_files[:10]

# 11. Execute a análise de code smells
python 03_analyze_llm.py

# 12. Verifique os resultados
ls -la ../data/results/llm
```

## Dicas Importantes

1. **Planejamento de Tempo**: O processo completo pode levar várias horas. Planeje adequadamente.

2. **Custos da API**: Analisar todos os arquivos Java de múltiplos repositórios pode gerar custos significativos com a API da OpenAI. Faça uma estimativa antes de começar:
   - Média de ~100-300 arquivos Java por repositório
   - 3 chamadas de API por arquivo (uma para cada abordagem)
   - Custo aproximado por chamada: ~$0.03 (GPT-4)
   - Estimativa total: $90-$270 para 10 repositórios completos

3. **Execução por Etapas**: Se preferir, faça a análise em lotes:
   - Modifique o script para analisar um repositório por vez
   - Ou limite a quantidade de arquivos analisados inicialmente para testar

4. **Backup dos Resultados**: Faça backup regular dos resultados parciais:
   ```bash
   # Execute isso periodicamente durante o processo
   cp -r data/results/llm data/results/llm_backup_$(date +%Y%m%d_%H%M%S)
   ```

## Exemplos de Uso

### Exemplo 1: Analisar um Repositório Específico

Para focar em um único repositório, edite o arquivo `01_clone_repos.py`:

```python
REPOSITORIES = [
    {"owner": "seu-alvo", "name": "repositorio-alvo"}
]
```

E execute os três scripts em sequência.

### Exemplo 2: Comparar Resultados com SonarQube

1. Execute uma análise do SonarQube nos mesmos repositórios
2. Compare os resultados em `data/results/llm/` com os resultados do SonarQube
3. Identifique quais abordagens detectam mais code smells relevantes

## Monitoramento de Uso da API

O script `03_analyze_llm.py` faz várias chamadas à API da OpenAI, o que pode gerar custos. Monitore seu uso:

1. Cada arquivo Java analisado requer 3 chamadas à API (uma para cada tipo de análise)
2. O script adiciona um atraso de 2 segundos entre as chamadas para evitar limites de taxa
3. Para 10 arquivos em um repositório, serão 30 chamadas à API

## Contribuindo

Sinta-se à vontade para contribuir para este projeto:

1. Faça um fork do repositório
2. Crie um branch para sua feature (`git checkout -b feature/nova-feature`)
3. Faça commit das suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Faça push para o branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

[Incluir informações de licença aqui]

## Próximos Passos

Algumas ideias para extender o projeto:

1. Adicionar análises comparativas entre os resultados do LLM e do SonarQube
2. Implementar visualizações dos code smells detectados
3. Criar um painel de controle para monitorar a qualidade dos repositórios
4. Adicionar suporte para outras linguagens além de Java
5. Implementar detecção automática de falsos positivos