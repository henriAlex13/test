# 📘 Guide Utilisateur - Application Gestion Factures CIE

## 📑 Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Premiers pas](#2-premiers-pas)
3. [Base Centrale](#3-base-centrale)
4. [Import des factures](#4-import-des-factures)
5. [Génération des pièces comptables](#5-génération-des-pièces-comptables)
6. [Statistiques et analyses](#6-statistiques-et-analyses)
7. [Factures non enregistrées](#7-factures-non-enregistrées)
8. [Gestion des utilisateurs](#8-gestion-des-utilisateurs)
9. [Cas pratiques](#9-cas-pratiques)
10. [Résolution des problèmes](#10-résolution-des-problèmes)
11. [Conseils et bonnes pratiques](#11-conseils-et-bonnes-pratiques)

---

## 1. Vue d'ensemble

### 🎯 Qu'est-ce que cette application ?

L'**Application Gestion Factures CIE** est un outil de traitement automatisé des factures d'électricité de la Compagnie Ivoirienne d'Électricité (CIE). Elle permet de :

✅ **Centraliser** toutes vos données de facturation dans une base unique  
✅ **Importer** automatiquement les factures Basse Tension (BT) et Haute Tension (HT)  
✅ **Générer** des pièces comptables prêtes pour l'export  
✅ **Analyser** vos consommations et coûts avec des graphiques interactifs  
✅ **Suivre** votre impact environnemental (émissions CO2)  
✅ **Gérer** les utilisateurs avec différents niveaux d'accès  

### 🏗️ Architecture de l'application

```
📊 Gestion Factures CIE
│
├── 🔐 Authentification (connexion sécurisée)
├── 📊 Base Centrale (référentiel des sites et factures)
├── 🔄 Import Factures BT (factures Basse Tension)
├── 🔄 Import Factures HT (factures Haute Tension)
├── ⚙️ Génération Fichiers (pièces comptables)
├── 📈 Statistiques (analyses et graphiques)
├── 📋 Non Enregistrées (factures sans correspondance)
└── 👥 Gestion Utilisateurs (admin uniquement)
```

### 📊 Structure des données

**Base Centrale** (14 colonnes) :

| Colonne | Type | Description | Exemple |
|---------|------|-------------|---------|
| **UC** | Texte | Unité Comptable | UC-001 |
| **CODE RED** | Texte | Code RED | RED-01 |
| **CODE AGCE** | Texte | Code Agence | AG-123 |
| **SITES** | Texte | Nom du site | Siège Social |
| **IDENTIFIANT** | Texte | Identifiant unique CIE | 123456 |
| **TENSION** | Texte | BASSE ou HAUTE | HAUTE |
| **DATE** | Texte | Période (MM/YYYY) | 01/2025 |
| **CONSO** | Nombre | Consommation (kWh) | 10000 |
| **MONTANT** | Nombre | Montant TTC (FCFA) | 1500000 |
| **DATE_COMPLEMENTAIRE** | Texte | Date facture complémentaire | 01/2025 |
| **STATUT** | Texte | ACTIF ou INACTIF | ACTIF |
| **PSABON** | Nombre | Puissance souscrite (kVA) | 100 |
| **PSATTEINTE** | Nombre | Puissance atteinte (kVA) | 95 |
| **COMPTE_CHARGE** | Texte | Compte de charges | 62183464 |

---

## 2. Premiers pas

### 🔐 Connexion à l'application

#### Étape 1 : Accéder à l'application
1. Ouvrez votre navigateur web
2. Accédez à l'URL de l'application
3. Vous arrivez sur la page de connexion

#### Étape 2 : Se connecter

**Première connexion (compte par défaut) :**
```
👤 Nom d'utilisateur : admin
🔑 Mot de passe : admin123
```

⚠️ **IMPORTANT** : Changez ce mot de passe après votre première connexion !

**Connexion ultérieure :**
1. Entrez votre nom d'utilisateur
2. Entrez votre mot de passe
3. Cliquez sur **"🚀 Se connecter"**

#### Étape 3 : Interface principale

Après connexion, vous voyez :
- **En-tête** : Titre de l'application et version
- **Barre latérale gauche** : Menu de navigation
- **Zone centrale** : Contenu de la page active
- **Pied de page** : Informations système

### 🧭 Navigation

**Menu principal (barre latérale) :**

| Icône | Page | Description |
|-------|------|-------------|
| 📊 | Base Centrale | Visualiser et gérer la base de données |
| 📋 | Non Enregistrées | Factures sans correspondance |
| 🔄 | Import Factures BT | Importer factures Basse Tension |
| 🔄 | Import Factures HT | Importer factures Haute Tension |
| 📈 | Statistiques | Analyses et graphiques |
| ⚙️ | Génération Fichiers | Créer pièces comptables |
| 👥 | Gestion Utilisateurs | Gérer comptes (admin) |

### 🔄 Workflow typique

```mermaid
graph LR
    A[Connexion] --> B[Vérifier Base Centrale]
    B --> C[Importer factures BT/HT]
    C --> D[Vérifier import]
    D --> E[Générer pièces comptables]
    E --> F[Consulter statistiques]
```

**Processus mensuel type :**
1. **Jour 1** : Recevoir les fichiers de factures CIE
2. **Jour 1-2** : Importer les factures BT et HT
3. **Jour 2** : Vérifier les factures non enregistrées
4. **Jour 3** : Générer les pièces comptables
5. **Jour 3** : Transmettre au service comptabilité
6. **En continu** : Consulter les statistiques

---

## 3. Base Centrale

### 📊 Qu'est-ce que la Base Centrale ?

La **Base Centrale** est le cœur de l'application. C'est une base de données qui contient :
- ✅ La **liste de tous vos sites** (identifiants CIE)
- ✅ Les **informations administratives** (UC, codes, noms)
- ✅ L'**historique des factures** période par période
- ✅ Les **consommations et montants** pour chaque site

### 📖 Consulter la Base Centrale

#### Accéder à la page
1. Cliquez sur **"📊 Base Centrale"** dans le menu
2. La base s'affiche automatiquement

#### Interface de consultation

**En haut de page :**
```
📊 Base Centrale - Référentiel Sites et Factures
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Total : 150 ligne(s)
[Rechercher] [Filtrer] [Télécharger Excel]
```

**Statistiques affichées :**
- 📊 **Nombre total de lignes**
- 📅 **Nombre de périodes** différentes
- 🏢 **Nombre de sites** uniques
- ⚡ **Répartition BT/HT**

#### Filtres disponibles

**1. Recherche globale**
```
🔍 Rechercher : [_____________]
```
- Tapez n'importe quel texte
- Recherche dans toutes les colonnes
- Résultats en temps réel

**2. Filtres par colonne**
- Cliquez sur l'en-tête d'une colonne
- Sélectionnez les valeurs à afficher
- Combinez plusieurs filtres

**Exemples de filtrage :**
```
✅ Afficher uniquement les sites HT
   → Filtre TENSION = "HAUTE"

✅ Afficher la période 01/2025
   → Filtre DATE = "01/2025"

✅ Afficher les sites inactifs
   → Filtre STATUT = "INACTIF"

✅ Afficher un site spécifique
   → Recherche globale : "123456"
```

### ✏️ Modifier la Base Centrale

#### Modifier une cellule
1. **Double-cliquez** sur la cellule à modifier
2. Modifiez la valeur
3. Appuyez sur **Entrée** pour valider
4. Cliquez sur **"💾 Sauvegarder les modifications"**

⚠️ **Attention** : Les modifications sont **permanentes** après sauvegarde !

#### Cas d'usage de modification

**Exemple 1 : Changer le statut d'un site**
```
Besoin : Mettre un site en INACTIF (fermé)

1. Trouver le site (recherche par IDENTIFIANT)
2. Double-clic sur la colonne STATUT
3. Changer "ACTIF" → "INACTIF"
4. Sauvegarder

Résultat : Le site n'apparaîtra plus dans les pièces comptables
```

**Exemple 2 : Modifier un compte de charges**
```
Besoin : Changer le compte comptable d'un site

1. Trouver le site
2. Double-clic sur COMPTE_CHARGE
3. Changer "62183464" → "62183999"
4. Sauvegarder

Résultat : Les futures pièces utiliseront le nouveau compte
```

**Exemple 3 : Corriger un nom de site**
```
Besoin : Corriger une faute de frappe dans SITES

1. Trouver les lignes concernées (même IDENTIFIANT)
2. Modifier la colonne SITES
3. Répéter pour chaque ligne
4. Sauvegarder

Résultat : Toutes les pièces futures auront le bon nom
```

### 📥 Télécharger la Base Centrale

#### Format Excel
1. Cliquez sur **"📥 Télécharger en Excel"**
2. Le fichier `Base_Centrale.xlsx` se télécharge
3. Ouvrez-le avec Excel/LibreOffice

**Utilité :**
- ✅ Archivage mensuel
- ✅ Partage avec d'autres services
- ✅ Analyses externes (Power BI, Tableau, etc.)
- ✅ Backup manuel

#### Format CSV
1. Dans Excel, faites **"Enregistrer sous"**
2. Choisissez format **"CSV (séparateur : point-virgule)"**
3. Utilisez pour imports dans d'autres systèmes

### 🔍 Interpréter les données

#### Ligne type - Site HAUTE TENSION
```
UC: UC-001
CODE RED: RED-01
CODE AGCE: AG-123
SITES: Siège Social
IDENTIFIANT: 123456
TENSION: HAUTE
DATE: 01/2025
CONSO: 10000 kWh
MONTANT: 1500000 FCFA
DATE_COMPLEMENTAIRE: (vide)
STATUT: ACTIF
PSABON: 100 kVA
PSATTEINTE: 95 kVA
COMPTE_CHARGE: 62183464
```

**Interprétation :**
- Site actif avec consommation normale
- Puissance utilisée : 95/100 kVA = **95% d'utilisation**
- Pas de facture complémentaire
- Compte de charges standard

#### Ligne type - Site BASSE TENSION
```
IDENTIFIANT: 789012
TENSION: BASSE
DATE: 01/2025
CONSO: 500 kWh
MONTANT: 75000 FCFA
PSABON: 0
PSATTEINTE: 0
```

**Interprétation :**
- Site BT avec petite consommation
- Pas de puissance (normal pour BT)
- Facture simple sans complément

---

## 4. Import des factures

### 🔄 Import Factures Basse Tension (BT)

#### 📋 Prérequis

**Format du fichier :**
- Extension : `.xlsx` ou `.xls`
- Provenance : Fichier export CIE

**Colonnes requises :**
| Nom exact dans le fichier | Description |
|---------------------------|-------------|
| `Référence Contrat` | Identifiant du site |
| `Montant facture TTC` | Montant en FCFA |
| `KWH Facturé` | Consommation en kWh |
| `Période Facture sur date fact` | Période (format : 202501) |

⚠️ **Les noms de colonnes doivent être exacts** (respecter majuscules/minuscules)

#### 📖 Procédure d'import

**Étape 1 : Accéder à la page**
1. Menu → **"🔄 Import Factures BT"**

**Étape 2 : Charger le fichier**
```
📌 BASSE TENSION
Import factures BT - Pas de factures complémentaires
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Parcourir...] Sélectionnez le fichier de factures BT
```

1. Cliquez sur **"Parcourir"**
2. Sélectionnez votre fichier Excel
3. Cliquez sur **"Ouvrir"**

**Étape 3 : Vérification automatique**

L'application vérifie :
- ✅ Format du fichier (Excel)
- ✅ Présence des colonnes requises
- ✅ Détection de la période

**Affichage des résultats :**
```
✅ Fichier chargé : 150 ligne(s)
✅ Période détectée : 01/2025

👁️ Aperçu des factures BT
[Tableau des 20 premières lignes]
```

**Étape 4 : Lancer l'import**
1. Vérifiez l'aperçu
2. Cliquez sur **"🔄 LANCER L'IMPORT BT"**

**Étape 5 : Résultats**
```
🎉 Import BT terminé : 145 ligne(s) ajoutée(s) !

✅ Lignes ajoutées : 145
📊 Total base centrale : 1500
📅 Période : 01/2025
🔄 Factures cumulées : 5

❌ 5 identifiant(s) non trouvé(s) dans la base centrale
```

#### 🔍 Comprendre les résultats

**Lignes ajoutées**
- Nouvelles lignes créées dans la base centrale
- Une ligne = un site pour une période

**Factures cumulées**
- Nombre de factures avec le **même identifiant** qui ont été fusionnées
- **Normal** : Un site peut avoir plusieurs factures BT par mois

**Exemple de cumul :**
```
Fichier d'import :
- IDENTIFIANT 123456 → Facture 1 : 500 kWh, 75000 FCFA
- IDENTIFIANT 123456 → Facture 2 : 300 kWh, 45000 FCFA

Résultat dans la base :
- IDENTIFIANT 123456 → Total : 800 kWh, 120000 FCFA
```

**Identifiants non trouvés**
- Factures pour des sites **absents de la base centrale**
- **Action requise** : Voir section "Factures non enregistrées"

#### ⚠️ Messages d'erreur courants

**Erreur 1 : Colonnes manquantes**
```
❌ Colonnes manquantes : Montant facture TTC
```
**Solution :** Vérifiez le nom exact des colonnes dans votre fichier Excel

**Erreur 2 : Aucune période détectée**
```
❌ Aucune période détectée dans le fichier
```
**Solution :** Vérifiez que la colonne `Période Facture sur date fact` contient des valeurs

**Erreur 3 : Fichier invalide**
```
❌ Erreur lors du traitement : ...
```
**Solution :** Vérifiez que le fichier n'est pas corrompu, essayez de le réenregistrer

### ⚡ Import Factures Haute Tension (HT)

#### 📋 Prérequis

**Colonnes requises :**
| Nom exact | Description |
|-----------|-------------|
| `refraccord` | Identifiant du site |
| `montfact` | Montant en FCFA |
| `conso` | Consommation en kWh |
| `Periode_Emission_Bordereau` | Période |
| `typefact` | Type de facture (E0/E1/E5) |
| `PSABON` | Puissance souscrite (kVA) |
| `PSATTEINTE` | Puissance atteinte (kVA) |

#### 📖 Procédure d'import (similaire à BT)

**Étapes identiques :**
1. Menu → **"🔄 Import Factures HT"**
2. Sélectionner le fichier
3. Vérifier l'aperçu
4. Lancer l'import

**Différence : Types de factures**

L'import HT gère **3 types de factures** :

```
📊 Statistiques par type de facture

E0 (Normal)         E1 (Complém.)      E5 (Avoir)        Autre
150 → 145           5                  2                 0
```

#### 📚 Types de factures HT

**Type E0 - Émission normale**
- Factures mensuelles classiques
- **Cumul automatique** si plusieurs factures même site
- Exemple : 2 factures E0 pour le site 123456 → 1 ligne dans la base

**Type E1 - Facture complémentaire**
- Complément de facturation (régularisation)
- **Non importée automatiquement** (nécessite contrôle manuel)
- Remplira `DATE_COMPLEMENTAIRE` lors de l'import manuel

**Type E5 - Avoir (crédit)**
- Remboursement ou correction
- **Montant négatif** dans la base
- Conserve la puissance

**Type Autre**
- Factures sans type ou type non reconnu
- Traitement normal (comme E0)

#### 🔧 Import manuel des factures E1

Les factures **E1 (complémentaires)** nécessitent une validation manuelle :

**Étape 1 : Aller dans "Non Enregistrées"**
1. Menu → **"📋 Non Enregistrées"**
2. Section **"Factures E1 (Complémentaires)"**

**Étape 2 : Vérifier les factures E1**
```
📋 5 facture(s) complémentaire(s) (E1) détectée(s)

[Tableau des factures E1]
IDENTIFIANT | Montant | Consommation | Période
123456      | 250000  | 1500         | 01/2025
789012      | 180000  | 1200         | 01/2025
```

**Étape 3 : Importer si valide**
1. Vérifiez que les montants sont corrects
2. Cliquez sur **"✅ Importer ces factures E1"**
3. Les factures sont ajoutées avec `DATE_COMPLEMENTAIRE` remplie

---

## 5. Génération des pièces comptables

### ⚙️ Qu'est-ce qu'une pièce comptable ?

Une **pièce comptable** est un fichier Excel formaté contenant :
- Les écritures comptables pour chaque facture
- Le compte de charges
- Les montants à imputer
- Les libellés détaillés

**Format de sortie :** Fichier Excel prêt à importer dans votre logiciel comptable

### 📖 Générer une pièce comptable

#### Étape 1 : Accéder à la page
1. Menu → **"⚙️ Génération Fichiers"**

#### Étape 2 : Sélectionner les paramètres

**Interface :**
```
⚙️ Génération des Pièces Comptables
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Période :        [Sélectionner...▼]
⚡ Type de tension : [○ Tout  ○ BT  ○ HT]
📝 Format :         [○ Excel  ○ CSV]

           [📥 GÉNÉRER LA PIÈCE COMPTABLE]
```

**1. Choisir la période**
- Liste déroulante des périodes disponibles
- Format : `01/2025`, `02/2025`, etc.
- Seules les périodes avec données apparaissent

**2. Choisir le type de tension**
- **📊 Tout** : BT + HT ensemble (recommandé)
- **🔌 BT uniquement** : Seulement Basse Tension
- **⚡ HT uniquement** : Seulement Haute Tension

**3. Choisir le format**
- **Excel** : Fichier `.xlsx` avec mise en forme (recommandé)
- **CSV** : Fichier texte pour imports spécifiques

#### Étape 3 : Générer le fichier

1. Cliquez sur **"📥 GÉNÉRER LA PIÈCE COMPTABLE"**
2. Attendez le traitement (quelques secondes)
3. Le fichier se télécharge automatiquement

**Nom du fichier généré :**
```
Piece_Comptable_BT_01_2025.xlsx
Piece_Comptable_HT_01_2025.xlsx
Piece_Comptable_TOUT_01_2025.xlsx
```

#### Étape 4 : Résultats affichés

```
🎉 Pièce comptable générée avec succès !

✅ Lignes générées : 145
📅 Période : 01/2025
⚡ Type : TOUT (BT + HT)
💰 Montant total : 15,500,000 FCFA

📥 [Télécharger le fichier Excel]

ℹ️ 5 site(s) inactif(s) exclu(s)
```

### 📊 Contenu de la pièce comptable

#### Structure du fichier Excel

**17 colonnes :**

| Colonne | Contenu | Exemple |
|---------|---------|---------|
| CODE AGENCE | Code agence | AG-123 |
| COMPTE DE CHARGES | Compte comptable | 62183464 |
| SENS | Débit/Crédit | D |
| MONTANT | Montant FCFA | 1500000 |
| CODE PAYT Lib 1-5 | Code paiement | 4200 |
| CODE CHARGE Lib 6-10 | (vide) | |
| TYPE DEP Lib 11 | (vide) | |
| MATR OBJ Lib 12-19 | (vide) | |
| LIBELLE COMPLEMENTAIRE | Description | CIE HT 01/2025 Siège Social |
| CODE AG | (vide) | |
| SENS_ | (vide) | |
| MONTANT_ | (vide) | |
| CODE FOURNISSEUR | (vide) | |
| FOURNISSEUR | (vide) | |
| CONTREPARTIE | (vide) | |
| LIB COMPLEMENTAIRE | (vide) | |
| IDENTIFIANT | Identifiant CIE | 123456 |

#### Mise en forme Excel

Le fichier généré est **formaté professionnellement** :

**En-tête :**
- Fond bleu (BT) ou orange (HT)
- Texte blanc en gras
- Bordures

**Données :**
- Alternance de couleurs (lignes paires/impaires)
- Montants formatés avec séparateurs de milliers
- Colonnes auto-ajustées

**Pied de page :**
- Total des montants
- Nombre de lignes
- Date de génération

### 📤 Utiliser la pièce comptable

#### Import dans un logiciel comptable

**Logiciels compatibles :**
- SAP
- Sage
- Ciel
- Quadratus
- EBP
- Odoo

**Procédure générale :**
1. Ouvrir le logiciel comptable
2. Aller dans **"Import écritures"**
3. Sélectionner le fichier Excel/CSV généré
4. Mapper les colonnes si nécessaire
5. Valider l'import

#### Vérifications avant import

**Checklist :**
- ✅ Toutes les lignes sont présentes
- ✅ Le total des montants est correct
- ✅ Les codes agence sont valides
- ✅ Les comptes de charges existent dans le plan comptable
- ✅ La période est correcte

#### Conservation des fichiers

**Recommandations :**
```
📁 Archives_CIE/
  └── 2025/
      ├── 01_Janvier/
      │   ├── Factures_CIE_BT_janvier.xlsx
      │   ├── Factures_CIE_HT_janvier.xlsx
      │   ├── Piece_Comptable_BT_01_2025.xlsx
      │   └── Piece_Comptable_HT_01_2025.xlsx
      └── 02_Fevrier/
          └── ...
```

**Durée de conservation :** Minimum 10 ans (obligations légales)

---

## 6. Statistiques et analyses

### 📈 Accéder aux statistiques

1. Menu → **"📈 Statistiques"**
2. L'interface se charge automatiquement

### 🎛️ Filtres et options

**Interface de filtrage :**
```
📈 Statistiques et Évolution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 12 période(s) disponible(s)

🏢 Filtrer par SITE        ⚡ Type d'analyse
[Tous ▼]                    [📊 Global (BT + HT) ▼]
```

#### Filtre par SITE

**Options :**
- **Tous** : Vue globale de tous les sites
- **Site spécifique** : Analyse d'un site particulier

**Exemple d'utilisation :**
```
Besoin : Analyser uniquement le "Siège Social"

1. Sélectionnez "Siège Social" dans la liste
2. Tous les graphiques se mettent à jour
3. Seules les données du Siège apparaissent
```

#### Filtre par Type

**Options :**
- **📊 Global (BT + HT)** : Tous les sites ensemble
- **🔌 Basse Tension uniquement** : Sites BT seulement
- **⚡ Haute Tension uniquement** : Sites HT seulement

### 📊 Graphique 1 : Évolution des Montants

**Titre :** 💰 Évolution des Montants

**Contenu :**
- Courbe bleue des montants par période
- Axe X : Périodes (01/2025, 02/2025, etc.)
- Axe Y : Montants en FCFA

**Interactions :**
- **Survol** : Affiche montant exact
- **Zoom** : Cliquez-glissez sur une zone
- **Réinitialiser** : Double-clic

**Utilité :**
- Voir les variations de coûts mois par mois
- Identifier les pics de dépenses
- Comparer les périodes

**Exemple d'analyse :**
```
Observation : Pic en août 2024 à 2,5M FCFA

Questions à se poser :
- Canicule → climatisation intensive ?
- Événement spécial → consommation exceptionnelle ?
- Erreur de facturation → vérifier les factures
```

### ⚡ Graphique 2 : Consommations et Émissions CO2

**Titre :** ⚡ Évolution des Consommations et Émissions CO2

**Configuration :**
```
[0.5] Facteur CO2 (kg/kWh)
💡 Émissions CO2 = Consommation × 0.5 kg CO2/kWh
```

**Contenu :**
- **Courbe rouge (axe gauche)** : Consommation en kWh
- **Courbe verte pointillée (axe droit)** : Émissions CO2 en kg

**Statistiques affichées :**
```
🌍 Total CO2    CO2 (tonnes)   🌳 Arbres équiv.   🚗 km voiture
   125,000 kg      125 t           5,000              1,041,667
```

**Ajuster le facteur d'émission :**
1. Modifiez la valeur dans le champ (ex: 0.45)
2. Le graphique se met à jour instantanément
3. Les statistiques se recalculent

**Équivalences environnementales :**
- **Arbres** : 1 arbre absorbe ~25 kg CO2/an
- **km voiture** : Voiture thermique émet ~120 g CO2/km

**Utilité :**
- Suivre l'impact environnemental
- Sensibiliser les équipes
- Reporting RSE (Responsabilité Sociétale)

**Exemple d'analyse :**
```
Objectif : Réduire émissions CO2 de 10%

Janvier 2025 : 10,000 kg CO2
Action : Optimisation climatisation
Février 2025 : 9,000 kg CO2
✅ Objectif atteint : -10%
```

### ⚡ Graphique 3 : Puissances (HT uniquement)

**Titre :** ⚡ Évolution des Puissances (HT uniquement)

**Affiché uniquement si :**
- Type = "Haute Tension" OU "Global"
- Des données de puissance existent

**Contenu :**
- **Courbe bleue** : Puissance Souscrite (PSABON) en kVA
- **Courbe rouge** : Puissance Atteinte (PSATTEINTE) en kVA

**Vue globale (Tous les sites) :**
- Moyennes des puissances par période
- Tendance générale

**Vue par site :**
```
Site : Siège Social
━━━━━━━━━━━━━━━━━━━━━━

PS Souscrite    PS Atteinte    Taux Utilisation
100.0 kVA       95.0 kVA       95.0% ✅ Normal
```

**Alertes de dépassement :**
- 🟢 **Normal** : < 90%
- 🟠 **Proche limite** : 90-100%
- 🔴 **Dépassement** : > 100%

**Utilité :**
- Optimiser les abonnements (réduire si sous-utilisé)
- Éviter les pénalités de dépassement
- Planifier les augmentations de puissance

**Exemple d'optimisation :**
```
Constat : Site X utilise 50 kVA sur 100 souscrit
Taux utilisation : 50%

Action : Réduire abonnement à 60 kVA
Économie annuelle : ~300,000 FCFA
```

### 📊 Détails par période (expanders)

**Bouton :** "📊 Détails par période"

**Contenu :**
Tableau avec toutes les données numériques :
```
Période  | Conso (kWh) | Montant (FCFA) | CO2 (kg) | PS Souscrite | PS Atteinte
---------|-------------|----------------|----------|--------------|-------------
01/2025  | 10,000      | 1,500,000      | 5,000    | 100.0        | 95.0
02/2025  | 9,500       | 1,425,000      | 4,750    | 100.0        | 92.0
```

**Utilité :**
- Export des données (copier-coller vers Excel)
- Vérifications précises
- Calculs personnalisés

---

## 7. Factures non enregistrées

### 📋 Qu'est-ce qu'une facture "non enregistrée" ?

Une facture **non enregistrée** est une facture importée dont **l'IDENTIFIANT n'existe pas** dans la Base Centrale.

**Causes possibles :**
- 🆕 **Nouveau site** : Nouveau contrat CIE non encore référencé
- ❌ **Erreur de saisie** : Identifiant mal saisi dans la base
- 🔄 **Changement d'identifiant** : CIE a changé l'identifiant du site
- 📋 **Base incomplète** : Site oublié lors de la création initiale

### 📖 Accéder aux factures non enregistrées

1. Menu → **"📋 Non Enregistrées"**

**Interface :**
```
📋 Factures Non Enregistrées
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ 12 facture(s) BT non enregistrée(s)
❌ 8 facture(s) HT non enregistrée(s)
⚠️ 5 facture(s) E1 (complémentaires) en attente

[Section BT] [Section HT] [Section E1]
```

### 🔌 Section BT - Factures non enregistrées

**Tableau affiché :**
```
IDENTIFIANT | Montant TTC | Consommation | Période   | Action
------------|-------------|--------------|-----------|--------
987654      | 125,000     | 800          | 01/2025   | [Ajouter]
654321      | 98,000      | 650          | 01/2025   | [Ajouter]
```

**Actions possibles :**

#### Option 1 : Ajouter à la base centrale

**Quand l'utiliser :**
- C'est un **nouveau site légitime**
- L'identifiant est **correct**

**Procédure :**
1. Cliquez sur **[Ajouter]** à côté de la facture
2. Remplissez le formulaire :
```
Ajouter le site 987654 à la Base Centrale
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UC :              [UC-___]
CODE RED :        [RED-___]
CODE AGCE :       [AG-___]
SITES :           [_______________]
STATUT :          [ACTIF ▼]
COMPTE_CHARGE :   [62183464]

        [✅ Ajouter et importer la facture]
```
3. Validez

**Résultat :**
- Le site est ajouté à la base
- La facture est importée automatiquement
- Toutes les futures factures seront reconnues

#### Option 2 : Ignorer

**Quand l'utiliser :**
- Facture **en double**
- Erreur de la CIE
- Site qui ne vous concerne pas

**Procédure :**
1. Ne rien faire
2. La facture reste dans "Non enregistrées"
3. Elle n'affecte pas vos pièces comptables

### ⚡ Section HT - Factures non enregistrées

**Identique à BT**, avec en plus la colonne **Type** :
```
IDENTIFIANT | Type | Montant  | Conso  | PSABON | PSATTEINTE
------------|------|----------|--------|--------|------------
147258      | E0   | 1,850,000| 12,000 | 150.0  | 145.0
```

### 📋 Section E1 - Factures complémentaires

**Interface :**
```
📋 Factures E1 (Complémentaires) en attente
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5 facture(s) complémentaire(s) détectée(s)

IDENTIFIANT | Montant   | Consommation | Période
------------|-----------|--------------|----------
123456      | 250,000   | 1,500        | 01/2025
789012      | 180,000   | 1,200        | 01/2025

[✅ Importer ces factures E1]
```

**Pourquoi sont-elles séparées ?**
- Nécessitent **vérification manuelle**
- Montants complémentaires à valider
- Éviter les doublons

**Procédure d'import :**
1. **Vérifier** que les montants sont corrects
2. **Comparer** avec les factures normales (E0)
3. Cliquer sur **"✅ Importer ces factures E1"**
4. Les factures sont ajoutées avec `DATE_COMPLEMENTAIRE` remplie

---

## 8. Gestion des utilisateurs

### 👥 Accès (Admin uniquement)

**Prérequis :** Être connecté avec un compte **admin**

1. Menu → **"👥 Gestion Utilisateurs"**

**Si vous n'êtes pas admin :**
```
❌ Accès réservé aux administrateurs
```

### 📖 Onglet "Liste"

**Interface :**
```
📋 Liste des utilisateurs
━━━━━━━━━━━━━━━━━━━━━━

Total : 5 | Actifs : 4 | Admins : 2

Utilisateur | Nom complet          | Rôle        | Actif | Créé le    | Dernière connexion
------------|----------------------|-------------|-------|------------|-------------------
admin       | Administrateur       | admin       | ✓     | 01/01/2025 | 05/02/2026 10:30
jdupont     | Jean Dupont         | utilisateur | ✓     | 15/01/2025 | 04/02/2026 14:20
mmartin     | Marie Martin        | utilisateur | ✓     | 20/01/2025 | 05/02/2026 09:15
pdurand     | Pierre Durand       | admin       | ✓     | 25/01/2025 | 03/02/2026 16:45
aleblanc    | Anne Leblanc        | utilisateur | ✗     | 30/01/2025 | 02/02/2026 11:00
```

**Colonnes :**
- **Utilisateur** : Nom de connexion (login)
- **Nom complet** : Prénom Nom
- **Rôle** : admin ou utilisateur
- **Actif** : Compte activé (✓) ou désactivé (✗)
- **Créé le** : Date de création du compte
- **Dernière connexion** : Dernier login

### ➕ Onglet "Ajouter"

**Formulaire de création :**
```
Ajouter un utilisateur
━━━━━━━━━━━━━━━━━━━━

Nom d'utilisateur :     [_______________]
Nom complet :           [_______________]
Mot de passe :          [••••••••••••••]
Confirmer mot de passe :[••••••••••••••]
Rôle :                  [utilisateur ▼]

              [➕ Ajouter]
```

**Règles de validation :**
- ✅ Tous les champs obligatoires
- ✅ Nom d'utilisateur **unique** (non existant)
- ✅ Mot de passe minimum **6 caractères**
- ✅ Mots de passe identiques

**Procédure :**
1. Remplir tous les champs
2. Choisir le rôle :
   - **utilisateur** : Accès normal (recommandé)
   - **admin** : Tous les droits (réservé)
3. Cliquer sur **[➕ Ajouter]**

**Résultat :**
```
✅ Utilisateur jdupont ajouté !
```

**Conseils :**
- Créez un utilisateur **par personne** (pas de partage)
- Nom d'utilisateur = prénom.nom ou initiales
- Rôle admin = uniquement responsables

### 🔧 Onglet "Modifier"

**Sélection de l'utilisateur :**
```
Modifier un utilisateur
━━━━━━━━━━━━━━━━━━━━

Sélectionner un utilisateur : [jdupont ▼]
```

#### Action 1 : Changer le mot de passe

```
🔑 Changer mot de passe
━━━━━━━━━━━━━━━━━━━━

Nouveau mot de passe : [••••••••]
Confirmer :            [••••••••]

          [Changer]
```

**Quand l'utiliser :**
- Utilisateur a **oublié** son mot de passe
- Mot de passe **compromis**
- Renouvellement périodique (sécurité)

**Procédure :**
1. Sélectionner l'utilisateur
2. Entrer le nouveau mot de passe (2 fois)
3. Cliquer sur **[Changer]**

**Résultat :**
```
✅ Mot de passe modifié !
```

**Note :** L'utilisateur devra utiliser le **nouveau mot de passe** dès sa prochaine connexion.

#### Action 2 : Activer/Désactiver

```
🔄 Activer/Désactiver
━━━━━━━━━━━━━━━━━━━

Statut actuel : ACTIF

    [🔴 Désactiver]
```

**Désactiver un compte :**
- L'utilisateur **ne peut plus se connecter**
- Ses données restent intactes
- Réversible (peut être réactivé)

**Quand désactiver :**
- Employé a **quitté l'entreprise**
- Compte **inutilisé** (sécurité)
- **Suspension temporaire**

**Réactiver un compte :**
```
Statut actuel : INACTIF

    [🟢 Activer]
```

### 🔐 Différences Admin vs Utilisateur

| Fonctionnalité | Admin | Utilisateur |
|----------------|-------|-------------|
| Consulter Base Centrale | ✅ | ✅ |
| **Modifier Base Centrale** | ✅ | ❌ |
| Importer factures BT/HT | ✅ | ✅ |
| Générer pièces comptables | ✅ | ✅ |
| Consulter statistiques | ✅ | ✅ |
| Gérer factures non enregistrées | ✅ | ✅ |
| **Gérer utilisateurs** | ✅ | ❌ |
| **Voir menu "👥 Gestion Utilisateurs"** | ✅ | ❌ |

**Recommandation :** 
- 1-2 comptes **admin** maximum (responsables)
- Tous les autres en **utilisateur**

### 🚪 Déconnexion

**Procédure :**
1. Barre latérale → Bas de page
2. Section **"👤 [Nom utilisateur]"**
3. Cliquer sur **"🚪 Déconnexion"**

**Résultat :**
- Retour à la page de connexion
- Session fermée

**Bonne pratique :** Toujours se déconnecter en fin de journée !

---

## 9. Cas pratiques

### 📋 Cas 1 : Traitement mensuel complet

**Contexte :** Début de mois, vous recevez les factures CIE de janvier 2025

**Fichiers reçus :**
- `Factures_BT_janvier_2025.xlsx`
- `Factures_HT_janvier_2025.xlsx`

**Workflow complet :**

```
Jour 1 - Import
─────────────────
09h00 : Connexion à l'application
        → Login : votre_username
        → Mot de passe : ••••••••

09h05 : Import factures BT
        → Menu "🔄 Import Factures BT"
        → Upload "Factures_BT_janvier_2025.xlsx"
        → Vérification aperçu
        → Lancer import
        → ✅ 145 lignes ajoutées
        → ⚠️ 5 non enregistrées

09h15 : Import factures HT
        → Menu "🔄 Import Factures HT"
        → Upload "Factures_HT_janvier_2025.xlsx"
        → Vérification aperçu
        → Lancer import
        → ✅ 89 lignes ajoutées
        → ⚠️ 3 non enregistrées
        → ⚠️ 5 factures E1 en attente

09h30 : Traiter factures non enregistrées (BT)
        → Menu "📋 Non Enregistrées"
        → Section BT : 5 factures
        → Analyser chaque facture :
           • 987654 → Nouveau site agence
             → [Ajouter] + remplir infos
           • 654321 → Erreur CIE (doublon)
             → Ignorer
           • Etc.

09h45 : Traiter factures non enregistrées (HT)
        → Section HT : 3 factures
        → Même processus

10h00 : Traiter factures E1 (complémentaires)
        → Section E1 : 5 factures
        → Vérifier montants
        → [✅ Importer ces factures E1]

10h10 : Vérification Base Centrale
        → Menu "📊 Base Centrale"
        → Filtrer DATE = "01/2025"
        → Vérifier nombre de lignes
        → Spot-check quelques montants

Jour 2 - Génération & Envoi
────────────────────────────
14h00 : Générer pièce comptable BT
        → Menu "⚙️ Génération Fichiers"
        → Période : 01/2025
        → Type : BT uniquement
        → Format : Excel
        → [📥 GÉNÉRER]
        → Télécharger "Piece_Comptable_BT_01_2025.xlsx"

14h05 : Générer pièce comptable HT
        → Même processus pour HT
        → Télécharger "Piece_Comptable_HT_01_2025.xlsx"

14h10 : Vérification des pièces
        → Ouvrir les 2 fichiers Excel
        → Vérifier totaux
        → Vérifier cohérence

14h20 : Envoi comptabilité
        → Email à compta@entreprise.com
        → Sujet : "Pièces comptables CIE - Janvier 2025"
        → Pièces jointes : 2 fichiers Excel

14h30 : Archivage
        → Créer dossier "2025/01_Janvier"
        → Copier tous les fichiers (imports + pièces)

Jour 3 - Analyse
─────────────────
10h00 : Consulter statistiques
        → Menu "📈 Statistiques"
        → Analyser évolution
        → Identifier anomalies

10h30 : Rapport mensuel
        → Capturer graphiques
        → Créer PowerPoint
        → Envoyer à direction
```

**Temps total estimé :** 2-3 heures

### 📋 Cas 2 : Nouveau site à ajouter

**Contexte :** Vous ouvrez un nouveau bureau, nouveau contrat CIE

**Informations CIE reçues :**
```
Identifiant CIE : 999888
Type : Basse Tension
Adresse : 123 Avenue principale, Abidjan
```

**Informations internes :**
```
UC : UC-050
CODE RED : RED-10
CODE AGCE : AG-456
Nom : Agence Plateau
```

**Procédure d'ajout manuel :**

**Option 1 : Via une facture (recommandé)**
1. Attendre la première facture CIE
2. Importer la facture (elle sera "non enregistrée")
3. Aller dans "📋 Non Enregistrées"
4. Cliquer sur [Ajouter] à côté de l'identifiant 999888
5. Remplir le formulaire
6. Valider → Site ajouté + facture importée

**Option 2 : Via Excel (pour plusieurs sites)**
1. Menu "📊 Base Centrale"
2. Télécharger la base en Excel
3. Ajouter une ligne manuellement :
```
UC: UC-050
CODE RED: RED-10
CODE AGCE: AG-456
SITES: Agence Plateau
IDENTIFIANT: 999888
TENSION: BASSE
DATE: (laisser vide pour l'instant)
CONSO: 0
MONTANT: 0
DATE_COMPLEMENTAIRE: (vide)
STATUT: ACTIF
PSABON: 0
PSATTEINTE: 0
COMPTE_CHARGE: 62183464
```
4. Sauvegarder le fichier
5. Remplacer `Base_Centrale.xlsx` sur le serveur
6. Redémarrer l'application

**Validation :**
1. Menu "📊 Base Centrale"
2. Rechercher "999888"
3. Vérifier que le site apparaît

### 📋 Cas 3 : Fermeture d'un site

**Contexte :** L'agence Riviera ferme définitivement

**IDENTIFIANT :** 111222

**Objectif :** Ne plus générer d'écritures comptables pour ce site

**Procédure :**

**Option 1 : Passer en INACTIF (recommandé)**
1. Menu "📊 Base Centrale"
2. Rechercher "111222"
3. Pour chaque ligne trouvée :
   - Double-clic sur colonne STATUT
   - Changer "ACTIF" → "INACTIF"
4. Cliquer sur "💾 Sauvegarder"

**Résultat :**
- Le site reste dans la base (historique conservé)
- N'apparaît plus dans les pièces comptables futures
- Visible dans les statistiques passées

**Option 2 : Supprimer (déconseillé)**
1. Télécharger la base en Excel
2. Supprimer toutes les lignes avec IDENTIFIANT = 111222
3. Réimporter

⚠️ **Attention :** Perte de l'historique !

**Validation :**
1. Générer une pièce comptable test
2. Vérifier que 111222 n'apparaît pas
3. Message : "X site(s) inactif(s) exclu(s)"

### 📋 Cas 4 : Corriger une erreur de montant

**Contexte :** La facture du site 123456 pour janvier 2025 est erronée

**Montant incorrect :** 1,500,000 FCFA  
**Montant correct :** 1,350,000 FCFA

**Procédure de correction :**

**Étape 1 : Trouver la ligne**
1. Menu "📊 Base Centrale"
2. Recherche globale : "123456"
3. Filtrer DATE = "01/2025"

**Étape 2 : Modifier le montant**
1. Trouver la ligne concernée
2. Double-clic sur colonne MONTANT
3. Remplacer 1500000 par 1350000
4. Appuyer sur Entrée

**Étape 3 : Sauvegarder**
1. Cliquer sur "💾 Sauvegarder les modifications"
2. Message : "✅ Modifications sauvegardées"

**Étape 4 : Régénérer la pièce**
1. Menu "⚙️ Génération Fichiers"
2. Générer à nouveau pour 01/2025
3. Le nouveau fichier aura le montant corrigé

**Étape 5 : Informer la comptabilité**
1. Email : "Correction pièce comptable janvier 2025"
2. Joindre la nouvelle pièce
3. Expliquer la correction

### 📋 Cas 5 : Analyser une hausse de consommation

**Contexte :** Le directeur demande pourquoi la facture d'août est élevée

**Procédure d'analyse :**

**Étape 1 : Statistiques globales**
1. Menu "📈 Statistiques"
2. Type : "📊 Global (BT + HT)"
3. Observer le graphique Consommations

**Constatation :**
```
Juillet 2024 : 80,000 kWh
Août 2024 : 120,000 kWh (+50%)
Septembre 2024 : 85,000 kWh
```

**Étape 2 : Identifier le(s) site(s)**
1. Filtrer par site, un par un
2. Comparer juillet vs août

**Résultat :**
```
Siège Social :
- Juillet : 50,000 kWh
- Août : 90,000 kWh (+80%) ← PROBLÈME ICI

Autres sites : Stables
```

**Étape 3 : Analyser les puissances (si HT)**
1. Graphique Puissances
2. Vérifier PSATTEINTE

**Constatation :**
```
Puissance atteinte août : 145 kVA
Puissance souscrite : 100 kVA
→ Dépassement de 45% !
```

**Étape 4 : Rechercher la cause**

**Causes possibles :**
- 🌡️ **Canicule** → Climatisation à fond
- 🏢 **Événement** → Conférence, salon
- ⚙️ **Équipement** → Nouveau serveur, machine
- 🐛 **Anomalie** → Fuite électrique, compteur défectueux

**Actions :**
1. Vérifier la météo d'août (canicule ?)
2. Consulter l'agenda (événements ?)
3. Audit technique du site
4. Contacter la CIE si anomalie

**Étape 5 : Rapport**
```
RAPPORT D'ANALYSE - Hausse consommation août 2024
═══════════════════════════════════════════════════

CONSTAT
-------
Consommation Siège Social : +80% vs juillet
50,000 kWh → 90,000 kWh
Dépassement puissance : 145 kVA (100 souscrit)

CAUSE IDENTIFIÉE
────────────────
Canicule exceptionnelle (40°C)
+ Conférence 300 personnes (23-25 août)
→ Climatisation maximale 24h/24

IMPACT FINANCIER
─────────────────
Surcoût : +600,000 FCFA
Pénalité dépassement : +150,000 FCFA
Total : +750,000 FCFA

ACTIONS CORRECTIVES
───────────────────
1. Réviser abonnement : 100 → 120 kVA
2. Optimiser climatisation (programmation)
3. Planifier événements hors canicule

Économie estimée : 400,000 FCFA/an
```

---

## 10. Résolution des problèmes

### ⚠️ Problème 1 : Import échoue

**Symptôme :**
```
❌ Erreur lors du traitement : 'Montant facture TTC'
```

**Cause :** Colonne manquante ou nom incorrect

**Solution :**
1. Ouvrir le fichier Excel d'import
2. Vérifier ligne 1 (en-têtes)
3. Comparer avec noms requis :
   - BT : `Référence Contrat`, `Montant facture TTC`, etc.
   - HT : `refraccord`, `montfact`, etc.
4. Corriger si nécessaire (respecter majuscules)
5. Réessayer l'import

**Si le problème persiste :**
- Copier les données dans un nouveau fichier Excel vierge
- Vérifier l'encodage du fichier (UTF-8)
- Contacter le support

### ⚠️ Problème 2 : Doublons dans la base

**Symptôme :**
```
Site 123456 apparaît 2 fois pour 01/2025
```

**Cause :** Import effectué 2 fois par erreur

**Solution :**

**Option 1 : Suppression manuelle**
1. Menu "📊 Base Centrale"
2. Rechercher "123456"
3. Filtrer DATE = "01/2025"
4. Identifier la ligne en double (comparer montants)
5. Télécharger la base en Excel
6. Supprimer la ligne en double
7. Sauvegarder et remplacer le fichier

**Option 2 : Réimport propre**
1. Télécharger backup de la base (avant import)
2. Remplacer la base actuelle
3. Refaire l'import correctement

### ⚠️ Problème 3 : Montants incohérents

**Symptôme :**
```
Total pièce comptable ≠ Total factures CIE
```

**Diagnostic :**

**Étape 1 : Compter les lignes**
```
Nombre factures CIE : 150
Nombre lignes pièce : 145

→ 5 lignes manquantes
```

**Étape 2 : Identifier les manquantes**
1. Exporter pièce comptable
2. Exporter factures CIE
3. Comparer les IDENTIFIANT (Excel VLOOKUP ou Python)

**Étape 3 : Vérifier**
Causes possibles :
- ✅ **Sites INACTIFS** → Exclus volontairement
- ❌ **Sites non enregistrés** → Aller dans "Non Enregistrées"
- ❌ **Factures E1** → En attente de validation

**Solution :**
1. Si sites INACTIFS : Normal ✅
2. Si non enregistrés : Les ajouter
3. Si E1 : Les importer manuellement

### ⚠️ Problème 4 : Application lente

**Symptôme :** Pages mettent 10-20 secondes à charger

**Causes possibles :**

**Cause 1 : Base trop volumineuse**
```
Nombre de lignes : >50,000
```
**Solution :**
- Archiver les anciennes périodes (>2 ans)
- Ne garder que 24 derniers mois

**Cause 2 : Connexion internet lente**
**Solution :**
- Utiliser câble Ethernet au lieu de Wi-Fi
- Fermer autres applications réseau

**Cause 3 : Navigateur surchargé**
**Solution :**
- Vider le cache du navigateur
- Fermer onglets inutiles
- Utiliser Chrome ou Firefox (recommandé)

**Cause 4 : Serveur surchargé**
**Solution :**
- Contacter l'administrateur système
- Augmenter les ressources serveur

### ⚠️ Problème 5 : Mot de passe oublié

**Pour un utilisateur normal :**
1. Contacter un **administrateur**
2. L'admin réinitialise le mot de passe
3. Se connecter avec le nouveau mot de passe

**Pour l'admin principal :**
1. Accéder au serveur (si possible)
2. Ouvrir `users.xlsx`
3. Modifier directement le hash du mot de passe
4. Ou réinitialiser via script Python

**Prévention :**
- Toujours avoir 2 comptes admin minimum
- Noter les mots de passe dans un gestionnaire sécurisé

### ⚠️ Problème 6 : Graphiques ne s'affichent pas

**Symptôme :** Zone blanche au lieu du graphique

**Causes et solutions :**

**Cause 1 : Pas de données**
```
⚠️ Aucune donnée disponible.
```
**Solution :** Importer des factures d'abord

**Cause 2 : JavaScript désactivé**
**Solution :**
- Paramètres navigateur → Activer JavaScript
- Ou utiliser un autre navigateur

**Cause 3 : Bloqueur de publicités**
**Solution :**
- Désactiver AdBlock sur cette URL
- Ajouter à la liste blanche

**Cause 4 : Navigateur obsolète**
**Solution :**
- Mettre à jour le navigateur
- Versions minimales :
  - Chrome 90+
  - Firefox 88+
  - Edge 90+

---

## 11. Conseils et bonnes pratiques

### 💡 Gestion quotidienne

#### Routine de début de journée
```
☑️ Se connecter à l'application
☑️ Vérifier s'il y a de nouvelles factures
☑️ Consulter les statistiques du jour précédent
☑️ Répondre aux alertes (dépassements, anomalies)
```

#### Routine de fin de mois
```
☑️ Importer toutes les factures du mois
☑️ Traiter les factures non enregistrées
☑️ Générer les pièces comptables
☑️ Vérifier la cohérence
☑️ Envoyer à la comptabilité
☑️ Archiver tous les fichiers
☑️ Consulter le rapport statistique
```

### 🔐 Sécurité

#### Mots de passe
- ✅ Minimum **8 caractères**
- ✅ Mélange majuscules/minuscules/chiffres
- ✅ Changer tous les **3 mois**
- ❌ Ne jamais partager
- ❌ Ne pas noter sur papier non sécurisé

#### Accès
- ✅ Se déconnecter après utilisation
- ✅ Verrouiller l'écran si vous vous absentez
- ✅ Limiter le nombre d'admins (2 maximum)
- ❌ Ne pas laisser la session ouverte

#### Données
- ✅ Backup hebdomadaire de `Base_Centrale.xlsx`
- ✅ Archivage mensuel des pièces
- ✅ Stockage sécurisé (serveur protégé)
- ❌ Ne pas partager par email non sécurisé

### 📊 Organisation des fichiers

**Structure recommandée :**
```
📁 CIE_Factures/
│
├── 📁 Base_Centrale/
│   ├── Base_Centrale.xlsx (actuelle)
│   └── 📁 Backups/
│       ├── Base_Centrale_2025-01-01.xlsx
│       ├── Base_Centrale_2025-02-01.xlsx
│       └── ...
│
├── 📁 2024/
│   ├── 01_Janvier/
│   ├── 02_Fevrier/
│   └── ...
│
├── 📁 2025/
│   ├── 📁 01_Janvier/
│   │   ├── Import_BT_janvier.xlsx
│   │   ├── Import_HT_janvier.xlsx
│   │   ├── Piece_BT_01_2025.xlsx
│   │   ├── Piece_HT_01_2025.xlsx
│   │   └── Rapport_janvier.pdf
│   │
│   ├── 📁 02_Fevrier/
│   └── ...
│
└── 📁 Documents/
    ├── Guide_utilisateur.pdf
    ├── Contacts_CIE.xlsx
    └── Procedures_internes.docx
```

### 📈 Optimisation des performances

#### Pour l'application
- Archiver les données > 2 ans
- Limiter la base à 30,000 lignes max
- Nettoyer les doublons régulièrement

#### Pour l'utilisateur
- Utiliser Chrome ou Firefox
- Connexion stable (Ethernet)
- Fermer onglets inutiles
- Vider le cache mensuellement

### 🎓 Formation des nouveaux utilisateurs

**Programme de formation (2 heures) :**

**Session 1 : Théorie (30 min)**
- Présentation de l'application
- Architecture des données
- Workflow type

**Session 2 : Pratique (1h30)**
1. Connexion (5 min)
2. Consultation Base Centrale (10 min)
3. Import factures BT (15 min)
4. Import factures HT (20 min)
5. Factures non enregistrées (15 min)
6. Génération pièces (10 min)
7. Statistiques (10 min)
8. Questions/Réponses (5 min)

**Exercices pratiques :**
- Import d'un fichier test
- Ajout d'un site fictif
- Génération d'une pièce
- Analyse de graphiques

**Documentation fournie :**
- ✅ Ce guide utilisateur
- ✅ Fichiers exemples
- ✅ Liste contacts support

### 📞 Support et assistance

**En cas de problème :**

**Niveau 1 : Auto-assistance**
1. Consulter ce guide (section 10 - Problèmes)
2. Vérifier la FAQ (si disponible)
3. Redémarrer l'application

**Niveau 2 : Support interne**
1. Contacter l'administrateur de l'application
2. Fournir :
   - Description du problème
   - Captures d'écran
   - Message d'erreur exact
   - Étapes pour reproduire

**Niveau 3 : Support technique**
1. Contacter le développeur/intégrateur
2. Ticket de support avec :
   - Contexte complet
   - Logs si disponibles
   - Urgence (critique/normale/basse)

**Informations à préparer :**
```
Sujet : [URGENT/NORMAL] Description courte

Utilisateur : Jean Dupont (jdupont)
Date/Heure : 05/02/2026 10:30
Action : Import factures BT
Erreur : "Colonnes manquantes : Montant facture TTC"

Fichier : Factures_BT_janvier.xlsx (joint)
Capture d'écran : erreur.png (joint)

Contexte :
- Première fois que j'importe ce type de fichier
- Fichier fourni par la CIE ce matin
- Autres imports fonctionnent normalement

Attente : Déblocage aujourd'hui (pièce comptable à envoyer demain)
```

### 🚀 Évolutions futures

**Fonctionnalités prévues :**
- 📊 Tableaux de bord personnalisables
- 📧 Notifications email automatiques
- 📱 Application mobile
- 🤖 Détection automatique d'anomalies
- 📈 Prévisions de consommation (IA)
- 🔗 Intégration ERP
- 📑 Export multi-formats (PDF, JSON)

**Demander une nouvelle fonctionnalité :**
1. Formulaire de suggestion (si disponible)
2. Ou email à l'administrateur
3. Décrire :
   - Besoin métier
   - Cas d'usage
   - Bénéfice attendu
   - Priorité

---

## 📚 Annexes

### A. Raccourcis clavier

| Action | Raccourci |
|--------|-----------|
| Rechercher dans Base | Ctrl + F |
| Actualiser page | F5 |
| Copier | Ctrl + C |
| Coller | Ctrl + V |
| Annuler | Ctrl + Z |
| Sauvegarder | Ctrl + S |

### B. Codes d'erreur courants

| Code | Signification | Action |
|------|---------------|--------|
| ERR_COL_MISSING | Colonne manquante | Vérifier noms colonnes |
| ERR_DUPLICATE | Doublon détecté | Supprimer doublon |
| ERR_INVALID_DATE | Format date incorrect | Format MM/YYYY |
| ERR_AUTH_FAILED | Échec connexion | Vérifier login/password |
| ERR_PERMISSION | Accès refusé | Contacter admin |

### C. Glossaire

| Terme | Définition |
|-------|------------|
| **Base Centrale** | Base de données principale de l'application |
| **BT** | Basse Tension (< 50 kVA) |
| **HT** | Haute Tension (≥ 50 kVA) |
| **E0** | Facture d'émission normale |
| **E1** | Facture complémentaire |
| **E5** | Avoir (crédit) |
| **PSABON** | Puissance Souscrite (kVA) |
| **PSATTEINTE** | Puissance Atteinte (kVA) |
| **UC** | Unité Comptable |
| **Pièce comptable** | Document Excel pour la comptabilité |

### D. Contacts utiles

| Service | Contact | Email | Téléphone |
|---------|---------|-------|-----------|
| CIE Service Client | - | client@cie.ci | +225 XX XX XX XX |
| Support Application | Admin Système | admin@entreprise.com | Interne : XXXX |
| Comptabilité | Chef Comptable | compta@entreprise.com | Interne : XXXX |

---

## 📝 Historique des versions

| Version | Date | Modifications |
|---------|------|---------------|
| 3.0 | 05/02/2026 | Version initiale avec toutes fonctionnalités |
| | | - Authentification |
| | | - Import BT/HT |
| | | - Gestion E0/E1/E5 |
| | | - Puissances HT |
| | | - Émissions CO2 |
| | | - Compte de charges dynamique |

---

## ✅ Checklist de prise en main

**Pour les nouveaux utilisateurs, cochez au fur et à mesure :**

- [ ] Connexion réussie avec identifiants
- [ ] Changement du mot de passe par défaut (si admin)
- [ ] Consultation de la Base Centrale
- [ ] Compréhension des colonnes
- [ ] Premier import BT réussi
- [ ] Premier import HT réussi
- [ ] Traitement factures non enregistrées
- [ ] Génération première pièce comptable
- [ ] Consultation statistiques
- [ ] Lecture complète du guide

**Vous êtes maintenant opérationnel ! 🎉**

---

**Guide rédigé le 05/02/2026**  
**Version 1.0**  
**Application : Gestion Factures CIE v3.0**

Pour toute question : consultez d'abord ce guide, puis contactez votre administrateur.
