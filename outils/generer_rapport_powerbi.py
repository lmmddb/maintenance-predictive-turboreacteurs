"""
Génère le rapport Power BI complet sous forme de projet texte (.pbip) :
  - un modèle sémantique en TMDL (tables, types, relations, mesures DAX, paramètre de dossier) ;
  - un rapport en PBIR (5 pages, visuels, thème, fonds de page, navigation, extraction).

Usage (depuis la racine du projet) :
    python outils/generer_rapport_powerbi.py
Puis double-cliquer sur rapport/Maintenance predictive.pbip (Power BI Desktop) et cliquer sur Actualiser.

Le chemin des données (paramètre DossierDonnees) est calculé à partir de l'emplacement du projet :
relancer ce script si le projet change de dossier.
"""

import hashlib
import json
import shutil
import uuid
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
DONNEES = RACINE / "outputs" / "powerbi"
ASSETS = RACINE / "powerbi_assets"
NOM = "Maintenance predictive"
SORTIE = RACINE / "rapport"
SM = SORTIE / f"{NOM}.SemanticModel"
RP = SORTIE / f"{NOM}.Report"

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
V_REPORT, V_PAGE, V_VISUAL, V_PAGES = "1.2.0", "1.3.0", "1.5.0", "1.0.0"
NAVY, ORANGE, ROUGE, VERT, GRIS = "#1F4E79", "#E67E22", "#C0392B", "#27AE60", "#9DB4CC"


def uid(*parts):
    """Identifiant stable (20 caractères hexadécimaux) : le rapport généré est reproductible."""
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:20]


def guid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "|".join(parts)))


def ecrire(chemin, contenu):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(contenu, (dict, list)):
        contenu = json.dumps(contenu, indent=2, ensure_ascii=False)
    chemin.write_text(contenu, encoding="utf-8")


# =====================================================================================
# 1. MODÈLE SÉMANTIQUE (TMDL)
# =====================================================================================
# Chaque table : (nom, fichier CSV, colonnes [(nom_source, nom_final, type, options)], étapes M en plus)
#   type : "texte" | "entier" | "decimal" ; options : "cache" (masquée), "aucun" (ne pas résumer)
TABLES = {
    "dim_moteur": (
        "dim_moteur.csv",
        [
            ("id_moteur", "id_moteur", "texte", ""),
            ("sous_jeu", "sous_jeu", "texte", ""),
            ("jeu", "jeu", "texte", ""),
            ("unit", "unit", "entier", "aucun"),
            ("vols_observes", "vols_observes", "entier", "aucun"),
            ("statut", "statut_donnees", "texte", ""),
        ],
    ),
    "dim_capteur": (
        "dim_capteur.csv",
        [
            ("capteur", "capteur", "texte", ""),
            ("libelle", "libelle", "texte", ""),
            ("correlation_rul", "correlation_rul", "decimal", "aucun"),
        ],
    ),
    "fact_predictions": (
        "fact_predictions.csv",
        [
            ("id_moteur", "id_moteur", "texte", ""),
            ("vols_observes", "vols_observes", "entier", "aucun"),
            ("rul_predite", "rul_predite", "decimal", ""),
            ("rul_basse_80", "rul_basse_80", "decimal", ""),
            ("rul_haute_80", "rul_haute_80", "decimal", ""),
            ("rul_reelle", "rul_reelle", "entier", "cache"),
            ("erreur", "erreur", "decimal", "cache"),
        ],
    ),
    "fact_alertes": (
        "fact_alertes.csv",
        [
            ("id_moteur", "id_moteur", "texte", ""),
            ("statut", "statut", "texte", ""),
            ("motif_alerte", "motif_alerte", "texte", ""),
            ("rul_predite", "rul_predite", "decimal", ""),
            ("rul_basse_80", "rul_basse_80", "decimal", ""),
            ("rul_reelle", "rul_reelle", "entier", "cache"),
        ],
    ),
    "fact_vols": ("fact_vols.csv", None),  # construit à part (dépivotage)
    "fact_stock_politiques": (
        "fact_stock_politiques.csv",
        [
            ("politique", "politique", "texte", ""),
            ("cout_total", "cout_total", "decimal", ""),
            ("commande", "commande", "decimal", ""),
            ("possession", "possession", "decimal", ""),
            ("rupture", "rupture", "decimal", ""),
            ("stock_moyen", "stock_moyen", "decimal", ""),
            ("taux_service", "taux_service", "decimal", ""),
            ("jours_immobilises_an", "jours_immobilises_an", "decimal", ""),
            ("taux_service_vise", "taux_service_vise", "entier", "aucun"),
        ],
    ),
    "fact_stock_journal": (
        "fact_stock_journal.csv",
        [
            ("jour", "jour", "entier", "aucun"),
            ("stock", "stock", "entier", ""),
            ("position", "position", "entier", ""),
            ("seuil", "seuil", "entier", ""),
            ("en_attente", "en_attente", "entier", ""),
            ("politique", "politique", "texte", ""),
        ],
    ),
    "fact_strategies": (
        "fact_strategies.csv",
        [
            ("stratégie", "strategie", "texte", ""),
            ("coût par vol (€)", "cout_par_vol", "decimal", ""),
            ("coût annuel flotte (M€)", "cout_annuel_meur", "decimal", ""),
            ("déposes non planifiées (sur 100)", "deposes_non_planifiees", "entier", ""),
            ("vie utilisée (%)", "vie_utilisee", "decimal", ""),
        ],
    ),
    "fact_sensibilite": (
        "fact_sensibilite.csv",
        [
            ("hypothèse", "hypothese", "texte", ""),
            ("-50 %", "gain_moins_50", "decimal", ""),
            ("+50 %", "gain_plus_50", "decimal", ""),
            ("amplitude", "amplitude", "decimal", ""),
            ("gain_reference", "gain_reference", "decimal", ""),
        ],
    ),
    "fact_marge": (
        "fact_marge.csv",
        [
            ("marge m", "marge_m", "entier", "aucun"),
            ("coût par vol (€)", "cout_par_vol", "decimal", ""),
            ("déposes non planifiées", "deposes_non_planifiees", "entier", ""),
            ("vols restants au minimum", "vols_restants_min", "entier", ""),
            ("vols restants (médiane)", "vols_restants_mediane", "decimal", ""),
        ],
    ),
}
TYPE_M = {"texte": "type text", "entier": "Int64.Type", "decimal": "type number"}
TYPE_TMDL = {"texte": "string", "entier": "int64", "decimal": "double"}
CAPTEURS = ["s11", "s4", "s12", "s7", "s15", "s21", "s20", "s17", "s2", "s3", "s8", "s13"]


def m_lire(fichier, colonnes, etapes_en_plus=""):
    """Code Power Query (M) : lecture du CSV, en-têtes, types (culture fr-FR), renommage."""
    types = ", ".join(f'{{"{src}", {TYPE_M[t]}}}' for src, _, t, _ in colonnes)
    renommes = [(src, fin) for src, fin, _, _ in colonnes if src != fin]
    lignes = [
        "let",
        f'    Source = Csv.Document(File.Contents(DossierDonnees & "{fichier}"), [Delimiter=";", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f'    Types = Table.TransformColumnTypes(Entetes, {{{types}}}, "fr-FR"),',
    ]
    derniere = "Types"
    if renommes:
        r = ", ".join(f'{{"{a}", "{b}"}}' for a, b in renommes)
        lignes.append(f"    Renommees = Table.RenameColumns(Types, {{{r}}}),")
        derniere = "Renommees"
    if etapes_en_plus:
        lignes += [e.replace("{precedent}", derniere) for e in etapes_en_plus]
        derniere = etapes_en_plus[-1].split("=")[0].strip()
    lignes[-1] = lignes[-1].rstrip(",")
    lignes += ["in", f"    {derniere}"]
    return lignes


def tmdl_colonne(nom, typ, options, extra=None):
    t = [f"\tcolumn {nom}", f"\t\tdataType: {TYPE_TMDL[typ]}"]
    if typ == "entier":
        t.append("\t\tformatString: 0")
    if "cache" in options:
        t.append("\t\tisHidden")
    t.append(f"\t\tlineageTag: {guid('col', nom, typ)}")
    t.append(f"\t\tsummarizeBy: {'none' if (typ == 'texte' or 'aucun' in options) else 'sum'}")
    t.append(f"\t\tsourceColumn: {nom}")
    for e in extra or []:
        t.append(f"\t\t{e}")
    return t + ["", "\t\tannotation SummarizationSetBy = Automatic", ""]


def tmdl_table(nom, colonnes_tmdl, m_lignes):
    t = [f"table {nom}", f"\tlineageTag: {guid('table', nom)}", ""]
    for c in colonnes_tmdl:
        t += c
    t += [f"\tpartition {nom} = m", "\t\tmode: import", "\t\tsource ="]
    t += ["\t\t\t\t" + x for x in m_lignes]
    t += ["", "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(t)


def construire_modele():
    tables = {}
    # --- tables simples
    for nom, (fichier, colonnes) in TABLES.items():
        if colonnes is None:
            continue
        en_plus = []
        cols = [tmdl_colonne(fin, t, opt) for _, fin, t, opt in colonnes]
        if nom == "fact_stock_politiques":
            en_plus = [
                '    AvecLibelle = Table.AddColumn({precedent}, "taux_service_libelle", each Text.From([taux_service_vise]) & " %", type text),'
            ]
            cols.append(
                tmdl_colonne(
                    "taux_service_libelle", "texte", "", ["sortByColumn: taux_service_vise"]
                )
            )
        if nom == "fact_alertes":
            # Tranche de 10 vols pour l'histogramme (et une colonne de tri pour l'ordre 0-9, 10-19, ...)
            en_plus = [
                '    AvecDebut = Table.AddColumn({precedent}, "tranche_debut", each Number.RoundDown([rul_predite] / 10) * 10, Int64.Type),',
                '    AvecTranche = Table.AddColumn(AvecDebut, "tranche", each Text.From([tranche_debut]) & "-" & Text.From([tranche_debut] + 9), type text),',
            ]
            cols.append(tmdl_colonne("tranche_debut", "entier", "cache aucun"))
            cols.append(tmdl_colonne("tranche", "texte", "", ["sortByColumn: tranche_debut"]))
        tables[nom] = tmdl_table(nom, cols, m_lire(fichier, colonnes, en_plus))

    # --- fact_vols : une ligne par moteur x vol x capteur (dépivotage)
    base = (
        [("id_moteur", "id_moteur", "texte", ""), ("cycle", "cycle", "entier", "aucun")]
        + [(s, s, "decimal", "") for s in CAPTEURS]
        + [("RUL", "RUL", "entier", "cache"), ("RUL_cap", "RUL_cap", "entier", "cache")]
    )
    m = m_lire(
        "fact_vols.csv",
        base,
        [
            '    Long = Table.UnpivotOtherColumns({precedent}, {"id_moteur", "cycle", "RUL", "RUL_cap"}, "capteur", "valeur"),',
            '    TypesLong = Table.TransformColumnTypes(Long, {{"valeur", type number}}),',
        ],
    )
    cols = [
        tmdl_colonne("id_moteur", "texte", ""),
        tmdl_colonne("cycle", "entier", "aucun"),
        tmdl_colonne("RUL", "entier", "cache"),
        tmdl_colonne("RUL_cap", "entier", "cache"),
        tmdl_colonne("capteur", "texte", ""),
        tmdl_colonne("valeur", "decimal", ""),
    ]
    tables["fact_vols"] = tmdl_table("fact_vols", cols, m)

    # --- Actualisation : date à laquelle le pipeline Python a écrit les données
    m = [
        "let",
        "    Fichiers = Folder.Files(DossierDonnees),",
        '    Alertes = Table.SelectRows(Fichiers, each [Name] = "fact_alertes.csv"),',
        '    Garde = Table.SelectColumns(Alertes, {"Date modified"}),',
        '    Renommee = Table.RenameColumns(Garde, {{"Date modified", "date_donnees"}}),',
        '    Typee = Table.TransformColumnTypes(Renommee, {{"date_donnees", type datetime}})',
        "in",
        "    Typee",
    ]
    cols = [
        [
            "\tcolumn date_donnees",
            "\t\tdataType: dateTime",
            "\t\tformatString: General Date",
            f"\t\tlineageTag: {guid('col', 'date_donnees')}",
            "\t\tsummarizeBy: none",
            "\t\tsourceColumn: date_donnees",
            "",
            "\t\tannotation SummarizationSetBy = Automatic",
            "",
        ]
    ]
    tables["Actualisation"] = tmdl_table("Actualisation", cols, m)

    # --- Paramètre « prix d'un module » (table déconnectée pour un segment)
    m = [
        "let",
        "    Valeurs = List.Numbers(100000, 9, 50000),",
        '    EnTable = Table.FromList(Valeurs, Splitter.SplitByNothing(), {"prix_module"}),',
        '    Typee = Table.TransformColumnTypes(EnTable, {{"prix_module", Int64.Type}})',
        "in",
        "    Typee",
    ]
    cols = [
        [
            "\tcolumn prix_module",
            "\t\tdataType: int64",
            "\t\tformatString: #,0",
            f"\t\tlineageTag: {guid('col', 'prix_module')}",
            "\t\tsummarizeBy: none",
            "\t\tsourceColumn: prix_module",
            "",
            "\t\tannotation SummarizationSetBy = User",
            "",
        ]
    ]
    tables["Prix module"] = tmdl_table("'Prix module'", cols, m)

    # --- Table des mesures
    tables["_Mesures"] = tmdl_mesures()
    return tables


MESURES = [
    # (nom, expression DAX, formatString ou None, dossier d'affichage)
    # ---- Business case
    (
        "Coût prédictive (M€)",
        'CALCULATE(SUM(fact_strategies[cout_annuel_meur]), FILTER(ALL(fact_strategies[strategie]), CONTAINSSTRING(fact_strategies[strategie], "Prédictive")))',
        "0.0",
        "1 Business case",
    ),
    (
        "Coût intervalle fixe (M€)",
        'CALCULATE(SUM(fact_strategies[cout_annuel_meur]), FILTER(ALL(fact_strategies[strategie]), CONTAINSSTRING(fact_strategies[strategie], "Intervalle fixe")))',
        "0.0",
        "1 Business case",
    ),
    (
        "Coût réactive (M€)",
        'CALCULATE(SUM(fact_strategies[cout_annuel_meur]), FILTER(ALL(fact_strategies[strategie]), CONTAINSSTRING(fact_strategies[strategie], "Réactive")))',
        "0.0",
        "1 Business case",
    ),
    (
        "Économie maintenance (M€)",
        "[Coût intervalle fixe (M€)] - [Coût prédictive (M€)]",
        "0.0",
        "1 Business case",
    ),
    (
        "Économie stock (M€)",
        "\n".join(
            [
                'VAR classique = CALCULATE(SUM(fact_stock_politiques[cout_total]), fact_stock_politiques[politique] = "Classique [R, Q]", fact_stock_politiques[taux_service_vise] = 95)',
                'VAR pilotee = CALCULATE(SUM(fact_stock_politiques[cout_total]), fact_stock_politiques[politique] = "Pilotée par le modèle", fact_stock_politiques[taux_service_vise] = 95)',
                "RETURN (classique - pilotee) / 1000000",
            ]
        ),
        "0.0",
        "1 Business case",
    ),
    (
        "Économie totale (M€)",
        "[Économie maintenance (M€)] + [Économie stock (M€)]",
        "0.0",
        "1 Business case",
    ),
    ("Moteurs en service", "COUNTROWS(fact_alertes)", "0", "2 Flotte"),
    (
        "Économie par moteur (k€)",
        "DIVIDE([Économie totale (M€)] * 1000, [Moteurs en service])",
        "0",
        "1 Business case",
    ),
    (
        "Économie pire scénario (M€)",
        "MIN(fact_sensibilite[gain_moins_50])",
        "0.0",
        "1 Business case",
    ),
    (
        "Déposes subies prédictive",
        'CALCULATE(SUM(fact_strategies[deposes_non_planifiees]), FILTER(ALL(fact_strategies[strategie]), CONTAINSSTRING(fact_strategies[strategie], "Prédictive")))',
        "0",
        "1 Business case",
    ),
    ("Coût annuel (M€)", "SUM(fact_strategies[cout_annuel_meur])", "0.0", "1 Business case"),
    (
        "Économie si hypothèse -50 % (M€)",
        "SUM(fact_sensibilite[gain_moins_50])",
        "0.0",
        "1 Business case",
    ),
    (
        "Économie si hypothèse +50 % (M€)",
        "SUM(fact_sensibilite[gain_plus_50])",
        "0.0",
        "1 Business case",
    ),
    # Textes affichés dans les cartes (le nom de la mesure sert de libellé)
    ("Économie annuelle", 'FORMAT([Économie totale (M€)], "0.0") & " M€"', None, "0 Affichage"),
    (
        "Par moteur et par an",
        'FORMAT([Économie par moteur (k€)], "0") & " k€"',
        None,
        "0 Affichage",
    ),
    ("Déposes subies (sur 100)", 'FORMAT([Déposes subies prédictive], "0")', None, "0 Affichage"),
    (
        "Dans le pire scénario testé",
        'FORMAT([Économie pire scénario (M€)], "0.0") & " M€"',
        None,
        "0 Affichage",
    ),
    (
        "Titre business case",
        '"Maintenance prédictive : " & FORMAT([Économie totale (M€)], "0.0") & " M€ d\'économie par an sur " & [Moteurs en service] & " moteurs"',
        None,
        "0 Affichage",
    ),
    # ---- Flotte
    (
        "Moteurs en alerte",
        'CALCULATE(COUNTROWS(fact_alertes), fact_alertes[statut] = "Alerte")',
        "0",
        "2 Flotte",
    ),
    (
        "Moteurs en surveillance",
        'CALCULATE(COUNTROWS(fact_alertes), fact_alertes[statut] = "Surveillance")',
        "0",
        "2 Flotte",
    ),
    (
        "Moteurs RAS",
        'CALCULATE(COUNTROWS(fact_alertes), fact_alertes[statut] = "RAS")',
        "0",
        "2 Flotte",
    ),
    ("Nombre de moteurs", "COUNTROWS(fact_alertes)", "0", "2 Flotte"),
    ("À planifier (alerte)", 'FORMAT([Moteurs en alerte], "0")', None, "0 Affichage"),
    ("À surveiller", 'FORMAT([Moteurs en surveillance], "0")', None, "0 Affichage"),
    ("RAS", 'FORMAT([Moteurs RAS], "0")', None, "0 Affichage"),
    (
        "Titre flotte",
        '"La flotte aujourd\'hui : " & [Moteurs en alerte] & " moteurs à planifier, " & [Moteurs en surveillance] & " à surveiller"',
        None,
        "0 Affichage",
    ),
    (
        "Couleur statut",
        'SWITCH(SELECTEDVALUE(fact_alertes[statut]), "Alerte", "#F5B7B1", "Surveillance", "#FAD7A0", "RAS", "#D5F5E3")',
        None,
        "2 Flotte",
    ),
    # ---- Stock
    (
        "Prix module sélectionné",
        "SELECTEDVALUE('Prix module'[prix_module], 250000)",
        "#,0",
        "3 Stock",
    ),
    (
        "Stock moyen classique",
        'CALCULATE(AVERAGE(fact_stock_politiques[stock_moyen]), fact_stock_politiques[politique] = "Classique [R, Q]", fact_stock_politiques[taux_service_vise] = 95)',
        "0.0",
        "3 Stock",
    ),
    (
        "Stock moyen piloté",
        'CALCULATE(AVERAGE(fact_stock_politiques[stock_moyen]), fact_stock_politiques[politique] = "Pilotée par le modèle", fact_stock_politiques[taux_service_vise] = 95)',
        "0.0",
        "3 Stock",
    ),
    (
        "Capital libéré (M€)",
        "([Stock moyen classique] - [Stock moyen piloté]) * [Prix module sélectionné] / 1000000",
        "0.0",
        "3 Stock",
    ),
    ("Coût du stock (k€/an)", "SUM(fact_stock_politiques[cout_total]) / 1000", "0", "3 Stock"),
    (
        "Économie de stock",
        'FORMAT([Économie stock (M€)] * 1000, "0") & " k€/an"',
        None,
        "0 Affichage",
    ),
    (
        "Modules en entrepôt (classique → piloté)",
        'FORMAT([Stock moyen classique], "0.0") & " → " & FORMAT([Stock moyen piloté], "0.0")',
        None,
        "0 Affichage",
    ),
    ("Capital libéré", 'FORMAT([Capital libéré (M€)], "0.0") & " M€"', None, "0 Affichage"),
    (
        "Titre stock",
        '"Stock de modules : " & FORMAT([Capital libéré (M€)], "0.0") & " M€ de capital libéré, à taux de service égal (95 %)"',
        None,
        "0 Affichage",
    ),
    # ---- Fiche moteur
    ("Statut", 'SELECTEDVALUE(fact_alertes[statut], "—")', None, "4 Fiche moteur"),
    (
        "Motif",
        'VAR m = SELECTEDVALUE(fact_alertes[motif_alerte]) RETURN IF(m = "", "—", m)',
        None,
        "4 Fiche moteur",
    ),
    (
        "Vols restants prévus",
        'VAR v = SELECTEDVALUE(fact_alertes[rul_predite]) RETURN IF(ISBLANK(v), "—", FORMAT(v, "0"))',
        None,
        "4 Fiche moteur",
    ),
    (
        "Scénario pessimiste",
        'VAR v = SELECTEDVALUE(fact_alertes[rul_basse_80]) RETURN IF(ISBLANK(v), "—", FORMAT(v, "0") & " vols")',
        None,
        "4 Fiche moteur",
    ),
    (
        "Titre fiche",
        '"Moteur " & SELECTEDVALUE(fact_alertes[id_moteur], "(choisir un moteur depuis la page Flotte)")',
        None,
        "0 Affichage",
    ),
    (
        "Dérive (écarts-types)",
        "\n".join(
            [
                "VAR c = MAX(fact_vols[cycle])",
                "VAR lissee = CALCULATE(AVERAGE(fact_vols[valeur]), REMOVEFILTERS(fact_vols[cycle]), fact_vols[cycle] > c - 10, fact_vols[cycle] <= c)",
                "VAR reference = CALCULATE(AVERAGE(fact_vols[valeur]), REMOVEFILTERS(fact_vols[cycle]), fact_vols[cycle] <= 10)",
                "VAR ecart = CALCULATE(STDEV.P(fact_vols[valeur]), REMOVEFILTERS(fact_vols[cycle]))",
                "RETURN DIVIDE(lissee - reference, ecart)",
            ]
        ),
        "0.0",
        "4 Fiche moteur",
    ),
    # ---- Accueil
    (
        "Données du",
        '"Données générées le " & FORMAT(MAX(Actualisation[date_donnees]), "dd/mm/yyyy") & " à " & FORMAT(MAX(Actualisation[date_donnees]), "hh:nn")',
        None,
        "0 Affichage",
    ),
    (
        "Moteurs à planifier",
        'FORMAT([Moteurs en alerte], "0") & " / " & FORMAT([Moteurs en service], "0")',
        None,
        "0 Affichage",
    ),
]


def nom_tmdl(n):
    return n if n.replace("_", "").isalnum() and n.isascii() else "'" + n.replace("'", "''") + "'"


def tmdl_mesures():
    t = ["table _Mesures", f"\tlineageTag: {guid('table', '_Mesures')}", ""]
    for nom, dax, fmt, dossier in MESURES:
        if "\n" in dax:
            t.append(f"\tmeasure {nom_tmdl(nom)} = ```")
            t += ["\t\t\t" + x for x in dax.split("\n")]
            t.append("\t\t\t```")
        else:
            t.append(f"\tmeasure {nom_tmdl(nom)} = {dax}")
        if fmt:
            t.append(f"\t\tformatString: {fmt}")
        t.append(f"\t\tdisplayFolder: {dossier}")
        t.append(f"\t\tlineageTag: {guid('measure', nom)}")
        t.append("")
    t += [
        "\tcolumn Value",
        "\t\tisHidden",
        "\t\tformatString: 0",
        f"\t\tlineageTag: {guid('col', 'mesures-value')}",
        "\t\tsummarizeBy: none",
        "\t\tisNameInferred",
        "\t\tsourceColumn: [Value]",
        "",
        "\t\tannotation SummarizationSetBy = Automatic",
        "",
        "\tpartition _Mesures = calculated",
        "\t\tmode: import",
        "\t\tsource = {0}",
        "",
    ]
    return "\n".join(t)


RELATIONS = [
    # (de, vers, un-à-un ?, filtre dans les deux sens ?)
    ("fact_vols.id_moteur", "dim_moteur.id_moteur", False, False),
    ("fact_vols.capteur", "dim_capteur.capteur", False, False),
    ("fact_predictions.id_moteur", "dim_moteur.id_moteur", True, True),
    ("fact_alertes.id_moteur", "dim_moteur.id_moteur", True, True),
]


def ecrire_modele():
    d = SM / "definition"
    tables = construire_modele()
    for nom, contenu in tables.items():
        ecrire(d / "tables" / f"{nom}.tmdl", contenu)
    ecrire(d / "database.tmdl", "database\n\tcompatibilityLevel: 1567\n")
    ordre = json.dumps(list(tables), ensure_ascii=False)
    ecrire(
        d / "model.tmdl",
        "\n".join(
            [
                "model Model",
                "\tculture: fr-FR",
                "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
                "\tsourceQueryCulture: fr-FR",
                "\tdataAccessOptions",
                "\t\tlegacyRedirects",
                "\t\treturnErrorValuesAsNull",
                "",
                "annotation __PBI_TimeIntelligenceEnabled = 0",
                "",
                f"annotation PBI_QueryOrder = {ordre}",
                "",
            ]
            + [f"ref table {nom_tmdl(n)}" for n in tables]
            + [""]
        ),
    )
    chemin = str(DONNEES) + ("\\" if "\\" in str(DONNEES) else "/")
    ecrire(
        d / "expressions.tmdl",
        f'expression DossierDonnees = "{chemin}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
        f"\tlineageTag: {guid('param', 'dossier')}\n\n\tannotation PBI_ResultType = Text\n",
    )
    rel = []
    for de, vers, un_un, deux_sens in RELATIONS:
        rel += [f"relationship {guid('rel', de, vers)}"]
        if un_un:
            rel += ["\tfromCardinality: one"]
        if deux_sens:
            rel += ["\tcrossFilteringBehavior: bothDirections"]
        rel += [f"\tfromColumn: {de}", f"\ttoColumn: {vers}", ""]
    ecrire(d / "relationships.tmdl", "\n".join(rel))
    ecrire(SM / "definition.pbism", {"version": "4.1", "settings": {}})
    ecrire(
        SM / ".platform",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": "SemanticModel", "displayName": NOM},
            "config": {"version": "2.0", "logicalId": guid("sm", NOM)},
        },
    )
    return tables


# =====================================================================================
# 2. RAPPORT (PBIR)
# =====================================================================================
def lit(v):
    """Encodage PBIR d'une valeur littérale."""
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, int):
        s = f"{v}D"
    elif isinstance(v, float):
        s = f"{v}D"
    else:
        s = "'" + str(v).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": s}}}


def couleur(hex_):
    return {"solid": {"color": lit(hex_)}}


def props(**kw):
    return {"properties": {k: v for k, v in kw.items()}}


def mesure(nom, table="_Mesures"):
    return {
        "field": {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": nom}},
        "queryRef": f"{table}.{nom}",
        "nativeQueryRef": nom,
    }


def colonne(table, col, active=None):
    p = {
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": col}},
        "queryRef": f"{table}.{col}",
        "nativeQueryRef": col,
    }
    if active is not None:
        p["active"] = active
    return p


def somme(table, col, fonction=0, libelle=None):
    noms = {0: "Sum", 1: "Avg"}
    p = {
        "field": {
            "Aggregation": {
                "Expression": {
                    "Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": col}
                },
                "Function": fonction,
            }
        },
        "queryRef": f"{noms[fonction]}({table}.{col})",
        "nativeQueryRef": f"{'Sum' if fonction == 0 else 'Average'} of {col}",
    }
    if libelle:
        p["displayName"] = libelle
    return p


def conteneur(titre=None, fond=True, bordure=True, padding=12):
    vco = {
        "padding": [
            props(top=lit(padding), bottom=lit(padding), left=lit(padding), right=lit(padding))
        ],
        "background": [props(show=lit(fond), transparency=lit(0))]
        if fond
        else [props(show=lit(False))],
        "border": [props(show=lit(bordure), color=couleur("#E3E8EF"), radius=lit(8), width=lit(1))]
        if bordure
        else [props(show=lit(False))],
    }
    if titre:
        vco["title"] = [
            props(
                show=lit(True),
                text=lit(titre),
                fontSize=lit(12),
                fontColor=couleur("#1F2A44"),
                bold=lit(True),
            )
        ]
    else:
        vco["title"] = [props(show=lit(False))]
    return vco


class Page:
    def __init__(self, nom, titre, fond, cache=False, extraction=None):
        self.id = uid("page", nom)
        self.nom, self.titre, self.fond, self.cache, self.extraction = (
            nom,
            titre,
            fond,
            cache,
            extraction,
        )
        self.visuels = []

    def ajouter(self, cle, x, y, w, h, visual):
        z = 1000 * (len(self.visuels) + 1)
        self.visuels.append(
            {
                "$schema": f"{SCHEMA}/visualContainer/{V_VISUAL}/schema.json",
                "name": uid(self.nom, cle),
                "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
                "visual": visual,
            }
        )


def carte_texte(
    mesures, taille_valeur=22, titre_page=False, couleur_valeur="#1F2A44", libelles=True
):
    """cardVisual : une ou plusieurs mesures ; le nom de la mesure sert de libellé."""
    v = {
        "visualType": "cardVisual",
        "query": {"queryState": {"Data": {"projections": [mesure(m) for m in mesures]}}},
        "objects": {
            "value": [
                {
                    **props(
                        fontSize=lit(taille_valeur),
                        fontColor=couleur(couleur_valeur),
                        bold=lit(True),
                    ),
                    "selector": {"id": "default"},
                }
            ],
            "label": [
                {
                    **props(show=lit(libelles), fontSize=lit(10), fontColor=couleur("#5B6B7F")),
                    "selector": {"id": "default"},
                }
            ],
            "outline": [{**props(show=lit(False)), "selector": {"id": "default"}}],
        },
        "drillFilterOtherVisuals": True,
    }
    if titre_page:  # titre posé sur le bandeau bleu : pas de fond, texte blanc, aligné à gauche
        v["objects"]["value"][0]["properties"]["fontColor"] = couleur("#FFFFFF")
        v["objects"]["label"][0]["properties"]["show"] = lit(False)
        v["objects"]["fillCustom"] = [{**props(show=lit(False)), "selector": {"id": "default"}}]
        v["visualContainerObjects"] = conteneur(fond=False, bordure=False, padding=0)
    else:
        v["visualContainerObjects"] = conteneur()
    return v


def bouton(texte, cible=None, retour=False, clair=False, largeur_police=12):
    lien = props(show=lit(True), type=lit("Back" if retour else "PageNavigation"))
    if cible:
        lien["properties"]["navigationSection"] = lit(cible)
    fond_ = "#FFFFFF" if clair else NAVY
    texte_c = NAVY if clair else "#FFFFFF"
    return {
        "visualType": "actionButton",
        "objects": {
            "text": [
                props(show=lit(True)),
                {
                    **props(
                        text=lit(texte),
                        fontSize=lit(largeur_police),
                        fontColor=couleur(texte_c),
                        horizontalAlignment=lit("left" if not clair else "center"),
                        bold=lit(True),
                    ),
                    "selector": {"id": "default"},
                },
            ],
            "icon": [props(show=lit(False))],
            "fill": [
                props(show=lit(True)),
                {
                    **props(fillColor=couleur(fond_), transparency=lit(0)),
                    "selector": {"id": "default"},
                },
                {
                    **props(fillColor=couleur(ORANGE if not clair else "#EAF0F6")),
                    "selector": {"id": "hover"},
                },
            ],
            "outline": [props(show=lit(False))],
            "shape": [props(tileShape=lit("rectangleRounded"))],
        },
        "visualContainerObjects": {
            "background": [props(show=lit(False))],
            "border": [props(show=lit(False))],
            "visualLink": [lien],
        },
        "drillFilterOtherVisuals": True,
    }


def couleurs_categories(table, col, valeurs_couleurs):
    """dataPoint : une couleur par valeur de catégorie / de série."""
    out = []
    for valeur, c in valeurs_couleurs.items():
        out.append(
            {
                **props(fill=couleur(c)),
                "selector": {
                    "data": [
                        {
                            "scopeId": {
                                "Comparison": {
                                    "ComparisonKind": 0,
                                    "Left": {
                                        "Column": {
                                            "Expression": {"SourceRef": {"Entity": table}},
                                            "Property": col,
                                        }
                                    },
                                    "Right": {
                                        "Literal": {"Value": "'" + valeur.replace("'", "''") + "'"}
                                    },
                                }
                            }
                        }
                    ]
                },
            }
        )
    return out


def axes_propres(etiquettes=True):
    return {
        "labels": [props(show=lit(etiquettes), fontSize=lit(10))],
        "valueAxis": [props(show=lit(True), gridlineShow=lit(False))],
        "categoryAxis": [props(show=lit(True), fontSize=lit(10))],
        "legend": [props(show=lit(True), position=lit("Top"), showTitle=lit(False))],
    }


def construire_pages():
    acc = Page("accueil", "Accueil", "fond_accueil.png")
    bc = Page("business", "Business case", "fond_page.png")
    fl = Page("flotte", "Flotte", "fond_page.png")
    st = Page("stock", "Stock", "fond_page.png")
    fi = Page(
        "fiche",
        "Fiche moteur",
        "fond_page.png",
        cache=True,
        extraction=("fact_alertes", "id_moteur"),
    )

    # ---------------- Accueil ----------------
    for i, (p, texte) in enumerate(
        [
            (bc, "Business case — combien ça rapporte ?"),
            (fl, "Flotte — quels moteurs traiter ?"),
            (st, "Stock — combien de modules garder ?"),
        ]
    ):
        acc.ajouter(
            f"nav{i}",
            620,
            168 + i * 72,
            400,
            56,
            bouton("   " + texte, cible=p.id, largeur_police=14),
        )
    acc.ajouter(
        "kpi",
        620,
        400,
        616,
        120,
        carte_texte(
            ["Économie annuelle", "Moteurs à planifier", "Dans le pire scénario testé"], 22
        ),
    )
    acc.ajouter(
        "maj",
        620,
        536,
        616,
        64,
        carte_texte(["Données du"], 11, couleur_valeur="#5B6B7F", libelles=False),
    )

    # Bouton Accueil + titre calculé sur le bandeau de chaque page de contenu
    for p, mesure_titre in [
        (bc, "Titre business case"),
        (fl, "Titre flotte"),
        (st, "Titre stock"),
        (fi, "Titre fiche"),
    ]:
        if p is fi:
            p.ajouter(
                "retour",
                16,
                10,
                96,
                36,
                bouton("◀ Retour", retour=True, clair=True, largeur_police=11),
            )
        else:
            p.ajouter(
                "accueil",
                16,
                10,
                96,
                36,
                bouton("◀ Accueil", cible=acc.id, clair=True, largeur_police=11),
            )
        p.ajouter("titre", 124, 6, 840, 46, carte_texte([mesure_titre], 16, titre_page=True))

    # ---------------- Business case ----------------
    bc.ajouter(
        "kpi",
        16,
        76,
        1248,
        112,
        carte_texte(
            [
                "Économie annuelle",
                "Par moteur et par an",
                "Déposes subies (sur 100)",
                "Dans le pire scénario testé",
            ],
            24,
        ),
    )
    v = {
        "visualType": "clusteredColumnChart",
        "query": {
            "queryState": {
                "Category": {"projections": [colonne("fact_strategies", "strategie", True)]},
                "Y": {"projections": [mesure("Coût annuel (M€)")]},
            },
            "sortDefinition": {
                "sort": [{"field": mesure("Coût annuel (M€)")["field"], "direction": "Descending"}]
            },
        },
        "objects": {
            **axes_propres(),
            "dataPoint": couleurs_categories(
                "fact_strategies",
                "strategie",
                {
                    "Réactive": ROUGE,
                    "Intervalle fixe (T = 152)": GRIS,
                    "Prédictive (marge 10)": NAVY,
                },
            ),
        },
        "visualContainerObjects": conteneur("Coût annuel de maintenance par stratégie (M€)"),
        "drillFilterOtherVisuals": True,
    }
    v["objects"]["legend"] = [props(show=lit(False))]
    bc.ajouter("strategies", 16, 204, 608, 476, v)
    v = {
        "visualType": "clusteredBarChart",
        "query": {
            "queryState": {
                "Category": {"projections": [colonne("fact_sensibilite", "hypothese", True)]},
                "Y": {
                    "projections": [
                        mesure("Économie si hypothèse -50 % (M€)"),
                        mesure("Économie si hypothèse +50 % (M€)"),
                    ]
                },
            }
        },
        "objects": {
            **axes_propres(),
            "dataPoint": [
                {
                    **props(fill=couleur(GRIS)),
                    "selector": {"metadata": "_Mesures.Économie si hypothèse -50 % (M€)"},
                },
                {
                    **props(fill=couleur(NAVY)),
                    "selector": {"metadata": "_Mesures.Économie si hypothèse +50 % (M€)"},
                },
            ],
        },
        "visualContainerObjects": conteneur(
            "L'économie reste positive quand chaque hypothèse varie de ±50 % (M€/an)"
        ),
        "drillFilterOtherVisuals": True,
    }
    bc.ajouter("sensibilite", 640, 204, 624, 476, v)

    # ---------------- Flotte ----------------
    fl.ajouter(
        "kpi", 16, 76, 760, 112, carte_texte(["À planifier (alerte)", "À surveiller", "RAS"], 26)
    )
    fl.ajouter(
        "segment",
        792,
        76,
        472,
        112,
        {
            "visualType": "slicer",
            "query": {
                "queryState": {"Values": {"projections": [colonne("fact_alertes", "statut", True)]}}
            },
            "objects": {
                "data": [props(mode=lit("Dropdown"))],
                "header": [props(show=lit(True), text=lit("Filtrer par statut"))],
            },
            "visualContainerObjects": conteneur(),
            "drillFilterOtherVisuals": True,
        },
    )
    v = {
        "visualType": "columnChart",
        "query": {
            "queryState": {
                "Category": {"projections": [colonne("fact_alertes", "tranche", True)]},
                "Series": {"projections": [colonne("fact_alertes", "statut")]},
                "Y": {"projections": [mesure("Nombre de moteurs")]},
            },
            "sortDefinition": {
                "sort": [
                    {"field": colonne("fact_alertes", "tranche")["field"], "direction": "Ascending"}
                ]
            },
        },
        "objects": {
            **axes_propres(),
            "dataPoint": couleurs_categories(
                "fact_alertes", "statut", {"Alerte": ROUGE, "Surveillance": ORANGE, "RAS": VERT}
            ),
        },
        "visualContainerObjects": conteneur("Moteurs par tranche de vols restants prévus"),
        "drillFilterOtherVisuals": True,
    }
    fl.ajouter("tranches", 16, 204, 520, 476, v)
    cols_table = [
        colonne("fact_alertes", c)
        for c in ["id_moteur", "statut", "motif_alerte", "rul_predite", "rul_basse_80"]
    ]
    libelles = {
        "id_moteur": "Moteur",
        "statut": "Statut",
        "motif_alerte": "Motif de l'alerte",
        "rul_predite": "Vols restants prévus",
        "rul_basse_80": "Scénario pessimiste",
    }
    for c in cols_table:
        c["displayName"] = libelles[c["nativeQueryRef"]]
    v = {
        "visualType": "tableEx",
        "query": {
            "queryState": {"Values": {"projections": cols_table}},
            "sortDefinition": {
                "sort": [
                    {
                        "field": colonne("fact_alertes", "rul_predite")["field"],
                        "direction": "Ascending",
                    }
                ]
            },
        },
        "objects": {
            "columnHeaders": [
                props(
                    fontColor=couleur("#FFFFFF"),
                    backColor=couleur(NAVY),
                    autoSizeColumnWidth=lit(True),
                    columnAdjustment=lit("growToFit"),
                )
            ],
            "values": [
                props(
                    fontSize=lit(10),
                    backColorPrimary=couleur("#FFFFFF"),
                    backColorSecondary=couleur("#F7F9FC"),
                ),
                {
                    **props(
                        backColor={"solid": {"color": {"expr": mesure("Couleur statut")["field"]}}}
                    ),
                    "selector": {
                        "data": [{"dataViewWildcard": {"matchingOption": 1}}],
                        "metadata": "fact_alertes.statut",
                    },
                },
            ],
        },
        "visualContainerObjects": conteneur(
            "Moteurs du plus urgent au plus sain · clic droit > Extraire > Fiche moteur"
        ),
        "drillFilterOtherVisuals": True,
    }
    fl.ajouter("liste", 552, 204, 712, 476, v)

    # ---------------- Stock ----------------
    st.ajouter(
        "kpi",
        16,
        76,
        984,
        112,
        carte_texte(
            ["Économie de stock", "Modules en entrepôt (classique → piloté)", "Capital libéré"], 22
        ),
    )
    st.ajouter(
        "prix",
        1016,
        76,
        248,
        112,
        {
            "visualType": "slicer",
            "query": {
                "queryState": {
                    "Values": {"projections": [colonne("Prix module", "prix_module", True)]}
                }
            },
            "objects": {
                "data": [props(mode=lit("Dropdown"))],
                "header": [props(show=lit(True), text=lit("Prix d'un module (€)"))],
            },
            "visualContainerObjects": conteneur(),
            "drillFilterOtherVisuals": True,
        },
    )
    v = {
        "visualType": "clusteredColumnChart",
        "query": {
            "queryState": {
                "Category": {
                    "projections": [colonne("fact_stock_politiques", "taux_service_libelle", True)]
                },
                "Series": {"projections": [colonne("fact_stock_politiques", "politique")]},
                "Y": {"projections": [mesure("Coût du stock (k€/an)")]},
            }
        },
        "objects": {
            **axes_propres(),
            "dataPoint": couleurs_categories(
                "fact_stock_politiques",
                "politique",
                {"Classique [R, Q]": GRIS, "Pilotée par le modèle": NAVY},
            ),
        },
        "visualContainerObjects": conteneur(
            "Coût de gestion du stock selon le taux de service visé (%) — k€/an"
        ),
        "drillFilterOtherVisuals": True,
    }
    st.ajouter("couts", 16, 204, 520, 476, v)
    v = {
        "visualType": "lineChart",
        "query": {
            "queryState": {
                "Category": {"projections": [colonne("fact_stock_journal", "jour", True)]},
                "Y": {
                    "projections": [
                        somme("fact_stock_journal", "stock", libelle="Modules en entrepôt"),
                        somme("fact_stock_journal", "seuil", libelle="Seuil de commande"),
                    ]
                },
                "Rows": {"projections": [colonne("fact_stock_journal", "politique")]},
            }
        },
        "objects": {
            "legend": [props(show=lit(True), position=lit("Top"), showTitle=lit(False))],
            "valueAxis": [props(show=lit(True), gridlineShow=lit(False))],
            "dataPoint": [
                {
                    **props(fill=couleur(NAVY)),
                    "selector": {"metadata": "Sum(fact_stock_journal.stock)"},
                },
                {
                    **props(fill=couleur(ROUGE)),
                    "selector": {"metadata": "Sum(fact_stock_journal.seuil)"},
                },
            ],
            "smallMultiplesLayout": [props(rowCount=lit(2), columnCount=lit(1))],
        },
        "visualContainerObjects": conteneur(
            "Deux ans de simulation : l'entrepôt reste plus bas quand le modèle pilote les commandes"
        ),
        "drillFilterOtherVisuals": True,
    }
    v["objects"]["smallMultiplesLayout"][0]["properties"] = {
        "rowCount": {"expr": {"Literal": {"Value": "2L"}}},
        "columnCount": {"expr": {"Literal": {"Value": "1L"}}},
    }
    st.ajouter("journal", 552, 204, 712, 476, v)

    # ---------------- Fiche moteur (page d'extraction) ----------------
    fi.ajouter(
        "kpi",
        16,
        76,
        1248,
        112,
        carte_texte(["Statut", "Motif", "Vols restants prévus", "Scénario pessimiste"], 18),
    )
    v = {
        "visualType": "lineChart",
        "query": {
            "queryState": {
                "Category": {"projections": [colonne("fact_vols", "cycle", True)]},
                "Y": {"projections": [mesure("Dérive (écarts-types)")]},
                "Rows": {"projections": [colonne("dim_capteur", "libelle")]},
            }
        },
        "objects": {
            "legend": [props(show=lit(False))],
            "valueAxis": [props(show=lit(True), gridlineShow=lit(False))],
            "dataPoint": [props(fill=couleur(NAVY))],
            "smallMultiplesLayout": [
                {
                    "properties": {
                        "rowCount": {"expr": {"Literal": {"Value": "3L"}}},
                        "columnCount": {"expr": {"Literal": {"Value": "4L"}}},
                    }
                }
            ],
        },
        "visualContainerObjects": conteneur(
            "Dérive de chaque capteur depuis que le moteur était neuf (moyenne sur 10 vols, en écarts-types)"
        ),
        "drillFilterOtherVisuals": True,
    }
    fi.ajouter("capteurs", 16, 204, 1248, 476, v)
    return [acc, bc, fl, st, fi]


def ecrire_rapport():
    d = RP / "definition"
    if d.exists():
        shutil.rmtree(d)
    # Ressources : thème personnalisé, thème de base, fonds de page
    res = RP / "StaticResources"
    images = {}
    for f in ["fond_accueil.png", "fond_page.png"]:
        nom_res = f.replace(".png", "") + "20261109000000000.png"
        ecrire_bin(res / "RegisteredResources" / nom_res, (ASSETS / f).read_bytes())
        images[f] = nom_res
    theme_nom = "theme_maintenance_predictive.json"
    ecrire_bin(res / "RegisteredResources" / theme_nom, (ASSETS / theme_nom).read_bytes())
    ecrire_bin(
        res / "SharedResources" / "BaseThemes" / "CY24SU10.json",
        (ASSETS / "CY24SU10.json").read_bytes(),
    )

    ecrire(
        d / "report.json",
        {
            "$schema": f"{SCHEMA}/report/{V_REPORT}/schema.json",
            "themeCollection": {
                "baseTheme": {
                    "name": "CY24SU10",
                    "reportVersionAtImport": "5.61",
                    "type": "SharedResources",
                },
                "customTheme": {
                    "name": theme_nom,
                    "reportVersionAtImport": "5.61",
                    "type": "RegisteredResources",
                },
            },
            "layoutOptimization": "None",
            "objects": {"outspacePane": [props(visible=lit(True), expanded=lit(False))]},
            "resourcePackages": [
                {
                    "name": "RegisteredResources",
                    "type": "RegisteredResources",
                    "items": [{"name": theme_nom, "path": theme_nom, "type": "CustomTheme"}]
                    + [{"name": n, "path": n, "type": "Image"} for n in images.values()],
                },
                {
                    "name": "SharedResources",
                    "type": "SharedResources",
                    "items": [
                        {
                            "name": "CY24SU10",
                            "path": "BaseThemes/CY24SU10.json",
                            "type": "BaseTheme",
                        }
                    ],
                },
            ],
            "settings": {
                "useStylableVisualContainerHeader": True,
                "defaultDrillFilterOtherVisuals": True,
                "allowChangeFilterTypes": True,
                "useEnhancedTooltips": True,
                "useDefaultAggregateDisplayName": True,
            },
        },
    )
    ecrire(
        d / "version.json",
        {"$schema": f"{SCHEMA}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"},
    )

    pages = construire_pages()
    ecrire(
        d / "pages" / "pages.json",
        {
            "$schema": f"{SCHEMA}/pagesMetadata/{V_PAGES}/schema.json",
            "pageOrder": [p.id for p in pages],
            "activePageName": pages[0].id,
        },
    )
    for p in pages:
        page = {
            "$schema": f"{SCHEMA}/page/{V_PAGE}/schema.json",
            "name": p.id,
            "displayName": p.titre,
            "displayOption": "FitToPage",
            "height": 720,
            "width": 1280,
            "objects": {
                "background": [
                    props(
                        image={
                            "image": {
                                "name": lit(p.fond),
                                "url": {
                                    "expr": {
                                        "ResourcePackageItem": {
                                            "PackageName": "RegisteredResources",
                                            "PackageType": 1,
                                            "ItemName": images[p.fond],
                                        }
                                    }
                                },
                                "scaling": lit("Fit"),
                            }
                        },
                        transparency=lit(0),
                    )
                ]
            },
        }
        if p.cache:
            page["visibility"] = "HiddenInViewMode"
        if p.extraction:
            table, col = p.extraction
            filtre = uid(p.nom, "filtre-extraction")
            page["type"] = "Drillthrough"
            page["filterConfig"] = {
                "filters": [
                    {
                        "name": filtre,
                        "field": {
                            "Column": {
                                "Expression": {"SourceRef": {"Entity": table}},
                                "Property": col,
                            }
                        },
                        "type": "Categorical",
                        "howCreated": "Drillthrough",
                    }
                ]
            }
            page["pageBinding"] = {
                "name": uid(p.nom, "binding"),
                "type": "Drillthrough",
                "referenceScope": "Default",
                "parameters": [
                    {
                        "name": uid(p.nom, "param"),
                        "boundFilter": filtre,
                        "fieldExpr": {
                            "Column": {
                                "Expression": {"SourceRef": {"Entity": table}},
                                "Property": col,
                            }
                        },
                    }
                ],
            }
        ecrire(d / "pages" / p.id / "page.json", page)
        for v in p.visuels:
            ecrire(d / "pages" / p.id / "visuals" / v["name"] / "visual.json", v)

    ecrire(
        RP / "definition.pbir",
        {"version": "4.0", "datasetReference": {"byPath": {"path": f"../{NOM}.SemanticModel"}}},
    )
    ecrire(
        RP / ".platform",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": "Report", "displayName": NOM},
            "config": {"version": "2.0", "logicalId": guid("report", NOM)},
        },
    )
    ecrire(
        SORTIE / f"{NOM}.pbip",
        {
            "version": "1.0",
            "artifacts": [{"report": {"path": f"{NOM}.Report"}}],
            "settings": {"enableAutoRecovery": True},
        },
    )
    ecrire(SORTIE / ".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
    return pages


def ecrire_bin(chemin, octets):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_bytes(octets)


def main():
    tables = ecrire_modele()
    pages = ecrire_rapport()
    nb_visuels = sum(len(p.visuels) for p in pages)
    print(f"Modèle : {len(tables)} tables, {len(MESURES)} mesures, {len(RELATIONS)} relations")
    print(f"Rapport : {len(pages)} pages, {nb_visuels} visuels")
    print(f"Données lues dans : {DONNEES}")
    print(f"Ouvrir : {SORTIE / (NOM + '.pbip')}")


if __name__ == "__main__":
    main()
