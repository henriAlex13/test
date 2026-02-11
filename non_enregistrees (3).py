"""
non_enregistrees.py
===================
Vue des lignes non enregistrées dans la base centrale
Utilise automatiquement les fichiers déjà importés
"""

import pandas as pd
import streamlit as st
import io
from models import normaliser_identifiant


def page_non_enregistrees():
    """
    Page Streamlit pour visualiser et gérer les lignes non enregistrées
    """
    st.markdown("## 📋 Lignes Non Enregistrées")
    st.markdown("---")
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #fa709a, #fee140); 
                color: white; 
                padding: 1.5rem; 
                border-radius: 10px;
                margin: 1rem 0;'>
        <h3 style='margin: 0;'>📋 LIGNES NON ENREGISTRÉES</h3>
        <p style='margin: 0.5rem 0 0 0;'>Analyse automatique des factures non importées dans la base centrale</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("""
    📌 **Cette vue utilise automatiquement** :
    - Les dernières factures BT importées
    - Les dernières factures HT importées
    
    💡 Pas besoin de recharger les fichiers !
    """)
    
    # Tabs pour BT et HT
    tab_bt, tab_ht = st.tabs(["🔌 Non Enregistrées BT", "⚡ Non Enregistrées HT"])
    
    with tab_bt:
        analyser_non_enregistrees_bt()
    
    with tab_ht:
        analyser_non_enregistrees_ht()


def analyser_non_enregistrees_bt():
    """
    Analyse des lignes BT non enregistrées
    Utilise automatiquement les dernières factures importées
    """
    st.markdown("### 🔌 Analyse Factures BT Non Enregistrées")
    
    # Configuration BT
    cle_facture = "Référence Contrat"
    montant_col = "Montant facture TTC"
    conso_col = "KWH Facturé"
    periode_col = "Période Facture sur date fact"
    
    # Vérifier si des factures BT ont été importées
    if 'df_factures_bt_dernier' in st.session_state and st.session_state.df_factures_bt_dernier is not None:
        st.success(f"✅ Utilisation des dernières factures BT importées")
        if 'periode_bt_dernier' in st.session_state:
            st.info(f"📅 Période : **{st.session_state.periode_bt_dernier}** | 📊 {len(st.session_state.df_factures_bt_dernier)} facture(s)")
        
        df_factures = st.session_state.df_factures_bt_dernier.copy()
        
        # Option pour analyser un autre fichier
        with st.expander("🔄 Analyser un autre fichier BT (optionnel)"):
            st.info("💡 Par défaut, on utilise les dernières factures importées. Uploadez ici seulement si vous voulez analyser un autre fichier.")
            fichier_bt_autre = st.file_uploader(
                "📥 Fichier BT alternatif",
                type=['xlsx', 'xls'],
                key="upload_bt_autre"
            )
            
            if fichier_bt_autre:
                try:
                    df_factures = pd.read_excel(fichier_bt_autre)
                    st.success(f"✅ Fichier alternatif chargé : {len(df_factures)} ligne(s)")
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")
                    return
    else:
        st.warning("⚠️ Aucune facture BT n'a encore été importée dans cette session.")
        st.info("💡 **Veuillez d'abord importer vos factures BT** :")
        st.markdown("1. Allez dans la page **'🔄 Import Factures BT'**")
        st.markdown("2. Uploadez votre fichier de factures")
        st.markdown("3. Cliquez sur **'LANCER L'IMPORT BT'**")
        st.markdown("4. Revenez ici pour voir l'analyse automatique")
        
        st.info("📌 Les données seront disponibles automatiquement après l'import !")
        return
    
    # Analyse
    try:
        # Vérifier colonnes
        if cle_facture not in df_factures.columns:
            st.error(f"❌ Colonne '{cle_facture}' introuvable")
            st.info(f"📋 Colonnes disponibles : {', '.join(df_factures.columns)}")
            return
        
        # Normaliser les identifiants
        df_factures['IDENTIFIANT_NORM'] = df_factures[cle_facture].apply(normaliser_identifiant)
        
        # Base centrale
        df_central = st.session_state.df_central
        identifiants_base = set(df_central['IDENTIFIANT'].unique())
        
        # Identifier les non enregistrées
        df_factures['ENREGISTREE'] = df_factures['IDENTIFIANT_NORM'].isin(identifiants_base)
        
        df_non_enregistrees = df_factures[~df_factures['ENREGISTREE']].copy()
        df_enregistrees = df_factures[df_factures['ENREGISTREE']].copy()
        
        # Statistiques
        st.markdown("---")
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("📊 Total factures", len(df_factures))
        with col_stat2:
            st.metric("✅ Enregistrées", len(df_enregistrees))
        with col_stat3:
            st.metric("❌ Non enregistrées", len(df_non_enregistrees))
        with col_stat4:
            taux = (len(df_enregistrees) / len(df_factures) * 100) if len(df_factures) > 0 else 0
            st.metric("📈 Taux", f"{taux:.1f}%")
        
        st.markdown("---")
        
        if len(df_non_enregistrees) > 0:
            st.warning(f"⚠️ **{len(df_non_enregistrees)} ligne(s) non enregistrée(s)**")
            
            # Afficher
            st.markdown("### 📋 Détail des lignes non enregistrées")
            
            colonnes_disponibles = df_non_enregistrees.columns.tolist()
            colonnes_affichees = st.multiselect(
                "Colonnes à afficher",
                colonnes_disponibles,
                default=[col for col in [cle_facture, montant_col, conso_col, periode_col] if col in colonnes_disponibles],
                key="colonnes_bt"
            )
            
            if colonnes_affichees:
                st.dataframe(
                    df_non_enregistrees[colonnes_affichees],
                    use_container_width=True,
                    height=400
                )
                
                # Exports
                st.markdown("---")
                col_exp1, col_exp2, col_exp3 = st.columns(3)
                
                with col_exp1:
                    output = io.BytesIO()
                    df_non_enregistrees.to_excel(output, index=False, engine='openpyxl')
                    output.seek(0)
                    
                    st.download_button(
                        "📥 Excel complet",
                        data=output,
                        file_name=f"BT_Non_Enregistrees_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col_exp2:
                    output_ids = io.BytesIO()
                    df_ids = pd.DataFrame({
                        'IDENTIFIANT': df_non_enregistrees['IDENTIFIANT_NORM'].unique()
                    })
                    df_ids.to_excel(output_ids, index=False, engine='openpyxl')
                    output_ids.seek(0)
                    
                    st.download_button(
                        "📥 Liste IDENTIFIANT",
                        data=output_ids,
                        file_name=f"BT_IDs_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col_exp3:
                    if st.button("🔄 Actualiser", use_container_width=True):
                        st.rerun()
            
            # Détail par ID
            st.markdown("---")
            st.markdown("### 🔍 Détail par IDENTIFIANT")
            
            id_select = st.selectbox(
                "Sélectionner",
                df_non_enregistrees['IDENTIFIANT_NORM'].unique(),
                key="select_id_bt"
            )
            
            if id_select:
                df_detail = df_non_enregistrees[df_non_enregistrees['IDENTIFIANT_NORM'] == id_select]
                st.dataframe(df_detail.T, use_container_width=True)
        
        else:
            st.success("✅ **Toutes les factures sont enregistrées !**")
            st.balloons()
        
        # Enregistrées (pour info)
        if len(df_enregistrees) > 0:
            with st.expander(f"✅ {len(df_enregistrees)} ligne(s) déjà enregistrée(s)"):
                cols = st.multiselect(
                    "Colonnes",
                    colonnes_disponibles,
                    default=[col for col in [cle_facture, montant_col, conso_col, periode_col] if col in colonnes_disponibles],
                    key="cols_bt_enreg"
                )
                if cols:
                    st.dataframe(df_enregistrees[cols], use_container_width=True, height=300)
    
    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")
        st.exception(e)


def analyser_non_enregistrees_ht():
    """
    Analyse des lignes HT non enregistrées
    Utilise automatiquement les dernières factures importées
    """
    st.markdown("### ⚡ Analyse Factures HT Non Enregistrées")
    
    # Configuration HT
    cle_facture = "refraccord"
    montant_col = "montfact"
    conso_col = "conso"
    periode_col = "Periode_Emission_Bordereau"
    typefact_col = "typefact"
    
    # Vérifier si des factures HT ont été importées
    if 'df_factures_ht_dernier' in st.session_state and st.session_state.df_factures_ht_dernier is not None:
        st.success(f"✅ Utilisation des dernières factures HT importées")
        if 'periode_ht_dernier' in st.session_state:
            st.info(f"📅 Période : **{st.session_state.periode_ht_dernier}** | 📊 {len(st.session_state.df_factures_ht_dernier)} facture(s)")
        
        df_factures = st.session_state.df_factures_ht_dernier.copy()
        has_typefact = st.session_state.get('has_typefact_ht', False)
        
        # Option pour analyser un autre fichier
        with st.expander("🔄 Analyser un autre fichier HT (optionnel)"):
            st.info("💡 Par défaut, on utilise les dernières factures importées.")
            fichier_ht_autre = st.file_uploader(
                "📥 Fichier HT alternatif",
                type=['xlsx', 'xls'],
                key="upload_ht_autre"
            )
            
            if fichier_ht_autre:
                try:
                    df_factures = pd.read_excel(fichier_ht_autre)
                    has_typefact = typefact_col in df_factures.columns
                    st.success(f"✅ Fichier alternatif : {len(df_factures)} ligne(s)")
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")
                    return
    else:
        st.warning("⚠️ Aucune facture HT n'a encore été importée dans cette session.")
        st.info("💡 **Veuillez d'abord importer vos factures HT** :")
        st.markdown("1. Allez dans la page **'🔄 Import Factures HT'**")
        st.markdown("2. Uploadez votre fichier de factures")
        st.markdown("3. Cliquez sur **'LANCER L'IMPORT HT'**")
        st.markdown("4. Revenez ici pour voir l'analyse automatique")
        
        st.info("📌 Les données seront disponibles automatiquement après l'import !")
        return
    
    # Analyse
    try:
        if cle_facture not in df_factures.columns:
            st.error(f"❌ Colonne '{cle_facture}' introuvable")
            st.info(f"📋 Disponibles : {', '.join(df_factures.columns)}")
            return
        
        if has_typefact:
            st.success("✅ Colonne 'typefact' détectée")
        
        df_factures['IDENTIFIANT_NORM'] = df_factures[cle_facture].apply(normaliser_identifiant)
        
        df_central = st.session_state.df_central
        identifiants_base = set(df_central['IDENTIFIANT'].unique())
        
        # Pour chaque facture, vérifier si elle est enregistrée
        def est_enregistree(row):
            identifiant = row['IDENTIFIANT_NORM']
            
            # Si l'identifiant n'existe pas du tout dans la base
            if identifiant not in identifiants_base:
                return False
            
            # Si c'est une E1, vérifier dans DATE_COMPLEMENTAIRE
            if has_typefact and typefact_col in row.index and row[typefact_col] == 'E1':
                # Extraire la période de la facture
                if periode_col in row.index and pd.notna(row[periode_col]):
                    periode_facture = str(row[periode_col])
                    # Convertir 202501 → 01/2025
                    if len(periode_facture) == 6:
                        periode_formatee = f"{periode_facture[4:6]}/{periode_facture[:4]}"
                    else:
                        periode_formatee = periode_facture
                    
                    # Vérifier si cette période existe dans DATE_COMPLEMENTAIRE pour cet identifiant
                    lignes_site = df_central[df_central['IDENTIFIANT'] == identifiant]
                    if 'DATE_COMPLEMENTAIRE' in df_central.columns:
                        dates_comp = lignes_site['DATE_COMPLEMENTAIRE'].dropna().unique()
                        return periode_formatee in dates_comp
                    return False
            
            # Pour E0 et autres, vérifier juste si l'identifiant existe
            return True
        
        df_factures['ENREGISTREE'] = df_factures.apply(est_enregistree, axis=1)
        
        df_non_enregistrees = df_factures[~df_factures['ENREGISTREE']].copy()
        df_enregistrees = df_factures[df_factures['ENREGISTREE']].copy()
        
        # Stats
        st.markdown("---")
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("📊 Total", len(df_factures))
        with col_stat2:
            st.metric("✅ Enregistrées", len(df_enregistrees))
        with col_stat3:
            st.metric("❌ Non enregistrées", len(df_non_enregistrees))
        with col_stat4:
            taux = (len(df_enregistrees) / len(df_factures) * 100) if len(df_factures) > 0 else 0
            st.metric("📈 Taux", f"{taux:.1f}%")
        
        # Stats par type
        if has_typefact and len(df_non_enregistrees) > 0:
            st.markdown("### 📊 Par type (non enregistrées)")
            
            types = df_non_enregistrees[typefact_col].value_counts()
            
            col_t1, col_t2, col_t3, col_t4 = st.columns(4)
            with col_t1:
                st.metric("E0", types.get('E0', 0))
            with col_t2:
                st.metric("E1", types.get('E1', 0))
            with col_t3:
                st.metric("E5", types.get('E5', 0))
            with col_t4:
                autres = len(df_non_enregistrees) - types.get('E0', 0) - types.get('E1', 0) - types.get('E5', 0)
                st.metric("Autre", autres)
        
        # ============================================
        # IMPORT MANUEL DES E1 (COMPLÉMENTAIRES)
        # ============================================
        if has_typefact and len(df_non_enregistrees) > 0:
            df_e1_non_enreg = df_non_enregistrees[df_non_enregistrees[typefact_col] == 'E1'].copy()
            
            if len(df_e1_non_enreg) > 0:
                st.markdown("---")
                st.markdown("### 📋 Factures E1 (Complémentaires) - Import Manuel")
                
                st.info(f"""
                📌 **{len(df_e1_non_enreg)} facture(s) complémentaire(s) (E1) détectée(s)**
                
                Les factures E1 nécessitent une validation manuelle avant import.
                Elles rempliront la colonne `DATE_COMPLEMENTAIRE` dans la base centrale.
                """)
                
                # Afficher les E1
                cols_e1 = [col for col in [cle_facture, montant_col, conso_col, periode_col] if col in df_e1_non_enreg.columns]
                if 'PSABON' in df_e1_non_enreg.columns:
                    cols_e1.append('PSABON')
                if 'PSATTEINTE' in df_e1_non_enreg.columns:
                    cols_e1.append('PSATTEINTE')
                
                st.dataframe(
                    df_e1_non_enreg[cols_e1],
                    use_container_width=True,
                    height=200
                )
                
                # Bouton d'import
                if st.button("✅ Importer ces factures E1", type="primary", use_container_width=True, key="import_e1"):
                    from models import ajouter_lignes_base_centrale
                    
                    lignes_a_ajouter = []
                    erreurs = []
                    
                    for idx, row in df_e1_non_enreg.iterrows():
                        identifiant = row['IDENTIFIANT_NORM']
                        
                        # Extraire la période
                        periode_brute = row[periode_col] if periode_col in row.index else None
                        if pd.notna(periode_brute):
                            periode_str = str(int(periode_brute)) if isinstance(periode_brute, float) else str(periode_brute)
                            if len(periode_str) == 6:
                                periode = f"{periode_str[4:6]}/{periode_str[:4]}"
                            else:
                                periode = periode_str
                        else:
                            erreurs.append(f"Période manquante pour {identifiant}")
                            continue
                        
                        # Récupérer les infos du site depuis la base
                        df_central = st.session_state.df_central
                        sites_existants = df_central[df_central['IDENTIFIANT'] == identifiant]
                        
                        if len(sites_existants) == 0:
                            erreurs.append(f"Site {identifiant} introuvable - Importez d'abord une facture E0")
                            continue
                        
                        site_info = sites_existants.iloc[0].to_dict()
                        
                        # Créer la ligne E1
                        ligne = {
                            'UC': site_info.get('UC', ''),
                            'CODE RED': site_info.get('CODE RED', ''),
                            'CODE AGCE': site_info.get('CODE AGCE', ''),
                            'SITES': site_info.get('SITES', ''),
                            'IDENTIFIANT': identifiant,
                            'TENSION': 'HAUTE',
                            'DATE': site_info.get('DATE', periode),
                            'CONSO': float(row[conso_col]) if pd.notna(row.get(conso_col)) else 0,
                            'MONTANT': float(row[montant_col]) if pd.notna(row.get(montant_col)) else 0,
                            'DATE_COMPLEMENTAIRE': periode,  # ✨ Période complémentaire
                            'STATUT': site_info.get('STATUT', 'ACTIF'),
                            'PSABON': float(row['PSABON']) if 'PSABON' in row.index and pd.notna(row.get('PSABON')) else site_info.get('PSABON', 0),
                            'PSATTEINTE': float(row['PSATTEINTE']) if 'PSATTEINTE' in row.index and pd.notna(row.get('PSATTEINTE')) else site_info.get('PSATTEINTE', 0),
                            'COMPTE_CHARGE': str(site_info.get('COMPTE_CHARGE', '62183464'))
                        }
                        
                        lignes_a_ajouter.append(ligne)
                    
                    if erreurs:
                        for err in erreurs:
                            st.error(f"❌ {err}")
                    
                    if lignes_a_ajouter:
                        # Ajouter à la base
                        df_nouvelles = pd.DataFrame(lignes_a_ajouter)
                        resultat = ajouter_lignes_base_centrale(
                            st.session_state.df_central,
                            df_nouvelles
                        )
                        
                        st.session_state.df_central = resultat['df_final']
                        
                        st.success(f"✅ {len(lignes_a_ajouter)} facture(s) E1 importée(s) avec succès !")
                        st.info(f"📅 DATE_COMPLEMENTAIRE remplie pour ces factures")
                        st.rerun()
                    else:
                        if not erreurs:
                            st.warning("⚠️ Aucune facture E1 valide à importer")
        
        st.markdown("---")
        
        if len(df_non_enregistrees) > 0:
            st.warning(f"⚠️ **{len(df_non_enregistrees)} non enregistrée(s)**")
            
            st.markdown("### 📋 Détail")
            
            colonnes_dispo = df_non_enregistrees.columns.tolist()
            default_cols = [col for col in [cle_facture, montant_col, conso_col, periode_col, typefact_col] if col in colonnes_dispo]
            
            colonnes_affichees = st.multiselect(
                "Colonnes",
                colonnes_dispo,
                default=default_cols,
                key="cols_ht"
            )
            
            if colonnes_affichees:
                st.dataframe(
                    df_non_enregistrees[colonnes_affichees],
                    use_container_width=True,
                    height=400
                )
                
                # Exports
                st.markdown("---")
                col_e1, col_e2, col_e3 = st.columns(3)
                
                with col_e1:
                    output = io.BytesIO()
                    df_non_enregistrees.to_excel(output, index=False, engine='openpyxl')
                    output.seek(0)
                    
                    st.download_button(
                        "📥 Excel complet",
                        data=output,
                        file_name=f"HT_Non_Enreg_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col_e2:
                    output_ids = io.BytesIO()
                    df_ids = pd.DataFrame({'IDENTIFIANT': df_non_enregistrees['IDENTIFIANT_NORM'].unique()})
                    df_ids.to_excel(output_ids, index=False, engine='openpyxl')
                    output_ids.seek(0)
                    
                    st.download_button(
                        "📥 Liste ID",
                        data=output_ids,
                        file_name=f"HT_IDs_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col_e3:
                    if st.button("🔄 Actualiser", use_container_width=True, key="refresh_ht"):
                        st.rerun()
            
            # Filtre par type
            if has_typefact:
                st.markdown("---")
                st.markdown("### 🔍 Filtrer par type")
                
                type_sel = st.selectbox(
                    "Type",
                    ['Tous'] + df_non_enregistrees[typefact_col].unique().tolist(),
                    key="type_filter"
                )
                
                if type_sel != 'Tous':
                    df_filtre = df_non_enregistrees[df_non_enregistrees[typefact_col] == type_sel]
                    st.info(f"📊 {len(df_filtre)} ligne(s) de type **{type_sel}**")
                    
                    if colonnes_affichees:
                        st.dataframe(df_filtre[colonnes_affichees], use_container_width=True, height=300)
            
            # Détail
            st.markdown("---")
            st.markdown("### 🔍 Détail")
            
            id_sel = st.selectbox(
                "IDENTIFIANT",
                df_non_enregistrees['IDENTIFIANT_NORM'].unique(),
                key="select_id_ht"
            )
            
            if id_sel:
                df_detail = df_non_enregistrees[df_non_enregistrees['IDENTIFIANT_NORM'] == id_sel]
                st.dataframe(df_detail.T, use_container_width=True)
        
        else:
            st.success("✅ **Toutes enregistrées !**")
            st.balloons()
        
        # Enregistrées
        if len(df_enregistrees) > 0:
            with st.expander(f"✅ {len(df_enregistrees)} enregistrée(s)"):
                cols = st.multiselect(
                    "Colonnes",
                    colonnes_dispo,
                    default=default_cols,
                    key="cols_ht_enreg"
                )
                if cols:
                    st.dataframe(df_enregistrees[cols], use_container_width=True, height=300)
    
    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")
        st.exception(e)
