#!/usr/bin/env python3
"""
Checker pour les imports dans un projet 'src layout'.
Vérifie que aucun fichier n'importe avec 'from src.' ou 'import src.'.
"""

import os
import re
import sys

# Racine de ton projet
SRC_DIR = "src"

# Regex pour détecter les imports invalides
IMPORT_REGEX = re.compile(r"^\s*(from|import)\s+src\.")  # capture 'from src.' ou 'import src.'

def check_file(file_path):
    """Vérifie un fichier pour les imports invalides."""
    errors = []
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            if IMPORT_REGEX.match(line):
                errors.append(f"{file_path}:{i}: {line.strip()}")
    return errors

def main():
    all_errors = []

    for root, dirs, files in os.walk(SRC_DIR):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                errors = check_file(file_path)
                all_errors.extend(errors)

    if all_errors:
        print("⚠️  Imports invalides détectés (utilisation de 'src.' non autorisée) :")
        for err in all_errors:
            print(err)
        sys.exit(1)
    else:
        print("✅ Tous les imports sont corrects (top-level packages).")
        sys.exit(0)

if __name__ == "__main__":
    main()
