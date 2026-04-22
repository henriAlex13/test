# Guide Utilisateur — Framework DQ Simplifié SGCI
## Tout ce que tu dois savoir pour valider tes extractions Teradata

**Auteur** : Data Engineering SGCI | **Version** : 1.0 — Juin 2026

---

## Table des matières

1. [À quoi sert ce framework ?](#1)
2. [Structure des dossiers](#2)
3. [Étape 0 — Setup](#3)
4. [Étape 1 — Se connecter à Teradata](#4)
5. [Étape 2 — Les 5 contrôles DQ](#5)
6. [Étape 3 — Lancer le pipeline avec run_dq()](#6)
7. [Étape 4 — Journaliser avec log()](#7)
8. [Étape 5 — Consulter les résultats](#8)
9. [Template pour une nouvelle requête](#9)
10. [Questions fréquentes](#10)

---

## 1. À quoi sert ce framework ? <a id='1'></a>

Chaque fois que tu extrais des données depuis Teradata dans Jupyter, tu as besoin de savoir si ces données sont fiables avant de les utiliser ou de les transmettre. Ce framework t'aide à répondre automatiquement à 5 questions essentielles.

### Les 5 questions posées sur chaque extraction

| # | Contrôle | Question posée | Exemple de problème détecté |
|---|---|---|---|
| 1 | **Unicité** | Y a-t-il des lignes entièrement dupliquées ? | La même transaction extraite 2 fois |
| 2 | **Complétude** | Le nombre de lignes est-il dans l'intervalle attendu ? | 0 lignes un jour de batch qui a planté |
| 3 | **Fraîcheur** | Les données contiennent-elles des lignes dans la période d'extraction ? | Extraction de J-2 au lieu de J-1 |
| 4 | **Cohérence** | Aucune colonne n'est-elle entièrement vide ? | Colonne BRANCH_CODE vide suite à une migration |
| 5 | **Validité** | Les colonnes sont-elles dans le bon type ? | Colonne MVT_ID retournée en float au lieu d'int |

### Ce qui se passe après les contrôles

```
Extraction Teradata
       ↓
   run_dq()  →  5 contrôles lancés automatiquement
       ↓
  Toutes OK ?
  ┌────┴────┐
 OUI       NON
  ↓         ↓
Export    Pas d'export
CSV       (erreur dans le log)
  ↓         ↓
 log()    log()
  ↓         ↓
journal_dq.csv mis à jour
```

- Si **toutes les dimensions sont OK** : le DataFrame est exporté en CSV dans le dossier `./EXPORTS/`, prêt à être utilisé.
- Si **au moins une dimension est en ECHEC** : aucun fichier n'est exporté. L'erreur est enregistrée dans le journal pour que tu puisses l'investiguer.

---

## 2. Structure des dossiers <a id='2'></a>

Après la première exécution, tu trouveras cette arborescence dans ton répertoire de travail :

```
ton_projet/
├── mon_notebook.ipynb          ← ton notebook Jupyter
│
├── JOURNAL/
│   ├── sgci_dq.log             ← log texte en temps réel (tous les messages)
│   └── journal_dq.csv          ← historique de toutes les exécutions
│
└── EXPORTS/
    ├── transactions_journalieres_20260615_060123.csv   ← export si DQ OK
    └── ...
```

### Le dossier JOURNAL

Le dossier `JOURNAL` contient deux fichiers complémentaires :

**`sgci_dq.log`** est le fichier de log en temps réel. Il enregistre chaque message du pipeline au moment où il se produit, avec l'heure exacte. Tu peux l'ouvrir avec un éditeur de texte ou le lire dans Jupyter. Il ressemble à ceci :

```
2026-06-15 06:00:01 | INFO     | sgci_dq | DQ — TRANSACTIONS JOURNALIERES | 250 lignes
2026-06-15 06:00:01 | INFO     | Unicité | OK — Aucun doublon
2026-06-15 06:00:01 | INFO     | Complétude | OK — 250 lignes dans [50, 1000]
2026-06-15 06:00:02 | ERROR    | Cohérence | ECHEC — Colonne(s) entièrement vide(s) : ['BRANCH_CODE']
2026-06-15 06:00:02 | WARNING  | Export annulé — 1 dimension(s) en ECHEC
```

**`journal_dq.csv`** est l'historique tabulaire de toutes les exécutions. Chaque ligne correspond à une exécution d'une requête. Tu peux l'ouvrir dans Excel ou le lire avec `pd.read_csv()`.

### Le dossier EXPORTS

Le dossier `EXPORTS` contient uniquement les données qui ont passé tous les contrôles. Les fichiers sont nommés automatiquement avec le nom de l'extraction et un horodatage :

```
transactions_journalieres_20260615_060123.csv
```

---

## 3. Étape 0 — Setup <a id='3'></a>

La cellule de setup doit être exécutée **une seule fois** au début de chaque session Jupyter. Elle importe les bibliothèques, crée les dossiers et initialise le logger.

### Ce que fait le setup

```python
import pandas as pd
import numpy as np
import logging, os, time, warnings
from datetime import datetime, date, timedelta
from pathlib import Path
import pytz

LOG_DIR       = "./JOURNAL/"    # dossier des logs
EXPORT_DIR    = "./EXPORTS/"    # dossier des exports CSV
LOG_FILE_NAME = "journal_dq.csv"
TZ_ABIDJAN    = pytz.timezone("Africa/Abidjan")  # UTC+0

# Création automatique des dossiers s'ils n'existent pas
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
```

### Le logger

Le logger est un outil qui écrit automatiquement des messages horodatés. Il écrit dans deux endroits en même temps : dans le fichier `sgci_dq.log` (pour l'archivage) et dans la console Jupyter (pour que tu voies ce qui se passe en direct).

Tu n'as pas besoin de toucher au logger directement. Il est utilisé en interne par `run_dq()`.

---

## 4. Étape 1 — Se connecter à Teradata <a id='4'></a>

### Définir ses credentials

Les mots de passe ne doivent **jamais** être écrits directement dans le code. On utilise des variables d'environnement que l'on définit une seule fois par session :

```python
import os
os.environ["TD_HOST"]     = "adresse_du_serveur_teradata"
os.environ["TD_USER"]     = "ton_identifiant"
os.environ["TD_PASSWORD"] = "ton_mot_de_passe"
```

> Ces valeurs disparaissent automatiquement à la fermeture du notebook. Elles ne sont jamais sauvegardées dans le fichier `.ipynb`.

### Extraire des données

La fonction `extraire()` exécute une requête SQL et retourne un DataFrame :

```python
df = extraire("""
    SELECT TRN_REF, ACCOUNT_ID, AMOUNT, CURRENCY, BOOKING_DATE
    FROM SGCI_DB.TRANSACTIONS
    WHERE BOOKING_DATE = CURRENT_DATE - 1
""", "transactions_J1")
```

Elle mesure automatiquement la durée d'extraction et log le nombre de lignes récupérées.

---

## 5. Étape 2 — Les 5 contrôles DQ <a id='5'></a>

Les 5 fonctions de contrôle sont indépendantes. Tu n'as généralement pas besoin de les appeler directement — `run_dq()` le fait pour toi. Mais voici comment chacune fonctionne pour que tu comprennes ce qui se passe sous le capot.

### Contrôle 1 — Unicité

```python
check_unicite(df)
```

Utilise `df.duplicated(keep=False)` pour compter les lignes qui ont exactement les mêmes valeurs sur **toutes** les colonnes. Si 2 lignes sont identiques colonne par colonne, elles sont considérées comme des doublons.

**Exemple de résultat :**
- ✅ `"Aucun doublon"` — toutes les lignes sont uniques
- ❌ `"4 ligne(s) entièrement dupliquée(s)"` — 2 paires de lignes identiques

**Quand ça arrive :** jointure SQL mal construite, extraction qui se chevauche avec la précédente, batch qui a tourné deux fois.

---

### Contrôle 2 — Complétude

```python
check_completude(df, min_lignes=50, max_lignes=1000)
```

Compare simplement `len(df)` à l'intervalle `[min_lignes, max_lignes]` que tu définis toi-même selon ce que tu attends de ta requête.

**Comment choisir l'intervalle ?**
Regarde les historiques de tes extractions sur les derniers jours. Si tu extrais en général entre 200 et 400 lignes, mets `min_lignes=100` et `max_lignes=600` pour avoir une marge. Si tu extrais 0 lignes, le batch a planté. Si tu en as 10 000 alors que tu en attends 300, il y a probablement un problème de filtre SQL.

**Exemple de résultat :**
- ✅ `"250 ligne(s) dans [50, 1000]"` — volume normal
- ❌ `"0 ligne(s) — en dessous du minimum (50)"` — table vide ou batch en échec

---

### Contrôle 3 — Fraîcheur

```python
check_fraicheur(df, col_date="BOOKING_DATE", date_debut=hier, date_fin=hier)
```

Convertit les valeurs de `col_date` en dates Python, puis compte combien de lignes tombent dans l'intervalle `[date_debut, date_fin]`. Si aucune ligne n'est dans cet intervalle, les données ne correspondent pas à la période attendue.

**Comment choisir les dates ?**
Pour une extraction quotidienne de J-1, utilise `date_debut=hier` et `date_fin=hier`. Pour une extraction hebdomadaire, utilise `date_debut=lundi_dernier` et `date_fin=hier`.

**Exemple de résultat :**
- ✅ `"250 ligne(s) dans [2026-06-14, 2026-06-14]"` — données fraîches
- ❌ `"Aucune ligne dans [2026-06-14, 2026-06-14] — dates trouvées : 2026-06-13 → 2026-06-13"` — données de J-2

---

### Contrôle 4 — Cohérence

```python
check_coherence(df)
```

Parcourt toutes les colonnes et vérifie qu'aucune n'est entièrement nulle avec `df[col].isnull().all()`. Une colonne 100% vide signifie en général un problème dans la requête SQL (mauvaise jointure, colonne inexistante dans la table source) ou une migration de données incomplète.

**Exemple de résultat :**
- ✅ `"Aucune colonne entièrement vide"` — toutes les colonnes ont au moins une valeur
- ❌ `"Colonne(s) entièrement vide(s) : ['BRANCH_CODE', 'REGION']"` — ces colonnes n'ont aucune valeur

---

### Contrôle 5 — Validité

```python
check_validite(df, types_attendus={"AMOUNT": float, "TRN_REF": str, "MVT_ID": int})
```

Vérifie que le type pandas de chaque colonne correspond au type Python que tu attends. Tu passes un dictionnaire avec les colonnes les plus importantes — pas besoin de lister toutes les colonnes, seulement celles qui comptent.

**Types acceptés :**

| Type Python | Signification | Exemple de valeur |
|---|---|---|
| `str` | Texte | `"TRN00000001"`, `"XOF"` |
| `float` | Nombre décimal | `125000.50`, `0.0` |
| `int` | Nombre entier | `42`, `1000` |
| `bool` | Booléen | `True`, `False` |

**Exemple de résultat :**
- ✅ `"Tous les types sont conformes"` — les types correspondent
- ❌ `"'MVT_ID' : attendu numérique entier, trouvé float64"` — Teradata a retourné un float

> **Note :** Teradata retourne souvent les colonnes avec des types légèrement différents de ce qu'on attend. Ce contrôle te permet de détecter ces écarts avant qu'ils ne causent des erreurs plus loin dans le traitement.

---

## 6. Étape 3 — Lancer le pipeline avec run_dq() <a id='6'></a>

`run_dq()` est la fonction centrale. Elle orchestre les 5 contrôles et décide si les données sont exportées ou non.

### Signature complète

```python
rapport = run_dq(
    df             = df,            # DataFrame extrait de Teradata
    nom            = "mon_extraction",  # Nom descriptif (utilisé pour nommer le CSV)
    min_lignes     = 50,            # Nombre minimum de lignes attendu
    max_lignes     = 1000,          # Nombre maximum de lignes attendu
    col_date       = "MA_DATE",     # Colonne de date pour le contrôle de fraîcheur
    date_debut     = hier,          # Début de la période attendue
    date_fin       = hier,          # Fin de la période attendue
    types_attendus = {              # Types attendus pour tes colonnes clés
        "MA_CLE"      : str,
        "MON_MONTANT" : float,
    }
)
```

### Ce que retourne run_dq()

La fonction retourne un dictionnaire que tu peux explorer :

```python
rapport = {
    "nom"        : "transactions_journalieres",
    "timestamp"  : "2026-06-15T06:00:01.234567",
    "nb_lignes"  : 250,
    "valide"     : True,         # True = toutes OK, False = au moins un ECHEC
    "controles"  : {             # Détail de chaque contrôle
        "Unicité"    : {"statut": "OK",    "message": "Aucun doublon"},
        "Complétude" : {"statut": "OK",    "message": "250 lignes dans [50, 1000]"},
        "Fraîcheur"  : {"statut": "OK",    "message": "250 lignes dans [2026-06-14, 2026-06-14]"},
        "Cohérence"  : {"statut": "OK",    "message": "Aucune colonne entièrement vide"},
        "Validité"   : {"statut": "OK",    "message": "Tous les types sont conformes"},
    },
    "duree_s"    : 0.12,
    "export_csv" : "./EXPORTS/transactions_journalieres_20260615_060001.csv"
    # export_csv = None si au moins un contrôle est en ECHEC
}
```

Pour vérifier rapidement si l'export a eu lieu :

```python
if rapport["export_csv"]:
    print(f"Données exportées : {rapport['export_csv']}")
else:
    print("Pas d'export — vérifier les erreurs dans le journal")
```

---

## 7. Étape 4 — Journaliser avec log() <a id='7'></a>

Après chaque appel à `run_dq()`, appelle `log()` pour enregistrer le résultat dans le journal CSV cumulatif.

```python
log(
    nom        = "transactions_journalieres",  # Nom de l'extraction
    rapport    = rapport,                      # Rapport retourné par run_dq()
    frequence  = "Quotidien",                  # Fréquence du traitement
    date_debut = hier,                         # Début des données
    date_fin   = hier                          # Fin des données
)
```

**Valeurs possibles pour `frequence`** : `"Quotidien"`, `"Hebdomadaire"`, `"Mensuel"`, `"Trimestriel"`, `"Semestriel"`.

### Ce qui est enregistré dans le journal

Chaque appel à `log()` ajoute une ligne au fichier `journal_dq.csv` avec ces colonnes :

| Colonne | Contenu | Exemple |
|---|---|---|
| `Execution_Date` | Horodatage de l'exécution | `2026-06-15T06:00:01` |
| `User` | Identifiant système | `alex` |
| `Extraction` | Nom de la requête | `transactions_journalieres` |
| `Frequency` | Fréquence du traitement | `Quotidien` |
| `Data_Begin` | Début des données | `2026-06-14` |
| `Data_End` | Fin des données | `2026-06-14` |
| `Row_Number` | Nombre de lignes extraites | `250` |
| `Duration(s)` | Durée du traitement | `0.12` |
| `Status` | Résultat global | `Good` ou `Bad` |
| `Export_CSV` | Chemin du fichier exporté | `./EXPORTS/transactions_...csv` |
| `Error_Reason` | Détail des erreurs | `Cohérence: Colonne vide ['X']` |

---

## 8. Étape 5 — Consulter les résultats <a id='8'></a>

### Lire le journal dans Jupyter

```python
df_journal = pd.read_csv("./JOURNAL/journal_dq.csv", sep=";")
df_journal
```

### Filtrer les exécutions en erreur

```python
df_journal[df_journal["Status"] == "Bad"]
```

### Voir les exports réalisés

```python
df_journal[df_journal["Export_CSV"].notna()][["Extraction", "Execution_Date", "Row_Number", "Export_CSV"]]
```

### Lire un fichier exporté

```python
df_export = pd.read_csv("./EXPORTS/transactions_journalieres_20260615_060001.csv", sep=";")
df_export.head()
```

### Lire les logs texte

```python
with open("./JOURNAL/sgci_dq.log", "r", encoding="utf-8") as f:
    print(f.read())
```

---

## 9. Template pour une nouvelle requête <a id='9'></a>

Copie ce bloc et adapte les paramètres à ta requête. C'est tout ce dont tu as besoin.

```python
# ── Paramètres à adapter ──────────────────────────────────────────────────────
NOM_EXTRACTION = "nom_de_ma_requete"   # nom court, sans espaces si possible
MIN_LIGNES     = 50                    # volume minimum attendu
MAX_LIGNES     = 5000                  # volume maximum attendu
COL_DATE       = "MA_COLONNE_DATE"     # colonne de date dans ta table
DATE_DEBUT     = hier                  # début de la période (hier pour J-1)
DATE_FIN       = hier                  # fin de la période
TYPES_ATTENDUS = {                     # types de tes colonnes importantes
    "MA_CLE"      : str,
    "MON_MONTANT" : float,
    "MON_ENTIER"  : int,
}
FREQUENCE      = "Quotidien"           # Quotidien / Hebdomadaire / Mensuel

# ── 1. Extraction ─────────────────────────────────────────────────────────────
# En production :
# df = extraire("""
#     SELECT col1, col2, MA_COLONNE_DATE, ...
#     FROM SGCI_DB.MA_TABLE
#     WHERE MA_COLONNE_DATE = CURRENT_DATE - 1
# """, NOM_EXTRACTION)

# En démo (remplacer par la ligne ci-dessus en production) :
df = mon_dataframe_simulé

# ── 2. Contrôles DQ + export CSV si OK ───────────────────────────────────────
rapport = run_dq(
    df             = df,
    nom            = NOM_EXTRACTION,
    min_lignes     = MIN_LIGNES,
    max_lignes     = MAX_LIGNES,
    col_date       = COL_DATE,
    date_debut     = DATE_DEBUT,
    date_fin       = DATE_FIN,
    types_attendus = TYPES_ATTENDUS
)

# ── 3. Journalisation ─────────────────────────────────────────────────────────
log(NOM_EXTRACTION, rapport, FREQUENCE, DATE_DEBUT, DATE_FIN)
```

---

## 10. Questions fréquentes <a id='10'></a>

**Q : Puis-je utiliser ce framework pour des extractions hebdomadaires ou mensuelles ?**

Oui. Il suffit d'adapter `date_debut` et `date_fin`. Par exemple pour une extraction mensuelle de janvier 2026 :

```python
date_debut = date(2026, 1, 1)
date_fin   = date(2026, 1, 31)
frequence  = "Mensuel"
```

---

**Q : Que faire si une dimension est en ECHEC ?**

Commence par regarder le message d'erreur affiché dans la console ou dans `rapport["controles"]`. Ensuite selon la dimension en cause :

- **Unicité** : vérifier si la requête SQL contient une jointure qui multiplie les lignes. Ajouter un `DISTINCT` ou revoir les conditions de jointure.
- **Complétude** : vérifier si le batch source a bien tourné. Si 0 lignes, la table n'est peut-être pas encore alimentée.
- **Fraîcheur** : vérifier le filtre de date dans la requête SQL. La table a peut-être un décalage de fuseau horaire.
- **Cohérence** : la colonne entièrement vide existe-t-elle vraiment dans la table source ? Vérifier le nom exact et la jointure.
- **Validité** : Teradata peut retourner des types inattendus. Convertir explicitement après extraction : `df["MVT_ID"] = df["MVT_ID"].astype(int)`.

---

**Q : Peut-on avoir un export partiel (seulement les lignes valides) ?**

Non, par choix de conception. Le framework exporte soit **tout** le DataFrame (si toutes les dimensions sont OK), soit **rien**. Cela garantit qu'un fichier présent dans `EXPORTS/` est toujours 100% validé. Si tu veux un export partiel (par exemple exclure les doublons), déduplique d'abord le DataFrame avant de le passer à `run_dq()`.

---

**Q : Comment ajouter un nouveau contrôle ?**

Crée une fonction qui retourne `{"statut": "OK"/"ECHEC", "message": "..."}`, puis ajoute-la dans le dictionnaire `controles` dans `run_dq()` :

```python
def check_mon_controle(df):
    # ... ta logique
    return {"statut": "OK", "message": "Tout va bien"}

# Dans run_dq() :
controles = {
    "Unicité"      : check_unicite(df),
    "Complétude"   : check_completude(df, min_lignes, max_lignes),
    "Fraîcheur"    : check_fraicheur(df, col_date, date_debut, date_fin),
    "Cohérence"    : check_coherence(df),
    "Validité"     : check_validite(df, types_attendus),
    "Mon contrôle" : check_mon_controle(df),   # ← ajout ici
}
```

---

**Q : Où trouver les fichiers exportés si j'oublie le chemin ?**

Le chemin est toujours dans `rapport["export_csv"]` et dans la colonne `Export_CSV` du journal :

```python
df_journal = pd.read_csv("./JOURNAL/journal_dq.csv", sep=";")
print(df_journal["Export_CSV"].dropna().tolist())
```

---

*SGCI Data Engineering · Guide Utilisateur Framework DQ v1.0 · Juin 2026*
