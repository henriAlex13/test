"""
models.py
=========
Gestion de la base centrale et des données
"""

import pandas as pd
import pickle
import os
from datetime import datetime

# Fichiers
FICHIER_CENTRAL = "Base_Centrale.xlsx"
SAVE_FILE_CENTRAL = "data_centrale.pkl"

# Colonnes de la base centrale
COLONNES_BASE_CENTRALE = [
    'UC', 'CODE RED', 'CODE AGCE', 'SITES', 'IDENTIFIANT', 
    'TENSION', 'DATE', 'CONSO', 'MONTANT', 'DATE_COMPLEMENTAIRE', 'STATUT',
    'PSABON', 'PSATTEINTE',  # Puissances HT
    'COMPTE_CHARGE'  # Compte de charges comptable
]


def normaliser_identifiant(valeur):
    """
    Normalise un identifiant : supprime .0, espaces, met en majuscules
    
    Exemples:
        123.0 → "123"
        "  abc  " → "ABC"
        "123.45" → "123.45"
    """
    if pd.isna(valeur):
        return ''
    
    valeur_str = str(valeur).strip()
    
    try:
        valeur_float = float(valeur_str)
        if valeur_float.is_integer():
            return str(int(valeur_float)).upper()
        else:
            return valeur_str.upper()
    except:
        return valeur_str.upper()


def load_central():
    """
    Charge la base centrale
    
    Priorité:
    1. Fichier pickle (data_centrale.pkl)
    2. Fichier Excel (Base_Centrale.xlsx) avec mapping intelligent
    3. Base vide avec les bonnes colonnes
    
    Returns:
        DataFrame avec les colonnes standardisées
    """
    if os.path.exists(SAVE_FILE_CENTRAL):
        print(f"✅ Chargement depuis {SAVE_FILE_CENTRAL}")
        try:
            with open(SAVE_FILE_CENTRAL, 'rb') as f:
                df = pickle.load(f)
            print(f"✅ Base centrale chargée avec succès")
        except Exception as e:
            print(f"⚠️ ERREUR lors du chargement du pickle : {str(e)}")
            print(f"🔄 Suppression du fichier corrompu et rechargement...")
            
            # Supprimer le fichier pickle corrompu
            try:
                os.remove(SAVE_FILE_CENTRAL)
                print(f"✅ Fichier {SAVE_FILE_CENTRAL} supprimé")
            except Exception as e_rm:
                print(f"⚠️ Impossible de supprimer : {str(e_rm)}")
            
            # Recharger depuis Excel ou créer base vide
            if os.path.exists(FICHIER_CENTRAL):
                print(f"🔄 Tentative de chargement depuis {FICHIER_CENTRAL}")
                try:
                    df_source = pd.read_excel(FICHIER_CENTRAL)
                    print(f"✅ Rechargé depuis Excel avec succès")
                    # Continuer avec le mapping ci-dessous
                except Exception as e_excel:
                    print(f"❌ Erreur Excel aussi : {str(e_excel)}")
                    print("✅ Création d'une base vide")
                    df = pd.DataFrame(columns=COLONNES_BASE_CENTRALE)
                    # S'assurer que STATUT existe
                    for col in COLONNES_BASE_CENTRALE:
                        if col not in df.columns:
                            if col == 'STATUT':
                                df[col] = 'ACTIF'
                            else:
                                df[col] = None
                    # Retourner directement pour éviter le mapping
                    if 'IDENTIFIANT' in df.columns:
                        df['IDENTIFIANT'] = df['IDENTIFIANT'].apply(normaliser_identifiant)
                    return df
            else:
                print("✅ Aucun fichier Excel, création base vide")
                df = pd.DataFrame(columns=COLONNES_BASE_CENTRALE)
                # S'assurer que STATUT existe
                for col in COLONNES_BASE_CENTRALE:
                    if col not in df.columns:
                        if col == 'STATUT':
                            df[col] = 'ACTIF'
                        else:
                            df[col] = None
                if 'IDENTIFIANT' in df.columns:
                    df['IDENTIFIANT'] = df['IDENTIFIANT'].apply(normaliser_identifiant)
                return df
    elif os.path.exists(FICHIER_CENTRAL):
        print(f"✅ Chargement depuis {FICHIER_CENTRAL}")
        df_source = pd.read_excel(FICHIER_CENTRAL)
        print(f"📊 Colonnes du fichier source : {', '.join(df_source.columns.tolist())}")
        print(f"📝 Nombre de lignes : {len(df_source)}")
        
        # Mapping intelligent des colonnes de l'ancien format vers le nouveau
        mapping_colonnes = {
            'UC': 'UC',
            'CODE RED': 'CODE RED',
            'CODE AGCE': 'CODE AGCE',
            'CODE AGENCE': 'CODE AGCE',  # Variante
            'SITES': 'SITES',
            'IDENTIFIANT': 'IDENTIFIANT',
            'REFERENCE': 'IDENTIFIANT',  # Fallback
            'TENSION': 'TENSION',
            'DATE': 'DATE',
            'CONSO': 'CONSO',
            'MONTANT': 'MONTANT',
            'DATE_COMPLEMENTAIRE': 'DATE_COMPLEMENTAIRE',
            'CORRESPONDANCE': 'SITES',  # Fallback pour SITES
            'STATUT': 'STATUT',
            'PSABON': 'PSABON',
            'PSATTEINTE': 'PSATTEINTE',
            'COMPTE_CHARGE': 'COMPTE_CHARGE'
        }
        
        # Créer le nouveau DataFrame
        df = pd.DataFrame()
        
        for col_new in COLONNES_BASE_CENTRALE:
            # Chercher la colonne dans le mapping
            col_trouvee = False
            for col_ancien, col_cible in mapping_colonnes.items():
                if col_cible == col_new and col_ancien in df_source.columns:
                    df[col_new] = df_source[col_ancien]
                    col_trouvee = True
                    print(f"  ✓ {col_new} ← {col_ancien}")
                    break
            
            # Si pas trouvée, créer colonne vide
            if not col_trouvee:
                df[col_new] = None
                print(f"  ✗ {col_new} (colonne vide)")
        
        # Si SITES est vide mais CORRESPONDANCE existe
        if df['SITES'].isna().all() and 'CORRESPONDANCE' in df_source.columns:
            df['SITES'] = df_source['CORRESPONDANCE']
            print(f"  ↻ SITES ← CORRESPONDANCE (fallback)")
        
        # Si DATE_COMPLEMENTAIRE n'existe pas, la créer vide
        if 'DATE_COMPLEMENTAIRE' not in df.columns or df['DATE_COMPLEMENTAIRE'].isna().all():
            df['DATE_COMPLEMENTAIRE'] = ''
            print(f"  + DATE_COMPLEMENTAIRE créée vide")
    else:
        print("⚠️ Aucun fichier trouvé - Création base vide")
        # Créer une base vide
        df = pd.DataFrame(columns=COLONNES_BASE_CENTRALE)
    
    # S'assurer que toutes les colonnes existent
    for col in COLONNES_BASE_CENTRALE:
        if col not in df.columns:
            if col == 'STATUT':
                df[col] = 'ACTIF'  # Par défaut, tous les sites sont actifs
            else:
                df[col] = None
    
    # Ne garder que les colonnes de la base centrale
    df = df[COLONNES_BASE_CENTRALE].copy()
    
    # Normaliser les identifiants
    if 'IDENTIFIANT' in df.columns:
        df['IDENTIFIANT'] = df['IDENTIFIANT'].apply(normaliser_identifiant)
    
    # Forcer COMPTE_CHARGE en type texte pour préserver les zéros initiaux
    if 'COMPTE_CHARGE' in df.columns:
        df['COMPTE_CHARGE'] = df['COMPTE_CHARGE'].astype(str)
        # Remplacer 'nan' par la valeur par défaut
        df['COMPTE_CHARGE'] = df['COMPTE_CHARGE'].replace('nan', '62183464')
        df['COMPTE_CHARGE'] = df['COMPTE_CHARGE'].replace('', '62183464')
    
    print(f"✅ Base centrale chargée : {len(df)} ligne(s)")
    return df


def save_central(df):
    """
    Sauvegarde la base centrale en pickle ET en Excel (backup)
    
    Args:
        df: DataFrame à sauvegarder
    """
    # Ne garder que les colonnes de la base centrale
    df_save = df[COLONNES_BASE_CENTRALE].copy()
    
    # Forcer COMPTE_CHARGE en type texte avant sauvegarde
    if 'COMPTE_CHARGE' in df_save.columns:
        df_save['COMPTE_CHARGE'] = df_save['COMPTE_CHARGE'].astype(str)
        df_save['COMPTE_CHARGE'] = df_save['COMPTE_CHARGE'].replace('nan', '62183464')
    
    try:
        # Essayer de sauvegarder en pickle
        with open(SAVE_FILE_CENTRAL, 'wb') as f:
            pickle.dump(df_save, f)
        print(f"✅ Base sauvegardée dans {SAVE_FILE_CENTRAL}")
    except Exception as e:
        print(f"⚠️ ERREUR lors de la sauvegarde : {str(e)}")
        
        # Tenter de supprimer le fichier corrompu
        if os.path.exists(SAVE_FILE_CENTRAL):
            try:
                os.remove(SAVE_FILE_CENTRAL)
                print(f"🗑️ Ancien fichier supprimé")
            except:
                pass
        
        # Réessayer une fois
        try:
            with open(SAVE_FILE_CENTRAL, 'wb') as f:
                pickle.dump(df_save, f)
            print(f"✅ Sauvegarde réussie au 2ème essai")
        except Exception as e2:
            print(f"❌ Échec définitif de la sauvegarde : {str(e2)}")
            print(f"💡 Les données restent en mémoire mais ne sont pas persistées")
            # Lever l'exception pour informer l'utilisateur
            raise Exception(f"Impossible de sauvegarder : {str(e2)}")
    
    # BACKUP EXCEL AUTOMATIQUE (protection contre perte de données)
    try:
        df_save.fillna('').to_excel(FICHIER_CENTRAL, index=False, engine='openpyxl')
        print(f"✅ Backup Excel créé : {FICHIER_CENTRAL}")
    except Exception as e_excel:
        # Si erreur Excel, ce n'est pas bloquant (pickle suffit)
        print(f"⚠️ Backup Excel échoué (non bloquant) : {str(e_excel)}")


def ajouter_lignes_base_centrale(df_base, nouvelles_lignes, periode):
    """
    Ajoute des nouvelles lignes à la base centrale
    
    Args:
        df_base: DataFrame base centrale existante
        nouvelles_lignes: List de dict ou DataFrame avec les nouvelles lignes
        periode: Période (DATE) pour ces lignes
    
    Returns:
        DataFrame mis à jour
        Nombre de lignes ajoutées
        Nombre de doublons supprimés
    """
    # Convertir en DataFrame si nécessaire
    if isinstance(nouvelles_lignes, list):
        df_nouvelles = pd.DataFrame(nouvelles_lignes)
    else:
        df_nouvelles = nouvelles_lignes.copy()
    
    # S'assurer que la DATE est remplie
    if 'DATE' in df_nouvelles.columns:
        df_nouvelles['DATE'] = df_nouvelles['DATE'].fillna(periode)
    
    # ========================================
    # S'assurer que toutes les colonnes existent
    # ========================================
    for col in COLONNES_BASE_CENTRALE:
        if col not in df_nouvelles.columns:
            if col == 'STATUT':
                df_nouvelles[col] = 'ACTIF'  # Par défaut ACTIF
            elif col in ['PSABON', 'PSATTEINTE']:
                df_nouvelles[col] = 0  # Par défaut 0 pour puissances
            elif col == 'COMPTE_CHARGE':
                df_nouvelles[col] = '62183464'  # Compte par défaut
            else:
                df_nouvelles[col] = ''  # Vide pour les autres
    
    # Remplir STATUT si vide
    if 'STATUT' in df_nouvelles.columns:
        df_nouvelles['STATUT'] = df_nouvelles['STATUT'].fillna('ACTIF')
        df_nouvelles['STATUT'] = df_nouvelles['STATUT'].replace('', 'ACTIF')
    
    # Remplir COMPTE_CHARGE si vide
    if 'COMPTE_CHARGE' in df_nouvelles.columns:
        df_nouvelles['COMPTE_CHARGE'] = df_nouvelles['COMPTE_CHARGE'].fillna('62183464')
        df_nouvelles['COMPTE_CHARGE'] = df_nouvelles['COMPTE_CHARGE'].replace('', '62183464')
        # Forcer en type texte pour préserver les zéros initiaux
        df_nouvelles['COMPTE_CHARGE'] = df_nouvelles['COMPTE_CHARGE'].astype(str)
    
    # Ajouter à la base
    df_resultat = pd.concat([df_base, df_nouvelles], ignore_index=True)
    
    # Compter avant suppression doublons
    nb_avant = len(df_resultat)
    
    # ========================================
    # CORRECTION : Supprimer doublons VRAIS uniquement
    # Permettre E0 ET E5 pour même IDENTIFIANT + DATE
    # Permettre E0 ET E1 pour même IDENTIFIANT + DATE
    # ========================================
    
    # Convertir MONTANT en numérique pour le test
    df_resultat['MONTANT'] = pd.to_numeric(df_resultat['MONTANT'], errors='coerce').fillna(0)
    
    # Créer une clé unique qui différencie E0, E1 et E5
    # E5 = montant négatif
    # E0 = montant positif + DATE_COMPLEMENTAIRE vide
    # E1 = montant positif + DATE_COMPLEMENTAIRE remplie
    def creer_cle_unique(row):
        if row['MONTANT'] < 0:
            return 'E5'  # Avoir
        elif pd.notna(row.get('DATE_COMPLEMENTAIRE')) and row.get('DATE_COMPLEMENTAIRE') != '':
            return f"E1_{row['DATE_COMPLEMENTAIRE']}"  # E1 avec sa période
        else:
            return 'E0'  # E0 normale
    
    df_resultat['_CLE_TYPE'] = df_resultat.apply(creer_cle_unique, axis=1)
    
    # Supprimer doublons avec (IDENTIFIANT + DATE + CLE_TYPE)
    # Ceci permet E0 + E1 + E5 pour même ID/DATE
    df_resultat = df_resultat.drop_duplicates(
        subset=['IDENTIFIANT', 'DATE', '_CLE_TYPE'], 
        keep='last'
    )
    
    # Supprimer la colonne temporaire
    df_resultat = df_resultat.drop(columns=['_CLE_TYPE'])
    
    # Statistiques
    nb_apres = len(df_resultat)
    nb_doublons = nb_avant - nb_apres
    nb_ajoutes = len(nouvelles_lignes) - nb_doublons
    
    return df_resultat, nb_ajoutes, nb_doublons


def generer_piece_comptable(df_base, periode, tension=None):
    """
    Génère la pièce comptable à partir de la base centrale
    
    IMPORTANT: Exclut automatiquement les sites avec STATUT = 'INACTIF'
    
    Args:
        df_base: DataFrame base centrale
        periode: Période à générer (format MM/YYYY)
        tension: 'BASSE' pour BT, 'HAUTE' pour HT, None pour tout
    
    Colonnes générées (17):
    - CODE AGENCE (depuis CODE AGCE)
    - COMPTE DE CHARGES (depuis COMPTE_CHARGE ou 62183464)
    - SENS (D)
    - MONTANT (depuis base)
    - CODE PAYT Lib 1-5 (4200)
    - CODE CHARGE Lib 6-10 (vide)
    - TYPE DEP Lib 11 (vide)
    - MATR OBJ Lib 12-19 (vide)
    - LIBELLE COMPLEMENTAIRE (généré)
    - CODE AG (vide)
    - SENS_ (vide)
    - MONTANT_ (vide)
    - CODE FOURNISSEUR (vide)
    - FOURNISSEUR (vide)
    - CONTREPARTIE (vide)
    - LIB COMPLEMENTAIRE (vide)
    - IDENTIFIANT (depuis base)
    
    Returns:
        DataFrame pièce comptable
    """
    # Filtrer par période
    # Toutes les factures du mois (E0, E1, E5) ont DATE = période du fichier
    # DATE_COMPLEMENTAIRE sert uniquement pour le libellé (traçabilité)
    df_filtre = df_base[df_base['DATE'] == periode].copy()
    
    # Filtrer par TENSION si spécifié
    if tension is not None:
        df_filtre = df_filtre[df_filtre['TENSION'] == tension]
    
    # IMPORTANT: Exclure les sites inactifs
    if 'STATUT' in df_filtre.columns:
        nb_total = len(df_filtre)
        df_filtre = df_filtre[df_filtre['STATUT'] != 'INACTIF']
        nb_exclus = nb_total - len(df_filtre)
        if nb_exclus > 0:
            # Cette info sera affichée dans l'interface
            df_filtre.attrs['nb_sites_inactifs_exclus'] = nb_exclus
    
    if len(df_filtre) == 0:
        return pd.DataFrame()
    
    # ✨ IMPORTANT : Réinitialiser l'index pour éviter les problèmes de lignes dupliquées
    df_filtre = df_filtre.reset_index(drop=True)
    
    # Créer la pièce comptable
    piece = pd.DataFrame()
    
    piece['CODE AGENCE'] = df_filtre['CODE AGCE']
    
    # ✨ NOUVEAU : Récupérer COMPTE_CHARGE depuis la base centrale
    # Si la colonne n'existe pas ou est vide, utiliser la valeur par défaut
    if 'COMPTE_CHARGE' in df_filtre.columns:
        piece['COMPTE DE CHARGES'] = df_filtre['COMPTE_CHARGE'].fillna('62183464').astype(str)
    else:
        piece['COMPTE DE CHARGES'] = '62183464'
    
    piece['SENS'] = 'D'
    
    # S'assurer que MONTANT est numérique
    piece['MONTANT'] = pd.to_numeric(df_filtre['MONTANT'], errors='coerce').fillna(0)
    
    piece['CODE PAYT Lib 1-5'] = '4200'
    piece['CODE CHARGE Lib 6-10'] = ''
    piece['TYPE DEP Lib 11'] = ''
    piece['MATR OBJ Lib 12-19'] = ''
    
    # Générer le LIBELLE COMPLEMENTAIRE
    libelles = []
    for _, row in df_filtre.iterrows():
        tension_prefix = "CIE BT" if row['TENSION'] == 'BASSE' else "CIE HT"
        site = row['SITES'] if pd.notna(row['SITES']) else ''
        date_str = row['DATE'] if pd.notna(row['DATE']) else ''
        
        # Vérifier si facture complémentaire
        if pd.notna(row['DATE_COMPLEMENTAIRE']) and row['DATE_COMPLEMENTAIRE'] != '':
            libelle = f"{tension_prefix} {date_str} {site} COMPLEMENTAIRE {row['DATE_COMPLEMENTAIRE']}"
        else:
            libelle = f"{tension_prefix} {date_str} {site}"
        
        libelles.append(libelle)
    
    piece['LIBELLE COMPLEMENTAIRE'] = libelles
    piece['CODE AG'] = ''
    piece['SENS_'] = ''
    piece['MONTANT_'] = ''
    piece['CODE FOURNISSEUR'] = ''
    piece['FOURNISSEUR'] = ''
    piece['CONTREPARTIE'] = ''
    piece['LIB COMPLEMENTAIRE'] = ''
    piece['IDENTIFIANT'] = df_filtre['IDENTIFIANT']
    
    return piece


def identifier_lignes_non_enregistrees(df_factures, df_base_centrale, cle_facture):
    """
    Identifie les lignes des factures qui ne sont pas dans la base centrale
    
    Args:
        df_factures: DataFrame des factures importées
        df_base_centrale: DataFrame base centrale
        cle_facture: Nom de la colonne clé dans les factures
    
    Returns:
        DataFrame avec les lignes non enregistrées
    """
    # Normaliser les identifiants des factures
    df_factures = df_factures.copy()
    df_factures['IDENTIFIANT_NORM'] = df_factures[cle_facture].apply(normaliser_identifiant)
    
    # Identifiants dans la base centrale
    identifiants_base = set(df_base_centrale['IDENTIFIANT'].unique())
    
    # Filtrer les lignes non enregistrées
    df_non_enregistrees = df_factures[~df_factures['IDENTIFIANT_NORM'].isin(identifiants_base)].copy()
    
    return df_non_enregistrees


def normaliser_periode(valeur):
    """
    Normalise une période au format MM/YYYY
    
    Exemples:
        202501 → "01/2025"
        "202501" → "01/2025"
        "202501.0" → "01/2025"
    
    Args:
        valeur: Valeur à normaliser
    
    Returns:
        String au format MM/YYYY
    """
    if pd.isna(valeur):
        return ''
    
    # Convertir en string et nettoyer
    valeur_str = str(valeur).strip().replace('.0', '').replace('.', '')
    
    # S'assurer que c'est 6 chiffres
    valeur_str = valeur_str.zfill(6)
    
    # Extraire mois et année
    if len(valeur_str) >= 6:
        annee = valeur_str[:4]
        mois = valeur_str[4:6]
        return f"{mois}/{annee}"
    
    return valeur_str
