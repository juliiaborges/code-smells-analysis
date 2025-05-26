# Code Smells Analysis - Reprodutibilidade

Este projeto automatiza a análise de code smells em projetos Java populares do GitHub usando o PMD, CheckStyle e Chat-GPT.

## Pré-requisitos

- **Python 3.8+** instalado
- **PMD 7.x** instalado ([download aqui](https://pmd.github.io/))
- **Checkstyle** instalado ([download aqui](https://checkstyle.org/))
- **Token do GitHub** válido (para clonar repositórios)
- Recomenda-se ambiente Windows (ajuste caminhos se usar Linux/Mac)

## 1. Clonando os repositórios

O script `01_clone_repos.py` busca e clona repositórios Java populares que usam Maven ou Gradle.

```bash
python scripts/01_clone_repos.py
```

- Os repositórios serão clonados na pasta `data/repositories`.
- O token do GitHub deve ser informado na variável `GITHUB_TOKEN` no início do script.

## 2. Rodando o PMD nos repositórios

O script `02_analyze_pmd.py` executa o PMD em cada repositório clonado e salva os relatórios CSV.

Antes de rodar, ajuste a variável `PMD_CMD` no início do script para o caminho do seu `pmd.bat` (exemplo: `C:\pmd\pmd-bin-7.13.0\bin\pmd.bat`).

```bash
python scripts/02_analyze_pmd.py
```

- Os relatórios serão salvos em `data/pmd_reports`.
- Se ocorrer erro de memória, o arquivo CSV terá uma mensagem de erro e será ignorado na próxima etapa.

## 3. Gerando sumarização dos code smells (PMD)

O script `03_total_smells_pmd.py` lê todos os relatórios CSV válidos e gera um resumo em JSON para cada repositório.

```bash
python scripts/03_total_smells_pmd.py
```

- Os arquivos de resumo serão salvos em `data/pmd_reports/summaries`.

---

## 4. Rodando o Checkstyle nos repositórios

O script `05_analyze_checkstyle.py` executa o Checkstyle em cada repositório clonado e salva os relatórios XML.

Antes de rodar, ajuste a variável `CHECKSTYLE_JAR` no início do script para o caminho do seu arquivo `.jar` do Checkstyle (exemplo: `C:\checkstyle\checkstyle-10.23.1-all.jar`).

```bash
python scripts/05_analyze_checkstyle.py
```

- Os relatórios serão salvos em `data/checkstyle_reports`.

## 5. Gerando sumarização dos code smells (Checkstyle)

O script `06_total_smells_checkstyle.py` lê todos os relatórios XML gerados pelo Checkstyle e gera um resumo em JSON para cada repositório.

```bash
python scripts/06_total_smells_checkstyle.py
```

- Os arquivos de resumo serão salvos em `data/checkstyle_reports/summaries`.

---

## Observações

- Se algum relatório CSV do PMD contiver a mensagem `PMD_ERROR`, ele será ignorado na sumarização.
- Os logs detalhados de cada etapa são salvos nas pastas `data/clone_logs`, `data/pmd_reports` e `data/checkstyle_reports`.
- Execute cada script separadamente e aguarde a conclusão antes de passar para o próximo.

---