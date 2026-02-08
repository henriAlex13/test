import os
import re
import logging
import fitz  # PyMuPDF
import pandas as pd
from datetime import datetime, timedelta
import shutil
import locale

# Configure locale
locale.setlocale(locale.LC_TIME, 'French_France')

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("process_swift.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Chemins configurables
# MX103_PATH = 'Y:/'
# MT910_PATH = 'Z:/SWIFT_SGCI'
# OUTPUT_PATH = 'Y:/TRAITEMENT_MX_MT910'

MX103_PATH = 'C:/Users/5368/Documents/DONNEES_D/ALEX_l/SWIFT/new/mx'
MT910_PATH = 'C:/Users/5368/Documents/DONNEES_D/ALEX_l/SWIFT/new/mt'
OUTPUT_PATH = 'C:/Users/5368/Documents/DONNEES_D/ALEX_l/SWIFT/new'

# Fichiers CSV pour stockage
CSV_DIR = os.path.join(OUTPUT_PATH, "csv_data")
MX103_CSV = os.path.join(CSV_DIR, "mx103_files.csv")
MT910_CSV = os.path.join(CSV_DIR, "mt910_files.csv")
MATCHES_CSV = os.path.join(CSV_DIR, "matches.csv")
COPIED_LOG_CSV = os.path.join(CSV_DIR, "copied_files_log.csv")

MATCHED_DIR = os.path.join(OUTPUT_PATH, "MATCH")
PAS_MATCH_DIR = os.path.join(OUTPUT_PATH, "PAS_MATCH")

# --- Gestion CSV ---

def init_csv_files():
    """Initialise les fichiers CSV s'ils n'existent pas"""
    os.makedirs(CSV_DIR, exist_ok=True)
    
    if not os.path.exists(MX103_CSV):
        pd.DataFrame(columns=['filename', 'filepath', 'cle_32A', 'adresse_debtor', 'date', 'montant']).to_csv(MX103_CSV, index=False)
    
    if not os.path.exists(MT910_CSV):
        pd.DataFrame(columns=['filename', 'filepath', 'cle_32A', 'texte_72', 'date', 'montant']).to_csv(MT910_CSV, index=False)
    
    if not os.path.exists(MATCHES_CSV):
        pd.DataFrame(columns=['match_id', 'cle_32A', 'filename_mx', 'filename_mt', 'date_mx', 'date_mt']).to_csv(MATCHES_CSV, index=False)
    
    if not os.path.exists(COPIED_LOG_CSV):
        pd.DataFrame(columns=['filepath', 'copied_at']).to_csv(COPIED_LOG_CSV, index=False)

def load_csv(csv_path):
    """Charge un fichier CSV"""
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        return pd.read_csv(csv_path)
    return pd.DataFrame()

def save_csv(df, csv_path):
    """Sauvegarde un DataFrame en CSV"""
    df.to_csv(csv_path, index=False)

def load_copied_files_log():
    """Charge la liste des fichiers déjà copiés"""
    df = load_csv(COPIED_LOG_CSV)
    return set(df['filepath'].tolist()) if not df.empty else set()

def append_to_copied_files_log(filepath):
    """Ajoute un fichier au log des fichiers copiés"""
    df = load_csv(COPIED_LOG_CSV)
    new_row = pd.DataFrame([{'filepath': filepath, 'copied_at': datetime.now().isoformat()}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.drop_duplicates(subset=['filepath'], keep='last', inplace=True)
    save_csv(df, COPIED_LOG_CSV)

# --- Extraction des infos depuis PDF ---

def extract_text_from_pdf(filename, max_pages=2):
    """Extrait le texte d'un fichier PDF"""
    try:
        doc = fitz.open(filename)
        num_pages = min(doc.page_count, max_pages)
        text = ""
        for i in range(num_pages):
            page_text = doc.load_page(i).get_text()
            if page_text:
                text += page_text
        if not text.strip():
            logger.warning(f"Fichier {filename} est vide (texte extrait vide).")
            return None
        return text
    except Exception as e:
        logger.error(f"Erreur ouverture fichier {filename}: {e}")
        return None

def safe_extract(func):
    """Wrapper pour extraction sécurisée"""
    try:
        return func()
    except Exception:
        return ""

def extract_mx103_info(filename):
    """Extrait les informations d'un fichier MX103/PACS.008"""
    text = extract_text_from_pdf(filename)
    if not text:
        return None

    try:
        montant = safe_extract(lambda: text.split("#")[1].strip())
        date_str = safe_extract(lambda: text.split("#")[2].split("InterbankSettlementDate:")[1].split("\n")[0].strip())
        date_formatted = date_str.replace('-', '')[2:] if date_str else ""
        adresse_debtor = safe_extract(lambda: text.split("Debtor")[1].split("\n")[1].split("Name:")[1].strip().replace(" ", ""))

        champ_32A = ""
        if date_formatted and montant:
            # Nettoyer le montant
            montant_clean = montant.replace('.', '').replace(',', '').strip()
            champ_32A = date_formatted + montant_clean

        return {
            "filename": os.path.basename(filename),
            "filepath": filename,
            "cle_32A": str(champ_32A).strip(),  # Forcer en string et strip
            "adresse_debtor": str(adresse_debtor).strip(),
            "date": str(date_formatted).strip(),
            "montant": str(montant).strip()
        }
    except Exception as e:
        logger.error(f"Erreur extraction MX103 dans {filename}: {e}")
        return None

def extract_mt910_info(filename):
    """Extrait les informations d'un fichier MT910"""
    text = extract_text_from_pdf(filename, max_pages=1)
    if not text:
        return None

    champ_32A, date, montant, champ_72 = "", "", "", ""

    try:
        if "32A:" in text:
            bloc_32A = text.split("32A:")[1].split("\n")[1:4]
            bloc_32A_clean = [e.replace(" ", "") for e in bloc_32A]

            date = next((s.replace("#", "").replace("Date:", "") for s in bloc_32A_clean if "Date:" in s), "")
            date = str(date).strip()
            
            # Validation du format de date
            if date and len(date) != 6:
                logger.warning(f"Format date invalide dans {filename}: {date}")
                date = ""
            
            montant = next((s.replace("#", "").replace("Amount:", "").replace(',', '') for s in bloc_32A_clean if "Amount:" in s), "")

            chiffres = ''.join(re.findall(r'\d+', ''.join(bloc_32A)))
            champ_32A = chiffres
    except Exception as e:
        logger.error(f"Erreur extraction bloc 32A dans {filename}: {e}")

    try:
        if "72:" in text:
            partie_72 = text.split("72:")[1]
            if "Receiver Information" in partie_72:
                partie_72 = partie_72.split("Receiver Information")[1]
            if "----------------" in partie_72:
                partie_72 = partie_72.split("----------------")[0]
            champ_72 = re.sub(r"\s+", "", partie_72)
    except Exception as e:
        logger.error(f"Erreur extraction bloc 72 dans {filename}: {e}")

    return {
        "filename": os.path.basename(filename),
        "filepath": filename,
        "cle_32A": str(champ_32A).strip(),  # Forcer en string et strip
        "texte_72": str(champ_72).strip(),
        "date": str(date).strip(),
        "montant": str(montant).strip()
    }

# --- Traitement des fichiers ---

def process_files(input_path, extract_func, csv_path, subdirs_filter, date_min="1125"):
    """Traite les fichiers et met à jour le CSV - filtré par date minimale"""
    df_exist = load_csv(csv_path)
    fichiers_traites = set(df_exist['filename']) if not df_exist.empty else set()
    
    new_data = []
    
    for root, dirs, files in os.walk(input_path):
        root_low = root.lower()
        
        # Vérifier si tous les filtres de sous-répertoires sont présents
        if all(filt.lower() in root_low for filt in subdirs_filter):
            
            # Extraire MMAA du chemin (format attendu: .../MMAA/JJMMAA/...)
            path_parts = root.split(os.sep)
            mmaa_folder = None
            
            # Chercher un dossier au format MMAA (4 chiffres)
            for part in path_parts:
                if len(part) == 4 and part.isdigit():
                    mmaa_folder = part
                    break
            
            # Filtrer par date
            if mmaa_folder and mmaa_folder >= date_min:
                for file in files:
                    if file.lower().endswith('.pdf') and file not in fichiers_traites:
                        full_path = os.path.join(root, file)
                        info = extract_func(full_path)
                        if info:
                            new_data.append(info)
            elif mmaa_folder:
                logger.debug(f"Dossier {mmaa_folder} ignoré (< {date_min})")
    
    if new_data:
        df_new = pd.DataFrame(new_data)
        df_combined = pd.concat([df_exist, df_new], ignore_index=True)
        df_combined.drop_duplicates(subset=['filename'], keep='last', inplace=True)
        save_csv(df_combined, csv_path)
        logger.info(f"Ajouté {len(new_data)} nouveaux fichiers dans {csv_path} (à partir de {date_min})")
    else:
        logger.info(f"Aucun nouveau fichier pour {csv_path} (à partir de {date_min})")

# --- Matching ---

def match_data():
    """Effectue le matching entre MX103 et MT910"""
    df_mx = load_csv(MX103_CSV)
    df_mt = load_csv(MT910_CSV)
    
    if df_mx.empty or df_mt.empty:
        logger.info("Aucune donnée pour le matching")
        return pd.DataFrame()
    
    # Nettoyage des clés 32A
    df_mx['cle_32A'] = df_mx['cle_32A'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df_mt['cle_32A'] = df_mt['cle_32A'].astype(str).str.replace('.0', '', regex=False).str.strip()
    
    # Nettoyage des champs de comparaison
    df_mx['adresse_debtor'] = df_mx['adresse_debtor'].astype(str).str.strip()
    df_mt['texte_72'] = df_mt['texte_72'].astype(str).str.strip()
    
    # Log pour debug
    logger.info(f"Nombre de MX103: {len(df_mx)}, Nombre de MT910: {len(df_mt)}")
    logger.info(f"Exemples cle_32A MX: {df_mx['cle_32A'].head(3).tolist()}")
    logger.info(f"Exemples cle_32A MT: {df_mt['cle_32A'].head(3).tolist()}")
    
    # Merge sur cle_32A
    df_match = pd.merge(df_mx, df_mt, on='cle_32A', suffixes=('_mx', '_mt'))
    logger.info(f"Après merge sur cle_32A: {len(df_match)} correspondances")
    
    # Filtre sur adresse_debtor dans texte_72
    def check_debtor_in_text(row):
        debtor = str(row['adresse_debtor']).lower().strip()
        texte = str(row['texte_72']).lower().strip()
        
        # Éviter les correspondances vides
        if not debtor or debtor == 'nan' or not texte or texte == 'nan':
            return False
        
        result = debtor in texte
        
        # Log pour debug (seulement quelques exemples)
        if not result and len(debtor) > 3:
            logger.debug(f"Pas de match - Debtor: {debtor[:20]}, Texte: {texte[:50]}")
        
        return result
    
    df_match = df_match[df_match.apply(check_debtor_in_text, axis=1)]
    logger.info(f"Après filtre debtor: {len(df_match)} correspondances")
    
    if df_match.empty:
        logger.warning("Aucune correspondance trouvée après filtrage")
        return df_match
    
    # Ajouter match_id
    df_match = df_match.reset_index(drop=True)
    df_match.insert(0, 'match_id', df_match.index + 1)
    
    # Sélectionner colonnes pertinentes
    df_match = df_match[['match_id', 'cle_32A', 'filename_mx', 'filename_mt', 'date_mx', 'date_mt']]
    
    # Sauvegarder matches (avec gestion des doublons)
    df_existing_matches = load_csv(MATCHES_CSV)
    df_combined_matches = pd.concat([df_existing_matches, df_match], ignore_index=True)
    df_combined_matches.drop_duplicates(subset=['cle_32A', 'filename_mx', 'filename_mt'], keep='last', inplace=True)
    save_csv(df_combined_matches, MATCHES_CSV)
    
    logger.info(f"Total matches sauvegardés: {len(df_combined_matches)}")
    
    return df_match

# --- Fonction de diagnostic ---

def diagnostic_matching():
    """Diagnostic des problèmes de matching"""
    df_mx = load_csv(MX103_CSV)
    df_mt = load_csv(MT910_CSV)
    
    print(f"\n=== DIAGNOSTIC MATCHING ===")
    print(f"Total MX103: {len(df_mx)}")
    print(f"Total MT910: {len(df_mt)}")
    
    print(f"\nTypes de données MX103:")
    print(df_mx.dtypes)
    
    print(f"\nTypes de données MT910:")
    print(df_mt.dtypes)
    
    print(f"\nExemples cle_32A MX103:")
    print(df_mx[['filename', 'cle_32A']].head(10))
    
    print(f"\nExemples cle_32A MT910:")
    print(df_mt[['filename', 'cle_32A']].head(10))
    
    # Chercher les clés communes
    cles_mx = set(df_mx['cle_32A'].astype(str).str.strip())
    cles_mt = set(df_mt['cle_32A'].astype(str).str.strip())
    
    print(f"\nClés uniques MX103: {len(cles_mx)}")
    print(f"Clés uniques MT910: {len(cles_mt)}")
    print(f"Clés communes: {len(cles_mx & cles_mt)}")
    
    if cles_mx & cles_mt:
        print(f"\nExemples de clés communes: {list(cles_mx & cles_mt)[:5]}")
    else:
        print("\nAUCUNE clé commune trouvée!")
        print("\nPremières clés MX103:", list(cles_mx)[:5])
        print("Premières clés MT910:", list(cles_mt)[:5])

# --- Gestion des fichiers ---

def construire_arborescence(date_str):
    """Construit l'arborescence MMAA/JJMMAA"""
    date_str = str(date_str).rstrip('.0')
    if len(date_str) != 6:
        return None, None
    yy, mm, dd = date_str[:2], date_str[2:4], date_str[4:6]
    return mm + yy, dd + mm + yy

def copier_fichier(filename, date_str, dossier_source, dossier_cible, sous_dossier_type='', prefix="", copied_files=None):
    """Copie un fichier vers la destination avec arborescence"""
    MMAA, JJMMAA = construire_arborescence(date_str)
    if not MMAA or not JJMMAA:
        logger.warning(f"Date invalide pour {filename}: {date_str}")
        return False

    dest_dir = os.path.join(dossier_cible, sous_dossier_type, MMAA, JJMMAA)
    os.makedirs(dest_dir, exist_ok=True)

    nom_dest = f"{prefix}{filename}"
    dest_file = os.path.join(dest_dir, nom_dest)

    # Vérifier si déjà copié
    if copied_files is not None and dest_file in copied_files:
        return True

    if os.path.exists(dest_file):
        if copied_files is not None:
            copied_files.add(dest_file)
        return True

    # Chercher fichier source
    chemin_source = None
    for root, dirs, files in os.walk(dossier_source):
        if filename in files:
            chemin_source = os.path.join(root, filename)
            break

    if chemin_source and os.path.exists(chemin_source):
        try:
            shutil.copy2(chemin_source, dest_file)
            logger.info(f"Copié {filename} vers {dest_file}")
            if copied_files is not None:
                copied_files.add(dest_file)
                append_to_copied_files_log(dest_file)
            return True
        except Exception as e:
            logger.error(f"Erreur copie {filename}: {e}")
            return False
    else:
        logger.warning(f"Fichier source introuvable: {filename}")
        return False

def copy_matched_files(df_match, copied_files):
    """Copie les fichiers matchés"""
    if df_match.empty:
        logger.info("Aucun fichier à copier (matching vide)")
        return

    os.makedirs(MATCHED_DIR, exist_ok=True)

    for _, row in df_match.iterrows():
        prefix = f"{row['match_id']}_"
        copier_fichier(row['filename_mx'], row['date_mx'], MX103_PATH, MATCHED_DIR, '', prefix, copied_files)
        copier_fichier(row['filename_mt'], row['date_mt'], MT910_PATH, MATCHED_DIR, '', prefix, copied_files)

def gerer_fichiers_pas_matches(csv_path, df_matches, dossier_source, dossier_pas_match, sous_dossier_type, copied_files, days_threshold=10):
    """Gère les fichiers non matchés"""
    df_complet = load_csv(csv_path)
    
    if df_complet.empty:
        logger.info(f"Aucun fichier dans {csv_path}")
        return
    
    # Identifier fichiers non matchés
    if sous_dossier_type == "MX":
        fichiers_match = set(df_matches['filename_mx']) if not df_matches.empty else set()
    elif sous_dossier_type == "MT":
        fichiers_match = set(df_matches['filename_mt']) if not df_matches.empty else set()
    else:
        logger.error("Sous dossier type invalide")
        return

    data_pas_match = df_complet[~df_complet['filename'].isin(fichiers_match)]

    if data_pas_match.empty:
        logger.info(f"Aucun fichier pas matché pour {sous_dossier_type}")
        return

    now = datetime.now()

    for _, row in data_pas_match.iterrows():
        date_str = str(row['date']).rstrip('.0')
        if len(date_str) != 6:
            continue
        
        try:
            date_obj = datetime.strptime(date_str, "%y%m%d")
        except Exception as e:
            logger.warning(f"Date invalide pour {row['filename']}: {date_str}")
            continue

        age = now - date_obj
        if age > timedelta(days=days_threshold):
            copier_fichier(row['filename'], date_str, dossier_source, dossier_pas_match, sous_dossier_type, '', copied_files)

def main():
    """Fonction principale"""
    logger.info(f"Démarrage du traitement {datetime.now()}")
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    
    # Initialiser CSV
    init_csv_files()
    
    # Charger log des fichiers copiés
    copied_files = load_copied_files_log()

    # Traiter MX103/PACS.008 - chemin 1 : manu/sgci
    process_files(
        input_path=MX103_PATH,
        extract_func=extract_mx103_info,
        csv_path=MX103_CSV,
        subdirs_filter=["entrant", "pacs.008", "manu", "sgci"]
    )
    
    # Traiter MX103/PACS.008 - chemin 2 : auto
    process_files(
        input_path=MX103_PATH,
        extract_func=extract_mx103_info,
        csv_path=MX103_CSV,
        subdirs_filter=["entrant", "pacs.008", "auto"]
    )
    
    # Traiter MT910
    process_files(
        input_path=MT910_PATH,
        extract_func=extract_mt910_info,
        csv_path=MT910_CSV,
        subdirs_filter=["entrant", "mt910"]
    )

    # Lancer le diagnostic (optionnel, commenter après debug)
    # diagnostic_matching()

    # Matching
    df_match = match_data()
    logger.info(f"Matching terminé: {len(df_match)} paires trouvées")

    # Copier fichiers matchés
    if not df_match.empty:
        copy_matched_files(df_match, copied_files)
        gerer_fichiers_pas_matches(MX103_CSV, df_match, MX103_PATH, PAS_MATCH_DIR, 'MX', copied_files)
        gerer_fichiers_pas_matches(MT910_CSV, df_match, MT910_PATH, PAS_MATCH_DIR, 'MT', copied_files)
    else:
        logger.info("Pas de fichiers matchés")
        gerer_fichiers_pas_matches(MX103_CSV, pd.DataFrame(columns=['filename_mx']), MX103_PATH, PAS_MATCH_DIR, 'MX', copied_files)
        gerer_fichiers_pas_matches(MT910_CSV, pd.DataFrame(columns=['filename_mt']), MT910_PATH, PAS_MATCH_DIR, 'MT', copied_files)

    logger.info(f"Fin du traitement {datetime.now()}")

if __name__ == "__main__":
    main()
