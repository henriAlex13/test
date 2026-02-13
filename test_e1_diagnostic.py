"""
DIAGNOSTIC COMPLET E1
=====================
Copiez ce code dans un fichier test_e1.py et exécutez-le pour diagnostiquer
"""

import pandas as pd
import sys

print("="*60)
print("DIAGNOSTIC COMPLET - FACTURES E1")
print("="*60)

# Charger la base centrale
try:
    df = pd.read_excel("Base_Centrale.xlsx")
    print(f"\n✅ Base centrale chargée : {len(df)} lignes")
except Exception as e:
    print(f"\n❌ Erreur chargement Base_Centrale.xlsx : {e}")
    sys.exit(1)

# Vérifier les colonnes
print(f"\n📋 Colonnes présentes :")
for col in df.columns:
    print(f"  - {col}")

# Demander la période à analyser
print("\n" + "="*60)
periode = input("Entrez la période à analyser (ex: 03/2025) : ").strip()

if not periode:
    print("❌ Période non fournie")
    sys.exit(1)

print(f"\n🔍 ANALYSE DE LA PÉRIODE : {periode}")
print("="*60)

# Filtrer par période et HT
df_ht_periode = df[
    (df['DATE'] == periode) & 
    (df['TENSION'] == 'HAUTE')
].copy()

print(f"\n1️⃣ LIGNES HT POUR {periode} : {len(df_ht_periode)}")

if len(df_ht_periode) == 0:
    print("   ⚠️ Aucune ligne HT trouvée pour cette période")
    sys.exit(0)

# Afficher les lignes
print(f"\n📊 DÉTAIL DES LIGNES :")
for idx, row in df_ht_periode.iterrows():
    identifiant = row.get('IDENTIFIANT', 'N/A')
    montant = row.get('MONTANT', 0)
    date_comp = row.get('DATE_COMPLEMENTAIRE', '')
    sites = row.get('SITES', 'N/A')
    
    type_facture = "E0"
    if montant < 0:
        type_facture = "E5 (avoir)"
    elif pd.notna(date_comp) and date_comp != '':
        type_facture = f"E1 (→ {date_comp})"
    
    print(f"\n   Ligne {idx}:")
    print(f"   - IDENTIFIANT : {identifiant}")
    print(f"   - SITES : {sites}")
    print(f"   - DATE : {row.get('DATE', 'N/A')}")
    print(f"   - MONTANT : {montant:,.0f}")
    print(f"   - DATE_COMPLEMENTAIRE : '{date_comp}'")
    print(f"   - TYPE : {type_facture}")

# Compter les E1
nb_e1 = 0
if 'DATE_COMPLEMENTAIRE' in df_ht_periode.columns:
    nb_e1 = (df_ht_periode['DATE_COMPLEMENTAIRE'].notna() & 
             (df_ht_periode['DATE_COMPLEMENTAIRE'] != '')).sum()

print(f"\n2️⃣ NOMBRE DE E1 DÉTECTÉES : {nb_e1}")

# Chercher les doublons
print(f"\n3️⃣ VÉRIFICATION DOUBLONS :")
doublons = df_ht_periode.groupby('IDENTIFIANT').size()
sites_avec_doublons = doublons[doublons > 1]

if len(sites_avec_doublons) > 0:
    print(f"   ✅ {len(sites_avec_doublons)} site(s) avec plusieurs lignes (normal si E0+E1) :")
    for ident, count in sites_avec_doublons.items():
        print(f"   - {ident} : {count} ligne(s)")
        
        # Détail de ce site
        lignes_site = df_ht_periode[df_ht_periode['IDENTIFIANT'] == ident]
        for _, row in lignes_site.iterrows():
            date_comp = row.get('DATE_COMPLEMENTAIRE', '')
            type_f = "E0" if not date_comp or date_comp == '' else f"E1 (→ {date_comp})"
            print(f"     * {type_f} : {row.get('MONTANT', 0):,.0f} FCFA")
else:
    print(f"   ⚠️ Aucun site avec plusieurs lignes")
    print(f"   → Si vous avez importé des E1, elles ont peut-être été supprimées par erreur")

# Tester la fonction generer_piece_comptable
print(f"\n4️⃣ TEST GÉNÉRATION PIÈCE COMPTABLE :")

try:
    from models import generer_piece_comptable
    
    piece = generer_piece_comptable(df, periode, tension='HAUTE')
    
    print(f"   ✅ Pièce générée : {len(piece)} ligne(s)")
    
    if len(piece) == 0:
        print(f"   ❌ PROBLÈME : Pièce vide !")
    else:
        print(f"\n   📋 DÉTAIL DES LIGNES DE LA PIÈCE :")
        for idx, row in piece.iterrows():
            libelle = row.get('LIBELLE COMPLEMENTAIRE', '')
            montant = row.get('MONTANT', 0)
            
            est_e1 = 'COMPLEMENTAIRE' in libelle
            type_ligne = "E1 ✨" if est_e1 else "E0"
            
            print(f"   Ligne {idx} [{type_ligne}]:")
            print(f"   - MONTANT : {montant:,.0f} FCFA")
            print(f"   - LIBELLÉ : {libelle[:80]}...")
        
        # Vérifier les E1
        nb_e1_piece = piece['LIBELLE COMPLEMENTAIRE'].str.contains('COMPLEMENTAIRE', na=False).sum()
        print(f"\n   🔍 Nombre de E1 dans la pièce : {nb_e1_piece}")
        
        if nb_e1 > 0 and nb_e1_piece == 0:
            print(f"   ❌ PROBLÈME : {nb_e1} E1 dans la base mais 0 dans la pièce !")
        elif nb_e1_piece == nb_e1:
            print(f"   ✅ OK : Toutes les E1 sont dans la pièce")
        
except Exception as e:
    print(f"   ❌ Erreur lors de la génération : {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("FIN DU DIAGNOSTIC")
print("="*60)
print("\n💡 Envoyez la sortie complète de ce script pour analyse")
