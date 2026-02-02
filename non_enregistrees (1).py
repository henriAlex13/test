"""
non_enregistrees.py
===================
Vue simplifiée des factures non enregistrées
"""

import pandas as pd
import streamlit as st
import io
from datetime import datetime
from models import normaliser_identifiant


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
    """Analyse BT - Version simplifiée"""
    
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
    
    # Résultats
    st.markdown("---")
    
    if len(df_non_enregistrees) > 0:
        st.warning(f"⚠️ **{len(df_non_enregistrees)} facture(s) non enregistrée(s)**")
        
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
    """Analyse HT - Version simplifiée"""
    
    st.markdown("### ⚡ Factures HT Non Enregistrées")
    
    # ==============================
    # SECTION E1 PRIORITAIRE
    # ==============================
    if 'df_e1_a_traiter' in st.session_state and st.session_state.df_e1_a_traiter is not None:
        df_e1 = st.session_state.df_e1_a_traiter
        if len(df_e1) > 0:
            st.warning(f"⚠️ **{len(df_e1)} facture(s) complémentaire(s) E1 - À importer manuellement**")
            
            with st.expander("📋 Voir les E1", expanded=True):
                st.info("""
                **Les E1 (complémentaires) nécessitent un import manuel** pour :
                - Vérifier les montants
                - Renseigner DATE_COMPLEMENTAIRE
                - Contrôler le lien avec la facture E0
                """)
                
                # Tableau E1
                cols_e1 = ['refraccord', 'montfact', 'conso', 'Periode_Emission_Bordereau', 'typefact']
                st.dataframe(df_e1[cols_e1], use_container_width=True, hide_index=True)
                
                # Export E1
                output_e1 = io.BytesIO()
                df_e1.to_excel(output_e1, index=False)
                output_e1.seek(0)
                
                st.download_button(
                    "📥 Télécharger E1 (Excel)",
                    data=output_e1,
                    file_name=f"E1_A_Traiter_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
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
    
    # Résultats
    st.markdown("---")
    
    if len(df_non_enregistrees) > 0:
        st.warning(f"⚠️ **{len(df_non_enregistrees)} facture(s) non enregistrée(s)**")
        
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
