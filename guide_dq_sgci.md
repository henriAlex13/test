# Guide Data Quality — SGCI
## Framework SchemaValidator + 6 Dimensions DQ + Journalisation
### Niveau débutant — Tout comprendre de A à Z

**Auteur** : Data Engineering SGCI | **Version** : 1.0 — Juin 2026

---

## Introduction — Pourquoi ce guide ?

En tant que Data Engineer à la SGCI, tu extrais chaque jour des données depuis **Teradata** via **Jupyter Notebook**. Ces données alimentent des reportings, des réconciliations comptables et des analyses risques.

Le problème : **une donnée de mauvaise qualité peut provoquer une erreur de reporting transmise à la BCEAO, une réconciliation fausse, ou une mauvaise décision métier.**

Ce guide t'explique, étape par étape, comment construire un **pipeline de validation automatique** qui vérifie tes données avant tout traitement.

---

## Vue d'ensemble du pipeline

Chaque fois que tu extrais des données depuis Teradata, le pipeline suit ces étapes dans l'ordre :

```
[Teradata]
    |
    v
[Étape 0] Configuration  →  Imports, constantes, logger
    |
    v
[Étape 1] Extraction SQL  →  Chargement des données dans un DataFrame
    |
    v
[Étape 2] SchemaValidator  →  Les données ont-elles la bonne structure ?
    |
    v
[Étape 3] 6 Dimensions DQ  →  Les données sont-elles de bonne qualité ?
    |
    v
[Étape 4] Pipeline principal  →  Décision : GO ou STOP
    |
    v
[Étape 5] Journalisation  →  Enregistrement du résultat dans un fichier log
```

Si une anomalie critique est détectée, le pipeline **s'arrête automatiquement** et enregistre l'erreur dans le journal.

---

## Étape 0 — Configuration

### Qu'est-ce que c'est ?

Avant de commencer à travailler, on prépare l'environnement : on importe les bibliothèques nécessaires, on définit les constantes et on crée le répertoire de logs.

### Pourquoi c'est important ?

Centraliser la configuration en haut du notebook permet de **changer un paramètre une seule fois** (par exemple le nom du projet ou le chemin des logs) sans avoir à modifier le code partout.

### Les éléments clés

**Les imports** sont les bibliothèques Python dont on a besoin :
- `pandas` : manipuler les tableaux de données (DataFrames)
- `numpy` : calculs numériques et statistiques
- `logging` : écrire des messages de log structurés
- `re` : vérifier les formats avec des expressions régulières (ex: format IBAN)
- `pytz` : gérer les fuseaux horaires (Abidjan = UTC+0)

**Les constantes** sont les valeurs fixes de ton projet :
- `LOG_DIR` : dossier où seront stockés les fichiers de log
- `LOG_FILE_NAME` : nom du fichier CSV de journal
- `TZ_ABIDJAN` : fuseau horaire local pour les calculs de dates
- `DEVISES_OK` : liste des devises autorisées à la SGCI (XOF, EUR, USD...)
- `TYPES_TRN_OK` : liste des types de transactions valides (VIR, PRE, CHQ...)

**Le logger** est un outil qui écrit des messages horodatés dans un fichier. C'est comme un journal de bord automatique de ton pipeline.

### Comment ça marche ?

```python
# Ce que fait le logger concrètement :
logger.info("Extraction démarrée")          # Message normal → INFO
logger.warning("3 valeurs nulles trouvées") # Anomalie non bloquante → WARNING
logger.error("Montants négatifs détectés")  # Erreur bloquante → ERROR

# Dans le fichier .log, tu verras :
# 2026-06-15 06:00:01 | INFO     | sgci_dq | Extraction démarrée
# 2026-06-15 06:00:02 | WARNING  | sgci_dq | 3 valeurs nulles trouvées
# 2026-06-15 06:00:03 | ERROR    | sgci_dq | Montants négatifs détectés
```

---

## Étape 1 — Connexion Teradata et Extraction

### Qu'est-ce que c'est ?

On se connecte à la base de données Teradata et on exécute une requête SQL pour récupérer les données dans un DataFrame pandas.

### Pourquoi c'est important ?

C'est le point de départ de tout. Si l'extraction échoue ou renvoie les mauvaises données, tout le reste est faux. On mesure aussi la durée de l'extraction pour la journaliser.

### Les éléments clés

**La connexion sécurisée** : on ne met jamais les mots de passe dans le code. On utilise des variables d'environnement :

```python
# MAUVAISE PRATIQUE — ne jamais faire ça
conn = teradatasql.connect(host="mon_serveur", password="MonMotDePasse123")

# BONNE PRATIQUE — lire depuis les variables d'environnement
conn = teradatasql.connect(
    host     = os.getenv("TD_HOST"),      # défini ailleurs, hors du code
    user     = os.getenv("TD_USER"),
    password = os.getenv("TD_PASSWORD")
)
```

**La requête SQL** est écrite séparément du code Python pour rester lisible et facilement modifiable :

```sql
SELECT t.TRN_REF, t.ACCOUNT_ID, t.AMOUNT, t.CURRENCY, ...
FROM SGCI_DB.TRANSACTIONS t
WHERE t.BOOKING_DATE = CURRENT_DATE - 1   -- données de J-1
```

**La mesure du temps** permet de savoir combien de temps dure l'extraction :

```python
t_debut = time.time()
df = pd.read_sql(query, connexion)
duree = round(time.time() - t_debut, 2)   # durée en secondes
```

### Mode démonstration

Comme on ne peut pas se connecter à Teradata en dehors du réseau SGCI, le notebook inclut une fonction `simuler_extraction()` qui crée un DataFrame fictif avec exactement la même structure que les vraies données. Elle injecte volontairement des anomalies pour tester que les contrôles DQ fonctionnent bien.

---

## Étape 2 — SchemaValidator

### Qu'est-ce que c'est ?

Le `SchemaValidator` est une classe Python qui vérifie la **structure** du DataFrame avant tout traitement. Il répond à la question : "Est-ce que mes données ont la bonne forme ?"

### Pourquoi c'est important ?

Si une colonne obligatoire manque, ou si les types de données sont incorrects, toutes les étapes suivantes vont planter. Le SchemaValidator détecte ces problèmes structurels en premier.

### La notion de "API fluente"

Le SchemaValidator utilise une syntaxe chaînée : chaque méthode retourne l'objet lui-même, ce qui permet d'enchaîner les contrôles sur une seule ligne :

```python
# Sans chaînage (verbeux)
sv = SchemaValidator("ma_table", logger)
sv.check_required_columns(df, ["col1", "col2"])
sv.check_no_null(df, ["col1"])
sv.check_positive(df, "montant")

# Avec chaînage (propre et lisible)
sv = (SchemaValidator("ma_table", logger)
      .check_required_columns(df, ["col1", "col2"])
      .check_no_null(df, ["col1"])
      .check_positive(df, "montant")
)
```

### Les 8 méthodes disponibles

**1. check_required_columns** — Vérifie que toutes les colonnes attendues sont présentes.

```python
# Exemple : si la colonne AMOUNT manque dans le DataFrame,
# c'est une ERREUR BLOQUANTE (le pipeline s'arrête)
.check_required_columns(df, ["TRN_REF", "ACCOUNT_ID", "AMOUNT"])
```

**2. check_no_null** — Vérifie qu'aucune valeur nulle n'est présente sur les colonnes importantes.

```python
# Exemple : TRN_REF ne peut jamais être null
# → c'est un AVERTISSEMENT (le pipeline continue mais alerte)
.check_no_null(df, ["TRN_REF", "ACCOUNT_ID"])
```

**3. check_range** — Vérifie que les valeurs sont dans un intervalle logique.

```python
# Exemple : un montant ne peut pas dépasser 500 millions XOF
.check_range(df, "AMOUNT", min_val=0, max_val=500_000_000)
```

**4. check_positive** — Vérifie que toutes les valeurs sont supérieures ou égales à zéro.

```python
# Exemple : un montant ne peut pas être négatif
.check_positive(df, "AMOUNT")
```

**5. check_negative** — Vérifie que toutes les valeurs sont inférieures ou égales à zéro.

```python
# Exemple : un solde débiteur doit toujours être négatif
.check_negative(df, "SOLDE_DEBITEUR")
```

**6. check_type** — Vérifie que les valeurs correspondent au type Python attendu.

```python
# Exemple : la référence transaction doit être une chaîne de caractères
.check_type(df, "TRN_REF", str)
```

**7. check_unique_by** — Vérifie l'absence de doublons sur une ou plusieurs colonnes.

```python
# Exemple : TRN_REF doit être unique dans toute la table
.check_unique_by(df, ["TRN_REF"])
```

**8. check_no_full_duplicates** — Vérifie qu'aucune ligne entière n'est identique à une autre.

```python
# Exemple : deux lignes ayant exactement les mêmes valeurs partout
# → c'est forcément une erreur d'extraction
.check_no_full_duplicates(df)
```

### La différence entre Erreur et Warning

| Type | Signification | Effet sur le pipeline |
|---|---|---|
| **ERREUR** | Problème structurel grave | Pipeline arrêté (FAIL) |
| **WARNING** | Anomalie non bloquante | Pipeline continue (PASS avec alerte) |

Par exemple, une colonne manquante est une ERREUR (on ne peut pas continuer), mais 3 valeurs nulles sur un champ non critique est un WARNING (on continue mais on note).

---

## Étape 3 — Les 6 Dimensions Data Quality

### Qu'est-ce que c'est ?

Les 6 dimensions sont les 6 angles sous lesquels on évalue la qualité des données. Chaque dimension répond à une question différente.

### Pourquoi 6 dimensions ?

Parce qu'une donnée peut avoir plusieurs types de problèmes en même temps. Un montant peut être présent (complétude OK), unique (unicité OK), mais complètement aberrant (exactitude KO). Il faut vérifier tous les angles.

---

### Dimension 1 — Complétude

**La question :** "Est-ce que toutes les valeurs obligatoires sont renseignées ?"

**Le risque SGCI :** Un montant null fausse les totaux. Une référence transaction nulle bloque la réconciliation.

**Comment ça marche :** On parcourt chaque colonne et on compte les valeurs nulles et les chaînes vides. Si une colonne critique a des valeurs manquantes, c'est un ECHEC.

```python
# Exemple concret :
# Sur 300 transactions, 3 ont un AMOUNT null
# → ces 3 lignes vont en quarantaine
# → le statut de la dimension est ECHEC
```

**Le taux de remplissage** mesure le pourcentage de valeurs présentes :
- 100% : parfait, toutes les valeurs sont là
- 95% : 5% de valeurs manquantes, à investiguer
- 80% : problème sérieux, probablement une erreur d'extraction

---

### Dimension 2 — Unicité

**La question :** "Est-ce que chaque enregistrement n'apparaît qu'une seule fois ?"

**Le risque SGCI :** Un doublon sur TRN_REF signifie que la même transaction est comptée deux fois dans les agrégats financiers.

**D'où viennent les doublons ?** En général de jointures SQL mal construites, ou d'une extraction qui chevauche une précédente (fenêtre temporelle mal paramétrée).

**Comment ça marche :** On utilise `duplicated()` de pandas pour trouver toutes les lignes qui partagent la même valeur sur la clé primaire.

```python
# Exemple concret :
# TRN00000001 apparaît 2 fois dans le DataFrame
# → 2 lignes dupliquées détectées
# → statut ECHEC
# → on peut dédupliquer avec deduplication_securisee()
```

**La déduplication sécurisée** supprime les doublons en loggant combien ont été supprimés. Trois stratégies disponibles :
- `garder_premier` : garde la première occurrence (le plus souvent utilisé)
- `garder_dernier` : garde la dernière occurrence
- `garder_tous` : retourne uniquement les doublons pour les examiner

---

### Dimension 3 — Validité

**La question :** "Est-ce que les valeurs respectent le format et le domaine autorisé ?"

**Le risque SGCI :** Une devise "CFA" au lieu de "XOF" bloque les traitements de conversion. Un IBAN mal formé empêche le virement.

**Les contrôles effectués :**

Pour les **devises** : on vérifie que la valeur est dans la liste `{XOF, EUR, USD, GBP, CHF, JPY, CNY}`. Si on trouve "CFA" ou "xof" (minuscule), c'est invalide.

Pour les **types de transaction** : on vérifie que la valeur est dans `{VIR, PRE, CHQ, CBK, FEE, INT, DIV, SWIFT}`. Un type inconnu signifie une donnée non référencée.

Pour les **dates** : on essaie de convertir en format date. Si la conversion échoue (ex: "32/13/2026"), la date est invalide.

Pour les **IBAN** : on vérifie le format avec une expression régulière. Un IBAN valide commence par 2 lettres, 2 chiffres, puis des caractères alphanumériques.

**L'astuce technique importante :** On applique `.str` uniquement sur les valeurs non-nulles pour éviter l'erreur `AttributeError: Can only use .str accessor with string values!`. C'est pourquoi on utilise `.notna()` avant.

---

### Dimension 4 — Exactitude

**La question :** "Est-ce que les valeurs numériques sont dans des plages cohérentes avec la réalité ?"

**Le risque SGCI :** Un montant négatif sur un crédit est une erreur de signe lors de la transformation. Un solde de 999 milliards XOF est probablement une erreur de chargement.

**Les contrôles effectués :**

**Montants négatifs** : un montant de transaction ne peut pas être négatif. Si c'est le cas, c'est une erreur de transformation (le signe a été inversé quelque part).

**Montants nuls** : un montant de 0 XOF sur une transaction ordinaire est suspect. C'est un avertissement, pas forcément bloquant (certaines opérations peuvent légitimement être à 0).

**Outliers par méthode IQR** : on utilise la méthode statistique IQR (Interquartile Range) pour détecter les valeurs aberrantes. On calcule les quartiles Q1 et Q3, puis on définit une borne supérieure à Q3 + 3×(Q3-Q1). Tout ce qui dépasse est suspect.

```
Exemple :
Q1 = 50 000 XOF, Q3 = 2 000 000 XOF
IQR = 2 000 000 - 50 000 = 1 950 000
Borne sup = 2 000 000 + 3 × 1 950 000 = 7 850 000 XOF
→ Toute transaction > 7 850 000 XOF est signalée comme outlier
```

On utilise ×3 (et non ×1.5 classique) car en banque, les montants ont naturellement une distribution très étalée. Un virement de 500 millions XOF est rare mais légitime.

---

### Dimension 5 — Cohérence

**La question :** "Est-ce que les données sont logiquement compatibles entre elles ?"

**Le risque SGCI :** Une VALUE_DATE antérieure de plus de 30 jours à la BOOKING_DATE indique une anomalie. Un déséquilibre entre le total des débits et des crédits invalide la journée comptable.

**Les contrôles effectués :**

**Cohérence temporelle** : la date de valeur (VALUE_DATE) ne peut pas être antérieure de plus de 30 jours à la date de comptabilisation (BOOKING_DATE). Si c'est le cas, les dates ont probablement été inversées.

**Équilibre débit/crédit** : sur une journée bancaire, le total des mouvements débit doit équilibrer le total des mouvements crédit (à 1 XOF près pour les arrondis). Un écart important signale une perte de données.

**Clés orphelines** : on croise les ACCOUNT_ID des transactions avec la table de référence des comptes. Si un compte apparaît dans les transactions mais pas dans le référentiel, c'est une incohérence (compte inconnu ou fermé).

**L'astuce technique importante :** On compare les dates uniquement sur les lignes où les deux dates sont non-nulles (`mask_valid`). Comparer une date valide avec une valeur `NaT` (date nulle) causerait une erreur.

---

### Dimension 6 — Fraîcheur

**La question :** "Est-ce que les données sont bien celles d'aujourd'hui (J-1) ?"

**Le risque SGCI :** Si la table Teradata n'a pas été rechargée la nuit, on extrait les données de J-2 en croyant avoir J-1. Le reporting du matin est alors basé sur des données périmées.

**Les contrôles effectués :**

**Date maximale** : on cherche la date la plus récente dans la colonne de référence (BOOKING_DATE). Si elle correspond à J-1, les données sont fraîches. Si elle correspond à J-2 ou avant, les données sont périmées.

**Extraction vide** : si le DataFrame est vide (0 lignes), soit la table n'a pas été alimentée, soit la requête SQL a un problème de filtre de date.

**Tolérance** : on peut configurer une tolérance de 1 jour. En pratique, cela signifie qu'on accepte J-1 mais pas J-2 ou avant.

```
Exemple concret :
Date du jour          : 2026-06-15
Date attendue (J-1)   : 2026-06-14
Date max dans les data: 2026-06-14  → ✅ Données fraîches
Date max dans les data: 2026-06-13  → ❌ Données périmées (retard 1 jour)
Date max dans les data: 2026-06-10  → ❌ Données périmées (retard 4 jours)
```

---

## Étape 4 — Pipeline principal

### Qu'est-ce que c'est ?

La fonction `run_pipeline_dq()` est le chef d'orchestre. Elle appelle le SchemaValidator puis les 6 dimensions dans l'ordre, collecte tous les résultats et produit un rapport structuré.

### Pourquoi un seul appel ?

Pour simplifier l'utilisation. Au lieu d'appeler 7 fonctions séparément et de gérer les résultats à la main, un seul appel fait tout :

```python
rapport = run_pipeline_dq(
    df                 = df_raw,
    nom_extraction     = "transactions_J1",
    colonnes_critiques = ["TRN_REF", "AMOUNT", "VALUE_DATE"],
    cles_primaires     = ["TRN_REF"],
    schema_validator   = sv,
    df_reference       = df_comptes,
    cle_jointure       = "ACCOUNT_ID",
    col_date_ref       = "BOOKING_DATE"
)
```

### Le rapport retourné

La fonction retourne un dictionnaire Python avec toutes les informations :

```python
rapport = {
    "extraction"  : "transactions_J1",      # Nom de l'extraction
    "timestamp"   : "2026-06-15T06:01:23",  # Date et heure d'exécution
    "date_donnees": "2026-06-14",           # Date des données (J-1)
    "nb_lignes"   : 303,                    # Nombre de lignes extraites
    "nb_colonnes" : 11,                     # Nombre de colonnes
    "valide"      : False,                  # True = GO, False = STOP
    "dimensions"  : {                       # Statut de chaque dimension
        "schema"     : "AVERTISSEMENT",
        "completude" : "ECHEC",
        "unicite"    : "ECHEC",
        "validite"   : "ECHEC",
        "exactitude" : "ECHEC",
        "coherence"  : "ECHEC",
        "fraicheur"  : "OK"
    },
    "erreurs"     : ["COMPLETUDE : ECHEC", "UNICITE : ECHEC"],
    "warnings"    : ["SCHEMA : 3 doublons"],
    "duration_s"  : 0.45                    # Durée en secondes
}
```

### Les 4 statuts possibles

| Statut | Signification | Couleur |
|---|---|---|
| **OK** | Aucune anomalie détectée | Vert |
| **AVERTISSEMENT** | Anomalie non bloquante | Orange |
| **ECHEC** | Anomalie bloquante | Rouge |
| **SKIP** | Contrôle non applicable | Gris |

---

## Étape 5 — Journalisation

### Qu'est-ce que c'est ?

La journalisation consiste à enregistrer le résultat de chaque exécution du pipeline dans des fichiers persistants. C'est la traçabilité du pipeline.

### Pourquoi c'est indispensable ?

En banque, tout doit être traçable. Si un incident survient, on doit pouvoir répondre à : "Le pipeline a-t-il bien tourné ce matin ? Combien de lignes ont été traitées ? Y avait-il des anomalies ?"

### Les 3 fichiers produits

**1. Le fichier `.log` (texte)** — écrit en temps réel pendant l'exécution :

```
2026-06-15 06:00:01 | INFO     | sgci_dq | Pipeline démarré
2026-06-15 06:00:02 | INFO     | sgci_dq | 303 lignes extraites en 0.12s
2026-06-15 06:00:03 | WARNING  | sgci_dq | SchemaValidator → PASS | 3 doublons
2026-06-15 06:00:04 | ERROR    | sgci_dq | Complétude → FAIL | AMOUNT : 3 nulls
```

**2. Le fichier `journal_dq.csv`** — une ligne par exécution, format tabulaire :

| Execution_Date | User | Project | File_Name | Frequency | Row_Number | Status | Error_Reason |
|---|---|---|---|---|---|---|---|
| 2026-06-15T06:00 | alex | SGCI_DQ | transactions_J1 | Quotidien | 303 | Bad | COMPLETUDE : ECHEC |
| 2026-06-14T06:00 | alex | SGCI_DQ | transactions_J1 | Quotidien | 298 | Good | |

Ce fichier est **cumulatif** : chaque nouvelle exécution ajoute une ligne. On peut ainsi suivre l'historique sur plusieurs semaines ou mois.

**3. Le rapport Excel** — 4 onglets pour partager avec les équipes :

- **Résumé** : une ligne avec toutes les métriques de l'exécution
- **Dimensions** : tableau avec le statut de chaque dimension DQ
- **Erreurs & Warnings** : liste détaillée de toutes les anomalies
- **Journal** : l'historique complet des exécutions passées

### La fonction log() en détail

```python
log(
    log_dir        = "./JOURNAL/",          # où stocker le fichier
    log_file_name  = "journal_dq.csv",      # nom du fichier
    Execution_Date = "2026-06-15T06:00:01", # quand ?
    User           = "alex",                # qui ?
    Project        = "SGCI_DQ",             # quel projet ?
    File_Name      = "transactions_J1",     # quelle extraction ?
    Frequency      = "Quotidien",           # quelle fréquence ?
    Data_Begin     = "2026-06-14",          # début des données
    Data_End       = "2026-06-14",          # fin des données
    File_Size      = 245.7,                 # taille en Ko
    Row_Number     = 303,                   # nb de lignes
    Column_Number  = 11,                    # nb de colonnes
    Duration       = 0.45,                  # durée en secondes
    Status         = "Bad",                 # Good ou Bad
    Error_Reason   = "COMPLETUDE : ECHEC"   # détail des erreurs
)
```

---

## Passer en production

Deux étapes suffisent pour passer du mode démo au mode production réel :

**Étape 1 : Définir les credentials Teradata** (une seule fois par session Jupyter) :

```python
import os
os.environ["TD_HOST"]     = "adresse_du_serveur_teradata"
os.environ["TD_USER"]     = "ton_identifiant"
os.environ["TD_PASSWORD"] = "ton_mot_de_passe"
```

**Étape 2 : Remplacer la simulation par les vraies extractions** :

```python
# Remplacer cette ligne :
df_raw, df_comptes = simuler_extraction(n=300)

# Par ces deux lignes :
df_raw     = extraire_depuis_teradata(QUERY_TRANSACTIONS, "transactions_J1")
df_comptes = extraire_depuis_teradata(QUERY_COMPTES, "referentiel_comptes")
```

---

## Résumé des fonctions

| Fonction | Rôle | Étape |
|---|---|---|
| `setup_pipeline_logger()` | Crée le logger fichier + console | 0 |
| `get_connection()` | Connexion sécurisée Teradata | 1 |
| `extraire_depuis_teradata()` | Extraction SQL + mesure durée | 1 |
| `SchemaValidator` | Validation structurelle (8 contrôles) | 2 |
| `verifier_completude()` | Dimension 1 — valeurs manquantes | 3 |
| `verifier_unicite()` | Dimension 2 — doublons | 3 |
| `verifier_validite()` | Dimension 3 — formats et domaines | 3 |
| `verifier_exactitude()` | Dimension 4 — plages numériques | 3 |
| `verifier_coherence()` | Dimension 5 — logique inter-colonnes | 3 |
| `verifier_fraicheur()` | Dimension 6 — données à jour | 3 |
| `run_pipeline_dq()` | Orchestre tout en un appel | 4 |
| `log()` | Journalise dans le CSV cumulatif | 5 |
| `exporter_rapport_excel()` | Rapport Excel 4 onglets | 5 |

---

## FAQ — Questions fréquentes

**Q : Pourquoi ne pas mettre le mot de passe directement dans le code ?**
R : Un code avec un mot de passe en clair peut être partagé accidentellement (email, Git, impression). En utilisant des variables d'environnement, le mot de passe n'est jamais dans le code.

**Q : Quelle est la différence entre une erreur et un warning ?**
R : Une erreur est bloquante : le pipeline s'arrête et les données ne sont pas chargées. Un warning est informatif : le pipeline continue mais l'anomalie est notée dans le journal.

**Q : Que faire si le pipeline retourne ECHEC ?**
R : Regarder dans `rapport["erreurs"]` pour identifier quelle dimension a échoué. Ouvrir le fichier Excel → onglet "Erreurs & Warnings" pour le détail. Corriger les données sources ou ajuster les paramètres de validation.

**Q : Peut-on utiliser ce framework pour d'autres tables que TRANSACTIONS ?**
R : Oui. Il suffit de changer la requête SQL, les `COLONNES_CRITIQUES`, les `CLES_PRIMAIRES` et les colonnes passées au SchemaValidator. Le reste fonctionne tel quel.

**Q : Que se passe-t-il si Teradata est indisponible ?**
R : La fonction `extraire_depuis_teradata()` va lever une exception. Le pipeline s'arrête, l'erreur est loggée. Il faut relancer manuellement quand Teradata est de nouveau disponible.

---

*SGCI Data Engineering · Guide Data Quality v1.0 · Juin 2026*
