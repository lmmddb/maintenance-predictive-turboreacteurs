"""
Chargement des données NASA C-MAPSS (turbofan).

Chaque fichier train/test est un texte séparé par des espaces, sans en-tête :
  - col 1   : numéro du moteur (unit)
  - col 2   : numéro du cycle (= un vol)
  - col 3-5 : 3 réglages opérationnels (altitude, Mach, manette des gaz… normalisés)
  - col 6-26: 21 capteurs

Les fichiers RUL_FDxxx.txt donnent, pour chaque moteur du test, le nombre de vols
qu'il lui restait réellement après le dernier vol observé (la "vérité terrain").
"""

from pathlib import Path

import pandas as pd

# Racine du projet = dossier parent de src/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIG_DIR = PROJECT_ROOT / "outputs" / "figures"
POWERBI_DIR = PROJECT_ROOT / "outputs" / "powerbi"

SETTINGS = ["setting_1", "setting_2", "setting_3"]
SENSORS = [f"s{i}" for i in range(1, 22)]
COLUMNS = ["unit", "cycle"] + SETTINGS + SENSORS

# Signification physique des capteurs (Saxena et al., 2008).
# Indispensable pour qu'un ingénieur ou un décideur sache de quoi on parle.
SENSOR_LABELS = {
    "s1": "T2 - Température entrée soufflante (°R)",
    "s2": "T24 - Température sortie compresseur BP (°R)",
    "s3": "T30 - Température sortie compresseur HP (°R)",
    "s4": "T50 - Température sortie turbine BP (°R)",
    "s5": "P2 - Pression entrée soufflante (psia)",
    "s6": "P15 - Pression conduit secondaire (psia)",
    "s7": "P30 - Pression totale sortie compresseur HP (psia)",
    "s8": "Nf - Vitesse physique soufflante (rpm)",
    "s9": "Nc - Vitesse physique corps HP (rpm)",
    "s10": "epr - Rapport de pression moteur",
    "s11": "Ps30 - Pression statique sortie compresseur HP (psia)",
    "s12": "phi - Débit carburant / Ps30 (pps/psi)",
    "s13": "NRf - Vitesse corrigée soufflante (rpm)",
    "s14": "NRc - Vitesse corrigée corps HP (rpm)",
    "s15": "BPR - Taux de dilution",
    "s16": "farB - Rapport carburant/air chambre",
    "s17": "htBleed - Enthalpie de prélèvement",
    "s18": "Nf_dmd - Vitesse soufflante demandée (rpm)",
    "s19": "PCNfR_dmd - Vitesse soufflante corrigée demandée (rpm)",
    "s20": "W31 - Prélèvement refroidissement turbine HP (lbm/s)",
    "s21": "W32 - Prélèvement refroidissement turbine BP (lbm/s)",
}


def _read_txt(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=r"\s+", header=None)
    # Certains fichiers ont des colonnes vides en fin de ligne : on les coupe.
    df = df.iloc[:, : len(COLUMNS)]
    df.columns = COLUMNS
    return df


def load_train(subset: str = "FD001") -> pd.DataFrame:
    """Trajectoires complètes : chaque moteur tourne jusqu'à la panne."""
    df = _read_txt(RAW_DIR / f"train_{subset}.txt")
    return add_rul(df)


def load_test(subset: str = "FD001") -> pd.DataFrame:
    """Trajectoires coupées avant la panne + RUL réelle au dernier vol observé."""
    df = _read_txt(RAW_DIR / f"test_{subset}.txt")
    rul_end = pd.read_csv(RAW_DIR / f"RUL_{subset}.txt", header=None).iloc[:, 0]
    rul_end.index = range(1, len(rul_end) + 1)  # moteur 1, 2, ...

    last_cycle = df.groupby("unit")["cycle"].transform("max")
    df["RUL"] = df["unit"].map(rul_end) + (last_cycle - df["cycle"])
    return df


def add_rul(df: pd.DataFrame) -> pd.DataFrame:
    """RUL = nombre de vols restants avant la panne.
    Dans le train, le dernier cycle observé EST la panne, donc :
    RUL = cycle_max_du_moteur - cycle_courant."""
    df = df.copy()
    df["RUL"] = df.groupby("unit")["cycle"].transform("max") - df["cycle"]
    return df
