"""
CODE CORRIGÉ POUR LA SAUVEGARDE - À REMPLACER DANS APP.PY
==========================================================

Cherche cette section dans app.py (ligne ~200-220) :

    with col1:
        if st.button("💾 Sauvegarder modifications", type="primary", use_container_width=True):
            try:
                # Mettre à jour les lignes modifiées
                ...

REMPLACE TOUT LE BLOC par ce code ci-dessous :
"""

    with col1:
        if st.button("💾 Sauvegarder modifications", type="primary", use_container_width=True):
            try:
                # ✨ ÉTAPE 1 : Détecter les lignes SUPPRIMÉES
                # Les lignes présentes dans df_filtered mais absentes de edited_df ont été supprimées
                indices_avant = set(df_filtered.index)
                indices_apres = set(edited_df.index)
                indices_supprimes = indices_avant - indices_apres
                
                if len(indices_supprimes) > 0:
                    # Supprimer ces lignes de la base centrale
                    st.session_state.df_central = st.session_state.df_central.drop(indices_supprimes)
                    st.session_state.df_central = st.session_state.df_central.reset_index(drop=True)
                    st.success(f"🗑️ {len(indices_supprimes)} ligne(s) supprimée(s)")
                
                # ✨ ÉTAPE 2 : Mettre à jour les lignes MODIFIÉES
                for idx in edited_df.index:
                    if idx in st.session_state.df_central.index:
                        st.session_state.df_central.loc[idx, COLONNES_BASE_CENTRALE] = edited_df.loc[idx, COLONNES_BASE_CENTRALE]
                
                # ✨ ÉTAPE 3 : Ajouter les lignes NOUVELLES
                nouvelles_lignes = edited_df[~edited_df.index.isin(df_filtered.index)]
                if len(nouvelles_lignes) > 0:
                    st.session_state.df_central = pd.concat([st.session_state.df_central, nouvelles_lignes], ignore_index=True)
                    st.success(f"➕ {len(nouvelles_lignes)} ligne(s) ajoutée(s)")
                
                # ✨ ÉTAPE 4 : Sauvegarder
                save_central(st.session_state.df_central)
                st.success("✅ Base centrale sauvegardée !")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur lors de la sauvegarde : {str(e)}")
                st.warning("⚠️ Les modifications sont conservées en mémoire mais non sauvegardées sur disque.")
                st.info("💡 Essayez d'exporter en Excel pour ne pas perdre vos données.")


"""
EXPLICATION
===========

Le data_editor de Streamlit permet de :
- ✅ Ajouter des lignes (bouton +)
- ✅ Modifier des cellules
- ✅ Supprimer des lignes (bouton poubelle)

AVANT : Le code détectait seulement les ajouts et modifications
APRÈS : Le code détecte aussi les suppressions en comparant les index

ÉTAPE 1 : Détecter suppressions
    indices_avant = {0, 1, 2, 3, 4}  # df_filtered
    indices_apres = {0, 1, 3, 4}     # edited_df (ligne 2 supprimée)
    indices_supprimes = {2}           # différence

ÉTAPE 2 : Mettre à jour modifications (comme avant)

ÉTAPE 3 : Ajouter nouvelles lignes (comme avant)

ÉTAPE 4 : Sauvegarder tout (comme avant)

Maintenant quand tu supprimes une ligne avec le bouton poubelle ️🗑️
et que tu cliques sur Sauvegarder, la ligne est vraiment supprimée ! ✅
"""
