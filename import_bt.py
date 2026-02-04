"""
import_bt.py
============
Gestion de l'import des factures Basse Tension (BT)
"""

import pandas as pd
import streamlit as st
from models import normaliser_identifiant, normaliser_periode, ajouter_lignes_base_centrale, save_central


# Configuration des colonnes BT
CONFIG_BT = {
    'cle_facture': 'Référence Contrat',
    'montant_col': 'Montant facture TTC',
    'conso_col': 'KWH Facturé',
    'periode_col': 'Période Facture sur date fact'
}


def traiter_fichier_bt(fichier_bt):
    """
    Traite un fichier de factures BT
    
    Args:
        fichier_bt: Fichier uploadé (BytesIO)
    
    Returns:
        df_bt: DataFrame des factures BT normalisées
        periode: Période détectée
        erreurs: Liste des erreurs rencontrées
    """
    erreurs = []
    
    try:
        # Charger le fichier
        df_bt = pd.read_excel(fichier_bt)
        
        # Vérifier les colonnes requises
        colonnes_manquantes = []
        for col in [CONFIG_BT['cle_facture'], CONFIG_BT['montant_col'], CONFIG_BT['periode_col']]:
            if col not in df_bt.columns:
                colonnes_manquantes.append(col)
        
        if colonnes_manquantes:
            erreurs.append(f"Colonnes manquantes : {', '.join(colonnes_manquantes)}")
            return None, None, erreurs
        
        # Normaliser la période
        df_bt[CONFIG_BT['periode_col']] = df_bt[CONFIG_BT['periode_col']].apply(normaliser_periode)
        
        # Normaliser les identifiants
        df_bt[CONFIG_BT['cle_facture']] = df_bt[CONFIG_BT['cle_facture']].apply(normaliser_identifiant)
        
        # Récupérer la période (première valeur non vide)
        periodes = df_bt[CONFIG_BT['periode_col']].dropna().unique()
        if len(periodes) > 0:
            periode = str(periodes[0])
        else:
            periode = ""
            erreurs.append("Aucune période détectée dans le fichier")
        
        return df_bt, periode, erreurs
    
    except Exception as e:
        erreurs.append(f"Erreur lors du traitement : {str(e)}")
        return None, None, erreurs


def importer_factures_bt(df_bt, df_base_centrale, periode):
    """
    Importe les factures BT dans la base centrale
    
    Pour BT : Cumul automatique si plusieurs factures même IDENTIFIANT
    → DATE_COMPLEMENTAIRE reste vide
    
    IMPORTANT: Préserve les modifications manuelles de la base centrale
    
    Args:
        df_bt: DataFrame des factures BT
        df_base_centrale: DataFrame base centrale existante
        periode: Période des factures
    
    Returns:
        df_updated: Base centrale mise à jour
        nb_ajoutes: Nombre de lignes ajoutées
        nb_doublons: Nombre de doublons supprimés
        non_trouves: Liste des identifiants non trouvés
    """
    # ============================================
    # ÉTAPE 1 : CUMUL si plusieurs factures même IDENTIFIANT
    # ============================================
    
    # Grouper par IDENTIFIANT et cumuler
    df_bt_cumul = df_bt.groupby(CONFIG_BT['cle_facture'], as_index=False).agg({
        CONFIG_BT['montant_col']: 'sum',
        CONFIG_BT['conso_col']: 'sum',
        CONFIG_BT['periode_col']: 'first'
    })
    
    # Statistiques cumul
    nb_factures_initiales = len(df_bt)
    nb_factures_apres_cumul = len(df_bt_cumul)
    nb_cumul = nb_factures_initiales - nb_factures_apres_cumul
    
    # ============================================
    # ÉTAPE 2 : IMPORT dans base centrale
    # ============================================
    
    nouvelles_lignes = []
    non_trouves = []
    
    for _, row_facture in df_bt_cumul.iterrows():
        identifiant = normaliser_identifiant(row_facture[CONFIG_BT['cle_facture']])
        
        # Chercher dans la base centrale (même IDENTIFIANT + même DATE)
        ligne_existante = df_base_centrale[
            (df_base_centrale['IDENTIFIANT'] == identifiant) & 
            (df_base_centrale['DATE'] == periode)
        ]
        
        if not ligne_existante.empty:
            # ✅ Ligne existe déjà pour cette période
            # → METTRE À JOUR au lieu de créer une nouvelle
            # → Préserve UC, CODE RED, CODE AGCE, SITES (modifs manuelles)
            # → Met à jour CONSO et MONTANT uniquement
            
            idx = ligne_existante.index[0]
            conso_val = row_facture.get(CONFIG_BT['conso_col'], 0) if CONFIG_BT['conso_col'] in df_bt_cumul.columns else 0
            montant_val = row_facture.get(CONFIG_BT['montant_col'], 0)
            
            # Convertir en numérique
            df_base_centrale.loc[idx, 'CONSO'] = pd.to_numeric(conso_val, errors='coerce') or 0
            df_base_centrale.loc[idx, 'MONTANT'] = pd.to_numeric(montant_val, errors='coerce') or 0
            # Garder les autres colonnes (UC, CODE, etc.) telles quelles
            
        else:
            # Ligne n'existe pas pour cette période
            # Chercher infos du site (n'importe quelle période)
            ligne_base = df_base_centrale[df_base_centrale['IDENTIFIANT'] == identifiant]
            
            if not ligne_base.empty:
                # Prendre les infos du site depuis la première occurrence
                site_info = ligne_base.iloc[0]
                
                # Créer une nouvelle ligne pour cette période
                conso_val = row_facture.get(CONFIG_BT['conso_col'], 0) if CONFIG_BT['conso_col'] in df_bt_cumul.columns else 0
                montant_val = row_facture.get(CONFIG_BT['montant_col'], 0)
                
                nouvelle_ligne = {
                    'UC': site_info.get('UC', ''),
                    'CODE RED': site_info.get('CODE RED', ''),
                    'CODE AGCE': site_info.get('CODE AGCE', ''),
                    'SITES': site_info.get('SITES', ''),
                    'IDENTIFIANT': identifiant,
                    'TENSION': 'BASSE',
                    'DATE': periode,
                    'CONSO': pd.to_numeric(conso_val, errors='coerce') or 0,
                    'MONTANT': pd.to_numeric(montant_val, errors='coerce') or 0,
                    'DATE_COMPLEMENTAIRE': '',
                    'STATUT': site_info.get('STATUT', 'ACTIF'),  # Préserver le statut existant
                    'PSABON': 0,  # BT n'a pas de puissance
                    'PSATTEINTE': 0
                }
                
                nouvelles_lignes.append(nouvelle_ligne)
            else:
                non_trouves.append(identifiant)
    
    # Ajouter à la base centrale uniquement les nouvelles lignes
    if nouvelles_lignes:
        df_updated, nb_ajoutes, nb_doublons = ajouter_lignes_base_centrale(
            df_base_centrale, 
            nouvelles_lignes, 
            periode
        )
    else:
        df_updated = df_base_centrale
        nb_ajoutes = 0
        nb_doublons = 0
    
    return df_updated, nb_ajoutes, nb_doublons, non_trouves, nb_cumul


def page_import_bt():
    """
    Page Streamlit pour l'import des factures BT
    """
    st.markdown("## 🔄 Import Factures - Basse Tension (BT)")
    st.markdown("---")
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea, #764ba2); 
                color: white; 
                padding: 1.5rem; 
                border-radius: 10px;
                margin: 1rem 0;'>
        <h3 style='margin: 0;'>🔌 BASSE TENSION</h3>
        <p style='margin: 0.5rem 0 0 0;'>Import factures BT - Pas de factures complémentaires</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("""
    📌 **Configuration BT** :
    - Clé : **Référence Contrat**
    - Colonnes : **Montant facture TTC**, **KWH Facturé**, **Période Facture sur date fact**
    
    💡 Pour BT, toutes les factures sont normales (pas de complémentaires).
    """)
    
    # Upload fichier
    fichier_bt = st.file_uploader(
        "Sélectionnez le fichier de factures BT",
        type=['xlsx', 'xls'],
        key="upload_bt"
    )
    
    if fichier_bt:
        # Traiter le fichier
        df_bt, periode, erreurs = traiter_fichier_bt(fichier_bt)
        
        if erreurs:
            for erreur in erreurs:
                st.error(f"❌ {erreur}")
            
            if df_bt is not None and len(df_bt) > 0:
                st.info(f"📋 Colonnes disponibles : {', '.join(df_bt.columns)}")
        
        if df_bt is not None and len(df_bt) > 0:
            st.success(f"✅ Fichier chargé : {len(df_bt)} ligne(s)")
            
            if periode:
                st.success(f"✅ Période détectée : **{periode}**")
                
                # Aperçu
                with st.expander("👁️ Aperçu des factures BT"):
                    cols_to_show = [CONFIG_BT['cle_facture'], CONFIG_BT['montant_col'], CONFIG_BT['periode_col']]
                    if CONFIG_BT['conso_col'] in df_bt.columns:
                        cols_to_show.insert(2, CONFIG_BT['conso_col'])
                    st.dataframe(df_bt[cols_to_show].head(20), use_container_width=True)
                
                st.markdown("---")
                
                # Bouton import
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🔄 LANCER L'IMPORT BT", type="primary", use_container_width=True):
                        with st.spinner("⏳ Import BT en cours..."):
                            df_base = st.session_state.df_central
                            
                            # Import
                            df_updated, nb_ajoutes, nb_doublons, non_trouves, nb_cumul = importer_factures_bt(
                                df_bt, df_base, periode
                            )
                            
                            # Sauvegarder
                            st.session_state.df_central = df_updated
                            save_central(df_updated)
                            
                            # Stocker les données BT pour la vue "Non Enregistrées"
                            st.session_state.df_factures_bt_dernier = df_bt.copy()
                            st.session_state.periode_bt_dernier = periode
                            
                            # Résultats
                            st.markdown("---")
                            st.success(f"🎉 Import BT terminé : {nb_ajoutes} ligne(s) ajoutée(s) !")
                            
                            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                            with col_r1:
                                st.metric("✅ Lignes ajoutées", nb_ajoutes)
                            with col_r2:
                                st.metric("📊 Total base centrale", len(df_updated))
                            with col_r3:
                                st.metric("📅 Période", periode)
                            with col_r4:
                                st.metric("🔄 Factures cumulées", nb_cumul)
                            
                            # Info cumul
                            if nb_cumul > 0:
                                st.info(f"""
                                📋 **{nb_cumul} facture(s) avec même IDENTIFIANT ont été cumulées automatiquement**
                                
                                {len(df_bt)} factures → {len(df_bt) - nb_cumul} lignes (après cumul)
                                """)
                            
                            if nb_doublons > 0:
                                st.info(f"ℹ️ {nb_doublons} doublon(s) détecté(s) et ignoré(s)")
                            
                            if non_trouves:
                                st.warning(f"⚠️ {len(non_trouves)} identifiant(s) non trouvé(s) dans la base centrale")
                                with st.expander("👁️ Voir les identifiants non trouvés"):
                                    st.write(non_trouves[:50])
                            
                            st.balloons()
