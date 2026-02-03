"""
import_ht.py
============
Gestion de l'import des factures Haute Tension (HT)
Traitement spécial : E0 (cumul), E1 (complémentaire), E5 (avoir)
"""

import pandas as pd
import streamlit as st
from models import normaliser_identifiant, normaliser_periode, ajouter_lignes_base_centrale, save_central


# Configuration des colonnes HT
CONFIG_HT = {
    'cle_facture': 'refraccord',
    'montant_col': 'montfact',
    'conso_col': 'conso',
    'periode_col': 'Periode_Emission_Bordereau',
    'typefact_col': 'typefact'
}


def traiter_fichier_ht(fichier_ht):
    """
    Traite un fichier de factures HT
    
    Args:
        fichier_ht: Fichier uploadé (BytesIO)
    
    Returns:
        df_ht: DataFrame des factures HT normalisées
        periode: Période détectée
        has_typefact: True si colonne typefact existe
        erreurs: Liste des erreurs rencontrées
    """
    erreurs = []
    
    try:
        # Charger le fichier
        df_ht = pd.read_excel(fichier_ht)
        
        # Vérifier les colonnes requises
        colonnes_manquantes = []
        for col in [CONFIG_HT['cle_facture'], CONFIG_HT['montant_col'], CONFIG_HT['periode_col']]:
            if col not in df_ht.columns:
                colonnes_manquantes.append(col)
        
        if colonnes_manquantes:
            erreurs.append(f"Colonnes manquantes : {', '.join(colonnes_manquantes)}")
            return None, None, False, erreurs
        
        # Vérifier si typefact existe
        has_typefact = CONFIG_HT['typefact_col'] in df_ht.columns
        
        # Normaliser la période
        df_ht[CONFIG_HT['periode_col']] = df_ht[CONFIG_HT['periode_col']].apply(normaliser_periode)
        
        # Normaliser les identifiants
        df_ht[CONFIG_HT['cle_facture']] = df_ht[CONFIG_HT['cle_facture']].apply(normaliser_identifiant)
        
        # Récupérer la période
        periodes = df_ht[CONFIG_HT['periode_col']].dropna().unique()
        if len(periodes) > 0:
            periode = str(periodes[0])
        else:
            periode = ""
            erreurs.append("Aucune période détectée dans le fichier")
        
        return df_ht, periode, has_typefact, erreurs
    
    except Exception as e:
        erreurs.append(f"Erreur lors du traitement : {str(e)}")
        return None, None, False, erreurs


def traiter_factures_e0(df_ht_e0, cle_facture, montant_col, conso_col, periode_col):
    """
    Traite les factures E0 (émission normale - factures multiples)
    → Cumule les montants par IDENTIFIANT
    
    Args:
        df_ht_e0: DataFrame des factures E0
        cle_facture: Nom colonne identifiant
        montant_col: Nom colonne montant
        conso_col: Nom colonne conso
        periode_col: Nom colonne période
    
    Returns:
        DataFrame cumulé
    """
    if len(df_ht_e0) == 0:
        return pd.DataFrame()
    
    # Grouper et cumuler
    df_cumul = df_ht_e0.groupby(cle_facture, as_index=False).agg({
        montant_col: 'sum',
        conso_col: 'sum',
        periode_col: 'first'
    })
    
    return df_cumul


def importer_factures_ht(df_ht, df_base_centrale, periode, has_typefact):
    """
    Importe les factures HT dans la base centrale
    
    Traitement selon typefact :
    - E0 : Émission normale → Cumul des montants par IDENTIFIANT
    - E1 : Complémentaire → Remplir DATE_COMPLEMENTAIRE
    - E5 : Avoir → Montant négatif
    - Autre : Traitement normal
    
    Args:
        df_ht: DataFrame des factures HT
        df_base_centrale: DataFrame base centrale existante
        periode: Période des factures
        has_typefact: True si colonne typefact existe
    
    Returns:
        df_updated: Base centrale mise à jour
        nb_ajoutes: Nombre de lignes ajoutées
        nb_doublons: Nombre de doublons supprimés
        non_trouves: Liste des identifiants non trouvés
        stats_typefact: Statistiques par type de facture
    """
    stats_typefact = {
        'E0': {'count': 0, 'cumul': 0},
        'E1': {'count': 0},
        'E5': {'count': 0},
        'Autre': {'count': 0}
    }
    
    if has_typefact:
        # Séparer par type de facture
        df_e0 = df_ht[df_ht[CONFIG_HT['typefact_col']] == 'E0'].copy()
        df_e1 = df_ht[df_ht[CONFIG_HT['typefact_col']] == 'E1'].copy()
        df_e5 = df_ht[df_ht[CONFIG_HT['typefact_col']] == 'E5'].copy()
        df_autres = df_ht[~df_ht[CONFIG_HT['typefact_col']].isin(['E0', 'E1', 'E5'])].copy()
        
        # Traiter E0 (cumul)
        if len(df_e0) > 0:
            stats_typefact['E0']['count'] = len(df_e0)
            df_e0_cumul = traiter_factures_e0(
                df_e0, 
                CONFIG_HT['cle_facture'], 
                CONFIG_HT['montant_col'],
                CONFIG_HT['conso_col'],
                CONFIG_HT['periode_col']
            )
            stats_typefact['E0']['cumul'] = len(df_e0_cumul)
        else:
            df_e0_cumul = pd.DataFrame()
        
        # Statistiques
        stats_typefact['E1']['count'] = len(df_e1)
        stats_typefact['E5']['count'] = len(df_e5)
        stats_typefact['Autre']['count'] = len(df_autres)
        
        # ✨ MODIFICATION : Exclure E1 de l'import automatique
        # E1 (complémentaires) doivent être importées MANUELLEMENT
        # pour avoir le contrôle sur DATE_COMPLEMENTAIRE
        df_traite = pd.concat([df_e0_cumul, df_e5, df_autres], ignore_index=True)
        
        # Stocker E1 pour affichage dans "Non Enregistrées"
        st.session_state.df_e1_a_traiter = df_e1.copy() if len(df_e1) > 0 else pd.DataFrame()
    else:
        # Pas de colonne typefact
        df_traite = df_ht.copy()
        df_e1 = pd.DataFrame()
        df_e5 = pd.DataFrame()
    
    # Créer les nouvelles lignes ou mettre à jour existantes
    nouvelles_lignes = []
    non_trouves = []
    
    for _, row_facture in df_traite.iterrows():
        identifiant = normaliser_identifiant(row_facture[CONFIG_HT['cle_facture']])
        
        # Déterminer le type de facture depuis la ligne traitée
        type_facture_original = ''
        if 'typefact' in row_facture.index:
            type_facture_original = str(row_facture['typefact']).upper()
        
        # Déterminer si c'est une facture complémentaire (E1)
        is_e1 = False
        if has_typefact and not df_e1.empty:
            is_e1 = identifiant in df_e1[CONFIG_HT['cle_facture']].apply(normaliser_identifiant).values
        
        # Déterminer si c'est un avoir (E5)
        is_e5 = (type_facture_original == 'E5')
        
        # Récupérer le montant
        montant = row_facture.get(CONFIG_HT['montant_col'], 0)
        
        # Convertir en numérique
        montant = pd.to_numeric(montant, errors='coerce') or 0
        
        # Si avoir (E5), montant négatif
        if is_e5:
            montant = -abs(montant)
        
        # ========================================
        # CORRECTION : Chercher ligne existante avec TYPE
        # Pour permettre E0 ET E5 pour même IDENTIFIANT
        # ========================================
        
        # Si E5, chercher ligne E5 existante (pas E0)
        # Si E0, chercher ligne E0 existante (pas E5)
        if is_e5:
            # Pour E5 : chercher ligne avec montant négatif (E5 existant)
            ligne_existante = df_base_centrale[
                (df_base_centrale['IDENTIFIANT'] == identifiant) & 
                (df_base_centrale['DATE'] == periode) &
                (df_base_centrale['MONTANT'] < 0)  # E5 = montant négatif
            ]
        else:
            # Pour E0 : chercher ligne avec montant positif (E0 existant)
            ligne_existante = df_base_centrale[
                (df_base_centrale['IDENTIFIANT'] == identifiant) & 
                (df_base_centrale['DATE'] == periode) &
                (df_base_centrale['MONTANT'] >= 0)  # E0/E1 = montant positif
            ]
        
        if not ligne_existante.empty:
            # ✅ Ligne existe déjà pour cette période ET ce type
            # → METTRE À JOUR
            
            idx = ligne_existante.index[0]
            conso_val = row_facture.get(CONFIG_HT['conso_col'], 0) if CONFIG_HT['conso_col'] in df_traite.columns else 0
            
            df_base_centrale.loc[idx, 'CONSO'] = pd.to_numeric(conso_val, errors='coerce') or 0
            df_base_centrale.loc[idx, 'MONTANT'] = montant
            df_base_centrale.loc[idx, 'DATE_COMPLEMENTAIRE'] = periode if is_e1 else ''
            # Garder les autres colonnes telles quelles
            
        else:
            # Ligne n'existe pas pour cette période
            # Chercher infos du site (n'importe quelle période)
            ligne_base = df_base_centrale[df_base_centrale['IDENTIFIANT'] == identifiant]
            
            if not ligne_base.empty:
                site_info = ligne_base.iloc[0]
                
                # Créer nouvelle ligne pour cette période
                conso_val = row_facture.get(CONFIG_HT['conso_col'], 0) if CONFIG_HT['conso_col'] in df_traite.columns else 0
                
                nouvelle_ligne = {
                    'UC': site_info.get('UC', ''),
                    'CODE RED': site_info.get('CODE RED', ''),
                    'CODE AGCE': site_info.get('CODE AGCE', ''),
                    'SITES': site_info.get('SITES', ''),
                    'IDENTIFIANT': identifiant,
                    'TENSION': 'HAUTE',
                    'DATE': periode,
                    'CONSO': pd.to_numeric(conso_val, errors='coerce') or 0,
                    'MONTANT': montant,
                    'DATE_COMPLEMENTAIRE': periode if is_e1 else '',
                    'STATUT': site_info.get('STATUT', 'ACTIF')  # Préserver le statut existant
                }
                
                nouvelles_lignes.append(nouvelle_ligne)
            else:
                non_trouves.append(identifiant)
    
    # Ajouter à la base centrale
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
    
    return df_updated, nb_ajoutes, nb_doublons, non_trouves, stats_typefact


def page_import_ht():
    """
    Page Streamlit pour l'import des factures HT
    """
    st.markdown("## 🔄 Import Factures - Haute Tension (HT)")
    st.markdown("---")
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #f093fb, #f5576c); 
                color: white; 
                padding: 1.5rem; 
                border-radius: 10px;
                margin: 1rem 0;'>
        <h3 style='margin: 0;'>⚡ HAUTE TENSION</h3>
        <p style='margin: 0.5rem 0 0 0;'>Import factures HT - Gestion E0/E1/E5</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("""
    📌 **Configuration HT** :
    - Clé : **refraccord**
    - Colonnes : **montfact**, **conso**, **Periode_Emission_Bordereau**, **typefact**
    
    💡 **Types de factures** :
    - **E0** : Émission normale → Cumul si plusieurs factures
    - **E1** : Complémentaire → Remplir DATE_COMPLEMENTAIRE
    - **E5** : Avoir → Montant négatif
    """)
    
    # Upload fichier
    fichier_ht = st.file_uploader(
        "Sélectionnez le fichier de factures HT",
        type=['xlsx', 'xls'],
        key="upload_ht"
    )
    
    if fichier_ht:
        # Traiter le fichier
        df_ht, periode, has_typefact, erreurs = traiter_fichier_ht(fichier_ht)
        
        if erreurs:
            for erreur in erreurs:
                st.error(f"❌ {erreur}")
            
            if df_ht is not None and len(df_ht) > 0:
                st.info(f"📋 Colonnes disponibles : {', '.join(df_ht.columns)}")
        
        if df_ht is not None and len(df_ht) > 0:
            st.success(f"✅ Fichier chargé : {len(df_ht)} ligne(s)")
            
            if has_typefact:
                st.success("✅ Colonne 'typefact' détectée - Gestion E0/E1/E5 activée")
            else:
                st.warning("⚠️ Colonne 'typefact' non trouvée - Traitement normal")
            
            if periode:
                st.success(f"✅ Période détectée : **{periode}**")
                
                # Aperçu
                with st.expander("👁️ Aperçu des factures HT"):
                    cols_to_show = [CONFIG_HT['cle_facture'], CONFIG_HT['montant_col'], CONFIG_HT['periode_col']]
                    if CONFIG_HT['conso_col'] in df_ht.columns:
                        cols_to_show.insert(2, CONFIG_HT['conso_col'])
                    if has_typefact:
                        cols_to_show.append(CONFIG_HT['typefact_col'])
                    st.dataframe(df_ht[cols_to_show].head(20), use_container_width=True)
                
                st.markdown("---")
                
                # Bouton import
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🔄 LANCER L'IMPORT HT", type="primary", use_container_width=True):
                        with st.spinner("⏳ Import HT en cours..."):
                            df_base = st.session_state.df_central
                            
                            # Import
                            df_updated, nb_ajoutes, nb_doublons, non_trouves, stats = importer_factures_ht(
                                df_ht, df_base, periode, has_typefact
                            )
                            
                            # Sauvegarder
                            st.session_state.df_central = df_updated
                            save_central(df_updated)
                            
                            # Stocker les données HT pour la vue "Non Enregistrées"
                            st.session_state.df_factures_ht_dernier = df_ht.copy()
                            st.session_state.periode_ht_dernier = periode
                            st.session_state.has_typefact_ht = has_typefact
                            
                            # Résultats
                            st.markdown("---")
                            st.success(f"🎉 Import HT terminé : {nb_ajoutes} ligne(s) ajoutée(s) !")
                            
                            col_r1, col_r2, col_r3 = st.columns(3)
                            with col_r1:
                                st.metric("✅ Lignes ajoutées", nb_ajoutes)
                            with col_r2:
                                st.metric("📊 Total base centrale", len(df_updated))
                            with col_r3:
                                st.metric("📅 Période", periode)
                            
                            # Statistiques par type
                            if has_typefact:
                                st.markdown("### 📊 Statistiques par type de facture")
                                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                                
                                with col_s1:
                                    e0_count = stats['E0']['count']
                                    e0_cumul = stats['E0']['cumul']
                                    st.metric("E0 (Normal)", f"{e0_count} → {e0_cumul}")
                                
                                with col_s2:
                                    e1_count = stats['E1']['count']
                                    st.metric("E1 (Complém.)", e1_count)
                                    if e1_count > 0:
                                        st.caption("⚠️ À importer manuellement")
                                
                                with col_s3:
                                    st.metric("E5 (Avoir)", stats['E5']['count'])
                                
                                with col_s4:
                                    st.metric("Autre", stats['Autre']['count'])
                            
                            if nb_doublons > 0:
                                st.info(f"ℹ️ {nb_doublons} doublon(s) détecté(s) et ignoré(s)")
                            
                            if non_trouves:
                                st.warning(f"⚠️ {len(non_trouves)} identifiant(s) non trouvé(s) dans la base centrale")
                                with st.expander("👁️ Voir les identifiants non trouvés"):
                                    st.write(non_trouves[:50])
                            
                            # Message E1
                            if has_typefact and stats['E1']['count'] > 0:
                                st.info(f"""
                                📋 **{stats['E1']['count']} facture(s) complémentaire(s) (E1) détectée(s)**
                                
                                Les factures E1 ne sont **pas importées automatiquement** pour vous permettre :
                                - De vérifier les montants
                                - De contrôler les dates complémentaires
                                - De les ajouter manuellement si nécessaire
                                
                                ➡️ Allez dans **"📋 Non Enregistrées"** pour voir et importer manuellement les E1.
                                """)
                            
                            st.balloons()
