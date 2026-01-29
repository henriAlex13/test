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
    'TENSION', 'DATE', 'CONSO', 'MONTANT', 'DATE_COMPLEMENTAIRE'
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
    2. Fichier Excel (Base_Centrale.xlsx)
    3. Base vide avec les bonnes colonnes
    
    Returns:
        DataFrame avec les colonnes standardisées
    """
    if os.path.exists(SAVE_FILE_CENTRAL):
        with open(SAVE_FILE_CENTRAL, 'rb') as f:
            df = pickle.load(f)
    elif os.path.exists(FICHIER_CENTRAL):
        df = pd.read_excel(FICHIER_CENTRAL)
    else:
        # Créer une base vide
        df = pd.DataFrame(columns=COLONNES_BASE_CENTRALE)
    
    # S'assurer que toutes les colonnes existent
    for col in COLONNES_BASE_CENTRALE:
        if col not in df.columns:
            df[col] = None
    
    # Ne garder que les colonnes de la base centrale
    df = df[COLONNES_BASE_CENTRALE].copy()
    
    # Normaliser les identifiants
    if 'IDENTIFIANT' in df.columns:
        df['IDENTIFIANT'] = df['IDENTIFIANT'].apply(normaliser_identifiant)
    
    return df


def save_central(df):
    """
    Sauvegarde la base centrale en pickle
    
    Args:
        df: DataFrame à sauvegarder
    """
    # Ne garder que les colonnes de la base centrale
    df_save = df[COLONNES_BASE_CENTRALE].copy()
    
    with open(SAVE_FILE_CENTRAL, 'wb') as f:
        pickle.dump(df_save, f)


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
    
    # Ajouter à la base
    df_resultat = pd.concat([df_base, df_nouvelles], ignore_index=True)
    
    # Compter avant suppression doublons
    nb_avant = len(df_resultat)
    
    # Supprimer les doublons (IDENTIFIANT + DATE)
    df_resultat = df_resultat.drop_duplicates(subset=['IDENTIFIANT', 'DATE'], keep='last')
    
    # Statistiques
    nb_apres = len(df_resultat)
    nb_doublons = nb_avant - nb_apres
    nb_ajoutes = len(nouvelles_lignes) - nb_doublons
    
    return df_resultat, nb_ajoutes, nb_doublons


def generer_piece_comptable(df_base, periode):
    """
    Génère la pièce comptable à partir de la base centrale
    
    Colonnes générées (17):
    - CODE AGENCE (depuis CODE AGCE)
    - COMPTE DE CHARGES (62183464)
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
    
    Args:
        df_base: DataFrame base centrale
        periode: Période à générer (format MM/YYYY)
    
    Returns:
        DataFrame pièce comptable
    """
    # Filtrer par période
    df_filtre = df_base[df_base['DATE'] == periode].copy()
    
    if len(df_filtre) == 0:
        return pd.DataFrame()
    
    # Créer la pièce comptable
    piece = pd.DataFrame()
    
    piece['CODE AGENCE'] = df_filtre['CODE AGCE']
    piece['COMPTE DE CHARGES'] = '62183464'
    piece['SENS'] = 'D'
    piece['MONTANT'] = df_filtre['MONTANT']
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
