"""
non_enregistrees.py
===================
Vue simplifiée des factures non enregistrées
Gestion import manuel E1 avec DATE_COMPLEMENTAIRE
"""

import pandas as pd
import streamlit as st
import io
from datetime import datetime
from models import normaliser_identifiant, ajouter_lignes_base_centrale, save_central


def extraire_periode(row, periode_col="Periode_Emission_Bordereau"):
    """Extrait et formate la période depuis une ligne de facture"""
    if periode_col not in row.index:
        return None
    
    periode_brute = row[periode_col]
    if pd.notna(periode_brute):
        periode_str = str(int(periode_brute)) if isinstance(periode_brute, float) else str(periode_brute)
        if len(periode_str) == 6:
            return f"{periode_str[4:6]}/{periode_str[:4]}"
        return periode_str
    return None


def page_non_enregistrees():
    """Page simplifiée des factures non enregistrées"""
    
    st.markdown("## 📋 Factures Non Enregistrées")
    st.markdown("---")
    
    st.info("💡 **Cette page affiche les factures présentes dans vos fichiers Excel mais absentes de la Base Centrale.**")
    
    # Tabs BT et HT
    tab_bt, tab_ht = st.tabs(["🔌 Basse Tension (BT)", "⚡ Haute Tension (HT)"])
    
    with tab_bt:
        analyser_bt_simple()
    
    with tab_ht:
        analyser_ht_simple()


def analyser_bt_simple():
    """Analyse BT - Version simplifiée avec vérification cohérence"""
    
    st.markdown("### 🔌 Factures BT Non Enregistrées")
    
    # Vérifier données
    if 'df_factures_bt_dernier' not in st.session_state or st.session_state.df_factures_bt_dernier is None:
        st.info("💡 Aucune facture BT importée. Allez dans '🔄 Import Factures BT' d'abord.")
        return
    
    df_factures = st.session_state.df_factures_bt_dernier.copy()
    periode = st.session_state.get('periode_bt_dernier', '')
    
    st.success(f"📅 Période : **{periode}** | 📊 {len(df_factures)} facture(s)")
    
    # Configuration
    cle_facture = "Référence Contrat"
    montant_col = "Montant facture TTC"
    
    # Analyse
    df_factures['IDENTIFIANT'] = df_factures[cle_facture].apply(normaliser_identifiant)
    
    df_central = st.session_state.df_central
    identifiants_base = set(df_central['IDENTIFIANT'].unique())
    
    df_factures['DANS_BASE'] = df_factures['IDENTIFIANT'].isin(identifiants_base)
    df_non_enregistrees = df_factures[~df_factures['DANS_BASE']].copy()
    df_enregistrees = df_factures[df_factures['DANS_BASE']].copy()
    
    # Vérification cohérence montants
    df_factures[montant_col] = pd.to_numeric(df_factures[montant_col], errors='coerce').fillna(0)
    df_non_enregistrees[montant_col] = pd.to_numeric(df_non_enregistrees[montant_col], errors='coerce').fillna(0)
    df_enregistrees[montant_col] = pd.to_numeric(df_enregistrees[montant_col], errors='coerce').fillna(0)
    
    total_factures = df_factures[montant_col].sum()
    total_non_enregistrees = df_non_enregistrees[montant_col].sum()
    total_enregistrees = df_enregistrees[montant_col].sum()
    
    # Montant dans base centrale pour cette période
    df_base_periode = df_central[
        (df_central['DATE'] == periode) & 
        (df_central['TENSION'] == 'BASSE')
    ].copy()
    df_base_periode['MONTANT'] = pd.to_numeric(df_base_periode['MONTANT'], errors='coerce').fillna(0)
    total_base_centrale = df_base_periode['MONTANT'].sum()
    
    # Afficher vérification
    st.markdown("---")
    st.markdown("### 🔍 Vérification Cohérence")
    
    col_v1, col_v2, col_v3, col_v4 = st.columns(4)
    
    with col_v1:
        st.metric("📄 Total Factures", f"{total_factures:,.0f} FCFA")
    
    with col_v2:
        st.metric("✅ Enregistrées", f"{total_enregistrees:,.0f} FCFA")
    
    with col_v3:
        st.metric("❌ Non Enregistrées", f"{total_non_enregistrees:,.0f} FCFA")
    
    with col_v4:
        st.metric("💾 Base Centrale", f"{total_base_centrale:,.0f} FCFA")
    
    # Vérification formule
    difference = abs(total_factures - (total_enregistrees + total_non_enregistrees))
    difference_base = abs(total_enregistrees - total_base_centrale)
    
    if difference < 1:
        st.success("✅ **Cohérence OK** : Total Factures = Enregistrées + Non Enregistrées")
    else:
        st.error(f"⚠️ **INCOHÉRENCE DÉTECTÉE** : Différence de {difference:,.0f} FCFA")
        st.warning("Vérifiez les données importées !")
    
    if difference_base < 1:
        st.success("✅ **Base Centrale OK** : Montants cohérents")
    else:
        st.warning(f"⚠️ Écart Base Centrale : {difference_base:,.0f} FCFA (peut être normal si factures antérieures)")
    
    # Résultats
    st.markdown("---")
    
    if len(df_non_enregistrees) > 0:
        st.warning(f"⚠️ **{len(df_non_enregistrees)} facture(s) non enregistrée(s) - Total : {total_non_enregistrees:,.0f} FCFA**")
        
        # Tableau
        st.dataframe(
            df_non_enregistrees[[cle_facture, montant_col, 'IDENTIFIANT']],
            use_container_width=True,
            hide_index=True
        )
        
        # Export
        output = io.BytesIO()
        df_non_enregistrees.to_excel(output, index=False)
        output.seek(0)
        
        st.download_button(
            "📥 Télécharger (Excel)",
            data=output,
            file_name=f"BT_Non_Enregistrees_{periode.replace('/', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.success("✅ **Toutes les factures BT sont enregistrées !**")
        st.balloons()


def analyser_ht_simple():
    """Analyse HT - Version simplifiée avec import manuel E1"""
    
    st.markdown("### ⚡ Factures HT Non Enregistrées")
    
    # ==============================
    # SECTION E1 IMPORT MANUEL
    # ==============================
    if 'df_e1_a_traiter' in st.session_state and st.session_state.df_e1_a_traiter is not None:
        df_e1_full = st.session_state.df_e1_a_traiter
        
        if len(df_e1_full) > 0:
            # Configuration colonnes
            cle_facture = 'refraccord'
            montant_col = 'montfact'
            conso_col = 'conso'
            periode_col = 'Periode_Emission_Bordereau'
            typefact_col = 'typefact'
            
            # Normaliser et déterminer quelles E1 sont déjà enregistrées
            df_e1_full['IDENTIFIANT_NORM'] = df_e1_full[cle_facture].apply(normaliser_identifiant)
            
            df_central = st.session_state.df_central
            identifiants_base = set(df_central['IDENTIFIANT'].unique())
            
            # ✨ Pour E1, vérifier dans DATE_COMPLEMENTAIRE
            def est_enregistree(row):
                identifiant = row['IDENTIFIANT_NORM']
                
                # Si l'identifiant n'existe pas du tout
                if identifiant not in identifiants_base:
                    return False
                
                # Pour E1, vérifier DATE_COMPLEMENTAIRE
                periode_facture = extraire_periode(row, periode_col)
                if not periode_facture:
                    return False
                
                # Vérifier si cette période existe dans DATE_COMPLEMENTAIRE
                lignes_site = df_central[df_central['IDENTIFIANT'] == identifiant]
                if 'DATE_COMPLEMENTAIRE' in df_central.columns:
                    dates_comp = lignes_site['DATE_COMPLEMENTAIRE'].dropna().unique()
                    return periode_facture in dates_comp
                
                return False
            
            df_e1_full['ENREGISTREE'] = df_e1_full.apply(est_enregistree, axis=1)
            df_e1_non_enreg = df_e1_full[~df_e1_full['ENREGISTREE']].copy()
            
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
                    lignes_a_ajouter = []
                    erreurs = []
                    
                    for idx, row in df_e1_non_enreg.iterrows():
                        identifiant = row['IDENTIFIANT_NORM']
                        
                        # Extraire la période
                        periode = extraire_periode(row, periode_col)
                        if not periode:
                            erreurs.append(f"Période manquante pour {identifiant}")
                            continue
                        
                        # Récupérer les infos du site depuis la base
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
                            'DATE': site_info.get('DATE', periode),  # DATE = période du site existant
                            'CONSO': float(row[conso_col]) if pd.notna(row.get(conso_col)) else 0,
                            'MONTANT': float(row[montant_col]) if pd.notna(row.get(montant_col)) else 0,
                            'DATE_COMPLEMENTAIRE': periode,  # ✨ DATE_COMPLEMENTAIRE = vraie période E1
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
                            df_nouvelles,
                            df_nouvelles.iloc[0]['DATE']  # Prendre DATE de la première ligne
                        )
                        
                        st.session_state.df_central = resultat[0]
                        save_central(st.session_state.df_central)
                        
                        st.success(f"✅ {len(lignes_a_ajouter)} facture(s) E1 importée(s) avec succès !")
                        st.info(f"📅 DATE_COMPLEMENTAIRE remplie pour ces factures")
                        st.rerun()
                    else:
                        if not erreurs:
                            st.warning("⚠️ Aucune facture E1 valide à importer")
    
    st.markdown("---")
    
    # ==============================
    # ANALYSE NORMALE (E0, E5, Autres)
    # ==============================
    
    # Vérifier données
    if 'df_factures_ht_dernier' not in st.session_state or st.session_state.df_factures_ht_dernier is None:
        st.info("💡 Aucune facture HT importée. Allez dans '🔄 Import Factures HT' d'abord.")
        return
    
    df_factures = st.session_state.df_factures_ht_dernier.copy()
    periode = st.session_state.get('periode_ht_dernier', '')
    
    st.success(f"📅 Période : **{periode}** | 📊 {len(df_factures)} facture(s)")
    
    # Configuration
    cle_facture = "refraccord"
    montant_col = "montfact"
    
    # Analyse
    df_factures['IDENTIFIANT'] = df_factures[cle_facture].apply(normaliser_identifiant)
    
    df_central = st.session_state.df_central
    identifiants_base = set(df_central['IDENTIFIANT'].unique())
    
    df_factures['DANS_BASE'] = df_factures['IDENTIFIANT'].isin(identifiants_base)
    df_non_enregistrees = df_factures[~df_factures['DANS_BASE']].copy()
    df_enregistrees = df_factures[df_factures['DANS_BASE']].copy()
    
    # Vérification cohérence montants
    df_factures[montant_col] = pd.to_numeric(df_factures[montant_col], errors='coerce').fillna(0)
    df_non_enregistrees[montant_col] = pd.to_numeric(df_non_enregistrees[montant_col], errors='coerce').fillna(0)
    df_enregistrees[montant_col] = pd.to_numeric(df_enregistrees[montant_col], errors='coerce').fillna(0)
    
    total_factures = df_factures[montant_col].sum()
    total_non_enregistrees = df_non_enregistrees[montant_col].sum()
    total_enregistrees = df_enregistrees[montant_col].sum()
    
    # Ajouter E1 au total
    total_e1 = 0
    if 'df_e1_a_traiter' in st.session_state and st.session_state.df_e1_a_traiter is not None:
        df_e1 = st.session_state.df_e1_a_traiter
        if len(df_e1) > 0 and montant_col in df_e1.columns:
            df_e1[montant_col] = pd.to_numeric(df_e1[montant_col], errors='coerce').fillna(0)
            total_e1 = df_e1[montant_col].sum()
    
    # Montant dans base centrale pour cette période
    df_base_periode = df_central[
        (df_central['DATE'] == periode) & 
        (df_central['TENSION'] == 'HAUTE')
    ].copy()
    df_base_periode['MONTANT'] = pd.to_numeric(df_base_periode['MONTANT'], errors='coerce').fillna(0)
    total_base_centrale = df_base_periode['MONTANT'].sum()
    
    # Afficher vérification
    st.markdown("### 🔍 Vérification Cohérence")
    
    col_v1, col_v3, col_v4, col_v5 = st.columns(4)
    
    with col_v1:
        st.metric("📄 Total Factures", f"{total_factures:,.0f} FCFA")
    
    with col_v3:
        st.metric("❌ Non Enregistrées", f"{total_non_enregistrees:,.0f} FCFA")
    
    with col_v4:
        st.metric("⚠️ E1 (Manuel)", f"{total_e1:,.0f} FCFA")
    
    with col_v5:
        st.metric("💾 Base Centrale", f"{total_base_centrale:,.0f} FCFA")
    
    # Vérification formule
    difference = abs(total_factures - (total_enregistrees + total_non_enregistrees + total_e1))
    difference_base = abs(total_enregistrees - total_base_centrale)
    
    if difference < 1:
        st.success("✅ **Cohérence OK** : Total Factures = Enregistrées + Non Enregistrées + E1")
    else:
        st.error(f"⚠️ **INCOHÉRENCE DÉTECTÉE** : Différence de {difference:,.0f} FCFA")
    
    if difference_base < 1:
        st.success("✅ **Base Centrale OK** : Montants cohérents")
    else:
        st.warning(f"⚠️ Écart Base Centrale : {difference_base:,.0f} FCFA")
    
    # Résultats
    st.markdown("---")
    
    if len(df_non_enregistrees) > 0:
        st.warning(f"⚠️ **{len(df_non_enregistrees)} facture(s) non enregistrée(s) - Total : {total_non_enregistrees:,.0f} FCFA**")
        
        # Tableau
        cols_affichage = [cle_facture, montant_col, 'IDENTIFIANT']
        if 'typefact' in df_non_enregistrees.columns:
            cols_affichage.append('typefact')
        
        st.dataframe(
            df_non_enregistrees[cols_affichage],
            use_container_width=True,
            hide_index=True
        )
        
        # Export
        output = io.BytesIO()
        df_non_enregistrees.to_excel(output, index=False)
        output.seek(0)
        
        st.download_button(
            "📥 Télécharger (Excel)",
            data=output,
            file_name=f"HT_Non_Enregistrees_{periode.replace('/', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.success("✅ **Toutes les factures HT sont enregistrées !**")
        st.balloons()
