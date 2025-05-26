import csv
import json
import os

# Mapeia os nomes exatos que queremos contar
TARGET_SMELLS = {
    "EmptyCatchBlock": "Empty Catch Block",
    "UnusedImports": "Unnecessary Import (Unused Imports)",
    "UnusedLocalVariable": "Unnecessary Local Before Return (Unused Local Variables)",
    "CyclomaticComplexity": "Cyclomatic Complexity",
    "GodClass": "God Class",
    "ClassNamingConventions": "Class Naming Conventions",
    "EmptyIfStmt": "Empty Control Statement",
    "TooManyFields": "Too Many Fields",
    "TooManyMethods": "Too Many Methods"
}

def process_pmd_csv(file_path, repository_name):
    smell_counts = {name: 0 for name in TARGET_SMELLS.values()}
    total_smells = 0

    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rule = row['Rule']
            if rule in TARGET_SMELLS:
                smell_label = TARGET_SMELLS[rule]
                smell_counts[smell_label] += 1
                total_smells += 1

    result = {
        "repository": repository_name,
        "code_smells": smell_counts,
        "total_smells": total_smells
    }

    return result

if __name__ == "__main__":
    reports_dir = "../data/pmd_reports"
    summaries_dir = os.path.join(reports_dir, "summaries")
    os.makedirs(summaries_dir, exist_ok=True)  

    for filename in os.listdir(reports_dir):
        if filename.endswith(".csv"):
            csv_file = os.path.join(reports_dir, filename)
            with open(csv_file, encoding="utf-8") as f:
                first_line = f.readline()
                if first_line.startswith("PMD_ERROR"):
                    print(f"Arquivo {filename} contém erro PMD, ignorando sumarização.")
                    continue
            repository_name = filename.replace("_pmd_report.csv", "")
            summary = process_pmd_csv(csv_file, repository_name)

            output_file = os.path.join(summaries_dir, f"{repository_name}_summary.json")
            with open(output_file, "w", encoding="utf-8") as jsonfile:
                json.dump(summary, jsonfile, indent=2, ensure_ascii=False)

            print(f"Resumo salvo em {output_file}")