# Projeto de Análise de Code Smells em Repositórios Java

Este projeto realiza uma análise automatizada de code smells em repositórios Java utilizando LLM (Large Language Models). O pipeline completo inclui clonagem de repositórios, compilação, análise com diferentes abordagens e geração de relatórios.

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
│       ├── llm/             # Resultados das análises de LLM
│       │   └── owner_name_llm_results.json
│       └── sonarqube/       # Resultados das análises do SonarQube
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
- Espaço em disco suficiente para repositórios e dados de análise

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

## Guia de Execução Completo

### Fase 1: Clonar Repositórios do GitHub

Este script busca e clona repositórios Java populares do GitHub para análise.

1. **Configure a lista de repositórios** (opcional):
   - Edite o script `01_clone_repos.py` para adicionar ou modificar a lista de repositórios
   - Ou mantenha a configuração padrão para clonar os repositórios pré-selecionados

2. **Execute o script de clonagem**:
   ```bash
   cd scripts
   python 01_clone_repos.py
   ```

3. **Verificação**:
   - Os repositórios serão clonados para a pasta `data/repositories/`
   - Um log será gerado em `data/clone_logs/clone_results.json`

### Fase 2: Compilar os Repositórios

Este script tenta compilar cada repositório Java clonado usando Maven.

1. **Verifique se o Maven está instalado**:
   ```bash
   mvn --version
   ```

2. **Execute o script de compilação**:
   ```bash
   python 02_build_repos.py
   ```

3. **O que acontece durante a execução**:
   - Cada repositório é compilado usando o comando `mvn clean install`
   - Testes são pulados com `-DskipTests` para acelerar o processo
   - Logs detalhados são salvos em `data/build_logs/`
   - Um resumo da compilação é criado em `data/build_logs/build_results.json`

4. **Verificação**:
   - Cheque o arquivo `build_results.json` para ver quais repositórios foram compilados com sucesso
   - Apenas repositórios compilados serão usados nas próximas etapas

### Fase 3: Analisar Code Smells com LLM

Este script analisa os arquivos Java dos repositórios compilados com êxito, utilizando GPT-4 para identificar code smells.

1. **Certifique-se de que sua chave da OpenAI está configurada**:
   - Edite o arquivo `03_analyze_llm.py`
   - Substitua `"SUA_CHAVE_API_OPENAI_AQUI"` pela sua chave real:
     ```python
     OPENAI_API_KEY = "sk-sua-chave-real-aqui"
     ```

2. **Execute o script de análise**:
   ```bash
   python 03_analyze_llm.py
   ```

3. **O que acontece durante a execução**:
   - O script carrega a lista de repositórios compilados com sucesso
   - Para cada repositório, ele encontra arquivos Java (limitado aos 10 primeiros)
   - Cada arquivo é analisado usando três abordagens diferentes:
     - **Zero-Shot**: Análise sem exemplos prévios
     - **One-Shot**: Análise com um exemplo para calibração
     - **Calibrado**: Análise baseada em regras do SonarQube
   - Os resultados são salvos em formato JSON

4. **Verificação**:
   - Os resultados estarão disponíveis em `data/results/llm/owner_name_llm_results.json`
   - Cada arquivo contém os code smells identificados nas três abordagens

## Tipos de Análise LLM

### 1. Zero-Shot
Analisa o código sem exemplos prévios, baseando-se apenas no conhecimento geral do modelo sobre code smells.

**Exemplo de prompt:**
```
Analise o seguinte código Java e identifique todos os code smells. 
Liste cada code smell encontrado com o nome, a linha onde ocorre e uma breve descrição do problema.
Classifique os code smells usando categorias padrão como Bloaters, Object-Orientation Abusers, 
Change Preventers, Dispensables, Couplers, etc.
```

### 2. One-Shot
Fornece um exemplo de análise para ajudar o modelo a calibrar seu formato de resposta.

**Exemplo de uso:**
- Inclui um exemplo de como identificar "Long Method", "Data Class" e "Feature Envy"
- Ajuda o modelo a entender o formato de saída esperado e os tipos de code smells a procurar

### 3. Calibrado
Utiliza um prompt baseado em regras específicas semelhantes às do SonarQube.

**Métricas analisadas:**
- Complexidade ciclomática
- Tamanho de métodos e classes
- Duplicação de código
- Nomes descritivos
- Comentários adequados
- Número de parâmetros
- Código morto
- Acoplamento e coesão

## Formato do JSON de Resultados

```json
{
  "repository": "owner_name",
  "zero_shot": {
    "caminho/do/arquivo.java": {
      "smells": [
        {
          "name": "Long Method",
          "category": "Bloaters",
          "line": "10-45",
          "description": "O método processData é muito longo com 35 linhas"
        },
        // outros code smells...
      ]
    }
  },
  "one_shot": {
    // resultados da análise one-shot...
  },
  "calibrated": {
    // resultados da análise calibrada...
  }
}
```

## Personalização e Extensão

### Modificar a Lista de Repositórios

Edite o arquivo `01_clone_repos.py` para alterar os repositórios-alvo:

```python
REPOSITORIES = [
    {"owner": "spring-projects", "name": "spring-boot"},
    {"owner": "elastic", "name": "elasticsearch"},
    # Adicione seus repositórios aqui...
]
```

### Ajustar Prompts de Análise

Para personalizar a análise, modifique as funções no arquivo `03_analyze_llm.py`:

- `analyze_with_zero_shot()`
- `analyze_with_one_shot()`
- `analyze_with_calibrated_prompt()`

### Aumentar o Número de Arquivos Analisados

Por padrão, apenas os 10 primeiros arquivos Java de cada repositório são analisados para controlar custos. Para analisar mais arquivos, modifique a linha:

```python
# Limitar a 10 arquivos para evitar custos excessivos com a API
java_files = java_files[:10]
```

## Solução de Problemas

### Problemas de Clonagem

**Sintoma**: Falha ao clonar repositórios.

**Soluções**:
- Verifique se o token do GitHub é válido e tem permissões suficientes
- Certifique-se de que a URL do repositório está correta
- Verifique sua conexão com a internet

### Problemas de Compilação

**Sintoma**: Muitos repositórios falham na compilação.

**Soluções**:
- Verifique se o JDK está instalado e configurado corretamente
- Certifique-se de que o Maven está instalado e acessível no PATH
- Verifique se há requisitos específicos de compilação nos READMEs dos repositórios

### Erros na API da OpenAI

**Sintoma**: Falhas nas chamadas à API da OpenAI.

**Soluções**:
- Confirme se a chave da API é válida e tem créditos disponíveis
- Verifique se você tem acesso ao modelo GPT-4
- Aumente o tempo de espera entre as chamadas para evitar limites de taxa

### Problemas de Memória

**Sintoma**: Erros de memória ao processar repositórios grandes.

**Soluções**:
- Use repositórios menores para análise
- Reduza o número de arquivos processados de uma vez
- Aumente a memória disponível para o Python

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