"""
Valide le rapport généré :
  1. chaque fichier JSON du rapport contre son schéma officiel Microsoft (dépôt microsoft/json-schemas) ;
  2. la cohérence entre rapport et modèle : chaque table, colonne et mesure utilisée par un visuel existe ;
  3. la cohérence modèle <-> données : les colonnes déclarées correspondent aux en-têtes des CSV.

Usage : python outils/valider_rapport_powerbi.py <dossier json-schemas cloné>
"""

import json
import re
import sys
from pathlib import Path

from jsonschema import Draft7Validator
from referencing import Registry, Resource

RACINE = Path(__file__).resolve().parents[1]
RAPPORT = RACINE / "rapport" / "Maintenance predictive.Report" / "definition"
MODELE = RACINE / "rapport" / "Maintenance predictive.SemanticModel" / "definition"
PREFIXE = "https://developer.microsoft.com/json-schemas/"


def charger_schemas(depot):
    """Tous les schémas du dépôt local, indexés par leur URL publique."""
    ressources = []
    for f in Path(depot).rglob("*.json"):
        try:
            contenu = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        url = PREFIXE + str(f.relative_to(depot)).replace("\\", "/")
        ressources.append((url, Resource.opaque(contenu)))
    return Registry().with_resources(ressources)


def valider_schemas(registry):
    erreurs, n = [], 0
    for f in sorted(RAPPORT.rglob("*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        url = doc.get("$schema")
        schema = registry.contents(url)
        v = (
            Draft7Validator(schema, registry=registry, _resolver=registry.resolver(base_uri=url))
            if "_resolver" in Draft7Validator.__init__.__code__.co_varnames
            else Draft7Validator(schema, registry=registry)
        )
        for e in v.iter_errors(doc):
            erreurs.append(
                f"{f.parent.name}/{f.name} : {'/'.join(map(str, e.absolute_path))} : {e.message[:200]}"
            )
        n += 1
    return n, erreurs


def lire_modele():
    tables = {}
    for f in (MODELE / "tables").glob("*.tmdl"):
        texte = f.read_text(encoding="utf-8")
        nom = re.match(r"table\s+'?([^'\n]+)'?", texte).group(1)
        cols = set(re.findall(r"^\tcolumn\s+'?([^'\n]+?)'?\s*$", texte, re.M))
        mesures = set(re.findall(r"^\tmeasure\s+'?(.+?)'?\s+=", texte, re.M))
        mesures = {m.replace("''", "'") for m in mesures}
        tables[nom] = {"colonnes": cols, "mesures": mesures}
    return tables


def references(obj, trouvees):
    """Toutes les références (Entity, Property, Column|Measure) contenues dans un visuel."""
    if isinstance(obj, dict):
        for genre in ("Column", "Measure"):
            if genre in obj and isinstance(obj[genre], dict) and "Property" in obj[genre]:
                ent = obj[genre].get("Expression", {}).get("SourceRef", {}).get("Entity")
                if ent:
                    trouvees.append((genre, ent, obj[genre]["Property"]))
        for v in obj.values():
            references(v, trouvees)
    elif isinstance(obj, list):
        for v in obj:
            references(v, trouvees)
    return trouvees


def valider_liens(tables):
    erreurs, n = [], 0
    for f in RAPPORT.rglob("*.json"):
        for genre, ent, prop in references(json.loads(f.read_text(encoding="utf-8")), []):
            n += 1
            if ent not in tables:
                erreurs.append(f"{f.name}: table inconnue {ent}")
            elif genre == "Column" and prop not in tables[ent]["colonnes"]:
                erreurs.append(f"{f.name}: colonne inconnue {ent}[{prop}]")
            elif genre == "Measure" and prop not in tables[ent]["mesures"]:
                erreurs.append(f"{f.name}: mesure inconnue {ent}[{prop}]")
    # Les mesures DAX ne doivent citer que des mesures et colonnes existantes
    texte = (MODELE / "tables" / "_Mesures.tmdl").read_text(encoding="utf-8")
    texte = re.sub(
        r'"[^"\n]*"', '""', texte
    )  # on ignore le contenu des chaînes ("Classique [R, Q]")
    toutes_mesures = set().union(*(t["mesures"] for t in tables.values()))
    for ref in re.findall(r"(?<![\w'])\[([^\]]+)\]", texte):
        if ref not in toutes_mesures and ref != "Value":
            erreurs.append(f"_Mesures : mesure inconnue [{ref}]")
    for tab, col in re.findall(r"'?([A-Za-z_][\w ]*?)'?\[([^\]]+)\]", texte):
        tab = tab.strip()
        if tab and tab in tables and col not in tables[tab]["colonnes"]:
            erreurs.append(f"_Mesures : colonne inconnue {tab}[{col}]")
    return n, erreurs


def valider_donnees():
    """Les colonnes sources déclarées dans le générateur existent dans les CSV et se convertissent dans leur type."""
    import pandas as pd

    sys.path.insert(0, str(Path(__file__).parent))
    from generer_rapport_powerbi import CAPTEURS, DONNEES, TABLES

    erreurs, n = [], 0
    for fichier, colonnes in TABLES.values():
        df = pd.read_csv(DONNEES / fichier, sep=";", decimal=",", dtype=str, keep_default_na=False)
        if colonnes is None:
            colonnes = (
                [("id_moteur", "", "texte", ""), ("cycle", "", "entier", "")]
                + [(c, "", "decimal", "") for c in CAPTEURS]
                + [("RUL", "", "entier", ""), ("RUL_cap", "", "entier", "")]
            )
        attendues = [c[0] for c in colonnes]
        if attendues != list(df.columns):
            erreurs.append(f"{fichier} : colonnes {list(df.columns)} au lieu de {attendues}")
            continue
        for src, _, typ, _ in colonnes:
            n += 1
            valeurs = df[src][df[src] != ""]
            if typ in ("entier", "decimal"):
                conv = pd.to_numeric(valeurs.str.replace(",", ".", regex=False), errors="coerce")
                if conv.isna().any():
                    erreurs.append(
                        f"{fichier}[{src}] : valeurs non numériques {valeurs[conv.isna()].unique()[:3]}"
                    )
                elif typ == "entier" and not (conv == conv.round()).all():
                    erreurs.append(f"{fichier}[{src}] : valeurs non entières")
    return n, erreurs


def main():
    depot = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    tables = lire_modele()
    total = []
    if depot:
        n, e = valider_schemas(charger_schemas(depot))
        print(f"Schémas : {n} fichiers JSON du rapport validés, {len(e)} erreur(s)")
        total += e
    n, e = valider_liens(tables)
    print(f"Liens rapport -> modèle : {n} références vérifiées, {len(e)} erreur(s)")
    total += e
    n, e = valider_donnees()
    print(f"Données : {n} colonnes vérifiées (nom + type), {len(e)} erreur(s)")
    total += e
    for x in total:
        print("  ✗", x)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
