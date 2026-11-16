"""
Centre de contrôle du projet : une seule interface pour tout piloter.

Lancement, depuis la racine du projet : python -m streamlit run centre_de_controle.py
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

RACINE = Path(__file__).resolve().parent
DONNEES = RACINE / "outputs" / "powerbi"
RAPPORT = RACINE / "rapport" / "Maintenance predictive.pbip"
PARAMETRES_RAPPORT = (
    RACINE / "rapport" / "Maintenance predictive.SemanticModel" / "definition" / "expressions.tmdl"
)
NOTEBOOKS = {
    "01_exploration_FD001.ipynb": "Les capteurs annoncent-ils la panne ?",
    "02_modele_RUL_FD001.ipynb": "Combien de vols reste-t-il à chaque moteur ?",
    "03_alertes_FD001.ipynb": "Quels moteurs planifier dans les 30 vols ?",
    "04_stock_pieces_FD001.ipynb": "Combien de modules garder, et quand commander ?",
    "05_business_case_FD001.ipynb": "Combien économise-t-on ?",
}
ENCRE = "#1B2A3A"  # couleur du texte, reprise dans le graphique
COULEURS_STATUT = {"Alerte": "#D6232A", "Surveillance": "#F2C230", "RAS": "#2E7D5B"}
# Avertissement technique sans conséquence émis par chaque noyau Jupyter : on le masque
BRUIT = re.compile(r"\[IPKernelApp\] WARNING \| Kernel is running over TCP.*")

st.set_page_config(page_title="Carnet de bord de la flotte", page_icon="✈️", layout="wide")
st.html(f"<style>{(RACINE / 'assets' / 'centre.css').read_text(encoding='utf-8')}</style>")


# ---------------------------------------------------------------- utilitaires
def lire(table):
    return pd.read_csv(DONNEES / f"{table}.csv", sep=";", decimal=",", keep_default_na=False)


def date_de(chemin):
    return datetime.fromtimestamp(chemin.stat().st_mtime) if chemin.exists() else None


def fr(x, decimales=1):
    """12345.6 -> '12 345,6' (écriture française)."""
    return f"{x:,.{decimales}f}".replace(",", " ").replace(".", ",")


def note(texte):
    """Annotation manuscrite dans la marge (une par page, pas plus)."""
    st.html(f'<p class="note">{texte}</p>')


def carnet(lignes, fiche=True):
    """Lignes du carnet, libellé à gauche et valeur à droite : [(libellé, valeur), ...].
    Un 3e élément (True/False) ajoute une pastille verte ou rouge devant le libellé.
    fiche=True pose les lignes sur une fiche blanche, pour rester lisibles sur le ciel."""
    html = ""
    for libelle, valeur, *ok in lignes:
        pastille = ("ok" if ok[0] else "ko") if ok else ""
        html += (
            f'<div class="ligne"><span class="{pastille}">{libelle}</span><em>{valeur}</em></div>'
        )
    st.html(f'<div class="fiche">{html}</div>' if fiche else html)


def dossier_lu_par_le_rapport():
    """Le dossier de données que le rapport Power BI va lire (paramètre DossierDonnees)."""
    if not PARAMETRES_RAPPORT.exists():
        return None
    texte = PARAMETRES_RAPPORT.read_text(encoding="utf-8")
    trouve = re.search(r'expression DossierDonnees = "([^"]*)"', texte)
    return trouve.group(1) if trouve else None


def rapport_relie_aux_donnees():
    dossier = dossier_lu_par_le_rapport()
    return dossier is not None and Path(dossier.rstrip("\\/")).resolve() == DONNEES.resolve()


def executer(script, *arguments, titre):
    """Lance un script Python du projet et affiche sa sortie en direct. Renvoie True si tout va bien."""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}
    commande = [sys.executable, "-u", script, *arguments]
    journal, zone = [], st.empty()
    with st.status(titre, expanded=True) as statut:
        with subprocess.Popen(
            commande,
            cwd=RACINE,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as proc:
            for sortie in proc.stdout:
                if sortie := BRUIT.sub("", sortie).rstrip():
                    journal.append(sortie)
                    zone.code("\n".join(journal[-25:]), language=None)
        reussi = proc.returncode == 0
        statut.update(
            label=f"{titre} : {'terminé' if reussi else 'échec, voir le journal'}",
            state="complete" if reussi else "error",
            expanded=not reussi,
        )
    return reussi


def ouvrir(chemin):
    if os.name == "nt":
        os.startfile(chemin)  # ouvre avec le programme associé (Power BI Desktop pour un .pbip)
    else:
        st.info(f"Ouverture automatique disponible sous Windows. Fichier : `{chemin}`")


# ---------------------------------------------------------------- en-tête et menu
maj = date_de(DONNEES / "fact_alertes.csv")
st.html(f"""
<div class="entete">
  <div><h1>Carnet de bord<br>de la flotte</h1>
       <p>100 turboréacteurs simulés par la NASA (C-MAPSS, FD001), suivis vol après vol.</p></div>
  <div class="flamme">{f"Données du {maj:%d/%m/%Y}" if maj else "Aucune donnée"}
       <small>{f"mises à jour à {maj:%H:%M}" if maj else "lancer une mise à jour"}</small></div>
</div>""")

PAGES = ["La flotte", "Mettre à jour", "Rapport Power BI", "Notebooks", "Documentation"]
page = st.segmented_control("Menu", PAGES, default=PAGES[0], label_visibility="collapsed")


# ---------------------------------------------------------------- pages
def la_flotte():
    try:
        strategies, alertes = lire("fact_strategies"), lire("fact_alertes")
        stock, sensibilite = lire("fact_stock_politiques"), lire("fact_sensibilite")
    except FileNotFoundError:
        st.error("Les tables n'existent pas encore : lancez « Mettre à jour ».")
        return

    cout = strategies.set_index("stratégie")["coût annuel flotte (M€)"]
    cout_fixe = cout[cout.index.str.startswith("Intervalle fixe")].iloc[0]
    cout_predictif = cout[cout.index.str.startswith("Prédictive")].iloc[0]
    stock95 = stock[stock["taux_service_vise"] == 95].set_index("politique")["cout_total"]
    economie_stock = (stock95["Classique [R, Q]"] - stock95["Pilotée par le modèle"]) / 1e6
    economie = cout_fixe - cout_predictif + economie_stock
    statuts = alertes["statut"].value_counts()

    st.html(f"""
    <div class="instruments">
      <div><b>{fr(economie)} M€</b><span>économisés par an face au meilleur intervalle fixe</span></div>
      <div class="alerte"><b>{statuts.get("Alerte", 0)}</b><span>moteurs à déposer dans les 30 vols</span></div>
      <div><b>{statuts.get("Surveillance", 0)}</b><span>moteurs à surveiller (≤ 60 vols prévus)</span></div>
      <div><b>{fr(sensibilite["-50 %"].min())} M€</b><span>d'économie dans le pire scénario testé</span></div>
    </div>""")
    note("↑ maintenance + stock de pièces. Même en noircissant les hypothèses, ça reste positif.")

    gauche, droite = st.columns([3, 2], gap="large")
    with gauche:
        st.subheader("Où en est chaque moteur ?")
        couleurs = alt.Scale(domain=list(COULEURS_STATUT), range=list(COULEURS_STATUT.values()))
        traits = (
            alt.Chart(alertes)
            .mark_tick(thickness=3, size=26)
            .encode(
                x=alt.X("rul_predite:Q", title="Vols restants prévus").scale(domain=[0, 130]),
                y=alt.Y("statut:N", title=None, sort=list(COULEURS_STATUT)),
                color=alt.Color("statut:N", scale=couleurs, legend=None),
                tooltip=["id_moteur", "statut", alt.Tooltip("rul_predite", format=".0f")],
            )
        )
        horizon = alt.Chart(pd.DataFrame({"x": [30]})).mark_rule(strokeDash=[4, 4]).encode(x="x")
        graphique = (
            (traits + horizon)
            .properties(height=190, background="transparent")
            .configure(font="Archivo")
            .configure_axis(labelFont="Archivo", titleFont="Archivo")
            .configure_axis(
                labelFontSize=13,
                titleFontSize=13,
                labelColor=ENCRE,
                titleColor=ENCRE,
                domainColor=ENCRE,
                gridColor="#E3EAF1",
            )
            .configure_view(stroke=None)
        )
        with st.container(key="fiche_graphique"):
            st.altair_chart(graphique, width="stretch", theme=None)
            st.caption("Un trait par moteur. Pointillés : l'horizon d'alerte de 30 vols.")

    with droite:
        st.subheader("Les plus urgents")
        urgents = alertes.nsmallest(8, "rul_predite")
        carnet(
            (m.id_moteur, f"{m.statut}, {m.rul_predite:.0f} vols (au pire {m.rul_basse_80:.0f})")
            for m in urgents.itertuples()
        )


def mettre_a_jour():
    st.subheader("Relancer les calculs")
    st.write(
        "Les 5 notebooks tournent dans l'ordre et réécrivent les tables lues par Power BI. "
        "Le pipeline s'arrête au premier notebook en échec."
    )
    dates = {nom: date_de(RACINE / "notebooks" / nom) for nom in NOTEBOOKS}
    carnet(
        (question, f"exécuté le {dates[nom]:%d/%m à %H:%M}" if dates[nom] else "jamais exécuté")
        for nom, question in NOTEBOOKS.items()
    )
    note("compter un peu moins de 2 minutes pour tout refaire ☕")
    depuis = st.selectbox(
        "Repartir du notebook",
        [1, 2, 3, 4, 5],
        format_func=lambda i: list(NOTEBOOKS)[i - 1].removesuffix(".ipynb"),
    )
    if st.button("Lancer la mise à jour", type="primary"):
        if executer("run_pipeline.py", "--depuis", str(depuis), titre="Mise à jour des données"):
            st.success("Données à jour. Dans Power BI : Accueil, puis Actualiser.")


def rapport_powerbi():
    st.subheader("Le rapport Power BI")
    if not RAPPORT.exists():
        st.warning("Le rapport n'a pas encore été généré sur ce poste : cliquez sur Générer.")
    elif not rapport_relie_aux_donnees():
        st.error(
            f"Le rapport lit ses données dans `{dossier_lu_par_le_rapport()}`, alors qu'elles "
            f"sont dans `{DONNEES}` sur ce poste. Cliquez sur Générer pour le réparer."
        )
    else:
        carnet([("Rapport relié aux données de ce poste", str(DONNEES), True)])

    a, b, c = st.columns(3)
    if a.button("Générer le rapport", type="primary", width="stretch"):
        if executer("outils/generer_rapport_powerbi.py", titre="Génération du rapport"):
            st.rerun()
    if b.button("Ouvrir dans Power BI", width="stretch", disabled=not RAPPORT.exists()):
        ouvrir(RAPPORT)
    if c.button("Vérifier le rapport", width="stretch", disabled=not RAPPORT.exists()):
        executer("outils/valider_rapport_powerbi.py", titre="Vérification du rapport")

    st.subheader("Les pages")
    images = {
        "Accueil": "accueil",
        "Business case": "business_case",
        "Flotte": "flotte",
        "Stock": "stock",
        "Fiche moteur": "fiche_moteur",
    }
    for onglet, fichier in zip(st.tabs(list(images)), images.values(), strict=True):
        onglet.image(str(RACINE / "docs" / "images" / f"rapport_{fichier}.png"), width="stretch")


def notebooks():
    st.subheader("Les notebooks, dans l'ordre")
    with st.container(key="fiche_notebooks"):
        for nom, question in NOTEBOOKS.items():
            texte, bouton = st.columns([6, 1], vertical_alignment="center")
            with texte:
                carnet([(question, nom)], fiche=False)
            if bouton.button("Ouvrir", key=nom, width="stretch"):
                ouvrir(RACINE / "notebooks" / nom)


def documentation():
    docs = {
        "Contexte et références": RACINE / "docs" / "contexte_et_references.md",
        "Fiches de lecture": RACINE / "docs" / "corpus_lectures.md",
        "README": RACINE / "README.md",
    }
    choix = st.radio("Document", list(docs), horizontal=True, label_visibility="collapsed")
    texte = docs[choix].read_text(encoding="utf-8")
    with st.container(key="fiche_doc"):
        st.markdown(re.sub(r"!\[[^\]]*\]\([^)]*\)", "", texte))  # images : page « Rapport »


{
    "La flotte": la_flotte,
    "Mettre à jour": mettre_a_jour,
    "Rapport Power BI": rapport_powerbi,
    "Notebooks": notebooks,
    "Documentation": documentation,
}.get(page or PAGES[0])()
