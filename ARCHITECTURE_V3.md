# NOUVELLE ARCHITECTURE - VERSION 3.0
# =====================================

## 📋 STRUCTURE DE LA BASE CENTRALE

### Colonnes (10 au total):
1. UC
2. CODE RED
3. CODE AGCE
4. SITES
5. IDENTIFIANT (clé unique)
6. TENSION (BASSE/HAUTE)
7. DATE (MM/YYYY)
8. CONSO
9. MONTANT
10. DATE_COMPLEMENTAIRE (optionnel)

### Règles:
- Éditable manuellement (ajouter/modifier/supprimer)
- Une ligne = un site pour une période donnée
- DATE_COMPLEMENTAIRE vide = facture normale
- DATE_COMPLEMENTAIRE remplie = facture complémentaire


## 📄 STRUCTURE PIÈCE COMPTABLE (17 colonnes)

1. CODE AGENCE → depuis base centrale (CODE AGCE)
2. COMPTE DE CHARGES → toujours "62183464"
3. SENS → toujours "D"
4. MONTANT → depuis base centrale
5. CODE PAYT Lib 1-5 → toujours "4200"
6. CODE CHARGE Lib 6-10 → vide
7. TYPE DEP Lib 11 → vide
8. MATR OBJ Lib 12-19 → vide
9. LIBELLE COMPLEMENTAIRE → généré automatiquement
10. CODE AG → vide
11. SENS_ → vide
12. MONTANT_ → vide
13. CODE FOURNISSEUR → vide
14. FOURNISSEUR → vide
15. CONTREPARTIE → vide
16. LIB COMPLEMENTAIRE → vide
17. IDENTIFIANT → depuis base centrale


## 🏷️ GÉNÉRATION LIBELLÉ COMPLEMENTAIRE

### Pour BT:
- Facture normale: "CIE BT {DATE} {SITE}"
- Facture complémentaire: "CIE BT {DATE} {SITE} COMPLEMENTAIRE {DATE_COMPLEMENTAIRE}"

### Pour HT:
- Facture normale: "CIE HT {DATE} {SITE}"
- Facture complémentaire: "CIE HT {DATE} {SITE} COMPLEMENTAIRE {DATE_COMPLEMENTAIRE}"

### Exemples:
"CIE BT 01/2025 ABOBO SANMAKE"
"CIE HT 01/2025 COCODY ANGRE COMPLEMENTAIRE 12/2024"


## 🔄 LOGIQUE IMPORT FACTURES

### Import BT:
- Pas de factures complémentaires
- Toutes les factures sont normales
- DATE_COMPLEMENTAIRE reste vide

### Import HT:
- Colonne "typefact" identifie le type:
  * E0 : Émission normale → cumul des montants par IDENTIFIANT
  * E1 : Complémentaire → remplir DATE_COMPLEMENTAIRE avec période concernée
  * E5 : Avoir → montant négatif

### Traitement E0 (factures multiples):
Si plusieurs lignes avec même IDENTIFIANT et typefact = E0:
→ CUMULER les montants et consos
→ Ne créer qu'UNE seule ligne dans base centrale


## 📊 PAGES DE L'APPLICATION

### 1. 📊 Base Centrale
- Affiche les 10 colonnes
- Éditable (ajouter/modifier/supprimer lignes)
- Filtres: UC, DATE, TENSION
- Bouton Sauvegarder
- Bouton Export Excel

### 2. 📋 Non Enregistrées
- Affiche lignes des factures NON dans base centrale
- Toutes les colonnes des fichiers factures
- Permet de voir ce qui n'a pas été importé
- Option d'ajout manuel à la base

### 3. 🔄 Import Factures BT
- Upload fichier Excel BT
- Détection automatique des colonnes
- Normalisation identifiants
- Création lignes dans base centrale
- DATE_COMPLEMENTAIRE = vide (toujours)

### 4. 🔄 Import Factures HT
- Upload fichier Excel HT
- Détection colonne "typefact"
- Traitement spécial E0 (cumul)
- Traitement spécial E1 (complémentaire)
- Traitement spécial E5 (avoir négatif)

### 5. 📈 Statistiques
- Graphiques évolution montants
- Graphiques évolution consos
- Filtres par site et tension
- Tableau variations

### 6. ⚙️ Génération Fichiers
- Sélection période
- Génération automatique pièce comptable
- 2 tabs: BT et HT
- Bouton téléchargement Excel formaté
- Avec récapitulatif et présentation pro


## 🔀 WORKFLOW COMPLET

### Étape 1: Import factures
```
Upload factures BT → Extraction données → Base centrale
Upload factures HT → Traitement E0/E1/E5 → Base centrale
```

### Étape 2: Vérification
```
Page "Non Enregistrées" → Voir lignes manquantes
Page "Base Centrale" → Ajuster manuellement si besoin
```

### Étape 3: Génération
```
Page "Génération Fichiers"
→ Sélectionner période
→ Génération automatique pièce comptable
→ Télécharger Excel formaté
```


## 📝 EXEMPLE CONCRET

### Base Centrale:
```
UC     | CODE RED | CODE AGCE | SITES           | IDENTIFIANT | TENSION | DATE    | CONSO | MONTANT | DATE_COMP
UC-001 | RED-01   | AG-123    | ABOBO SANMAKE  | 12345       | BASSE   | 01/2025 | 150   | 50000   | 
UC-002 | RED-02   | AG-456    | COCODY ANGRE   | 67890       | HAUTE   | 01/2025 | 300   | 120000  | 12/2024
```

### Pièce Comptable Générée:
```
CODE AGENCE | COMPTE      | SENS | MONTANT | ... | LIBELLE COMPLEMENTAIRE                          | IDENTIFIANT
AG-123      | 62183464    | D    | 50000   | ... | CIE BT 01/2025 ABOBO SANMAKE                   | 12345
AG-456      | 62183464    | D    | 120000  | ... | CIE HT 01/2025 COCODY ANGRE COMPLEMENTAIRE 12/2024 | 67890
```


## ⚙️ CONFIGURATIONS TECHNIQUES

### Fichiers:
- Base_Centrale.xlsx (optionnel, pour init)
- data_centrale.pkl (sauvegarde auto)

### Normalisation IDENTIFIANT:
- Suppression .0
- Suppression espaces
- Majuscules
- Exemples: "123.0" → "123", "abc" → "ABC"

### Format DATE:
- Toujours MM/YYYY
- Exemples: "01/2025", "12/2024"

### Types TENSION:
- "BASSE" pour BT
- "HAUTE" pour HT


## 🎯 AVANTAGES NOUVELLE VERSION

1. ✅ Base centrale simplifiée (10 colonnes essentielles)
2. ✅ Gestion factures complémentaires (DATE_COMPLEMENTAIRE)
3. ✅ Édition manuelle complète
4. ✅ Vue dédiée "Non Enregistrées"
5. ✅ Génération automatique pièce comptable (17 colonnes)
6. ✅ Traitement intelligent HT (E0/E1/E5)
7. ✅ Libellés automatiques avec règles métier
8. ✅ Export Excel professionnel
