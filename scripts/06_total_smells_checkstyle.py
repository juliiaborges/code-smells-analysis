import os
import json
import xml.etree.ElementTree as ET
from collections import Counter
import xml.etree.ElementTree as ET

REPORTS_DIR = "../data/checkstyle_reports"
SUMMARIES_DIR = os.path.join(REPORTS_DIR, "summaries")
os.makedirs(SUMMARIES_DIR, exist_ok=True)

def parse_checkstyle_report(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    results = []

    for file_element in root.findall('file'):
        file_name = file_element.get('name')
        file_issues = []

        for error in file_element.findall('.//error'):
            line = error.get('line')
            column = error.get('column', '0')
            severity = error.get('severity')
            message = error.get('message')
            source = error.get('source', '').split('.')[-1]
            if source.endswith('Check'):
                source = source[:-5]
            file_issues.append({
                "line": line,
                "column": column,
                "severity": severity,
                "message": message,
                "rule": source
            })

        results.append({
            "file": file_name,
            "issues": file_issues
        })

    return results

def generate_summary_json(repo_name, detailed_results):
    rule_mapping = {
        "UnusedImports": "Unused Imports",
        "CyclomaticComplexity": "Cyclomatic Complexity",
        "EmptyCatchBlock": "Empty Catch Block",
        "TypeName": "Naming Conventions",
        "ClassFanOutComplexity": "Potential God Class",
        "EmptyStatement": "Empty Control Statement",
        "ClassDataAbstractionCoupling": "Too Many Fields"
    }

    counter = Counter()
    for file_result in detailed_results:
        for issue in file_result.get("issues", []):
            rule = issue.get("rule")
            nice_rule = rule_mapping.get(rule)
            if nice_rule:
                counter[nice_rule] += 1

    total_smells = sum(counter.values())

    summary = {
        "repository": repo_name,
        "code_smells": dict(counter),
        "total_smells": total_smells
    }

    summary_path = os.path.join(SUMMARIES_DIR, f"{repo_name}_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Summary salvo em {summary_path}")

import xml.etree.ElementTree as ET

def main():
    xml_files = [f for f in os.listdir(REPORTS_DIR) if f.endswith("_checkstyle_raw.xml")]

    if not xml_files:
        print("Nenhum arquivo XML encontrado em", REPORTS_DIR)
        return

    print(f"Processando {len(xml_files)} arquivos para gerar resumos...")

    for xml_file in xml_files:
        repo_name = xml_file.replace("_checkstyle_raw.xml", "")
        xml_path = os.path.join(REPORTS_DIR, xml_file)
        try:
            detailed_results = parse_checkstyle_report(xml_path)
        except ET.ParseError:
            print(f"Arquivo XML inválido ou corrompido: {xml_file}, ignorando.")
            continue
        generate_summary_json(repo_name, detailed_results)

if __name__ == "__main__":
    main()
