# Explication des fonctions — Framework DQ Simplifié SGCI
## Document de présentation équipe Data Engineering
**Auteur** : Data Engineering SGCI | **Version** : 1.0 — Juin 2026

---

## Vue d'ensemble — Architecture du framework

Le framework est composé de **9 fonctions** qui s'enchaînent dans un ordre précis. Voici la carte complète avant d'entrer dans le détail de chacune.

```
┌─────────────────────────────────────────────────────────────────┐
│                     FONCTIONS DU FRAMEWORK                      │
├──────────────────┬──────────────────────────────────────────────┤
│  INFRASTRUCTURE  │  setup_logger()   get_connection()           │
│                  │  extraire()                                   │
├──────────────────┼──────────────────────────────────────────────┤
│  5 CONTRÔLES DQ  │  check_unicite()       check_completude()    │
│                  │  check_fraicheur()     check_coherence()      │
│                  │  check_validite()                             │
├──────────────────┼──────────────────────────────────────────────┤
│  ORCHESTRATION   │  run_dq()                                     │
├──────────────────┼──────────────────────────────────────────────┤
│  JOURNALISATION  │  log()                                        │
└──────────────────┴──────────────────────────────────────────────┘
```

**Principe de conception :** chaque fonction a **une seule responsabilité**. Les 5 contrôles retournent tous le même format `{"statut": ..., "message": ...}`, ce qui permet à `run_dq()` de les orchestrer de façon uniforme.

---

## PARTIE 1 — Infrastructure

---

### `setup_logger(project_name, log_dir)`

**Rôle :** Crée et configure un logger Python avec deux handlers : un fichier `.log` pour l'archivage complet, et un handler console pour afficher les messages INFO et supérieurs dans Jupyter.

**Pourquoi deux handlers ?**
- Le **FileHandler** capture tout (DEBUG+) pour l'audit — on veut garder la trace de chaque étape même si elle n'est pas affichée à l'écran.
- Le **StreamHandler** n'affiche que INFO+ dans la console pour ne pas noyer l'utilisateur de messages techniques.

**Point technique clé — nettoyage des handlers :**
```python
if logger.handlers:
    logger.handlers.clear()
```
Sans cette ligne, chaque fois que la cellule est ré-exécutée dans Jupyter, un nouveau handler est ajouté sur le même logger. Résultat : les messages sont dupliqués (2x, 3x, 4x...). Le nettoyage préalable évite ce problème classique avec `logging` en Jupyter.

**Ce que retourne la fonction :**
Un objet `logging.Logger` nommé `project_name`. Ce logger est passé en variable globale `logger` et utilisé en interne par toutes les autres fonctions.

**Format des messages de log :**
```
2026-06-15 06:00:01 | INFO     | sgci_dq | Message ici
│                     │          │          │
│                     │          │          └─ contenu du message
│                     │          └─ nom du projet (project_name)
│                     └─ niveau (DEBUG/INFO/WARNING/ERROR/CRITICAL)
└─ horodatage précis à la seconde
```

---

### `get_connection()`

**Rôle :** Ouvre et retourne une connexion Teradata sécurisée en lisant les credentials depuis les variables d'environnement.

**Pourquoi les variables d'environnement ?**
Un credential hardcodé dans le code source peut être exposé accidentellement via Git, un email, une impression. Les variables d'environnement sont locales à la session et ne persistent pas dans le fichier `.ipynb`.

**Mécanisme `os.getenv()` :**
```python
os.getenv("TD_HOST")  # retourne None si la variable n'existe pas
```
Si une variable n'est pas définie, `teradatasql.connect()` reçoit `None` et lève une exception explicite — ce qui est préférable à un comportement silencieux.

**Usage avec `with` (context manager) :**
```python
with get_connection() as con:
    df = pd.read_sql(query, con)
# La connexion est automatiquement fermée ici, même en cas d'exception
```
Le `with` garantit que la connexion est toujours fermée proprement, même si une erreur survient pendant l'extraction. Sans ça, des connexions orphelines peuvent s'accumuler côté Teradata.

---

### `extraire(query, nom)`

**Rôle :** Exécute une requête SQL sur Teradata, mesure la durée d'extraction, log le résultat et retourne un DataFrame pandas.

**Paramètres :**
- `query` : la requête SQL complète sous forme de chaîne de caractères
- `nom` : un label descriptif utilisé dans les messages de log pour identifier l'extraction

**Mesure de la durée :**
```python
t0 = time.time()
df = pd.read_sql(query, con)
duree = round(time.time() - t0, 2)
```
`time.time()` retourne un timestamp Unix en secondes avec précision microseconde. La soustraction donne la durée réelle de l'appel réseau + exécution SQL + transfert des données.

**Ce que retourne la fonction :**
Un `pd.DataFrame` dont les colonnes correspondent aux colonnes SELECT de la requête. Les types pandas sont inférés automatiquement par `pd.read_sql()` — d'où l'importance du contrôle `check_validite()` en aval.

---

## PARTIE 2 — Les 5 contrôles DQ

**Convention commune à toutes les fonctions de contrôle :**

Chaque fonction retourne un dictionnaire avec exactement deux clés :
```python
{"statut": "OK",    "message": "Description du résultat"}
{"statut": "ECHEC", "message": "Description de l'anomalie"}
```
Cette interface uniforme est essentielle : `run_dq()` itère sur les résultats sans avoir besoin de connaître la logique interne de chaque contrôle. Si tu ajoutes un 6ème contrôle demain, il suffit qu'il respecte ce contrat.

---

### `check_unicite(df)`

**Rôle :** Détecte les lignes entièrement dupliquées dans le DataFrame, c'est-à-dire les lignes qui ont la même valeur sur **toutes** leurs colonnes.

**Implémentation :**
```python
n = df.duplicated(keep=False).sum()
```

**Décryptage de `duplicated(keep=False)` :**

`df.duplicated()` retourne une Series booléenne. Le paramètre `keep` contrôle quelles lignes sont marquées :
- `keep="first"` → marque toutes sauf la première occurrence (pour supprimer)
- `keep="last"` → marque toutes sauf la dernière occurrence
- `keep=False` → marque **toutes** les occurrences (pour compter)

On utilise `keep=False` parce qu'on veut compter le nombre total de lignes impliquées dans une duplication, pas juste les "copies". Si 3 lignes sont identiques, on veut savoir qu'il y a 3 lignes problématiques, pas 2.

**Exemple concret :**
```
DataFrame :
  A  B          duplicated(keep=False)
  1  x          True   ← impliquée
  2  y          False  ← unique
  1  x          True   ← impliquée
  3  z          False  ← unique

.sum() = 2  →  "2 ligne(s) entièrement dupliquée(s)"
```

**Limite de ce contrôle :** il vérifie la duplication sur **toutes** les colonnes. Si deux transactions ont le même montant et la même date mais des références différentes, elles ne seront pas détectées comme doublons — et c'est correct. Pour détecter les doublons sur une clé spécifique (ex: `TRN_REF`), on utiliserait `df.duplicated(subset=["TRN_REF"])`.

---

### `check_completude(df, min_lignes, max_lignes)`

**Rôle :** Vérifie que le volume de données extrait est dans l'intervalle `[min_lignes, max_lignes]` défini par l'utilisateur.

**Implémentation :**
```python
n = len(df)
if n < min_lignes: ...
if n > max_lignes: ...
```

**Pourquoi `len(df)` et pas `df.shape[0]` ?**
Les deux sont équivalents pour un DataFrame. `len(df)` est plus lisible et idiomatique en Python. `df.shape[0]` est utile quand on veut aussi récupérer le nombre de colonnes (`df.shape[1]`) dans la même expression.

**Logique de l'intervalle :**
L'intervalle `[min_lignes, max_lignes]` est défini par l'utilisateur selon sa connaissance métier de l'extraction. Il n'est pas calculé automatiquement car le framework n'a pas accès à l'historique des extractions passées. En pratique, on le détermine en observant les volumes habituels sur quelques semaines, puis on prend une marge de sécurité.

**Deux cas d'échec distincts :**
- Volume trop faible : le batch source n'a peut-être pas tourné, ou le filtre SQL est trop restrictif
- Volume trop élevé : jointure SQL qui multiplie les lignes, ou filtre de date mal positionné

---

### `check_fraicheur(df, col_date, date_debut, date_fin)`

**Rôle :** Vérifie que le DataFrame contient au moins une ligne dont la colonne `col_date` tombe dans l'intervalle `[date_debut, date_fin]`.

**Implémentation :**
```python
dates = pd.to_datetime(df[col_date], errors="coerce").dt.date
n = dates.between(date_debut, date_fin).sum()
```

**Décryptage ligne par ligne :**

`pd.to_datetime(df[col_date], errors="coerce")` — convertit la colonne en timestamps pandas. Le paramètre `errors="coerce"` transforme les valeurs non convertibles en `NaT` (Not a Time) au lieu de lever une exception. C'est défensif : si quelques dates sont mal formées, le contrôle continue sur les dates valides.

`.dt.date` — extrait uniquement la partie date (sans l'heure) depuis un timestamp pandas. Résultat : une Series de `datetime.date` Python, comparables directement avec `date_debut` et `date_fin`.

`.between(date_debut, date_fin)` — retourne une Series booléenne. Les bornes sont **incluses** (équivalent à `>=` et `<=`). Les valeurs `NaT` retournent `False`, ce qui est le comportement voulu.

**Ce que ce contrôle ne fait pas :**
Il ne vérifie pas que **toutes** les lignes sont dans la période, seulement qu'**au moins une** y est. Si tu extrais 300 lignes dont 299 sont à J-2 et 1 seule à J-1, le contrôle retourne OK. C'est un choix de simplicité — pour un contrôle plus strict, on pourrait comparer le ratio de lignes dans la période.

---

### `check_coherence(df)`

**Rôle :** Vérifie qu'aucune colonne du DataFrame n'est entièrement vide (100% de valeurs nulles).

**Implémentation :**
```python
colonnes_vides = [col for col in df.columns if df[col].isnull().all()]
```

**Décryptage :**

`df[col].isnull()` — retourne une Series booléenne, `True` là où la valeur est `NaN`, `None`, `NaT` ou `pd.NA`.

`.all()` — retourne `True` uniquement si **toutes** les valeurs sont `True`, c'est-à-dire si toutes les valeurs de la colonne sont nulles.

La list comprehension collecte les noms de toutes les colonnes répondant à cette condition.

**Pourquoi ce contrôle détecte des problèmes réels :**
Une colonne entièrement vide après une extraction Teradata indique presque toujours un problème structurel : la colonne n'existe pas dans la table source, la jointure qui devait la remplir a échoué, ou une migration de données est incomplète. Ce n'est jamais un état normal pour des données de production.

**Nuance importante :** ce contrôle détecte les colonnes à 100% vides. Une colonne à 80% vide ne sera pas détectée ici — ce serait le rôle d'un contrôle de complétude colonne par colonne (comme dans le `SchemaValidator` du framework complet).

---

### `check_validite(df, types_attendus)`

**Rôle :** Vérifie que le type pandas de chaque colonne listée dans `types_attendus` correspond au type Python attendu.

**Paramètre `types_attendus` :**
```python
types_attendus = {
    "TRN_REF" : str,    # colonne de texte
    "AMOUNT"  : float,  # colonne numérique décimale
    "MVT_ID"  : int,    # colonne numérique entière
}
```

**Implémentation — les trois branches :**

```python
if type_attendu in (int, float):
    if not pd.api.types.is_numeric_dtype(df[col]):
        erreurs.append(...)

elif type_attendu == str:
    if not (pd.api.types.is_string_dtype(df[col]) or
            pd.api.types.is_object_dtype(df[col])):
        erreurs.append(...)

elif type_attendu == bool:
    if not pd.api.types.is_bool_dtype(df[col]):
        erreurs.append(...)
```

**Pourquoi `is_numeric_dtype` et pas `== int` ou `== float` ?**
Pandas a plusieurs types numériques : `int32`, `int64`, `float32`, `float64`. Comparer avec `== int` ne capturerait que `int64`. `pd.api.types.is_numeric_dtype()` retourne `True` pour tous les types numériques, ce qui est plus robuste.

**Pourquoi `is_string_dtype` OU `is_object_dtype` pour `str` ?**
Pandas représente le texte de deux façons selon la version :
- Ancien comportement (pandas < 1.0) : dtype `object`
- Nouveau comportement (pandas >= 1.0 avec `StringDtype`) : dtype `string`
En acceptant les deux, le contrôle fonctionne quelle que soit la version de pandas installée.

**La ligne `if df[col].dropna().empty: continue` :**
Si une colonne est entièrement nulle, `dropna()` retourne un DataFrame vide. On skip le contrôle de type car on ne peut pas inférer le type de `NaN`. Le contrôle de cohérence (`check_coherence`) aura déjà signalé ce problème.

---

## PARTIE 3 — Orchestration

---

### `run_dq(df, nom, min_lignes, max_lignes, col_date, date_debut, date_fin, types_attendus)`

**Rôle :** Orchestre les 5 contrôles DQ dans l'ordre, affiche le rapport, et exporte le DataFrame en CSV uniquement si tous les contrôles sont OK.

**Structure interne :**

```python
# 1. Lancer les 5 contrôles et collecter les résultats
controles = {
    "Unicité"    : check_unicite(df),
    "Complétude" : check_completude(df, min_lignes, max_lignes),
    "Fraîcheur"  : check_fraicheur(df, col_date, date_debut, date_fin),
    "Cohérence"  : check_coherence(df),
    "Validité"   : check_validite(df, types_attendus),
}

# 2. Décision globale
all_ok = all(r["statut"] == "OK" for r in controles.values())

# 3. Export conditionnel
if all_ok:
    df.to_csv(export_csv, sep=";", index=False, encoding="utf-8")
```

**Décryptage de `all(r["statut"] == "OK" for r in controles.values())` :**

C'est une expression génératrice passée à `all()`. Elle parcourt les valeurs du dictionnaire `controles` et évalue `r["statut"] == "OK"` pour chacune. `all()` retourne `True` uniquement si **tous** les éléments sont `True`. Dès qu'un `False` est rencontré, Python court-circuite l'évaluation et retourne `False` immédiatement — c'est efficace.

**Nommage automatique du fichier CSV :**
```python
ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
nom_clean = nom.lower().replace(" ", "_")
export_csv = os.path.join(EXPORT_DIR, f"{nom_clean}_{ts}.csv")
```
Le nom contient un horodatage à la seconde près, ce qui garantit l'unicité même si la même extraction tourne plusieurs fois dans la journée. `os.path.join()` est utilisé à la place de la concaténation de chaînes pour garantir la compatibilité Windows/Linux/Mac.

**Ce que retourne la fonction :**

```python
{
    "nom"        : str,   # nom de l'extraction
    "timestamp"  : str,   # horodatage ISO 8601
    "nb_lignes"  : int,   # len(df)
    "valide"     : bool,  # True si tous OK, False sinon
    "controles"  : dict,  # détail de chaque contrôle
    "duree_s"    : float, # durée totale en secondes
    "export_csv" : str    # chemin du CSV, ou None si non exporté
}
```

La clé `export_csv` vaut `None` si l'export n'a pas eu lieu. Cela permet à l'appelant de vérifier facilement : `if rapport["export_csv"]: ...`

---

## PARTIE 4 — Journalisation

---

### `log(nom, rapport, frequence, date_debut, date_fin)`

**Rôle :** Ajoute une ligne au fichier CSV `journal_dq.csv` avec les métadonnées de l'exécution. Le fichier est **cumulatif** : chaque appel concatène une nouvelle ligne.

**Construction du message d'erreur :**
```python
detail_erreurs = " | ".join([
    f"{k}: {v['message']}"
    for k, v in rapport["controles"].items()
    if v["statut"] == "ECHEC"
])
```
Cette list comprehension filtre uniquement les contrôles en ECHEC et concatène leurs messages avec ` | ` comme séparateur. Si tous les contrôles sont OK, `detail_erreurs` est une chaîne vide `""`.

**Mécanisme de cumul :**
```python
if os.path.isfile(full_path):
    df_old = pd.read_csv(full_path, sep=";", encoding="utf-8")
    df_new = pd.concat([df_old, df_new], ignore_index=True)
df_new.to_csv(full_path, sep=";", index=False, encoding="utf-8")
```

Pattern classique en pandas pour l'écriture cumulative :
1. Si le fichier existe → lire l'ancien, concaténer avec la nouvelle ligne
2. Si le fichier n'existe pas → écrire directement la nouvelle ligne

`ignore_index=True` dans `pd.concat()` réinitialise l'index pour éviter les doublons d'index après concaténation.

**Pourquoi pas `mode="a"` dans `to_csv()` ?**
Utiliser `df.to_csv(path, mode="a")` (append) serait plus simple mais réécrirait les en-têtes à chaque fois, corrompant le fichier. La lecture + concaténation + réécriture complète est plus coûteuse en I/O mais garantit l'intégrité du fichier.

**Colonne `Export_CSV` dans le journal :**
```python
"Export_CSV" : rapport["export_csv"] or ""
```
`rapport["export_csv"]` vaut soit un chemin (str), soit `None`. L'expression `or ""` convertit `None` en chaîne vide pour que le CSV reste propre (pas de `None` littéral dans les cellules).

---

## Récapitulatif — Tableau des fonctions

| Fonction | Entrée | Sortie | Effet de bord |
|---|---|---|---|
| `setup_logger()` | `project_name`, `log_dir` | `Logger` | Crée le fichier `.log` |
| `get_connection()` | — | Connexion Teradata | — |
| `extraire()` | `query`, `nom` | `DataFrame` | Log dans `.log` |
| `check_unicite()` | `df` | `dict {statut, message}` | — |
| `check_completude()` | `df`, `min`, `max` | `dict {statut, message}` | — |
| `check_fraicheur()` | `df`, `col`, `debut`, `fin` | `dict {statut, message}` | — |
| `check_coherence()` | `df` | `dict {statut, message}` | — |
| `check_validite()` | `df`, `types` | `dict {statut, message}` | — |
| `run_dq()` | `df` + 7 paramètres | `dict rapport` | Export CSV + log dans `.log` |
| `log()` | `nom`, `rapport`, `freq`, dates | — | Écrit dans `journal_dq.csv` |

---

## Points de conception à retenir

**1. Interface uniforme des contrôles**
Tous les contrôles retournent `{"statut": ..., "message": ...}`. Ajouter un nouveau contrôle ne nécessite pas de modifier `run_dq()` — il suffit de l'ajouter au dictionnaire `controles`.

**2. Séparation des responsabilités**
Chaque fonction fait une seule chose. `run_dq()` ne sait pas comment fonctionne `check_unicite()` — elle sait juste qu'elle retourne un dict avec `statut` et `message`.

**3. Export tout-ou-rien**
Le CSV n'est exporté que si **tous** les contrôles sont OK. Un fichier présent dans `EXPORTS/` est donc toujours certifié valide.

**4. Traçabilité complète**
Chaque exécution laisse deux traces : une ligne dans `journal_dq.csv` (tabulaire, requêtable) et des messages dans `sgci_dq.log` (séquentiel, pour le debugging).

---
*SGCI Data Engineering · Explication des fonctions v1.0 · Juin 2026*
