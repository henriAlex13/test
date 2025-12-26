"""
Surveillance automatique simple pour traitement SWIFT
Détecte 2 fichiers TXT et lance le traitement automatiquement

Auteur: Alex - SGCI
"""

import pandas as pd
import numpy as np
import glob
import os
from sklearn.feature_extraction import text
import re
import unicodedata
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import warnings
warnings.filterwarnings("ignore")


# ============================================================================
# VOS FONCTIONS DE TRAITEMENT (CODE ORIGINAL)
# ============================================================================

def remove_accent_from_text(text):
    text = text.encode("utf-8").decode("utf-8")
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore")
    text = text.decode("utf-8")
    return str(text)


def tokenize_by_alex(texte):
    tokens = re.findall(r"\w+|[^\w\s]", texte, re.UNICODE)
    return tokens


def open_and_convert_file(files_to_open, cle):
    df_loop = pd.DataFrame()
    df_final = pd.DataFrame()
    df_temporary = []

    for filename in files_to_open:
        if cle in remove_accent_from_text(filename).lower():
            initial_file = open(filename, 'r')
            temp_file = initial_file.readlines()
            temp_file = [i.replace("\n", " ") for i in temp_file]
            temp_file = [''.join(temp_file[:])]
            temp_file = str(temp_file)
            temp_file = temp_file.split('$')
            df_loop = pd.DataFrame(temp_file, columns=['Data'])
            df_loop['filename'] = os.path.basename(filename)
            df_temporary.append(df_loop)
    
    df_final = pd.concat(df_temporary, axis=0)
    df_final.reset_index(drop=True, inplace=True)
    return df_final


def get_message_field(df, column_name, first_tag, last_tag='}{'):
    df[column_name] = df['Data'].apply(lambda x: x.split(first_tag, 1).pop(-1))
    df[column_name] = df[column_name].apply(lambda x: x.split(last_tag).pop(0))
    return df


def get_BIC_code(name):
    Regex_1 = re.compile(r'[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{4,4}){0,1}')
    Regex_result_1 = re.search(Regex_1, name)
    BIC_CODE = Regex_result_1.group()
    i = 8
    BIC_CODE = BIC_CODE[:i] + BIC_CODE[i+1:]
    return BIC_CODE


def get_sender(df, function):
    df['SENDER'] = df['Data'].apply(lambda x: x.split('2:', 1).pop(-1))
    df['SENDER'] = df['SENDER'].apply(lambda x: x.split('}{', 1).pop(0))
    df['COUNTRY'] = df['SENDER'].apply(lambda x: x[4:6])
    return df


def get_date(df):
    df["DATE"] = df["BLOCK_2"].str[-11:-5]
    df['DATE'] = df['DATE'].apply(lambda x: '-'.join(x[i:i+2] for i in range(0, len(x), 2)))
    df['DATE'] = pd.to_datetime(df['DATE'], format="%Y/%m/%d", errors='ignore')
    return df


def text_cleaner(df):
    stop = text.ENGLISH_STOP_WORDS
    df['CLEANED_TEXT'] = df['CHAMP 79'].str.lower()
    df['CLEANED_TEXT'] = df['CLEANED_TEXT'].apply(tokenize_by_alex)
    df['CLEANED_TEXT'] = df['CLEANED_TEXT'].apply(lambda x: [word for word in x if word not in (stop)])
    df['CLEANED_TEXT'] = df['CLEANED_TEXT'].apply(lambda x: [word for word in x if word.isalpha()])
    df['CLEANED_TEXT'] = df['CLEANED_TEXT'].str.join(" ")
    return df


def recherche_RFI_sanctions(df, column_name, word_list):
    df_final = df[df[column_name].str.contains(word_list)]
    return df_final


def remove_duplicates_message(df, column):
    df = df.drop_duplicates(subset=[column])
    return df


def merge_sent_and_received_messages(df1, df2, field_1, field_2):
    df1["CHAMP_20_joint"] = df1[field_1]
    df2.insert(0, 'CHAMP_21_joint', df2[field_2])
    df_final = pd.merge(df1, df2, how='left', left_on=['CHAMP_20_joint'], right_on=['CHAMP_21_joint'])
    return df_final


# ============================================================================
# FONCTION DE TRAITEMENT PRINCIPALE
# ============================================================================

def traiter_dossier(dossier_path, words_to_search="Sanc|abc|tio|LEmb"):
    """
    Traite un dossier contenant 2 fichiers TXT (recu et emi)
    """
    print(f"\n{'='*60}")
    print(f"🎯 TRAITEMENT: {dossier_path.name}")
    print(f"{'='*60}")
    
    # Récupérer tous les fichiers TXT
    INTIX_files = [str(f) for f in dossier_path.glob('*.txt')]
    date = dossier_path.name
    
    # Traitement messages reçus
    print("📥 Traitement des messages reçus...")
    MTx99_received = open_and_convert_file(INTIX_files, "recu")
    MTx99_received = get_message_field(MTx99_received, 'BASIC HEADER', '1:')
    MTx99_received = remove_duplicates_message(MTx99_received, 'BASIC HEADER')
    MTx99_received = get_message_field(MTx99_received, 'BLOCK_2', '2:')
    MTx99_received = get_date(MTx99_received)
    MTx99_received = get_sender(MTx99_received, get_BIC_code)
    MTx99_received = get_message_field(MTx99_received, 'CHAMP 20', ':20:', last_tag=':21:')
    MTx99_received = get_message_field(MTx99_received, 'CHAMP 21', ':21:', last_tag=':79:')
    MTx99_received = get_message_field(MTx99_received, 'CHAMP 79', ':79:')
    MTx99_received = text_cleaner(MTx99_received)
    
    RFI_received = recherche_RFI_sanctions(MTx99_received, 'CLEANED_TEXT', words_to_search)
    print(f"   ✓ {len(MTx99_received)} messages reçus, {len(RFI_received)} RFI trouvés")
    
    # Traitement messages émis
    print("📤 Traitement des messages émis...")
    MTx99_sent = open_and_convert_file(INTIX_files, "emi")
    MTx99_sent = get_message_field(MTx99_sent, 'BASIC HEADER', '1:')
    MTx99_sent = remove_duplicates_message(MTx99_sent, 'BASIC HEADER')
    MTx99_sent = get_message_field(MTx99_sent, 'BLOCK_2', '2:')
    MTx99_sent = get_date(MTx99_sent)
    MTx99_sent = get_sender(MTx99_sent, get_BIC_code)
    MTx99_sent = get_message_field(MTx99_sent, 'CHAMP 20', ':20:', last_tag=':21:')
    MTx99_sent = get_message_field(MTx99_sent, 'CHAMP 21', ':21:', last_tag=':79:')
    MTx99_sent = get_message_field(MTx99_sent, 'CHAMP 79', ':79:')
    MTx99_sent = text_cleaner(MTx99_sent)
    print(f"   ✓ {len(MTx99_sent)} messages émis")
    
    # Fusion
    print("🔗 Fusion des données...")
    Final_table = merge_sent_and_received_messages(RFI_received, MTx99_sent, "CHAMP 20", "CHAMP 21")
    
    # Génération Excel
    print("📊 Génération de l'Excel...")
    output_file = dossier_path / f'RFI_FAhd_{date}.xlsx'
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        RFI_received.to_excel(writer, sheet_name='MTx99_received', index=False)
        MTx99_sent.to_excel(writer, sheet_name='MTx99_sent', index=False)
        Final_table.to_excel(writer, sheet_name='Merged_data', index=False)
    
    print(f"✅ Terminé: {output_file.name}")
    print(f"{'='*60}\n")


# ============================================================================
# SURVEILLANCE AVEC WATCHDOG
# ============================================================================

class SurveillanceSimple(FileSystemEventHandler):
    """Surveille et traite quand 2 fichiers TXT sont détectés"""
    
    def __init__(self, dossier_base, words_to_search):
        self.dossier_base = Path(dossier_base)
        self.words_to_search = words_to_search
        self.dossiers_traites = set()  # Pour éviter les doublons
    
    def on_created(self, event):
        """Quand un fichier est créé"""
        if not event.is_directory and event.src_path.endswith('.txt'):
            self.verifier_dossier(Path(event.src_path).parent)
    
    def on_modified(self, event):
        """Quand un fichier est modifié"""
        if not event.is_directory and event.src_path.endswith('.txt'):
            self.verifier_dossier(Path(event.src_path).parent)
    
    def verifier_dossier(self, dossier):
        """Vérifie si le dossier a 2 fichiers TXT et lance le traitement"""
        time.sleep(2)  # Attendre que le fichier soit complètement copié
        
        fichiers_txt = list(dossier.glob('*.txt'))
        
        if len(fichiers_txt) == 2 and str(dossier) not in self.dossiers_traites:
            try:
                traiter_dossier(dossier, self.words_to_search)
                self.dossiers_traites.add(str(dossier))
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    def scanner_initial(self):
        """Scanne les dossiers existants au démarrage"""
        print(f"\n{'='*60}")
        print("🔍 SCAN INITIAL")
        print(f"{'='*60}")
        
        for item in self.dossier_base.rglob('*'):
            if item.is_dir():
                fichiers_txt = list(item.glob('*.txt'))
                if len(fichiers_txt) == 2 and str(item) not in self.dossiers_traites:
                    try:
                        traiter_dossier(item, self.words_to_search)
                        self.dossiers_traites.add(str(item))
                    except Exception as e:
                        print(f"❌ Erreur sur {item.name}: {e}")
        
        print(f"{'='*60}\n")


def demarrer_surveillance(dossier_racine, mots_cles="Sanc|abc|tio|LEmb"):
    """Démarre la surveillance automatique"""
    
    print("\n" + "="*60)
    print("🚀 SURVEILLANCE AUTOMATIQUE SWIFT")
    print("="*60)
    print(f"📂 Dossier: {dossier_racine}")
    print(f"🔍 Mots-clés: {mots_cles}")
    print(f"⏹️  Arrêter: Ctrl+C")
    print("="*60)
    
    gestionnaire = SurveillanceSimple(dossier_racine, mots_cles)
    
    # Scan initial
    gestionnaire.scanner_initial()
    
    # Démarrer la surveillance
    observer = Observer()
    observer.schedule(gestionnaire, dossier_racine, recursive=True)
    observer.start()
    
    print("👀 Surveillance active...\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de la surveillance")
        observer.stop()
    
    observer.join()
    print("✅ Terminé\n")


# ============================================================================
# LANCEMENT
# ============================================================================

if __name__ == "__main__":
    
    # CONFIGURATION
    DOSSIER = r"E:\Décembre 2025"  # ← Modifiez votre chemin ici
    MOTS_CLES = "Sanc|abc|tio|LEmb"
    
    # Lancer
    demarrer_surveillance(DOSSIER, MOTS_CLES)
