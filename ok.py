import streamlit as st
import pandas as pd
import json
import PyPDF2
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER

# LangChain imports
from langchain_openai import ChatOpenAI
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
if "benchmarks" not in st.session_state:
    st.session_state.benchmarks = {}
if "catalogues_concurrents" not in st.session_state:
    st.session_state.catalogues_concurrents = {}

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key
    api_key = st.text_input("Clé API OpenAI", type="password", key="api_key")
    
    if api_key and st.session_state.llm is None:
        st.session_state.llm = ChatOpenAI(
            api_key=api_key,
            model="gpt-4o-mini",
            temperature=0.7
        )
        st.success("✅ Connecté à OpenAI !")
    
    st.divider()
    
    # Section Upload PDF
    st.header("📄 Catalogue Produits")
    
    uploaded_pdf = st.file_uploader(
        "Charger le PDF des conditions bancaires",
        type=["pdf"],
        help="Uploadez le document des conditions générales de la banque (mis à jour chaque semestre)"
    )
    
    if uploaded_pdf is not None:
        try:
            # Lire le PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_pdf.read()))
            
            # Extraire le texte
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text() + "\n"
            
            st.session_state.produits_bancaires_text = pdf_text
            
            st.success(f"✅ PDF chargé ! ({len(pdf_reader.pages)} pages)")
            
            # Aperçu
            with st.expander("📄 Aperçu du contenu"):
                st.text(pdf_text[:800] + "...")
                
        except Exception as e:
            st.error(f"❌ Erreur lors de la lecture du PDF: {e}")
    
    elif st.session_state.produits_bancaires_text:
        st.info("✅ Catalogue produits chargé en mémoire")
        if st.button("🗑️ Supprimer le catalogue"):
            st.session_state.produits_bancaires_text = None
            st.rerun()
    else:
        st.warning("⚠️ Aucun catalogue chargé")
        st.caption("Les personas seront générés sans recommandations de produits spécifiques")
    
    st.divider()
    st.info("💡 Configurez votre clé API et chargez le catalogue produits pour commencer")

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

def create_prompt(segment):
    base_info = f"""Génère une description complète et détaillée d'une persona marketing pour un segment bancaire avec les caractéristiques suivantes:

Nom du segment: {segment.get('name', 'N/A')}
Âge moyen: {segment.get('age', 'N/A')} ans
Nombre de produits utilisés: {segment.get('nbProducts', 'N/A')}
Revenu mensuel (Hommes): {segment.get('revenueHommes', 'N/A')}
Revenu mensuel (Femmes): {segment.get('revenueFemmes', 'N/A')}
Accessibilité mobile: {segment.get('mobileAccess', 'N/A')}
Accessibilité email: {segment.get('emailAccess', 'N/A')}
Caractéristiques principales: {segment.get('characteristics', 'N/A')}"""

    if st.session_state.produits_bancaires_text:
        produits_info = f"""

CATALOGUE DES PRODUITS BANCAIRES DISPONIBLES:
{st.session_state.produits_bancaires_text[:8000]}"""
        recommendation_note = """
- RECOMMANDATIONS DE PRODUITS BANCAIRES :
  
  **A. PROPOSITION GÉNÉRALE**
  Basée sur l'analyse complète du segment (âge, nombre de produits, revenu, accessibilité digitale, caractéristiques comportementales), propose des CATÉGORIES de produits bancaires adaptés sans référence au catalogue. Justifie chaque recommandation par la synthèse des critères de segmentation.
  
  **B. PROPOSITION BASÉE SUR LE CATALOGUE PRODUIT**
  En utilisant le catalogue fourni ci-dessus, identifie les produits SPÉCIFIQUES avec leurs NOMS EXACTS, TARIFS et CONDITIONS du catalogue qui correspondent aux besoins identifiés en partie A. Crée un package produit personnalisé détaillé."""
    else:
        produits_info = ""
        recommendation_note = """
- RECOMMANDATIONS DE PRODUITS BANCAIRES :
  
  **A. PROPOSITION GÉNÉRALE**
  Basée sur l'analyse complète du segment (âge, nombre de produits, revenu, accessibilité digitale, caractéristiques comportementales), propose des CATÉGORIES de produits bancaires adaptés. Justifie chaque recommandation par la synthèse des critères de segmentation.
  
  Note: Aucun catalogue produits chargé, donc pas de proposition spécifique en partie B."""
    
    prompt = base_info + produits_info + """

Fournis une description professionnelle en français incluant:
- Profil démographique détaillé (avec différences possibles entre hommes et femmes)
- Comportements d'achat et patterns de consommation
- Besoins et préférences spécifiques
- Motivations et douleurs (pain points)
- Stratégie marketing recommandée
- Canaux de communication préférés
- Proposition de valeur unique""" + recommendation_note + """

IMPORTANT pour les recommandations:
  * Âge et maturité professionnelle (épargne retraite, assurance-vie, crédits immobiliers pour seniors vs jeunes actifs)
  * Nombre de produits déjà utilisés (cross-selling intelligent, packages pour multi-équipés vs produits d'entrée pour nouveaux clients)
  * Niveau de revenu (produits premium vs accessibles, plafonds et frais adaptés)
  * Accessibilité mobile et email (banking digital, notifications, apps mobiles pour connectés vs agences physiques pour autres)
  * Caractéristiques comportementales (produits automatisés pour actifs pressés, conseils personnalisés pour retraités, etc.)

Format: Utilise des sections claires avec des titres en gras."""
    
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

def generate_persona(segment):
    """
    Génère un persona avec LangChain LLM invoke
    """
    if st.session_state.llm is None:
        st.error("❌ Veuillez d'abord configurer votre clé API dans la barre latérale.")
        return None
    
    prompt = create_prompt(segment)
    
    try:
        # Utilisation de invoke avec LangChain
        messages = [HumanMessage(content=prompt)]
        response = st.session_state.llm.invoke(messages)
        
        # Récupérer le contenu de la réponse
        persona_content = response.content
        
        st.session_state.personas[segment.get("id", 0)] = persona_content
        return persona_content
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la génération: {e}")
        return None

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
            df = pd.read_csv(uploaded_file)
            st.session_state.loaded_segments = df.to_dict('records')
            st.dataframe(df, use_container_width=True)
            st.success("✅ Fichier chargé avec succès!")
            current_segments = st.session_state.loaded_segments
        else:
            st.info("💡 Veuillez charger un fichier CSV pour continuer")
            current_segments = []
    else:
        current_segments = segments_data
    
    if current_segments:
        st.divider()
        st.subheader("Segments à traiter")
        cols = st.columns(2)
        for idx, segment in enumerate(current_segments):
            with cols[idx % 2]:
                st.markdown(f"""
                <div class="cluster-box">
                    <h4>CLUSTER {segment.get('id', idx)}: {segment.get('name', 'Sans nom')}</h4>
                    <p><b>Âge moyen:</b> {segment.get('age', 'N/A')} ans</p>
                    <p><b>Produits:</b> {segment.get('nbProducts', 'N/A')}</p>
                    <p><b>Revenu Hommes:</b> {segment.get('revenueHommes', 'N/A')}</p>
                    <p><b>Revenu Femmes:</b> {segment.get('revenueFemmes', 'N/A')}</p>
                    <p><b>Accès Mobile:</b> {segment.get('mobileAccess', 'N/A')}</p>
                    <p><b>Accès Email:</b> {segment.get('emailAccess', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)

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
        selected_segments = st.multiselect(
            "Sélectionnez les segments à traiter",
            options=[(s.get("id", idx), s.get("name", f"Segment {idx}")) for idx, s in enumerate(segments_to_use)],
            format_func=lambda x: f"Cluster {x[0]}: {x[1][:30]}...",
            default=[(segments_to_use[0].get("id", 0), segments_to_use[0].get("name", "Segment 0"))]
        )
        
        if st.button("🚀 Générer les Personas", type="primary"):
            if not selected_segments:
                st.warning("⚠️ Sélectionnez au moins un segment")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, (seg_id, _) in enumerate(selected_segments):
                    segment = next((s for s in segments_to_use if s.get("id", -1) == seg_id), None)
                    if segment:
                        status_text.text(f"Génération du Cluster {seg_id}...")
                        
                        generate_persona(segment)
                        
                        progress_bar.progress((idx + 1) / len(selected_segments))
                
                st.success("✅ Tous les personas ont été générés!")
    
    with col2:
        if st.session_state.personas:
            st.write("**Personas générés:**")
            
            persona_options = [
                f"Cluster {k}: {next((s.get('name', 'Unknown') for s in segments_to_use if s.get('id', -1) == k), 'Unknown')[:40]}..."
                for k in sorted(st.session_state.personas.keys())
            ]
            
            selected_persona = st.selectbox("Afficher le persona de:", persona_options)
            
            if selected_persona:
                persona_id = int(selected_persona.split(":")[0].replace("Cluster ", ""))
                
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
                    segment_name = next((s.get("name", "Unknown") for s in segments_to_use if s.get("id", -1) == persona_id), "Unknown")
                    
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
with tab4:
    st.subheader("📊 Analyse Concurrentielle - Benchmark des Banques")
    
    if st.session_state.llm is None:
        st.warning("⚠️ Veuillez configurer votre clé API OpenAI d'abord.")
    else:
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
                "Charger le PDF des conditions bancaires",
                type=["pdf"],
                key="concurrent_pdf"
            )
            
            if st.button("➕ Ajouter cette banque", type="primary"):
                if not nom_banque:
                    st.error("❌ Veuillez entrer le nom de la banque")
                elif not uploaded_concurrent:
                    st.error("❌ Veuillez charger un fichier PDF")
                elif nom_banque in st.session_state.catalogues_concurrents:
                    st.warning("⚠️ Cette banque existe déjà. Supprimez-la d'abord pour la mettre à jour.")
                else:
                    try:
                        # Lire le PDF
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_concurrent.read()))
                        pdf_text = ""
                        for page in pdf_reader.pages:
                            pdf_text += page.extract_text() + "\n"
                        
                        st.session_state.catalogues_concurrents[nom_banque] = pdf_text
                        st.success(f"✅ {nom_banque} ajoutée avec succès ! ({len(pdf_reader.pages)} pages)")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la lecture du PDF: {e}")
        
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
Sois PRÉCIS avec les chiffres (prix exacts en FCFA) et FACTUEL dans l'analyse."""
                        
                        try:
                            messages = [HumanMessage(content=benchmark_prompt)]
                            response = st.session_state.llm.invoke(messages)
                            benchmark_result = response.content
                            
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

# TAB 4 - CHAT
with tab3:
    st.subheader("💬 Assistant Intelligent pour Personas")
    
    if st.session_state.llm is None:
        st.warning("⚠️ Veuillez configurer votre clé API d'abord.")
    else:
        if "loaded_segments" in st.session_state and st.session_state.loaded_segments:
            segments_for_chat = st.session_state.loaded_segments
        else:
            segments_for_chat = segments_data
        
        st.write("**Personas générés disponibles:**")
        if st.session_state.personas:
            for persona_id, content in st.session_state.personas.items():
                segment_name = next((s.get("name", "Unknown") for s in segments_for_chat if s.get("id", -1) == persona_id), "Unknown")
                st.info(f"✅ Cluster {persona_id}: {segment_name}")
        else:
            st.warning("⚠️ Aucun persona généré. Générez d'abord des personas dans l'onglet 'Générer Personas'")
        
        st.divider()
        st.write("Posez des questions sur les personas, les segments ou demandez des recommandations marketing.")
        
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
                        segment_name = next((s.get("name", "Unknown") for s in segments_for_chat if s.get("id", -1) == persona_id), "Unknown")
                        personas_context += f"\n--- Cluster {persona_id}: {segment_name} ---\n{content[:2000]}...\n"
                else:
                    personas_context += "Aucun persona généré."
                
                segments_context = "\n\nSEGMENTS:\n"
                for segment in segments_for_chat:
                    segments_context += f"- ID: {segment.get('id')}, Nom: {segment.get('name')}, Âge: {segment.get('age')}, "
                    segments_context += f"Produits: {segment.get('nbProducts')}, Revenu H: {segment.get('revenueHommes')}, Revenu F: {segment.get('revenueFemmes')}\n"
                
                if st.session_state.produits_bancaires_text:
                    produits_context = f"\n\nCATALOGUE PRODUITS:\n{st.session_state.produits_bancaires_text[:8000]}"
                else:
                    produits_context = "\n\nNote: Aucun catalogue produits chargé."
                
                system_content = f"""Tu es un expert en marketing bancaire et segmentation client de Société Générale Côte d'Ivoire.

{personas_context}
{segments_context}
{produits_context}

Utilise ces informations pour répondre aux questions. Recommande des produits spécifiques avec tarifs quand le catalogue est disponible."""
                
                # Construire les messages pour LangChain
                messages = [SystemMessage(content=system_content)]
                
                for msg in st.session_state.conversation_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
                
                # Invoquer le LLM
                response = st.session_state.llm.invoke(messages)
                assistant_message = response.content
                
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
                with st.chat_message("assistant"):
                    st.markdown(assistant_message)
            
            except Exception as e:
                st.error(f"❌ Erreur: {e}")
