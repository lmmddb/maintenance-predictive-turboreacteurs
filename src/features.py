"""
Variables construites à partir des capteurs (expliquées pas à pas dans le notebook 02).

Règle respectée partout : la variable d'un vol n'utilise que ce vol et les précédents du même
moteur (seule exception : la référence « moteur neuf », moyenne de ses 10 premiers vols).
"""

import numpy as np
import pandas as pd

FENETRE = 10  # moyenne glissante sur 10 vols
N_REFERENCE = 10  # les 10 premiers vols définissent « le moteur neuf »
FENETRE_PENTE = 20  # pente sur les 20 derniers vols


def ajouter_moyenne_glissante(df, capteurs, fenetre=FENETRE):
    df = df.copy()  # on ne modifie jamais le tableau d'origine
    for s in capteurs:
        par_moteur = df.groupby("unit")[s]
        df[f"{s}_moy"] = par_moteur.transform(lambda x: x.rolling(fenetre, min_periods=1).mean())
    return df


def ajouter_ecart_reference(df, capteurs, n_ref=N_REFERENCE):
    df = df.copy()
    for s in capteurs:
        reference = df.groupby("unit")[f"{s}_moy"].transform(lambda x: x.iloc[:n_ref].mean())
        df[f"{s}_delta"] = df[f"{s}_moy"] - reference
    return df


def pente_glissante(x, fenetre=FENETRE_PENTE):
    """Pente de la droite des moindres carrés sur les derniers vols : cov(x, t) / var(t)."""
    t = pd.Series(np.arange(len(x)), index=x.index, dtype=float)  # le « temps » : 0, 1, 2...
    cov = x.rolling(fenetre, min_periods=2).cov(t)
    var = t.rolling(fenetre, min_periods=2).var()
    return (cov / var).fillna(0)  # au 1er vol, pas de pente possible -> 0


def ajouter_pente(df, capteurs):
    df = df.copy()
    for s in capteurs:
        df[f"{s}_pente"] = df.groupby("unit")[s].transform(pente_glissante)
    return df


def construire_variables(df, capteurs):
    """Les trois étapes à la suite : moyenne -> écart à la référence -> pente."""
    df = ajouter_moyenne_glissante(df, capteurs)
    df = ajouter_ecart_reference(df, capteurs)
    return ajouter_pente(df, capteurs)
