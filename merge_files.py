import os
import re
import argparse
from pathlib import Path

def merge_python_files(source_dir, output_file, exclude_files):
    source_path = Path(source_dir)
    all_imports = set()
    all_content = []
    all_names = []

    # Regex pour capturer les imports, les classes et __all__
    import_re = re.compile(r'^(from\s+\S+\s+import\s+.+|import\s+.+)$')
    class_re = re.compile(r'^class\s+(\w+)')
    all_var_re = re.compile(r'^__all__\s*=\s*\[(.*?)\]', re.DOTALL)

    print(f"--- Analyse du dossier : {source_path} ---")

    for file_path in sorted(source_path.glob("*.py")):
        if file_path.name in exclude_files:
            continue
        
        print(f"Traitement de : {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

            # 1. Extraction et filtrage des imports
            lines = content.splitlines()
            body_lines = []
            
            for line in lines:
                import_match = import_re.match(line)
                if import_match:
                    imp = import_match.group(1)
                    # Exclure les imports relatifs (commençant par .)
                    # et les imports pointant vers le même dossier (models.)
                    if not imp.startswith("from .") and "models." not in imp:
                        all_imports.add(imp)
                elif line.startswith("__all__") or "# ---" in line:
                    continue # Ignorer les blocs __all__ individuels et séparateurs
                else:
                    body_lines.append(line)

            # 2. Collecte des noms de classes pour le __all__ final
            classes = class_re.findall(content)
            all_names.extend(classes)

            # 3. Stockage du corps du fichier
            all_content.append("\n".join(body_lines).strip())

    # 4. Construction du fichier final
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Fichier généré automatiquement - Fusion des modèles\n")
        
        # Écriture des imports uniques
        for imp in sorted(list(all_imports)):
            f.write(f"{imp}\n")
        
        f.write("\n\n")
        
        # Écriture du contenu des classes
        f.write("\n\n".join(all_content))
        
        f.write("\n\n# --- Export Global ---\n")
        f.write("__all__ = [\n")
        for name in sorted(list(set(all_names))):
            f.write(f"    \"{name}\",\n")
        f.write("]\n")

    print(f"\nSuccès ! Fichier généré : {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fusionne les fichiers DTO/Model en un seul.")
    parser.add_argument("--dir", type=str, required=True, help="Chemin du dossier source")
    parser.add_argument("--out", type=str, default="models_all.py", help="Nom du fichier de sortie")
    parser.add_argument("--exclude", nargs='*', default=["__init__.py"], help="Fichiers à exclure")

    args = parser.parse_args()
    merge_python_files(args.dir, args.out, args.exclude)