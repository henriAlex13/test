"""
app.py
======
Application principale - Gestion Factures CIE V3.0
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import plotly.graph_objects as go

# Imports des modules
from models import load_central, save_central, COLONNES_BASE_CENTRALE
from import_bt import page_import_bt
from import_ht import page_import_ht
from generation import page_generation_fichiers

st.set_page_config(
    page_title="Gestion Factures CIE - V3",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-title {
        color: white;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation
if 'df_central' not in st.session_state:
    st.session_state.df_central = load_central()

# Header
st.markdown("""
<div class="main-header">
    <h1 class="main-title" style="color: #f0f0f0">📊 Gestion Factures CIE</h1>
    <p class="main-subtitle" style="color: #f0f0f0; text-align: center; margin-top: 0.5rem;">
        Version 3.0 - Gestion simplifiée avec pièces comptables
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📋 Navigation")
    
    page = st.radio(
        "Menu principal",
        [
            "📊 Base Centrale", 
            "📋 Non Enregistrées", 
            "🔄 Import Factures BT", 
            "🔄 Import Factures HT", 
            "📈 Statistiques", 
            "⚙️ Génération Fichiers"
        ]
    )
    
    st.markdown("---")
    st.markdown("### 📊 Informations")
    
    df_central = st.session_state.df_central
    nb_lignes = len(df_central[df_central['DATE'].notna() & (df_central['DATE'] != '')])
    st.metric("📝 Lignes", nb_lignes)
    
    if 'DATE' in df_central.columns:
        periodes = df_central['DATE'].dropna().nunique()
        st.metric("📅 Périodes", periodes)


# ===== PAGES =====

if page == "📊 Base Centrale":
    st.markdown("## 📊 Base Centrale")
    st.markdown("---")
    
    st.info("""
    📌 **Colonnes de la base centrale** :
    - UC, CODE RED, CODE AGCE, SITES, IDENTIFIANT
    - TENSION, DATE, CONSO, MONTANT, DATE_COMPLEMENTAIRE
    
    💡 Vous pouvez ajouter, modifier ou supprimer des lignes manuellement.
    """)
    
    df_central = st.session_state.df_central
    
    # Statistiques
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        nb_total = len(df_central[df_central['DATE'].notna() & (df_central['DATE'] != '')])
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea;">📝</h3>
            <h2>{nb_total}</h2>
            <p style="color: #666;">Lignes totales</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_stat2:
        sites_uniques = df_central['IDENTIFIANT'].nunique() if 'IDENTIFIANT' in df_central.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea;">🏢</h3>
            <h2>{sites_uniques}</h2>
            <p style="color: #666;">Sites uniques</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_stat3:
        periodes = df_central['DATE'].dropna().nunique() if 'DATE' in df_central.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea;">📅</h3>
            <h2>{periodes}</h2>
            <p style="color: #666;">Périodes</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_stat4:
        total = df_central['MONTANT'].sum() if 'MONTANT' in df_central.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea;">💰</h3>
            <h2>{total/1000:.0f}K</h2>
            <p style="color: #666;">Total FCFA</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filtres
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        if 'UC' in df_central.columns:
            ucs = ['Tous'] + sorted(df_central['UC'].dropna().unique().tolist())
            uc_filter = st.selectbox("Filtrer par UC", ucs)
        else:
            uc_filter = 'Tous'
    
    with col_f2:
        if 'DATE' in df_central.columns:
            dates = ['Tous'] + sorted(df_central['DATE'].dropna().unique().tolist(), reverse=True)
            date_filter = st.selectbox("Filtrer par DATE", dates)
        else:
            date_filter = 'Tous'
    
    with col_f3:
        if 'TENSION' in df_central.columns:
            tensions = ['Tous'] + sorted(df_central['TENSION'].dropna().unique().tolist())
            tension_filter = st.selectbox("Filtrer par TENSION", tensions)
        else:
            tension_filter = 'Tous'
    
    # Appliquer filtres
    df_filtered = df_central.copy()
    
    if uc_filter != 'Tous':
        df_filtered = df_filtered[df_filtered['UC'] == uc_filter]
    if date_filter != 'Tous':
        df_filtered = df_filtered[df_filtered['DATE'] == date_filter]
    if tension_filter != 'Tous':
        df_filtered = df_filtered[df_filtered['TENSION'] == tension_filter]
    
    st.markdown(f"### 📋 Données ({len(df_filtered)} ligne(s))")
    
    # Éditeur
    edited_df = st.data_editor(
        df_filtered[COLONNES_BASE_CENTRALE],
        use_container_width=True,
        num_rows="dynamic",
        height=500,
        key="editor_central"
    )
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
            # Mettre à jour la base centrale
            for idx in edited_df.index:
                if idx in st.session_state.df_central.index:
                    st.session_state.df_central.loc[idx, COLONNES_BASE_CENTRALE] = edited_df.loc[idx, COLONNES_BASE_CENTRALE]
            
            # Ajouter les nouvelles lignes
            nouvelles_lignes = edited_df[~edited_df.index.isin(st.session_state.df_central.index)]
            if len(nouvelles_lignes) > 0:
                st.session_state.df_central = pd.concat([st.session_state.df_central, nouvelles_lignes], ignore_index=True)
            
            save_central(st.session_state.df_central)
            st.success("✅ Base centrale sauvegardée !")
            st.rerun()
    
    with col2:
        # Export Excel
        output = io.BytesIO()
        df_filtered[COLONNES_BASE_CENTRALE].fillna('').to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        st.download_button(
            "📥 Exporter Excel",
            data=output,
            file_name=f"Base_Centrale_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col3:
        if st.button("🔄 Actualiser", use_container_width=True):
            st.rerun()

elif page == "📋 Non Enregistrées":
    st.markdown("## 📋 Lignes Non Enregistrées")
    st.markdown("---")
    
    st.info("""
    📌 **Cette vue affiche** :
    - Les lignes présentes dans les fichiers de factures
    - MAIS non enregistrées dans la base centrale
    
    💡 Fonctionnalité disponible après import des factures.
    """)
    
    st.warning("⚠️ Cette fonctionnalité sera implémentée dans une prochaine version.")
    st.markdown("Pour le moment, vous pouvez :")
    st.markdown("1. Importer vos factures BT/HT")
    st.markdown("2. Vérifier la base centrale")
    st.markdown("3. Ajouter manuellement les lignes manquantes dans 'Base Centrale'")

elif page == "🔄 Import Factures BT":
    page_import_bt()

elif page == "🔄 Import Factures HT":
    page_import_ht()

elif page == "📈 Statistiques":
    st.markdown("## 📈 Statistiques et Évolution")
    st.markdown("---")
    
    df_central = st.session_state.df_central
    
    if 'DATE' not in df_central.columns or df_central['DATE'].isna().all():
        st.warning("⚠️ Aucune période enregistrée. Importez d'abord des factures.")
    else:
        periodes_brutes = sorted(df_central['DATE'].dropna().unique().tolist())
        
        if len(periodes_brutes) == 0:
            st.warning("⚠️ Aucune donnée disponible.")
        else:
            st.success(f"✅ {len(periodes_brutes)} période(s) disponible(s)")
            
            # Filtres
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                if 'SITES' in df_central.columns:
                    sites = ['Tous'] + sorted(df_central['SITES'].dropna().unique().tolist())
                    site_filter = st.selectbox("🏢 Filtrer par SITE", sites)
                else:
                    site_filter = 'Tous'
            
            with col_f2:
                type_graphique = st.selectbox(
                    "⚡ Type d'analyse",
                    ["📊 Global (BT + HT)", "🔌 Basse Tension uniquement", "⚡ Haute Tension uniquement"]
                )
            
            # Appliquer les filtres
            df_filtered = df_central.copy()
            
            if site_filter != 'Tous':
                df_filtered = df_filtered[df_filtered['SITES'] == site_filter]
            
            if "Basse Tension" in type_graphique:
                df_filtered = df_filtered[df_filtered['TENSION'] == 'BASSE']
            elif "Haute Tension" in type_graphique:
                df_filtered = df_filtered[df_filtered['TENSION'] == 'HAUTE']
            
            # Grouper par DATE
            df_grouped = df_filtered.groupby('DATE').agg({
                'MONTANT': 'sum',
                'CONSO': 'sum'
            }).reset_index()
            
            df_grouped = df_grouped.sort_values('DATE')
            
            st.markdown("---")
            
            # GRAPHIQUE MONTANTS
            st.markdown("### 💰 Évolution des Montants")
            
            fig_montant = go.Figure()
            
            fig_montant.add_trace(go.Scatter(
                x=df_grouped['DATE'],
                y=df_grouped['MONTANT'],
                mode='lines+markers',
                name='Montant',
                line=dict(color='#667eea', width=3),
                marker=dict(size=10, color='#667eea'),
                hovertemplate='<b>%{x}</b><br>Montant: %{y:,.0f} FCFA<extra></extra>'
            ))
            
            fig_montant.update_layout(
                xaxis_title="Période",
                yaxis_title="Montant (FCFA)",
                hovermode='x unified',
                template='plotly_white',
                height=400
            )
            
            st.plotly_chart(fig_montant, use_container_width=True)
            
            # GRAPHIQUE CONSOMMATIONS
            st.markdown("### ⚡ Évolution des Consommations")
            
            fig_conso = go.Figure()
            
            fig_conso.add_trace(go.Scatter(
                x=df_grouped['DATE'],
                y=df_grouped['CONSO'],
                mode='lines+markers',
                name='Consommation',
                line=dict(color='#f5576c', width=3),
                marker=dict(size=10, color='#f5576c'),
                hovertemplate='<b>%{x}</b><br>Conso: %{y:,.0f} kWh<extra></extra>'
            ))
            
            fig_conso.update_layout(
                xaxis_title="Période",
                yaxis_title="Consommation (kWh)",
                hovermode='x unified',
                template='plotly_white',
                height=400
            )
            
            st.plotly_chart(fig_conso, use_container_width=True)

elif page == "⚙️ Génération Fichiers":
    page_generation_fichiers()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; color: #666;'>
    <p><strong>Système de traitement des factures CIE</strong> - Version 3.0</p>
</div>
""", unsafe_allow_html=True)
