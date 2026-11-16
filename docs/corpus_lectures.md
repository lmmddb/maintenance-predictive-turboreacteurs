# Corpus de lectures — fiches de synthèse

Cinq documents, lus en entier, résumés pour savoir de quoi ils parlent sans les relire. Chaque fiche suit le même plan : **l'idée en une phrase → ce qu'il faut retenir → les chiffres clés → ce qu'on en fait dans le projet → l'esprit critique**.

Les PDF ne sont pas redistribués ici (droits d'auteur) : les liens sont dans `contexte_et_references.md`, auquel renvoient les numéros [x].

---

## Le fil rouge : comment les 5 documents s'emboîtent

```
POURQUOI c'est important          → Oliver Wyman 2026 [14]
   flotte vieillissante, ateliers moteurs saturés, chaque dépose imprévue coûte plus cher
        │
QUI le fait, et COMMENT           → Bastard et al. 2016 (Safran) [10]
   la chaîne industrielle : capteur → normalisation → alerte → diagnostic → RUL → rapport client
        │
SUR QUELLES DONNÉES               → Saxena et al. 2008 [1]
   comment C-MAPSS a été fabriqué, donc ce que nos données contiennent vraiment
        │
COMMENT BIEN MODÉLISER            → Ramasso & Saxena 2014 [3]
   ce qui a marché sur ces données, les pièges, et les scores à battre
        │
COMMENT TRANSFORMER ÇA EN €       → Rodrigues & Yoneyama 2012 [8]
   passer d'une prédiction de panne à un point de commande de pièces
```

Notre projet suit exactement ce fil : notebooks 01-03 pour la prédiction, 04-05 pour le stock et les euros, 06 pour le rapport au décideur.

---

## Fiche 1 — Oliver Wyman (février 2026), *Global Fleet and MRO Market Forecast 2026-2036*

**Auteurs :** Brian Prentice, Paul Harper, Livia Hayes. 26e édition annuelle de la prévision de référence du secteur.

### L'idée en une phrase
La demande de transport aérien explose mais les avionneurs ne livrent pas assez d'avions neufs : les compagnies font donc voler des avions plus vieux, plus longtemps, ce qui fait flamber la maintenance, surtout celle des moteurs.

### Ce qu'il faut retenir
1. **2025 est une année record côté demande** : recettes passagers au-dessus de 1 000 milliards de dollars pour la première fois, trafic 9 % au-dessus du pic de 2019.
2. **L'offre ne suit pas.** Environ 17 000 avions en commande, soit plus de 12 ans de production au rythme actuel. La production de fin 2025 reste 24 % sous 2019. Airbus vise 75 A320 par mois en 2027 mais en sort 54 ; Boeing vise 57 737 mais n'est autorisé qu'à 42.
3. **Donc la flotte vieillit et vole plus.** L'âge moyen approche 13 ans, un an et demi de plus en un an, et les heures de vol par avion augmentent encore.
4. **La maintenance (MRO) est en « supercycle ».** Plus d'entretien, plus de pièces, des prix qui montent. **Les moteurs sont le premier poste du marché MRO et le plus touché** par les goulots d'étranglement : pénurie de titane et de composites, retard accumulé pendant le Covid et l'immobilisation du 737 MAX (l'effet « vague d'étrave »), délais d'atelier qui s'allongent.
5. **La main-d'œuvre manque.** Aux États-Unis, 41 % des mécaniciens certifiés ont plus de 60 ans, et environ 45 000 partiront à la retraite dans la décennie.
6. **Les géographies qui montent :** l'Inde (+7,1 % par an de flotte) et le Moyen-Orient (+5 %). Ce sont justement les environnements chauds et poussiéreux qui usent le plus les moteurs (cf. kits de durabilité LEAP [12]).

### Chiffres clés
| Indicateur | Valeur |
|---|---|
| Marché MRO mondial 2025 | **136 Md$** (+8 % vs 126 Md$ en 2024) |
| Marché MRO fin de décennie | ~193 Md$, presque le double de 2019 |
| Marché MRO 2036 (scénario révisé) | ~198 Md$, croissance de 3,7 %/an |
| Flotte mondiale | ~30 000 avions en 2026 → ~41 000 en 2036 |
| Bénéfice net des compagnies 2025 | 39,5 Md$ (marge 3,9 %) |

### Ce qu'on en fait dans le projet
- **L'introduction du rapport décideur** : on n'optimise pas la maintenance par plaisir, on le fait parce que les ateliers moteurs sont saturés et que chaque dépose imprévue immobilise un avion plus longtemps qu'avant.
- **Le business case (notebook 05)** : dans ce contexte, un moteur ou un module de rechange disponible vaut plus cher qu'en temps normal. Ça justifie de tester des coûts de rupture de stock élevés dans l'analyse de sensibilité.

### Esprit critique
- C'est une **page web de synthèse**, pas le rapport complet (payant). On a les grandes tendances, pas le détail par segment ni la part exacte des moteurs.
- Une petite incohérence interne : la croissance de flotte est de 3,2 % par an dans le corps du texte et de 3,5 % dans la mise à jour géopolitique. C'est le scénario révisé après un choc au Moyen-Orient ; on cite le chiffre en précisant le scénario.

---

## Fiche 2 — Bastard, Lacaille, Coupard, Stouky (2016), *Engine Health Management in Safran Aircraft Engines*

**Contexte :** PHM Society, 2016. Les quatre auteurs sont chez Safran Aircraft Engines (site de Réau / Moissy-Cramayel). Jérôme Lacaille y est **Expert Émérite Safran** pour les algorithmes de surveillance moteur.

### L'idée en une phrase
Safran décrit l'architecture de son système de surveillance de santé moteur (EHM) : comment les données remontent de l'avion, sont transformées en indicateurs, en alertes, en prédictions de durée de vie, puis en recommandations au client.

### Ce qu'il faut retenir
1. **Ce n'est pas nouveau chez Safran** : plus de 30 ans de suivi de tendance moteur. L'EHM est vu comme un **service client** (fidélisation, contrats à l'heure de vol), pas seulement comme un outil technique.
2. **Une partie embarquée, une partie au sol.** L'avion calcule et compresse des « instantanés » de données en vol, les envoie par ACARS, SATCOM, 3G ou Wi-Fi souvent avant même l'atterrissage. Le sol décode, stocke, calcule les indicateurs, et vise une mise à disposition **en moins de 5 minutes**.
3. **Une architecture standard en 6 couches (OSA-CBM)** :

| Couche | Rôle | Équivalent dans notre projet |
|---|---|---|
| DA — acquisition | sélectionner les données utiles | chargement C-MAPSS (`data_loader.py`) |
| DM — préparation | nettoyer, **retirer l'effet du contexte de vol** (altitude, température…) | qualité des données + normalisation par régime (FD004) |
| SD — détection | comparer à une référence saine, lever une alerte si dérive | indice de santé, seuil d'alerte (notebook 03) |
| HA — diagnostic | identifier quelle panne | mode de panne HPC vs soufflante (FD003/FD004) |
| PA — pronostic | **estimer la RUL** | modèle RUL (notebook 02) |
| AG — aide à la décision | tableaux de bord, rapports, recommandations | **Power BI** (notebook 06) |

4. **Des objectifs de performance explicites** : moins de 5 % de fausses alertes, au moins 80 % des événements détectés. Chaque alerte est **validée par un humain** (le Customer Support Center) avant d'être envoyée à la compagnie, sous forme de rapport client (CNR) sur un portail web.
5. **Le suivi de la marge EGT est exactement notre problème** : Safran normalise la température des gaz d'échappement aux conditions standard, suit sa tendance et **pronostique le nombre de cycles avant d'atteindre la limite**.
6. **La vision « au-delà de la maintenance »** : relier l'EHM à la GMAO pour planifier « juste à temps », fournir les pièces de rechange « juste ce qu'il faut », et à l'ERP pour **anticiper les dépenses**. C'est la passerelle vers notre partie stock.
7. **Interprétabilité vs performance** : pour le diagnostic, les réseaux bayésiens sont préférés pour leur lisibilité, les forêts aléatoires sont plus robustes mais moins interprétables. Le même arbitrage qu'on aura à expliquer au décideur.
8. Exemple décrit en détail : le **Silvercrest** (moteur d'avion d'affaires) ; les plateformes LEAP arrivent, avec un environnement commun en construction.

### Ce qu'on en fait dans le projet
- **Structurer le rapport final selon les 6 couches OSA-CBM.** Ça montre qu'on parle le langage du métier.
- **Reprendre leurs objectifs comme critères d'acceptation** de notre alerte « panne dans les 30 vols » (notebook 03) : taux de fausses alertes < 5 %, taux de détection ≥ 80 %.
- **Assumer le « human in the loop »** : notre modèle propose, l'ingénieur valide. À écrire dans le rapport décideur.

### Esprit critique
- Le papier décrit une architecture, **sans aucun résultat chiffré** sur les économies réalisées.
- Il date de 2016 et porte sur un moteur d'affaires, pas sur le LEAP. Les principes restent, les outils ont évolué.

---

## Fiche 3 — Saxena, Goebel, Simon, Eklund (2008), *Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation*

**Contexte :** NASA Ames, NASA Glenn et GE Global Research. Conférence PHM08. C'est le papier qui a **créé nos données**.

### L'idée en une phrase
Comme personne ne publie de vraies données moteur jusqu'à la panne, la NASA en a simulé avec C-MAPSS en imposant une usure progressive aux modules, et ce papier explique comment.

### Ce qu'il faut retenir
1. **Le simulateur** représente un gros turbofan civil de la classe 90 000 livres de poussée, avec son système de régulation. 21 des 58 sorties possibles sont fournies comme capteurs.
2. **L'usure est exponentielle** : quasi invisible au début, elle s'accélère vers la fin. Elle est simulée comme une perte de débit et de rendement du module.
3. **Chaque moteur part d'un état différent** (usure initiale jusqu'à 1 %, liée aux variations de fabrication), avec sa propre vitesse d'usure.
4. **Trois couches de bruit** : variations de fabrication, bruit de « processus » (qui inclut la maintenance courante entre les vols, d'où des moteurs qui semblent parfois s'améliorer), et bruit de mesure capteur.
5. **La « panne » est un seuil, pas une casse** : l'indice de santé est la plus faible de plusieurs marges (décrochage soufflante et compresseurs, température des gaz). Quand il atteint zéro, le moteur doit être déposé.
6. **Le score officiel est asymétrique** : une prédiction en retard est plus pénalisée qu'une prédiction en avance, et la pénalité grimpe de façon exponentielle avec l'erreur.

### Ce qu'on en fait
Détaillé dans `contexte_et_references.md`, section 2 : plafond RUL, comparaison de chaque moteur à lui-même, lissage, normalisation par régime de vol, score asymétrique.

### Esprit critique
- Ce sont des **données simulées**. Elles sont propres, sans trous ni capteurs en panne, et chaque moteur ne subit qu'une usure de type perte de performance. La vraie vie est plus sale (cf. Fiche 2 : Safran surveille aussi la dérive des capteurs eux-mêmes).
- Le papier recommande lui-même de **pondérer davantage les moteurs proches de la fin de vie** et de vérifier la **régularité** du modèle sur la flotte.

---

## Fiche 4 — Ramasso & Saxena (2014), *Performance Benchmarking and Analysis of Prognostic Methods for CMAPSS Datasets*

**Contexte :** FEMTO-ST (Besançon) et NASA Ames. Revue publiée dans l'*International Journal of PHM*, six ans après la sortie des données.

### L'idée en une phrase
Plus de 7 000 téléchargements et 70 publications plus tard, presque personne n'a évalué ses résultats de la même façon. Les auteurs remettent de l'ordre : ce qui distingue les jeux de données, ce qui a marché, et des scores de référence pour se comparer honnêtement.

### Ce qu'il faut retenir
1. **Le constat sévère** : sur 40 publications vraiment exploitables, seule une poignée a utilisé correctement le protocole complet (entraîner sur le train, évaluer sur le test officiel). Beaucoup comparent des résultats obtenus sur des jeux différents, ce qui n'a pas de sens.
2. **FD001 → FD004 est une progression** à suivre dans l'ordre : on ajoute d'abord les régimes de vol, puis un deuxième mode de panne. FD001 représente à lui seul environ 70 % des usages, parce que c'est le plus simple.
3. **Trois grandes familles de méthodes** :

| Famille | Principe | Exemple |
|---|---|---|
| 1. Capteurs → RUL directement | apprentissage supervisé classique | réseaux de neurones, Heimes (2e du challenge) |
| 2. Capteurs → **indice de santé** → RUL | on résume d'abord l'état du moteur en un seul chiffre, puis on projette sa courbe | régressions exponentielles, processus de Wiener, mises à jour bayésiennes |
| 3. **Similarité** | on compare la trajectoire du moteur à celles des moteurs déjà tombés en panne | Wang et al., **gagnant du challenge** |

   Les méthodes par similarité généralisent bien sur les quatre jeux, malgré le bruit et les régimes multiples.

4. **Les recettes des gagnants** : lissage du bruit (filtre de Kalman, lissage à noyau), **regroupement des 6 régimes de vol par K-means** puis normalisation par régime, sélection de capteurs, et **plafonnement de la RUL prédite** pour éviter les prédictions tardives, très pénalisées. Heimes décrit l'usure en 4 phases (stable, coude, accélération, panne) et plafonne à 130.
5. **Le sous-ensemble de capteurs le plus utilisé** dans la littérature est issu du gagnant. ⚠️ Le papier les numérote **par colonne du fichier** (7, 8, 9, 12, 16, 17, 20), pas par numéro de capteur. Traduit dans notre notation, ça donne **s2, s3, s4, s7, s11, s12, s15**. Les 7 font partie de nos 12 capteurs retenus dans le notebook 01.
6. **Pas de métrique universelle** : un algorithme mal classé au score PHM peut être meilleur sur d'autres critères. On choisit ses métriques selon l'usage métier.
7. **Les 5 étapes recommandées** : comprendre les données → définir le problème → préparer (découper le train en train/validation, sélectionner les capteurs) → apprendre et prédire → évaluer avec plusieurs métriques.

### Chiffres clés : les scores à battre sur FD001
Meilleur résultat publié sur le protocole complet, à la date de la revue (méthode RULCLIPPER) :

| Métrique | FD001 | FD002 | FD003 | FD004 |
|---|---|---|---|---|
| Score PHM (plus bas = mieux) | **216** | 2 796 | 317 | 3 132 |
| Erreur absolue moyenne (vols) | **10** | 17 | 12 | 18 |
| Erreur quadratique moyenne | 176 (soit ~13 vols d'erreur type) | 524 | 256 | 592 |

### Ce qu'on en fait dans le projet
- **Objectif chiffré pour le notebook 02** : sur FD001, viser une erreur type autour de 13 vols et un score PHM autour de 200-250. On le présente comme « niveau de l'état de l'art 2014 », pas comme une vérité absolue.
- **Protocole propre** : validation croisée *par moteur* sur le train (jamais deux bouts du même moteur dans le train et la validation), puis une seule évaluation finale sur le test officiel.
- **Comparer deux familles** : un modèle direct (gradient boosting) et une approche par similarité, plus explicable pour un décideur.
- **Comparer notre sélection de capteurs** à celle de la littérature (vérification ajoutée au notebook 01).

### Esprit critique
- La revue date de 2014. Le deep learning a depuis amélioré les scores (Li et al. 2018 [6] et suivants). Nos objectifs sont un plancher raisonnable, pas un plafond.
- Petite incohérence entre ce papier et le readme NASA sur le nombre de moteurs de FD004. Vérification faite sur nos fichiers : **249 en train, 248 en test**. C'est ce papier qui a raison, le readme les inverse.

---

## Fiche 5 — Rodrigues & Yoneyama (2012), *Spare Parts Inventory Control for Non-Repairable Items Based on PHM Information*

**Contexte :** Embraer et ITA (Brésil). Conférence PHM Society, 2012.

### L'idée en une phrase
Les prédictions de panne ne servent pas qu'à la maintenance : la logistique peut s'en servir pour commander les pièces au bon moment. Le papier montre qu'on tient le même taux de service avec un coût total plus bas.

### Ce qu'il faut retenir
1. **Les trois coûts d'un stock** :
   - **commande** : un coût fixe par commande, plus le prix des pièces ;
   - **stockage** : capital immobilisé, entrepôt, assurance, obsolescence, par pièce et par jour ;
   - **rupture** : l'avion attend sa pièce (AOG), par pièce manquante et par jour.
2. **Le modèle classique [R, Q]** : dès que le stock (y compris les commandes en route) descend au **point de commande R**, on commande **Q pièces**. Q se calcule avec la formule de la quantité économique de commande (EOQ), qui équilibre coût de commande, de stockage et de rupture. R se fixe pour couvrir la demande pendant le délai fournisseur, avec un **taux de service** choisi par le management (par exemple 95 % de chances de ne pas être en rupture). Dans ce modèle, R est **fixe**.
3. **L'idée du papier : un point de commande R(t) qui bouge chaque jour** selon les prédictions de panne. Exemple concret :
   - le délai fournisseur est de 15 jours ;
   - le système PHM dit que le composant A a 80 % de chances de tomber en panne d'ici là, B 50 %, C 10 % ;
   - on en déduit la probabilité d'avoir 0, 1, 2 ou 3 pannes avant la livraison : 9 %, 46 %, 41 %, 4 % ;
   - pour un taux de service de 95 %, il faut **2 pièces** en stock (96 % de chances d'être couvert). Donc R(t) = 2 aujourd'hui. Demain, avec de nouvelles prédictions, R(t) changera.
4. **La simulation** : deux flottes identiques de 10 avions sur 15 ans, l'une gérée en [R, Q] classique, l'autre avec R(t) piloté par le PHM. Paramètres : délai 15 jours, une panne tous les 180 jours en moyenne (± 30), rupture 5 fois plus chère par jour que le stockage. Cinq taux de service testés (80 à 99 %), 15 simulations chacun.
5. **Le résultat** : le modèle piloté par le PHM est **moins cher à tous les taux de service**, et l'écart grandit quand on vise un taux de service élevé. L'économie vient **entièrement du coût de stockage** : on achète les pièces plus près du moment où on en a besoin, elles dorment moins longtemps en entrepôt. Les coûts de commande et de rupture restent quasi identiques.

### Ce qu'on en fait dans le projet
- **C'est le squelette du notebook 04.** On reprend exactement cette comparaison : [R, Q] classique contre R(t) piloté par nos prédictions de RUL, sur notre flotte C-MAPSS.
- **Conséquence importante pour le notebook 02** : la méthode a besoin d'une **probabilité de panne avant une date**, pas d'une RUL unique. Notre modèle devra donc fournir **une incertitude** (une fourchette de RUL, par exemple par régression quantile ou à partir de la distribution des erreurs en validation). C'est un vrai choix de conception à anticiper dès maintenant.
- **Le message décideur est simple et chiffrable** : même taux de service, moins de capital immobilisé en stock.

### Esprit critique
- Les coûts sont en **unités monétaires fictives**, et la flotte est petite (10 avions). L'ordre de grandeur de l'économie n'est pas transposable tel quel.
- Le modèle traite **une seule pièce, non réparable, un seul entrepôt**. Or un module moteur est réparable : il part en atelier et revient. Les auteurs le citent eux-mêmes comme extension à faire.
- La qualité de la méthode dépend **entièrement de la qualité des probabilités** fournies par le modèle de pronostic. Si notre modèle est trop confiant, on sera en rupture plus souvent que prévu. On vérifiera la calibration.

---

## Ce que ces lectures changent concrètement à la suite

| Décision | Source | Notebook |
|---|---|---|
| Normaliser les capteurs par régime de vol (K-means sur les 3 réglages) | Ramasso & Saxena [3], Bastard et al. [10] | 02 (FD004) |
| Validation croisée par moteur, une seule évaluation sur le test officiel | Ramasso & Saxena [3] | 02 |
| Objectif : ~13 vols d'erreur type et score PHM ~200-250 sur FD001 | Ramasso & Saxena [3] | 02 |
| Prédire une **fourchette** de RUL, pas seulement une valeur | Rodrigues & Yoneyama [8] | 02 |
| Tester une approche par similarité en plus du modèle direct | Ramasso & Saxena [3], Wang et al. [5] | 02 |
| Critères de l'alerte : < 5 % de fausses alertes, ≥ 80 % de détection | Bastard et al. [10] | 03 |
| Point de commande dynamique R(t) vs [R, Q] classique | Rodrigues & Yoneyama [8] | 04 |
| Coûts de rupture élevés dans l'analyse de sensibilité (ateliers saturés) | Oliver Wyman [14] | 05 |
| Rapport final structuré selon les 6 couches OSA-CBM | Bastard et al. [10] | 06 |
