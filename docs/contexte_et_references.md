# Contexte métier et références

Ce document répond à trois questions :
1. **De quoi parle-t-on ?** Le vocabulaire et les enjeux de la maintenance moteur, pour quelqu'un qui ne vient pas de l'aéro.
2. **Qu'est-ce que le papier de référence change à notre modèle ?** Les choix concrets qu'on en tire.
3. **Sur quoi s'appuie-t-on ?** La bibliographie annotée, avec pour chaque source ce qu'on en retient et où on s'en sert dans le projet.

---

## 1. Le contexte en 5 minutes

### Le problème industriel

Un turboréacteur civil (type CFM56 ou LEAP, produits par CFM International, coentreprise 50/50 Safran–GE) s'use à chaque vol. Ses modules tournants (soufflante, compresseurs basse et haute pression, turbines haute et basse pression) perdent progressivement en **débit** et en **rendement**. Le moteur compense en chauffant plus et en consommant plus, jusqu'au moment où il sort de ses marges de sécurité. Il faut alors le **déposer** et l'envoyer en atelier : c'est une **visite atelier** (*shop visit*).

Tout l'enjeu est le moment de cette dépose :
- **trop tôt**, on jette de la durée de vie utile et on paie une visite atelier inutilement tôt ;
- **trop tard**, la dépose devient non programmée, voire l'avion est cloué au sol (**AOG**, *Aircraft On Ground*). C'est le scénario le plus cher : avion immobilisé, passagers à indemniser, pièces et moteur de remplacement à trouver en urgence.

Entre les deux, il y a la logistique : pour remplacer un moteur ou un module déposé, il faut une pièce **disponible au bon endroit au bon moment**. Trop de stock immobilise du capital (un moteur de rechange vaut plusieurs millions d'euros). Pas assez, et la moindre dépose imprévue devient un AOG.

### Pourquoi c'est un sujet brûlant en 2025-2026

- La flotte LEAP dépasse les **4 000 avions livrés** (CFM, novembre 2025). Ses premières années de service ont révélé une usure plus rapide que prévu de la **turbine haute pression** dans les environnements sévères (chauds, poussiéreux). Résultat : des visites atelier plus fréquentes que sur le CFM56, son prédécesseur.
- CFM a répondu par un **kit de durabilité HPT** (certifié fin 2024, plus de 1 200 kits produits en moins d'un an), censé plus que doubler le temps sous l'aile en environnement sévère, et déployé sur le LEAP-1B (737 MAX) à partir de 2026.
- Le marché de la maintenance (**MRO**, *Maintenance, Repair & Overhaul*) est saturé et les chaînes d'approvisionnement tendues. Les ateliers et les pièces manquent, donc chaque dépose mal anticipée coûte plus cher qu'avant.

**Conséquence pour notre projet :** prévoir *quand* un moteur doit être déposé, et en déduire *combien* de pièces avoir en stock, n'est pas un exercice académique. C'est exactement ce que font les équipes **EHM** (*Engine Health Management*) de Safran Aircraft Engines.

### Glossaire

| Terme | Ce que ça veut dire |
|---|---|
| **RUL** (*Remaining Useful Life*) | Durée de vie restante, ici en nombre de vols (cycles) avant la panne |
| **Cycle** | Un vol complet (décollage → atterrissage). Unité de base de l'usure moteur |
| **EHM / PHM** | *Engine / Prognostics & Health Management* : surveiller l'état de santé d'un équipement et prédire son évolution |
| **Pronostic vs diagnostic** | Diagnostic = « qu'est-ce qui ne va pas ? ». Pronostic = « combien de temps ça va encore tenir ? » |
| **HPC / HPT / LPC / LPT** | Compresseur haute pression / turbine haute pression / compresseur basse pression / turbine basse pression |
| **EGT** (*Exhaust Gas Temperature*) | Température des gaz en sortie. L'indicateur d'usure le plus suivi en exploitation : un moteur usé chauffe plus |
| **Marge EGT** | Écart entre l'EGT actuelle et la limite autorisée. Quand elle tombe à zéro, le moteur doit être déposé |
| **Visite atelier** (*shop visit*) | Dépose du moteur et passage en atelier de révision |
| **Temps sous l'aile** (*time on wing*) | Durée pendant laquelle un moteur reste en service entre deux visites atelier |
| **AOG** (*Aircraft On Ground*) | Avion immobilisé faute de pièce ou de moteur en état de voler |
| **MRO** | Maintenance, réparation et révision : le marché de l'après-vente aéro |
| **Moteur de rechange** (*spare engine*) | Moteur posé à la place d'un moteur déposé pour que l'avion reprenne le service pendant la révision |
| **Point de commande** (*reorder point*) | Niveau de stock qui déclenche une commande, calculé pour couvrir la demande pendant le délai fournisseur |

---

## 2. Ce que le papier de référence change à notre modèle

**Saxena, Goebel, Simon & Eklund (2008)** est le papier qui a créé le jeu de données C-MAPSS pour le challenge PHM'08. Il explique *comment* les pannes ont été simulées, donc *ce que* les données contiennent vraiment. Six points orientent directement nos choix.

| Ce que dit le papier | Ce qu'on en fait |
|---|---|
| **L'usure suit une loi exponentielle** : elle est quasi invisible au début puis s'accélère vers la fin. | Confirme le plafonnement de la cible RUL (notebook 01, section 7) : inutile de demander au modèle de distinguer deux moteurs encore sains. |
| **Chaque moteur démarre avec une usure initiale différente** (jusqu'à 1 % de dégradation), liée aux variations de fabrication. | Dans le notebook 02, on ajoutera des variables « écart par rapport aux premiers vols du moteur ». On compare chaque moteur à lui-même, pas à la moyenne de la flotte. |
| **La maintenance entre deux vols est simulée comme du bruit** : un moteur peut sembler « s'améliorer » d'un vol à l'autre. Le bruit capteur s'ajoute par-dessus. | Justifie le lissage (moyennes glissantes) avant modélisation. Un vol isolé ne veut rien dire, c'est la tendance qui compte. |
| **La panne est déclarée quand l'indice de santé atteint zéro**, cet indice étant la **plus faible** des marges (décrochage soufflante, HPC, HPT, EGT). | Notre « panne » est un seuil d'exploitation, pas une casse physique. En langage métier : c'est le moment où le moteur doit être déposé. C'est ce qu'on prédit. |
| **Les conditions de vol (altitude, Mach, manette) modifient fortement les capteurs.** | Pour FD002 et FD004 (6 régimes de vol), on normalisera chaque capteur *par régime* avant de modéliser. Sinon le modèle confond « vol à haute altitude » et « moteur usé ». |
| **Le score officiel est asymétrique** : prédire une panne trop tard est plus pénalisé que la prédire trop tôt. La pénalité grimpe de façon exponentielle avec l'erreur (paramètres 13 si en avance, 10 si en retard). | On évaluera nos modèles avec **ce score en plus du RMSE**. C'est aussi un argument métier : une prédiction tardive veut dire un AOG, une prédiction précoce une dépose un peu prématurée. |

Le papier suggère aussi deux pistes qu'on reprend :
- **donner plus de poids aux moteurs proches de la fin de vie** dans l'évaluation, parce que c'est là que l'erreur coûte cher ;
- **vérifier la régularité du modèle sur toute la flotte**, pas seulement son erreur moyenne. Un modèle excellent sur 80 moteurs et catastrophique sur 20 est inutilisable pour planifier.

---

## 3. Bibliographie annotée

### A. Les données

**[1] Saxena, A., Goebel, K., Simon, D., Eklund, N. (2008).** *Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation.* 1st International Conference on Prognostics and Health Management (PHM08), Denver. DOI : 10.1109/PHM.2008.4711414.
→ Le papier fondateur du jeu de données, détaillé en section 2. **Utilisé partout.**

**[2] Arias Chao, M., Kulkarni, C., Goebel, K., Fink, O. (2021).** *Aircraft Engine Run-to-Failure Dataset under Real Flight Conditions for Prognostics and Diagnostics.* Data, 6(1), 5. https://www.mdpi.com/2306-5729/6/1/5
→ N-CMAPSS, la version plus réaliste : vols complets enregistrés sur un avion de ligne, 5 modules pouvant se dégrader. **Piste d'extension** si on veut montrer que la méthode tient sur des données plus proches du réel.

**[3] Ramasso, E., Saxena, A. (2014).** *Performance Benchmarking and Analysis of Prognostic Methods for CMAPSS Datasets.* International Journal of PHM, 5(2). https://papers.phmsociety.org/index.php/ijphm/article/view/2236
→ Revue de plus de 70 publications utilisant C-MAPSS, avec les performances des gagnants du challenge PHM'08 comme référence. Les auteurs soulignent que beaucoup de résultats publiés sont incomparables faute de protocole commun. **Utilisé pour situer nos performances** (notebook 02) et suivre un protocole propre.

### B. Méthodes de prédiction de la RUL

**[4] Heimes, F. O. (2008).** *Recurrent Neural Networks for Remaining Useful Life Estimation.* PHM08, pp. 1-6. DOI : 10.1109/PHM.2008.4711422
→ Un des meilleurs classements du challenge PHM'08, et le travail qui a popularisé la **cible RUL plafonnée** (constante tant que le moteur est sain, puis décroissante). **Justifie notre choix du notebook 01.**

**[5] Wang, T., Yu, J., Siegel, D., Lee, J. (2008).** *A Similarity-Based Prognostics Approach for Remaining Useful Life Estimation of Engineered Systems.* PHM08. DOI : 10.1109/PHM.2008.4711421
→ L'approche gagnante du challenge : comparer la trajectoire d'un moteur en service à celles des moteurs déjà tombés en panne, et s'inspirer des plus ressemblants. Très explicable pour un décideur (« ce moteur ressemble à ces 5 moteurs, qui ont tenu encore 40 vols »). **Candidat comme modèle de référence interprétable.**

**[6] Li, X., Ding, Q., Sun, J.-Q. (2018).** *Remaining Useful Life Estimation in Prognostics Using Deep Convolution Neural Networks.* Reliability Engineering & System Safety, 172, 1-11.
→ Référence deep learning très citée sur C-MAPSS, avec un plafond RUL à 125. **Sert de point de comparaison** : on montrera ce qu'un modèle plus simple et plus explicable (gradient boosting) perd ou non par rapport à ce niveau.

### C. Évaluer un modèle de pronostic

**[7] Saxena, A., Celaya, J., Saha, B., Saha, S., Goebel, K. (2010).** *Metrics for Offline Evaluation of Prognostic Performance.* International Journal of PHM, 1(1). https://papers.phmsociety.org/index.php/ijphm/article/view/1336
→ Propose des métriques propres au pronostic : elles jugent si la prédiction s'améliore à l'approche de la panne, et pas seulement l'erreur moyenne. **Utilisé pour le choix des métriques** du notebook 02.

### D. Du pronostic au stock de pièces

**[8] Rodrigues, L. R., Yoneyama, T. (2012).** *Spare Parts Inventory Control for Non-Repairable Items Based on Prognostics and Health Monitoring Information.* Annual Conference of the PHM Society, 4(1). DOI : 10.36001/phmconf.2012.v4i1.2118
→ Auteurs chez Embraer et à l'ITA (Brésil). Ils comparent une gestion de stock classique (point de commande + quantité économique) à une gestion qui commande en fonction des RUL prédites, par simulation. **C'est le squelette du notebook 04** : même comparaison, appliquée à notre flotte.

**[9] Rodrigues, L. R., Yoneyama, T. (2013).** *Maintenance Planning Optimization Based on PHM Information and Spare Parts Availability.* Annual Conference of the PHM Society, 5(1). https://papers.phmsociety.org/index.php/phmconf/article/view/2215
→ Va plus loin : planifier les déposes en tenant compte des pièces disponibles. Le papier avance certaines déposes pour éviter que plusieurs moteurs tombent en même temps quand le stock ne suit pas. Sur 15 ans simulés, la disponibilité de la flotte s'améliore et le coût total baisse. **Inspire le notebook 05** (business case).

### E. Contexte industriel Safran / CFM

**[10] Bastard, G., Lacaille, J., Coupard, J., Stouky, Y. (2016).** *Engine Health Management in Safran Aircraft Engines.* Annual Conference of the PHM Society, 8(1). https://papers.phmsociety.org/index.php/phmconf/article/view/2523
→ Écrit par des ingénieurs de Safran Aircraft Engines, dont Jérôme Lacaille, Expert Émérite Safran pour les algorithmes de surveillance moteur. Décrit l'architecture de leur système de surveillance moteur. **La preuve que notre projet correspond à un vrai métier chez Safran.**

**[11] Safran (2019).** *Analyzing data to improve engine maintenance.* https://www.safran-group.com/news/analyzing-data-improve-engine-maintenance-2019-06-12
→ Présente les services data de Safran : collecte des données de vol (WEFA), analyse (Cassiopée), suivi moteur aviation d'affaires (ForeVision), planification de maintenance hélicoptères (BOOST). Objectif affiché : prévoir les pannes pour planifier la maintenance et réduire l'immobilisation. **Pour l'introduction.**

**[12] CFM International (17 novembre 2025).** *CFM International reaches new milestones for LEAP engine maturity.* https://www.cfmaeroengines.com/press-articles/cfm-international-reaches-new-milestones---for-leap-engine-maturity
→ Plus de 4 000 avions livrés, plus de 1 200 kits de durabilité HPT produits en moins d'un an, kit censé plus que doubler le temps sous l'aile en environnement sévère, déploiement LEAP-1B en 2026. **Pour l'introduction : l'usure moteur est un sujet d'actualité.**

**[13] Diagilev, E. (2025).** *The real cost of AOG.* Air Cargo Week. https://aircargoweek.com/the-real-cost-of-aog/
→ Ordres de grandeur du coût d'un AOG moteur : de 50 000 à 150 000 $ par jour, plus de 600 000 $ au-delà de trois jours. Une dépose non programmée coûterait 30 à 50 % de plus qu'une dépose planifiée. ⚠️ **Source commerciale** (fournisseur de bancs moteurs), chiffres non sourcés. On ne l'utilise que pour **calibrer les hypothèses de coûts** du notebook 05, en le disant explicitement, et on fera une analyse de sensibilité.

**[14] Prentice, B., Harper, P., Hayes, L. (février 2026).** *Global Fleet and MRO Market Forecast 2026-2036.* Oliver Wyman. https://www.oliverwyman.com/our-expertise/insights/2026/feb/global-fleet-and-mro-market-forecast-2026-2036.html.
→ La prévision annuelle de référence du secteur. Marché MRO de 136 Md$ en 2025 (+8 %), environ 193 Md$ d'ici la fin de la décennie. Les moteurs sont le premier poste et le plus touché par les goulots d'étranglement. La flotte vieillit (près de 13 ans d'âge moyen) faute de livraisons suffisantes. **Pour l'introduction et le business case.**

---

## Fiches de lecture

Les documents [1], [3], [8], [10] et [14] sont résumés en détail dans [`corpus_lectures.md`](corpus_lectures.md) : idée principale, chiffres clés, ce qu'on en fait dans le projet, esprit critique et message en une phrase.

## Pistes

- Une référence sur la gestion des moteurs de rechange (dimensionnement d'un pool de *spare engines*).
