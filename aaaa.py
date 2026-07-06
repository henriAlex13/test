# DEBUG TEMPORAIRE
st.write("### DEBUG BORDEREAU")
st.write("Colonnes:", list(df_central.columns))
st.write("NUM_BORDEREAU présent:", 'NUM_BORDEREAU' in df_central.columns)
if 'NUM_BORDEREAU' in df_central.columns:
    st.write("Valeurs uniques NUM_BORDEREAU:", df_central['NUM_BORDEREAU'].unique())
    st.write("Période sélectionnée:", periode_bt)
    st.write("Tensions disponibles:", df_central['TENSION'].unique())
    df_debug = df_central[df_central['DATE'] == periode_bt][['IDENTIFIANT', 'DATE', 'TENSION', 'NUM_BORDEREAU']]
    st.write("Lignes pour cette période:", df_debug)
