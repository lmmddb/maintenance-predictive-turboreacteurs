"""
Pipeline complet : relance les 5 notebooks dans l'ordre et régénère les tables Power BI.

Usage (depuis la racine du projet, environnement activé) :
    python run_pipeline.py             # tout relancer
    python run_pipeline.py --depuis 3  # relancer à partir du notebook 03

Ensuite, dans Power BI Desktop : Accueil -> Actualiser.
"""

import argparse
import sys
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient

RACINE = Path(__file__).resolve().parent
NOTEBOOKS = sorted((RACINE / "notebooks").glob("0*.ipynb"))  # 01_... à 05_..., dans l'ordre
TABLES_POWERBI = RACINE / "outputs" / "powerbi"


def executer(chemin):
    """Exécute un notebook (depuis son dossier) et l'enregistre avec ses résultats."""
    nb = nbformat.read(chemin, as_version=4)
    NotebookClient(nb, timeout=1800, resources={"metadata": {"path": str(chemin.parent)}}).execute()
    nbformat.write(nb, chemin)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--depuis", type=int, default=1, help="premier notebook à relancer (1 à 5)")
    depuis = parser.parse_args().depuis

    debut = time.time()
    for chemin in NOTEBOOKS[depuis - 1 :]:
        print(f"▶ {chemin.name} ...", end=" ", flush=True)
        t = time.time()
        try:
            executer(chemin)
        except Exception as erreur:  # on s'arrête : les notebooks suivants dépendent de celui-ci
            sys.exit(f"ÉCHEC\n\n{type(erreur).__name__} : {erreur}"[:2000])
        print(f"ok ({time.time() - t:.0f} s)")

    nb_tables = len(list(TABLES_POWERBI.glob("*.csv")))
    print(f"\n✅ Terminé en {time.time() - debut:.0f} s · {nb_tables} tables dans {TABLES_POWERBI}")
    print("   Dans Power BI Desktop : Accueil -> Actualiser.")


if __name__ == "__main__":
    main()
