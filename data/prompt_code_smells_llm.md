# Prompt para Análise de Code Smells Java com LLM

## Zero-Shot

Analise o seguinte código Java e informe o número de ocorrências dos seguintes **code smells**:

- Empty Catch Block  
- Unnecessary Import (Unused Imports)  
- Unnecessary Local Before Return (Unused Local Variables)  
- Cyclomatic Complexity  
- God Class  
- Class Naming Conventions  
- Empty Control Statement  
- Too Many Fields  
- Too Many Methods  

Responda no seguinte formato **JSON**:

```json
{
  "repository": "<nome_repositorio>",
  "code_smells": {
    "Empty Catch Block": <int>,
    "Unnecessary Import (Unused Imports)": <int>,
    "Unnecessary Local Before Return (Unused Local Variables)": <int>,
    "Cyclomatic Complexity": <int>,
    "God Class": <int>,
    "Class Naming Conventions": <int>,
    "Empty Control Statement": <int>,
    "Too Many Fields": <int>,
    "Too Many Methods": <int>
  },
  "total_smells": <int>
}
```

## One-Shot

Você é um especialista em detecção de code smells em código Java. Analise o repositório, acessando o link do GitHub fornecido, e conte quantos code smells de cada tipo você encontra, considerando apenas os seguintes tipos:

- Empty Catch Block  
- Unnecessary Import (Unused Imports)  
- Unnecessary Local Before Return (Unused Local Variables)  
- Cyclomatic Complexity  
- God Class  
- Class Naming Conventions  
- Empty Control Statement  
- Too Many Fields  
- Too Many Methods  

Retorne **APENAS** um objeto JSON com a seguinte estrutura, sem texto adicional:

```json
{
  "repository": "NOME_DO_REPOSITORIO",
  "code_smells": {
    "Empty Catch Block": QUANTIDADE,
    "Unnecessary Import (Unused Imports)": QUANTIDADE,
    "Unnecessary Local Before Return (Unused Local Variables)": QUANTIDADE,
    "Cyclomatic Complexity": QUANTIDADE,
    "God Class": QUANTIDADE,
    "Class Naming Conventions": QUANTIDADE,
    "Empty Control Statement": QUANTIDADE,
    "Too Many Fields": QUANTIDADE,
    "Too Many Methods": QUANTIDADE
  },
  "total_smells": QUANTIDADE_TOTAL
}
```

Importante: foque apenas em code smells estruturais significativos que afetam a manutenibilidade do código. Ignore problemas superficiais como estilo, formatação ou documentação.

### Exemplo

**Entrada (link do repositório):**  
https://github.com/dbeaver/dbeaver.git

**Saída esperada:**

```json
{
  "repository": "dbeaver_dbeaver",
  "code_smells": {
    "Empty Catch Block": 193,
    "Unnecessary Import (Unused Imports)": 0,
    "Unnecessary Local Before Return (Unused Local Variables)": 0,
    "Cyclomatic Complexity": 1659,
    "God Class": 397,
    "Class Naming Conventions": 3,
    "Empty Control Statement": 0,
    "Too Many Fields": 78,
    "Too Many Methods": 457
  },
  "total_smells": 2787
}
```

Agora, faça o mesmo para o repositório abaixo:

https://github.com/NOVO_REPOSITORIO_AQUI.git

## Especializado

Você é um especialista em análise de código Java. Sua tarefa é analisar o repositório fornecido e identificar a ocorrência dos seguintes **code smells estruturais**, usando as regras abaixo como referência:

### Code Smells a serem detectados e regras:

- **Empty Catch Block**: blocos `catch` vazios devem ser reportados.  
- **Unnecessary Import (Unused Imports)**: imports não utilizados devem ser contados; ignore se forem apenas para Javadoc.  
- **Unnecessary Local Before Return (Unused Local Variables)**: conte variáveis locais declaradas mas nunca utilizadas (prioridade 3).  
- **Cyclomatic Complexity**: conte métodos que tenham complexidade ciclomática maior que 10.  
- **God Class**: considere qualquer classe que ultrapasse **ao menos um** dos seguintes limites:  
  - Mais de 7 classes acopladas  
  - Complexidade de saída maior que 20  
  - Mais de 100 métodos  
  - Mais de 30 atributos  
  - NPathComplexity maior que 200  
- **Class Naming Conventions**: nomes de classes devem seguir o padrão `^[A-Z][a-zA-Z0-9]*$`.  
- **Empty Control Statement**: `if`, `while` ou `for` com blocos vazios devem ser reportados.  
- **Too Many Fields**: classes com mais de 30 atributos devem ser contadas.  
- **Too Many Methods**: classes com mais de 100 métodos devem ser contadas.  

### Instruções de saída:

- A resposta deve ser **apenas um objeto JSON**.  
- Use a estrutura abaixo e preencha com as quantidades encontradas.  
- **Não** inclua explicações, comentários ou qualquer outro texto fora do JSON.  

```json
{
  "repository": "owner_repositorio",
  "code_smells": {
    "Empty Catch Block": QUANTIDADE,
    "Unnecessary Import (Unused Imports)": QUANTIDADE,
    "Unnecessary Local Before Return (Unused Local Variables)": QUANTIDADE,
    "Cyclomatic Complexity": QUANTIDADE,
    "God Class": QUANTIDADE,
    "Class Naming Conventions": QUANTIDADE,
    "Empty Control Statement": QUANTIDADE,
    "Too Many Fields": QUANTIDADE,
    "Too Many Methods": QUANTIDADE
  },
  "total_smells": QUANTIDADE_TOTAL
}
```

### Exemplo de entrada:

https://github.com/dbeaver/dbeaver.git

### Exemplo de saída (valores simulados):

```json
{
  "repository": "dbeaver_dbeaver",
  "code_smells": {
    "Empty Catch Block": 193,
    "Unnecessary Import (Unused Imports)": 0,
    "Unnecessary Local Before Return (Unused Local Variables)": 0,
    "Cyclomatic Complexity": 1659,
    "God Class": 397,
    "Class Naming Conventions": 3,
    "Empty Control Statement": 0,
    "Too Many Fields": 78,
    "Too Many Methods": 457
  },
  "total_smells": 2787
}
```

Agora, aplique a mesma análise ao repositório abaixo:

https://github.com/NOVO_REPOSITORIO_AQUI.git