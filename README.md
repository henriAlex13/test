# 📊 Application Gestion Factures CIE - Version 3.0

## 📁 Structure des fichiers

```
projet/
├── app.py                  # Application principale (Streamlit)
├── models.py              # Gestion base centrale et modèles de données
├── import_bt.py           # Import factures Basse Tension
├── import_ht.py           # Import factures Haute Tension (E0/E1/E5)
├── generation.py          # Génération pièces comptables
├── ARCHITECTURE_V3.md     # Documentation architecture
└── README.md             # Ce fichier
```

## 🚀 Installation

### Prérequis
- Python 3.8+
- pip

### Installation des dépendances

```bash
pip install streamlit pandas openpyxl plotly
```

## ▶️ Lancement de l'application

```bash
streamlit run app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse : `http://localhost:8501`

## 📋 Utilisation

### 1️⃣ Base Centrale
- **Affiche** : Les 10 colonnes essentielles
- **Actions** : Ajouter/Modifier/Supprimer des lignes manuellement
- **Filtres** : Par UC, DATE, TENSION
- **Export** : Excel simple

### 2️⃣ Import Factures BT
1. Téléverser fichier Excel BT
2. Vérifier colonnes détectées
3. Cliquer sur "LANCER L'IMPORT BT"
4. ✅ Les lignes sont ajoutées à la base centrale

**Colonnes requises** :
- Référence Contrat
- Montant facture TTC
- KWH Facturé
- Période Facture sur date fact

### 3️⃣ Import Factures HT
1. Téléverser fichier Excel HT
2. Vérifier colonnes et typefact
3. Cliquer sur "LANCER L'IMPORT HT"
4. ✅ Traitement automatique E0/E1/E5

**Colonnes requises** :
- refraccord
- montfact
- conso
- Periode_Emission_Bordereau
- typefact (optionnel)

**Types de factures HT** :
- **E0** : Normale → Cumul si plusieurs factures
- **E1** : Complémentaire → Remplit DATE_COMPLEMENTAIRE
- **E5** : Avoir → Montant négatif

### 4️⃣ Statistiques
- Graphiques évolution montants
- Graphiques évolution consommations
- Filtres par site et tension

### 5️⃣ Génération Fichiers
1. Sélectionner période
2. Choisir onglet BT ou HT
3. Visualiser aperçu
4. Télécharger pièce comptable Excel

**Colonnes générées** (17 au total) :
- CODE AGENCE, COMPTE DE CHARGES, SENS, MONTANT
- CODE PAYT Lib 1-5, CODE CHARGE Lib 6-10
- TYPE DEP Lib 11, MATR OBJ Lib 12-19
- LIBELLE COMPLEMENTAIRE
- CODE AG, SENS_, MONTANT_
- CODE FOURNISSEUR, FOURNISSEUR
- CONTREPARTIE, LIB COMPLEMENTAIRE
- IDENTIFIANT

## 🎯 Workflow Complet

```
1. IMPORT
   ├─ Importer factures BT → Base centrale
   └─ Importer factures HT → Base centrale (avec E0/E1/E5)

2. VÉRIFICATION
   ├─ Consulter "Base Centrale"
   ├─ Vérifier données importées
   └─ Ajouter manuellement si nécessaire

3. GÉNÉRATION
   ├─ Aller dans "Génération Fichiers"
   ├─ Sélectionner période
   └─ Télécharger pièce comptable Excel
```

## 📊 Structure Base Centrale

### Colonnes (10)
1. **UC** : Unité comptable
2. **CODE RED** : Code RED
3. **CODE AGCE** : Code agence
4. **SITES** : Nom du site
5. **IDENTIFIANT** : Clé unique (normalisée)
6. **TENSION** : BASSE ou HAUTE
7. **DATE** : Période (MM/YYYY)
8. **CONSO** : Consommation (kWh)
9. **MONTANT** : Montant facture (FCFA)
10. **DATE_COMPLEMENTAIRE** : Date complémentaire (si E1)

### Règles
- **IDENTIFIANT** : Clé unique pour correspondance
- **DATE** : Format obligatoire MM/YYYY (ex: 01/2025)
- **TENSION** : "BASSE" pour BT, "HAUTE" pour HT
- **DATE_COMPLEMENTAIRE** : Vide = normale, Rempli = complémentaire

## 🔧 Fonctionnalités Clés

### Normalisation IDENTIFIANT
Tous les identifiants sont normalisés automatiquement :
- `123.0` → `"123"`
- `"  abc  "` → `"ABC"`
- `"123.45"` → `"123.45"`

### Traitement HT E0 (Factures multiples)
Si plusieurs factures avec même IDENTIFIANT et typefact = E0 :
→ **CUMUL** automatique des montants et consos
→ Une seule ligne dans la base centrale

### Libellé Complémentaire
- **Normal** : "CIE BT 01/2025 ABOBO SANMAKE"
- **Complémentaire** : "CIE HT 01/2025 COCODY ANGRE COMPLEMENTAIRE 12/2024"

## 🗂️ Fichiers de données

### Créés automatiquement
- `data_centrale.pkl` : Sauvegarde auto de la base centrale
- Mis à jour à chaque modification/import

### Optionnels
- `Base_Centrale.xlsx` : Base initiale (si vous voulez démarrer avec des données)

## ⚙️ Configuration

Les configurations sont dans les fichiers modules :

**models.py** :
```python
COLONNES_BASE_CENTRALE = [
    'UC', 'CODE RED', 'CODE AGCE', 'SITES', 'IDENTIFIANT', 
    'TENSION', 'DATE', 'CONSO', 'MONTANT', 'DATE_COMPLEMENTAIRE'
]
```

**import_bt.py** :
```python
CONFIG_BT = {
    'cle_facture': 'Référence Contrat',
    'montant_col': 'Montant facture TTC',
    'conso_col': 'KWH Facturé',
    'periode_col': 'Période Facture sur date fact'
}
```

**import_ht.py** :
```python
CONFIG_HT = {
    'cle_facture': 'refraccord',
    'montant_col': 'montfact',
    'conso_col': 'conso',
    'periode_col': 'Periode_Emission_Bordereau',
    'typefact_col': 'typefact'
}
```

## 🐛 Dépannage

### Erreur "Colonnes manquantes"
→ Vérifiez que votre fichier Excel contient les bonnes colonnes (voir configs ci-dessus)

### Aucune ligne importée
→ Vérifiez que les IDENTIFIANT existent dans la base centrale

### Montants vides dans pièce comptable
→ Vérifiez que la période sélectionnée existe dans la base centrale

### Erreur pickle
→ Supprimez `data_centrale.pkl` et relancez l'application

## 📞 Support

Pour toute question ou problème :
1. Consultez `ARCHITECTURE_V3.md` pour comprendre la logique
2. Vérifiez les fichiers de configuration
3. Testez avec un petit fichier d'exemple

## 🔄 Mises à jour

**Version 3.0** (Actuelle)
- ✅ Base centrale simplifiée (10 colonnes)
- ✅ Gestion factures complémentaires (DATE_COMPLEMENTAIRE)
- ✅ Traitement HT intelligent (E0/E1/E5)
- ✅ Génération pièces comptables (17 colonnes)
- ✅ Interface modulaire propre
