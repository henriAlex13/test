import streamlit as st
import pandas as pd
import json
import io
import PyPDF2
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from services.socgenai_models import llm_model, UPLOAD_DIRECTORY
from langchain.schema import HumanMessage, SystemMessage, AIMessage

# Configuration Streamlit
st.set_page_config(
    page_title="Générateur de Personas Marketing",
    page_icon="🎯",
    layout="wide"
)

# CSS personnalisé
st.markdown("""
    <style>
    .header {
        background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .cluster-box {
        border-left: 5px solid #d32f2f;
        padding: 15px;
        background-color: #f5f5f5;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .persona-output {
        background-color: #fafafa;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    .mapping-section {
        background-color: #fff3e0;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #ffb74d;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="header">
        <h1>🎯 Générateur de Personas Marketing</h1>
        <p>Générez automatiquement des descriptions de personas pour chaque segment client</p>
    </div>
""", unsafe_allow_html=True)

# Initialiser la session
if "llm" not in st.session_state:
    st.session_state.llm = None
if "personas" not in st.session_state:
    st.session_state.personas = {}
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "produits_bancaires_text" not in st.session_state:
    st.session_state.produits_bancaires_text = None
if "loaded_segments" not in st.session_state:
    st.session_state.loaded_segments = None
if "column_mapping" not in st.session_state:
    st.session_state.column_mapping = None
if "segments_df" not in st.session_state:
    st.session_state.segments_df = None
if "benchmarks" not in st.session_state:
    st.session_state.benchmarks = {}
if "catalogues_concurrents" not in st.session_state:
    st.session_state.catalogues_concurrents = {}

# Sidebar - Configuration
with st.sidebar:
   
    st.header("📊 Catalogue Produits")
    
    uploaded_excel = st.file_uploader(
        "Charger le fichier Excel du catalogue produits",
        type=["xlsx", "xls"],
        help="Fichier Excel avec colonnes détaillées sur les produits bancaires",
        key="excel_produits"
    )
    
    if uploaded_excel is not None:
        try:
            # Lire le fichier Excel
            df_produits = pd.read_excel(uploaded_excel)
            
            st.success(f"✅ Excel chargé ! ({len(df_produits)} produits)")
            st.info(f"📊 Colonnes détectées: {', '.join(df_produits.columns.tolist())}")
            
            # Aperçu des données
            with st.expander("📊 Aperçu des produits"):
                st.dataframe(df_produits.head(10), use_container_width=True)
            
            # Convertir en texte structuré
            catalogue_text = "CATALOGUE PRODUITS BANCAIRES (DÉTAILLÉ):\n\n"
            
            for idx, row in df_produits.iterrows():
                catalogue_text += f"--- PRODUIT {idx + 1} ---\n"
                for col in df_produits.columns:
                    value = str(row[col])
                    # Nettoyer les valeurs NaN
                    if value.lower() != 'nan':
                        catalogue_text += f"{col}: {value}\n"
                catalogue_text += "\n"
            
            st.session_state.produits_bancaires_text = catalogue_text
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la lecture du fichier Excel: {e}")
            st.info("Vérifiez que le fichier Excel est valide et contient des données")
    
    # Statut du catalogue
    if st.session_state.produits_bancaires_text:
        st.info("✅ Catalogue produits chargé en mémoire")
        if st.button("🗑️ Supprimer le catalogue"):
            st.session_state.produits_bancaires_text = None
            st.rerun()
    else:
        st.warning("⚠️ Aucun catalogue chargé")
        st.caption("Uploadez un fichier Excel avec les informations détaillées sur les produits bancaires")
    
    st.divider()

# Données des segments par défaut
segments_data = [
    {
        "id": 0,
        "name": "Les clients fidèles et hyper-connectés",
        "age": 40,
        "nbProducts": 8,
        "revenueHommes": "100 000 - 200 000 FCFA",
        "revenueFemmes": "100 000 - 200 000 FCFA",
        "mobileAccess": "99%",
        "emailAccess": "85%",
        "characteristics": "Maturité professionnelle, clients de base stable"
    },
    {
        "id": 1,
        "name": "Les racines de confiance",
        "age": 62,
        "nbProducts": 8,
        "revenueHommes": "200 000 - 300 000 FCFA",
        "revenueFemmes": "0 - 100 000 FCFA",
        "mobileAccess": "97%",
        "emailAccess": "57%",
        "characteristics": "Anciens fonctionnaires, revenus constants"
    },
    {
        "id": 2,
        "name": "Les ambassadeurs de demain",
        "age": 36,
        "nbProducts": 3,
        "revenueHommes": "0 - 100 000 FCFA",
        "revenueFemmes": "0 - 100 000 FCFA",
        "mobileAccess": "98%",
        "emailAccess": "60%",
        "characteristics": "En transition professionnelle, hyper-connectés"
    },
    {
        "id": 3,
        "name": "Les champions fonctionnaires",
        "age": 44,
        "nbProducts": 14,
        "revenueHommes": "300 000 - 400 000 FCFA",
        "revenueFemmes": "0 - 100 000 FCFA",
        "mobileAccess": "99%",
        "emailAccess": "88%",
        "characteristics": "Plus grands utilisateurs, hyper-consommateurs"
    },
    {
        "id": 4,
        "name": "Les fidèles discrets",
        "age": 41,
        "nbProducts": 3,
        "revenueHommes": "0 - 100 000 FCFA",
        "revenueFemmes": "0 - 100 000 FCFA",
        "mobileAccess": "98%",
        "emailAccess": "N/A",
        "characteristics": "Employés stables, utilisation minimale"
    }
]

def format_segment_info(segment, column_mapping=None):
    """
    Formate les informations d'un segment de manière flexible
    """
    if column_mapping:
        # Utiliser le mapping personnalisé
        formatted_info = ""
        for key, col_name in column_mapping.items():
            if col_name and col_name in segment:
                value = segment[col_name]
                formatted_info += f"{key}: {value}\n"
        return formatted_info
    else:
        # Format par défaut - afficher toutes les colonnes
        formatted_info = ""
        for key, value in segment.items():
            formatted_info += f"{key}: {value}\n"
        return formatted_info

def create_prompt(segment, column_mapping=None):
    """
    Crée un prompt flexible qui s'adapte à la structure des données
    """
    
    # En-tête du prompt
    base_info = "Génère une description complète et détaillée d'une persona marketing pour un segment bancaire avec les caractéristiques suivantes:\n\n"
    
    # Ajouter toutes les informations du segment de manière flexible
    base_info += format_segment_info(segment, column_mapping)

    if st.session_state.produits_bancaires_text:
        produits_info = f"""

CATALOGUE DES PRODUITS BANCAIRES DISPONIBLES:
{st.session_state.produits_bancaires_text[:10000]}

MÉTHODOLOGIE DE RECOMMANDATION:
Analyse TOUTES les caractéristiques fournies du segment pour recommander les produits les plus adaptés:

1. Identifie les informations démographiques (âge, genre, revenus, etc.)
2. Analyse les comportements bancaires (nombre de produits, types d'opérations, etc.)
3. Évalue la connectivité digitale (accès mobile, email, internet, etc.)
4. Considère les caractéristiques socio-professionnelles
5. Identifie tous les autres attributs pertinents fournis

LOGIQUE DE RECOMMANDATION PRODUITS:
- Matcher les produits avec les BESOINS RÉELS basés sur le catalogue détaillé
- Considérer les segments cibles mentionnés dans le catalogue
- Analyser les caractéristiques produits vs profil segment
- Justifier les recommandations avec des détails spécifiques du catalogue

IMPORTANT:
- NE JAMAIS recommander un produit uniquement parce qu'il est cher ou prestigieux
- TOUJOURS justifier en se basant sur les BESOINS RÉELS du segment
- Considérer le RAPPORT QUALITÉ-PRIX et l'ADÉQUATION aux usages
- Identifier les GAPS (produits manquants malgré le besoin)
- Référencer les détails spécifiques des produits du catalogue
- Ne pas numeroter les produits du catalogue"""
        
        recommendation_note = """

RECOMMANDATIONS DE PRODUITS BANCAIRES :

**A. ANALYSE DES BESOINS**
Basée sur l'analyse complète de TOUTES les caractéristiques du segment, identifie les BESOINS PRIORITAIRES.

**B. PRODUITS RECOMMANDÉS DU CATALOGUE**
Pour CHAQUE produit recommandé, justifie en citant:
 - Les caractéristiques du segment qui le justifient
 - Le besoin spécifique couvert
 - L'adéquation avec le profil complet
 - Le prix exact du catalogue
 - Pourquoi ce produit correspond vs les alternatives

Structure:
- Produits Prioritaires (Haute priorité)
- Produits Complémentaires (Priorité moyenne)
- Produits de Développement (Long terme)"""
    else:
        produits_info = ""
        recommendation_note = """

RECOMMANDATIONS DE PRODUITS BANCAIRES :

**A. PROPOSITION GÉNÉRALE**
Basée sur l'analyse complète de TOUTES les caractéristiques du segment, propose des CATÉGORIES de produits bancaires adaptés. Justifie chaque recommandation.

Note: Aucun catalogue produits chargé, donc pas de proposition spécifique avec prix."""
    
    prompt = base_info + produits_info + """

Fournis une description professionnelle en FRANÇAIS incluant:

1. PROFIL DÉMOGRAPHIQUE DÉTAILLÉ (basé sur les données fournies)
2. COMPORTEMENTS ET PATTERNS BANCAIRES
3. BESOINS ET PRÉFÉRENCES
4. MOTIVATIONS ET PAIN POINTS
5. STRATÉGIE MARKETING RECOMMANDÉE""" + recommendation_note + """

7. PROPOSITION DE VALEUR UNIQUE

Format: Utilise des sections claires avec des titres en gras. Rédige tout en FRANÇAIS.
Adapte ton analyse en fonction de TOUTES les informations disponibles sur le segment."""
    
    return prompt


def generate_persona_pdf(persona_id, persona_content, segment_name):
    """
    Génère un PDF formaté pour un persona
    """
    buffer = io.BytesIO()
    
    # Créer le document PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Style personnalisé pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#d32f2f',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Style pour les sous-titres
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor='#b71c1c',
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Style pour le texte normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=10
    )
    
    # Contenu du PDF
    story = []
    
    # Titre
    story.append(Paragraph(f"PERSONA MARKETING", title_style))
    story.append(Paragraph(f"Cluster {persona_id}: {segment_name}", heading_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Convertir le contenu markdown en paragraphes PDF
    lines = persona_content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.3*cm))
            continue
        
        # Détection des titres (lignes avec **)
        if line.startswith('**') and line.endswith('**'):
            title_text = line.replace('**', '')
            story.append(Paragraph(title_text, heading_style))
        elif line.startswith('###'):
            title_text = line.replace('###', '').strip()
            story.append(Paragraph(title_text, heading_style))
        elif line.startswith('##'):
            title_text = line.replace('##', '').strip()
            story.append(Paragraph(title_text, heading_style))
        elif line.startswith('#'):
            title_text = line.replace('#', '').strip()
            story.append(Paragraph(title_text, heading_style))
        elif line.startswith('- ') or line.startswith('• '):
            # Liste à puces
            text = line[2:].strip()
            story.append(Paragraph(f"• {text}", normal_style))
        else:
            # Texte normal - nettoyer le markdown basique
            text = line.replace('**', '')
            if text:
                story.append(Paragraph(text, normal_style))
    
    # Footer
    story.append(Spacer(1, 1*cm))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor='gray',
        alignment=TA_CENTER
    )
    story.append(Paragraph("Généré par le Générateur de Personas Marketing - Société Générale Côte d'Ivoire", footer_style))
    
    # Générer le PDF
    doc.build(story)
    
    buffer.seek(0)
    return buffer

def generate_benchmark_pdf(benchmark_data):
    """
    Génère un PDF formaté pour un benchmark
    """
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#d32f2f',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor='#b71c1c',
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=10
    )
    
    story = []
    
    # Titre
    story.append(Paragraph("BENCHMARK CONCURRENTIEL", title_style))
    story.append(Paragraph(f"Généré le {benchmark_data['date']}", heading_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Métadonnées
    story.append(Paragraph(f"Banques analysées: {', '.join(benchmark_data['banques'])}", normal_style))
    story.append(Paragraph(f"Catégories: {', '.join(benchmark_data['categories'])}", normal_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Contenu
    lines = benchmark_data['contenu'].split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.3*cm))
            continue
        
        if line.startswith('**') and line.endswith('**'):
            title_text = line.replace('**', '')
            story.append(Paragraph(title_text, heading_style))
        elif line.startswith('###'):
            title_text = line.replace('###', '').strip()
            story.append(Paragraph(title_text, heading_style))
        elif line.startswith('##'):
            title_text = line.replace('##', '').strip()
            story.append(Paragraph(title_text, heading_style))
        elif line.startswith('#'):
            title_text = line.replace('#', '').strip()
            story.append(Paragraph(title_text, heading_style))
        elif line.startswith('- ') or line.startswith('• '):
            text = line[2:].strip()
            story.append(Paragraph(f"• {text}", normal_style))
        else:
            text = line.replace('**', '')
            if text and not text.startswith('|'):  # Skip markdown tables
                story.append(Paragraph(text, normal_style))
    
    # Footer
    story.append(Spacer(1, 1*cm))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor='gray',
        alignment=TA_CENTER
    )
    story.append(Paragraph("Benchmark Concurrentiel - Société Générale Côte d'Ivoire", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_persona(segment, model, column_mapping=None):
    """
    Génère un persona avec les LLM
    """
    st.session_state.llm = llm_model
    
    prompt = create_prompt(segment, column_mapping)
    
    try:
        # Utilisation de invoke avec LangChain
        messages = [HumanMessage(content=prompt)]
        response = st.session_state.llm.invoke(messages)
        
        # Récupérer le contenu de la réponse
        persona_content = response
        
        # Utiliser un identifiant flexible
        segment_id = segment.get("id", segment.get("ID", segment.get("cluster_id", list(segment.values())[0])))
        st.session_state.personas[segment_id] = persona_content
        return persona_content
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la génération: {e}")
        return None

def get_segment_identifier(segment):
    """
    Récupère l'identifiant d'un segment de manière flexible
    """
    # Essayer différentes clés possibles pour l'ID
    for key in ['id', 'ID', 'Id', 'cluster_id', 'segment_id', 'numero', 'number']:
        if key in segment:
            return segment[key]
    
    # Si aucun ID trouvé, utiliser la première valeur
    return list(segment.values())[0] if segment else 0

def get_segment_name(segment):
    """
    Récupère le nom d'un segment de manière flexible
    """
    # Essayer différentes clés possibles pour le nom
    for key in ['name', 'Name', 'nom', 'Nom', 'libelle', 'label', 'segment_name', 'cluster_name']:
        if key in segment:
            return str(segment[key])
    
    # Si aucun nom trouvé, créer un nom générique
    segment_id = get_segment_identifier(segment)
    return f"Segment {segment_id}"

# Onglets principaux
tab1, tab2, tab3, tab4 = st.tabs(["📋 Segments", "🎯 Générer Personas", "📊 Benchmark Concurrentiel", "💬 Chat Intelligent"])

# TAB 1 - SEGMENTS
with tab1:
    st.subheader("Segments Clients Disponibles")
    
    data_source = st.radio(
        "Source de données",
        ["Données par défaut", "Charger un CSV personnalisé"],
        index=0
    )
    
    if data_source == "Charger un CSV personnalisé":
        st.divider()
        st.subheader("📤 Charger vos propres données")
        uploaded_file = st.file_uploader("Chargez un fichier CSV avec vos segments", type="csv")
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.segments_df = df
                st.session_state.loaded_segments = df.to_dict('records')
                
                st.success(f"✅ Fichier chargé avec succès! ({len(df)} segments)")
                st.dataframe(df, use_container_width=True)
                
                # Afficher les colonnes détectées
                st.markdown('<div class="mapping-section">', unsafe_allow_html=True)
                st.write("**📊 Colonnes détectées:**")
                cols_display = st.columns(3)
                for idx, col in enumerate(df.columns):
                    with cols_display[idx % 3]:
                        st.code(col)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.info("✅ Les personas seront générés en utilisant TOUTES les colonnes disponibles de manière automatique.")
                
                current_segments = st.session_state.loaded_segments
                
            except Exception as e:
                st.error(f"❌ Erreur lors du chargement du CSV: {e}")
                current_segments = []
        else:
            if st.session_state.loaded_segments:
                current_segments = st.session_state.loaded_segments
                st.info(f"💡 {len(current_segments)} segments chargés en mémoire")
            else:
                st.info("💡 Veuillez charger un fichier CSV pour continuer")
                current_segments = []
    else:
        current_segments = segments_data
        st.session_state.segments_df = None
    
    if current_segments:
        st.divider()
        st.subheader("Segments à traiter")
        
        # Affichage flexible des segments
        cols = st.columns(2)
        for idx, segment in enumerate(current_segments):
            with cols[idx % 2]:
                segment_id = get_segment_identifier(segment)
                segment_name = get_segment_name(segment)
                
                # Créer l'affichage dynamique
                display_content = f"<h4>CLUSTER {segment_id}: {segment_name}</h4>"
                
                # Afficher toutes les autres colonnes
                for key, value in segment.items():
                    if key not in ['id', 'ID', 'Id', 'name', 'Name', 'nom', 'Nom']:
                        display_content += f"<p><b>{key}:</b> {value}</p>"
                
                st.markdown(f'<div class="cluster-box">{display_content}</div>', unsafe_allow_html=True)

# TAB 2 - GÉNÉRATION
with tab2:
    st.subheader("🎯 Générer des Personas")
    
    if "loaded_segments" in st.session_state and st.session_state.loaded_segments:
        segments_to_use = st.session_state.loaded_segments
    else:
        segments_to_use = segments_data
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("**Segments disponibles:**")
        
        # Créer les options de manière flexible
        segment_options = []
        for idx, s in enumerate(segments_to_use):
            seg_id = get_segment_identifier(s)
            seg_name = get_segment_name(s)
            segment_options.append((seg_id, seg_name))
        
        selected_segments = st.multiselect(
            "Sélectionnez les segments à traiter",
            options=segment_options,
            format_func=lambda x: f"Cluster {x[0]}: {x[1][:30]}...",
            default=[segment_options[0]] if segment_options else []
        )
        
        if st.button("🚀 Générer les Personas", type="primary"):
            if not selected_segments:
                st.warning("⚠️ Sélectionnez au moins un segment")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                success_count = 0
                error_count = 0
                errors_details = []
                
                for idx, (seg_id, seg_name) in enumerate(selected_segments):
                    # Trouver le segment correspondant
                    segment = None
                    for s in segments_to_use:
                        if get_segment_identifier(s) == seg_id:
                            segment = s
                            break
                    
                    if segment:
                        status_text.text(f"⏳ Génération du Cluster {seg_id}: {seg_name[:30]}...")
                        
                        try:
                            result = generate_persona(segment, llm_model, st.session_state.column_mapping)
                            
                            if result:
                                success_count += 1
                                status_text.success(f"✅ Cluster {seg_id} généré avec succès!")
                            else:
                                error_count += 1
                                errors_details.append(f"Cluster {seg_id}: Échec de génération (résultat vide)")
                                status_text.error(f"❌ Échec pour Cluster {seg_id}")
                        
                        except Exception as e:
                            error_count += 1
                            errors_details.append(f"Cluster {seg_id}: {str(e)}")
                            status_text.error(f"❌ Erreur pour Cluster {seg_id}: {str(e)}")
                    else:
                        error_count += 1
                        errors_details.append(f"Cluster {seg_id}: Segment non trouvé")
                        status_text.error(f"❌ Cluster {seg_id} non trouvé dans les données")
                    
                    progress_bar.progress((idx + 1) / len(selected_segments))
                
                # Résumé final
                status_text.empty()
                
                if success_count > 0:
                    st.success(f"✅ {success_count} persona(s) généré(s) avec succès!")
                
                if error_count > 0:
                    st.error(f"❌ {error_count} échec(s) de génération")
                    
                    with st.expander("📋 Détails des erreurs"):
                        for error in errors_details:
                            st.write(f"• {error}")
                
                if success_count == 0 and error_count > 0:
                    st.warning("⚠️ Aucun persona n'a été généré. Vérifiez les erreurs ci-dessus.")
    
    with col2:
        if st.session_state.personas:
            st.write("**Personas générés:**")
            
            # Créer les options de manière flexible
            persona_options = []
            for k in sorted(st.session_state.personas.keys()):
                # Trouver le nom correspondant
                seg_name = "Unknown"
                for s in segments_to_use:
                    if get_segment_identifier(s) == k:
                        seg_name = get_segment_name(s)
                        break
                persona_options.append(f"Cluster {k}: {seg_name[:40]}...")
            
            selected_persona = st.selectbox("Afficher le persona de:", persona_options)
            
            if selected_persona:
                # Extraire l'ID du persona
                persona_id_str = selected_persona.split(":")[0].replace("Cluster ", "").strip()
                try:
                    persona_id = int(persona_id_str)
                except:
                    persona_id = persona_id_str
                
                st.markdown("---")
                st.markdown('<div class="persona-output">', unsafe_allow_html=True)
                st.markdown(st.session_state.personas[persona_id])
                st.markdown('</div>', unsafe_allow_html=True)
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.download_button(
                        label="📥 Télécharger en TXT",
                        data=st.session_state.personas[persona_id],
                        file_name=f"persona_cluster_{persona_id}.txt",
                        mime="text/plain"
                    )
                
                with col_b:
                    # Trouver le nom du segment
                    segment_name = "Unknown"
                    for s in segments_to_use:
                        if get_segment_identifier(s) == persona_id:
                            segment_name = get_segment_name(s)
                            break
                    
                    # Générer le PDF
                    pdf_buffer = generate_persona_pdf(persona_id, st.session_state.personas[persona_id], segment_name)
                    
                    st.download_button(
                        label="📥 Télécharger en PDF",
                        data=pdf_buffer,
                        file_name=f"persona_cluster_{persona_id}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.info("💡 Générez des personas pour les voir ici")

# TAB 3 - BENCHMARK CONCURRENTIEL
with tab3:
    st.subheader("📊 Analyse Concurrentielle - Benchmark des Banques")
    
    st.session_state.llm = llm_model
    
    st.info("💡 Chargez les catalogues de produits des banques concurrentes pour analyser les évolutions de prix et l'offre produits du marché.")
    
    # Section 1: Charger le catalogue de référence (SGCI)
    st.markdown("### 📄 Catalogue de Référence (Société Générale CI)")
    
    if st.session_state.produits_bancaires_text:
        st.success("✅ Catalogue SGCI déjà chargé dans l'onglet Configuration")
        with st.expander("📄 Aperçu du catalogue SGCI"):
            st.text(st.session_state.produits_bancaires_text[:500] + "...")
    else:
        st.warning("⚠️ Aucun catalogue SGCI chargé. Veuillez charger votre catalogue dans la barre latérale.")
    
    st.divider()
    
    # Section 2: Charger les catalogues concurrents
    st.markdown("### 🏦 Catalogues des Banques Concurrentes")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("**Ajouter une banque concurrente:**")
        
        nom_banque = st.text_input("Nom de la banque", placeholder="Ex: Ecobank, BICICI, BOA...")
        
        uploaded_concurrent = st.file_uploader(
            "Charger le PDF ou Excel des conditions bancaires",
            type=["pdf", "xlsx", "xls"],
            key="concurrent_file"
        )
        
        if st.button("➕ Ajouter cette banque", type="primary"):
            if not nom_banque:
                st.error("❌ Veuillez entrer le nom de la banque")
            elif not uploaded_concurrent:
                st.error("❌ Veuillez charger un fichier")
            elif nom_banque in st.session_state.catalogues_concurrents:
                st.warning("⚠️ Cette banque existe déjà. Supprimez-la d'abord pour la mettre à jour.")
            else:
                try:
                    file_extension = uploaded_concurrent.name.split('.')[-1].lower()
                    
                    if file_extension == 'pdf':
                        # Lire le PDF
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_concurrent.read()))
                        pdf_text = ""
                        for page in pdf_reader.pages:
                            pdf_text += page.extract_text() + "\n"
                        
                        st.session_state.catalogues_concurrents[nom_banque] = pdf_text
                        st.success(f"✅ {nom_banque} ajoutée avec succès ! ({len(pdf_reader.pages)} pages)")
                    
                    elif file_extension in ['xlsx', 'xls']:
                        # Lire le fichier Excel
                        df_concurrent = pd.read_excel(uploaded_concurrent)
                        
                        # Convertir en texte structuré
                        excel_text = f"CATALOGUE {nom_banque.upper()} (DÉTAILLÉ):\n\n"
                        
                        for idx, row in df_concurrent.iterrows():
                            excel_text += f"--- PRODUIT {idx + 1} ---\n"
                            for col in df_concurrent.columns:
                                value = str(row[col])
                                if value.lower() != 'nan':
                                    excel_text += f"{col}: {value}\n"
                            excel_text += "\n"
                        
                        st.session_state.catalogues_concurrents[nom_banque] = excel_text
                        st.success(f"✅ {nom_banque} ajoutée avec succès ! ({len(df_concurrent)} produits)")
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors de la lecture du fichier: {e}")
    
    with col2:
        st.write("**Banques concurrentes chargées:**")
        
        if st.session_state.catalogues_concurrents:
            for banque_name in list(st.session_state.catalogues_concurrents.keys()):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.info(f"🏦 {banque_name}")
                with col_b:
                    if st.button("🗑️", key=f"del_{banque_name}"):
                        del st.session_state.catalogues_concurrents[banque_name]
                        st.rerun()
        else:
            st.warning("⚠️ Aucune banque concurrente chargée")
    
    st.divider()
    
    # Section 3: Générer le benchmark
    st.markdown("### 🎯 Générer l'Analyse Benchmark")
    
    if not st.session_state.catalogues_concurrents:
        st.info("💡 Ajoutez au moins une banque concurrente pour générer un benchmark")
    else:
        col_x, col_y = st.columns([1, 1])
        
        with col_x:
            categories_benchmark = st.multiselect(
                "Catégories de produits à analyser",
                [
                    "Comptes courants",
                    "Comptes épargne",
                    "Cartes bancaires",
                    "Crédits (consommation, immobilier, auto)",
                    "Virements et transferts",
                    "Services digitaux (mobile banking, e-banking)",
                    "Assurances",
                    "Produits d'investissement",
                    "Frais et commissions générales"
                ],
                default=["Comptes courants", "Cartes bancaires", "Comptes épargne"]
            )
        
        with col_y:
            banques_a_comparer = st.multiselect(
                "Banques à inclure dans le benchmark",
                options=list(st.session_state.catalogues_concurrents.keys()),
                default=list(st.session_state.catalogues_concurrents.keys())
            )
        
        if st.button("🚀 Générer le Benchmark Complet", type="primary"):
            if not categories_benchmark:
                st.warning("⚠️ Sélectionnez au moins une catégorie de produits")
            elif not banques_a_comparer:
                st.warning("⚠️ Sélectionnez au moins une banque concurrente")
            else:
                with st.spinner("🔄 Analyse en cours des catalogues concurrents..."):
                    
                    # Construire le prompt de benchmark
                    benchmark_prompt = f"""Tu es un expert en analyse concurrentielle bancaire pour le marché ivoirien.

MISSION: Analyser les catalogues de produits bancaires pour produire un benchmark concurrentiel détaillé.

CATALOGUE DE RÉFÉRENCE - SOCIÉTÉ GÉNÉRALE CÔTE D'IVOIRE:
{st.session_state.produits_bancaires_text[:10000] if st.session_state.produits_bancaires_text else "Non disponible"}

CATALOGUES DES BANQUES CONCURRENTES:
"""
                    
                    for banque in banques_a_comparer:
                        benchmark_prompt += f"\n--- {banque.upper()} ---\n{st.session_state.catalogues_concurrents[banque][:8000]}\n"
                    
                    benchmark_prompt += f"""

CATÉGORIES À ANALYSER: {', '.join(categories_benchmark)}

ANALYSE DEMANDÉE:

1. **TABLEAU COMPARATIF DES PRIX**
   Pour chaque catégorie sélectionnée, crée un tableau comparatif avec:
   - SGCI (référence)
   - {', '.join(banques_a_comparer)}
   - Colonnes: Produit | SGCI | {' | '.join(banques_a_comparer)} | Écart vs meilleur prix du marché

2. **ÉVOLUTION DES PRIX**
   Identifie les tendances de prix sur le marché:
   - Produits où SGCI est plus cher que la concurrence (et de combien)
   - Produits où SGCI est moins cher (avantage compétitif)
   - Produits au prix du marché
   
3. **INNOVATION PRODUITS**
   Identifie les produits/services présents chez les concurrents mais absents chez SGCI:
   - Nouveaux produits digitaux
   - Offres packagées innovantes
   - Services à valeur ajoutée

4. **POSITIONNEMENT CONCURRENTIEL**
   Pour chaque catégorie:
   - Position de SGCI (leader, suiveur, premium, low-cost)
   - Forces et faiblesses vs concurrence
   - Opportunités d'amélioration

5. **RECOMMANDATIONS STRATÉGIQUES**
   - Ajustements tarifaires à considérer
   - Nouveaux produits à lancer
   - Améliorations à apporter aux offres existantes

FORMAT: Utilise des tableaux markdown, des sections claires avec titres en gras, et des bullet points pour les insights clés.
Sois PRÉCIS avec les chiffres (prix exacts en FCFA) et FACTUEL dans l'analyse.
Rédige tout en FRANÇAIS."""
                    
                    try:
                        messages = [HumanMessage(content=benchmark_prompt)]
                        response = st.session_state.llm.invoke(messages)
                        benchmark_result = response
                        
                        # Stocker le résultat
                        benchmark_key = f"benchmark_{len(st.session_state.benchmarks)}"
                        st.session_state.benchmarks[benchmark_key] = {
                            "date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                            "banques": banques_a_comparer,
                            "categories": categories_benchmark,
                            "contenu": benchmark_result
                        }
                        
                        st.success("✅ Benchmark généré avec succès!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la génération: {e}")
        
        st.divider()
        
        # Section 4: Afficher les benchmarks générés
        if st.session_state.benchmarks:
            st.markdown("### 📈 Benchmarks Générés")
            
            benchmark_keys = list(st.session_state.benchmarks.keys())
            
            for idx, bm_key in enumerate(reversed(benchmark_keys)):
                bm = st.session_state.benchmarks[bm_key]
                
                with st.expander(f"📊 Benchmark #{len(benchmark_keys)-idx} - {bm['date']} - {len(bm['banques'])} banques"):
                    st.markdown(f"**Banques analysées:** {', '.join(bm['banques'])}")
                    st.markdown(f"**Catégories:** {', '.join(bm['categories'])}")
                    st.divider()
                    st.markdown(bm['contenu'])
                    
                    col_dl1, col_dl2 = st.columns(2)
                    
                    with col_dl1:
                        st.download_button(
                            label="📥 Télécharger (TXT)",
                            data=bm['contenu'],
                            file_name=f"benchmark_{bm['date']}.txt",
                            mime="text/plain",
                            key=f"dl_txt_{bm_key}"
                        )
                    
                    with col_dl2:
                        # Générer PDF du benchmark
                        pdf_buffer = generate_benchmark_pdf(bm)
                        st.download_button(
                            label="📥 Télécharger (PDF)",
                            data=pdf_buffer,
                            file_name=f"benchmark_{bm['date']}.pdf",
                            mime="application/pdf",
                            key=f"dl_pdf_{bm_key}"
                        )

# TAB 4 - CHAT
with tab4:
    st.subheader("💬 Assistant Intelligent pour Personas")
    
    st.session_state.llm = llm_model

    if "loaded_segments" in st.session_state and st.session_state.loaded_segments:
        segments_for_chat = st.session_state.loaded_segments
    else:
        segments_for_chat = segments_data
    
    st.write("**Personas générés disponibles:**")

    if st.session_state.personas:
        for persona_id, content in st.session_state.personas.items():
            # Trouver le nom du segment
            segment_name = "Unknown"
            for s in segments_for_chat:
                if get_segment_identifier(s) == persona_id:
                    segment_name = get_segment_name(s)
                    break
            st.info(f"✅ Cluster {persona_id}: {segment_name}")
    else:
        st.warning("⚠️ Aucun persona généré. Générez d'abord des personas dans l'onglet 'Générer Personas'")
    
    st.divider()
    st.markdown("Posez des questions sur les personas, les segments ou demandez des recommandations marketing.")
    
    for message in st.session_state.conversation_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    user_input = st.chat_input("Posez votre question...")
    if user_input:
    
        st.session_state.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        with st.chat_message("user"):
            st.markdown(user_input)
        
        try:
            personas_context = "PERSONAS GÉNÉRÉS:\n"
            if st.session_state.personas:
                for persona_id, content in st.session_state.personas.items():
                    segment_name = "Unknown"
                    for s in segments_for_chat:
                        if get_segment_identifier(s) == persona_id:
                            segment_name = get_segment_name(s)
                            break
                    personas_context += f"\n--- Cluster {persona_id}: {segment_name} ---\n{content[:2000]}...\n"
            else:
                personas_context += "Aucun persona généré."
            
            segments_context = "\n\nSEGMENTS:\n"
            for segment in segments_for_chat:
                seg_id = get_segment_identifier(segment)
                seg_name = get_segment_name(segment)
                segments_context += f"- ID: {seg_id}, Nom: {seg_name}\n"
                # Ajouter toutes les autres caractéristiques
                for key, value in segment.items():
                    if key not in ['id', 'ID', 'name', 'Name', 'nom']:
                        segments_context += f"  {key}: {value}\n"
            
            if st.session_state.produits_bancaires_text:
                produits_context = f"\n\nCATALOGUE PRODUITS:\n{st.session_state.produits_bancaires_text[:10000]}"
            else:
                produits_context = "\n\nNote: Aucun catalogue produits chargé."
            
            system_prompt = f"""Tu es un expert en marketing bancaire et segmentation client de Société Générale Côte d'Ivoire.
                            {personas_context}
                            {segments_context}
                            {produits_context}
                            Utilise ces informations pour répondre aux questions. 
                            Recommande des produits spécifiques avec tarifs quand le catalogue est disponible."""

            messages_with_system = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input)
            ]

            response = st.session_state.llm.invoke(messages_with_system)
        
            assistant_message = response
            st.session_state.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
                
            with st.chat_message("assistant"):
                st.markdown(assistant_message)

        except Exception as e:
            st.error(f"❌ Erreur: {e}")
