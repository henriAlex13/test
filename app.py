import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard KPI – SocGen CI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = "kpi_socgen.db"


# ── Utilitaire hash ────────────────────────────────────────────────────────────
def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ── KPI Référentiel ────────────────────────────────────────────────────────────
KPI_REFERENCE = [
    {"categorie": "Activite Commerciale",             "kpi": "Encours de depots retail",                           "periodicite": "Mensuelle",     "email": "jacques.akponi@socgen.com",       "nom": "jacques"},
    {"categorie": "Activite Commerciale",             "kpi": "Encours de depots corporate",                        "periodicite": "Mensuelle",     "email": "jacques.akponi@socgen.com",       "nom": "jacques"},
    {"categorie": "Activite Commerciale",             "kpi": "Taux de credit corporate",                           "periodicite": "Mensuelle",     "email": "yssouf.soumahoro@socgen.com",     "nom": "yssouf"},
    {"categorie": "Activite Commerciale",             "kpi": "Taux de credit Retail",                              "periodicite": "Mensuelle",     "email": "yssouf.soumahoro@socgen.com",     "nom": "yssouf"},
    {"categorie": "Activite Commerciale",             "kpi": "Taux de dossiers de credits echus Corporate",        "periodicite": "Mensuelle",     "email": "Hafsatou.THIAM@socgen.com",       "nom": "Hafsatou"},
    {"categorie": "Activite Commerciale",             "kpi": "Taux de dossiers de credits echus Retail",           "periodicite": "Mensuelle",     "email": "aymard.konan@socgen.com",         "nom": "aymard"},
    {"categorie": "Activite Commerciale",             "kpi": "Nombre de forcage Corporate",                        "periodicite": "Mensuelle",     "email": "Hafsatou.THIAM@socgen.com",       "nom": "Hafsatou"},
    {"categorie": "Activite Commerciale",             "kpi": "Nombre de Decaissement Non Conforme Corporate",      "periodicite": "Mensuelle",     "email": "Hafsatou.THIAM@socgen.com",       "nom": "Hafsatou"},
    {"categorie": "Performance Financiere",           "kpi": "Commissions sur les produits Retail",                "periodicite": "Mensuelle",     "email": "yssouf.soumahoro@socgen.com",     "nom": "yssouf"},
    {"categorie": "Performance Financiere",           "kpi": "Commissions sur les produits Corporate",             "periodicite": "Mensuelle",     "email": "yssouf.soumahoro@socgen.com",     "nom": "yssouf"},
    {"categorie": "Performance Financiere",           "kpi": "Suspens Comptable",                                  "periodicite": "Trimestrielle", "email": "Jean-Joseph.KOUASSI@socgen.com",  "nom": "Jean-Joseph"},
    {"categorie": "Qualite de portefeuille et risque","kpi": "Nombre de PDI retail",                               "periodicite": "Mensuelle",     "email": "aymard.konan@socgen.com",         "nom": "aymard"},
    {"categorie": "Qualite de portefeuille et risque","kpi": "CNR global",                                         "periodicite": "Mensuelle",     "email": "esther.toure@socgen.com",         "nom": "esther"},
    {"categorie": "Qualite de portefeuille et risque","kpi": "CNR retail",                                         "periodicite": "Mensuelle",     "email": "esther.toure@socgen.com",         "nom": "esther"},
    {"categorie": "Qualite de portefeuille et risque","kpi": "CNR Corporate",                                      "periodicite": "Mensuelle",     "email": "esther.toure@socgen.com",         "nom": "esther"},
    {"categorie": "Ressources humaines",              "kpi": "Taux de chaises vides par direction",                "periodicite": "Mensuelle",     "email": "Nicanor.ANDJU@socgen.com",        "nom": "Nicanor"},
    {"categorie": "Ressources humaines",              "kpi": "Taux d'absenteisme par direction",                   "periodicite": "Mensuelle",     "email": "Nicanor.ANDJU@socgen.com",        "nom": "Nicanor"},
    {"categorie": "Ressources humaines",              "kpi": "Taux de turn over par direction",                    "periodicite": "Mensuelle",     "email": "Nicanor.ANDJU@socgen.com",        "nom": "Nicanor"},
    {"categorie": "Gouvernance et Conformite",        "kpi": "Nombre d'incidents financiers eleves et tres eleves","periodicite": "Mensuelle",     "email": "Isabelle.Dirabou@socgen.com",     "nom": "Isabelle"},
    {"categorie": "Gouvernance et Conformite",        "kpi": "Nombre d'incidents operationnels",                   "periodicite": "Mensuelle",     "email": "Isabelle.Dirabou@socgen.com",     "nom": "Isabelle"},
    {"categorie": "Gouvernance et Conformite",        "kpi": "Montant des incidents Operationnels",                "periodicite": "Mensuelle",     "email": "Isabelle.Dirabou@socgen.com",     "nom": "Isabelle"},
    {"categorie": "Digitalisation",                  "kpi": "Disponibilite des GAB (Gobla et Top 5)",              "periodicite": "Mensuelle",     "email": "Serge-francois.KOFFI@socgen.com", "nom": "Serge-francois"},
]

df_ref = pd.DataFrame(KPI_REFERENCE)

# ── Utilisateurs ───────────────────────────────────────────────────────────────
USERS = {
    "admin":          {"password": _hash("Admin@2026"),        "role": "admin", "nom_ref": None,             "display": "Administrateur"},
    "jacques":        {"password": _hash("Jacques@2026"),      "role": "user",  "nom_ref": "jacques",        "display": "Jacques Akponi"},
    "yssouf":         {"password": _hash("Yssouf@2026"),       "role": "user",  "nom_ref": "yssouf",         "display": "Yssouf Soumahoro"},
    "hafsatou":       {"password": _hash("Hafsatou@2026"),     "role": "user",  "nom_ref": "Hafsatou",       "display": "Hafsatou Thiam"},
    "aymard":         {"password": _hash("Aymard@2026"),       "role": "user",  "nom_ref": "aymard",         "display": "Aymard Konan"},
    "jean-joseph":    {"password": _hash("JeanJoseph@2026"),   "role": "user",  "nom_ref": "Jean-Joseph",    "display": "Jean-Joseph Kouassi"},
    "esther":         {"password": _hash("Esther@2026"),       "role": "user",  "nom_ref": "esther",         "display": "Esther Toure"},
    "nicanor":        {"password": _hash("Nicanor@2026"),      "role": "user",  "nom_ref": "Nicanor",        "display": "Nicanor Andju"},
    "isabelle":       {"password": _hash("Isabelle@2026"),     "role": "user",  "nom_ref": "Isabelle",       "display": "Isabelle Dirabou"},
    "serge-francois": {"password": _hash("Serge@2026"),        "role": "user",  "nom_ref": "Serge-francois", "display": "Serge-François Koffi"},
}


# ── Base de données ────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS saisies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            login       TEXT NOT NULL,
            nom_resp    TEXT NOT NULL,
            categorie   TEXT NOT NULL,
            kpi         TEXT NOT NULL,
            periodicite TEXT,
            periode     TEXT NOT NULL,
            valeur      REAL NOT NULL,
            unite       TEXT,
            commentaire TEXT,
            date_saisie TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs_connexion (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            login     TEXT,
            action    TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_connexion(login: str, action: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO logs_connexion (login, action, timestamp) VALUES (?,?,?)",
        (login, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()


def insert_saisie(data: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO saisies
          (login, nom_resp, categorie, kpi, periodicite, periode, valeur, unite, commentaire, date_saisie)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        data["login"], data["nom_resp"], data["categorie"], data["kpi"],
        data["periodicite"], data["periode"], data["valeur"],
        data["unite"], data["commentaire"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()


def load_saisies(login: str = None) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    if login and login != "admin":
        df = pd.read_sql(
            "SELECT * FROM saisies WHERE login=? ORDER BY date_saisie DESC",
            conn, params=(login,)
        )
    else:
        df = pd.read_sql("SELECT * FROM saisies ORDER BY date_saisie DESC", conn)
    conn.close()
    return df


def delete_saisie(row_id: int, login: str):
    conn = sqlite3.connect(DB_PATH)
    if login == "admin":
        conn.execute("DELETE FROM saisies WHERE id=?", (row_id,))
    else:
        conn.execute("DELETE FROM saisies WHERE id=? AND login=?", (row_id, login))
    conn.commit()
    conn.close()


def load_logs() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM logs_connexion ORDER BY timestamp DESC LIMIT 300", conn)
    conn.close()
    return df


init_db()


# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;600;700&family=IBM+Plex+Mono&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.main { background: #f5f6fa; }
.kpi-card {
    background: white; border-left: 4px solid #cc0000;
    border-radius: 4px; padding: 16px 20px; margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.kpi-val   { font-size: 2rem; font-weight: 700; color: #1a1a2e; font-family: 'IBM Plex Mono'; }
.kpi-label { font-size: 0.78rem; color: #666; text-transform: uppercase; letter-spacing: .08em; }
.section-header {
    font-size: 1.05rem; font-weight: 700; color: #cc0000;
    border-bottom: 2px solid #cc0000; padding-bottom: 4px; margin: 20px 0 12px;
    text-transform: uppercase; letter-spacing: .06em;
}
.alert-box {
    background: #fff8e1; border-left: 4px solid #ffc107;
    padding: 10px 16px; border-radius: 4px; font-size:.88rem; margin-bottom:6px;
}
.badge-admin { background:#1a1a2e; color:white; padding:3px 12px; border-radius:20px; font-size:.8rem; font-weight:600; }
.badge-user  { background:#cc0000; color:white; padding:3px 12px; border-radius:20px; font-size:.8rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTIFICATION
# ═══════════════════════════════════════════════════════════════════════════════
def show_login():
    st.markdown("""
    <div style="text-align:center;margin-top:40px;">
        <img src="https://upload.wikimedia.org/wikipedia/fr/thumb/9/9a/Soci%C3%A9t%C3%A9_G%C3%A9n%C3%A9rale.svg/200px-Soci%C3%A9t%C3%A9_G%C3%A9n%C3%A9rale.svg.png" width="160">
        <h2 style="color:#cc0000;margin-top:16px;">Dashboard KPI – SocGen CI</h2>
        <p style="color:#888;font-size:.9rem;">Saisie &amp; suivi des indicateurs de performance</p>
    </div>
    """, unsafe_allow_html=True)

    _, col_f, _ = st.columns([1, 1.1, 1])
    with col_f:
        with st.form("login_form"):
            st.markdown("#### 🔐 Connexion")
            login_input = st.text_input("Identifiant", placeholder="ex: jacques")
            pwd_input   = st.text_input("Mot de passe", type="password")
            submitted   = st.form_submit_button("Se connecter", use_container_width=True, type="primary")

        if submitted:
            key = login_input.strip().lower()
            if key in USERS and USERS[key]["password"] == _hash(pwd_input):
                st.session_state.update({
                    "logged_in":    True,
                    "login":        key,
                    "role":         USERS[key]["role"],
                    "nom_ref":      USERS[key]["nom_ref"],
                    "display_name": USERS[key]["display"],
                })
                log_connexion(key, "LOGIN")
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")

        st.caption("⚠️ Accès restreint – SocGen Côte d'Ivoire 2026")


if not st.session_state.get("logged_in"):
    show_login()
    st.stop()

# ── Variables session ─────────────────────────────────────────────────────────
CUR_LOGIN   = st.session_state["login"]
CUR_ROLE    = st.session_state["role"]
CUR_NOM_REF = st.session_state["nom_ref"]
CUR_DISPLAY = st.session_state["display_name"]
IS_ADMIN    = CUR_ROLE == "admin"

df_mes_kpis = df_ref.copy() if IS_ADMIN else df_ref[df_ref["nom"] == CUR_NOM_REF].copy()


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/fr/thumb/9/9a/Soci%C3%A9t%C3%A9_G%C3%A9n%C3%A9rale.svg/200px-Soci%C3%A9t%C3%A9_G%C3%A9n%C3%A9rale.svg.png", width=130)
    st.markdown("---")
    badge = "badge-admin" if IS_ADMIN else "badge-user"
    label = "Admin" if IS_ADMIN else "Responsable"
    st.markdown(f'<span class="{badge}">{label}</span> &nbsp;<b>{CUR_DISPLAY}</b>', unsafe_allow_html=True)
    st.markdown("---")

    pages_admin = ["📊 Dashboard Global", "📝 Saisie KPI", "🗃️ Historique", "📋 Référentiel", "🔐 Logs connexion"]
    pages_user  = ["📊 Mon Dashboard",    "📝 Saisie KPI", "🗃️ Mes saisies", "📋 Référentiel"]
    page = st.radio("Navigation", pages_admin if IS_ADMIN else pages_user)

    st.markdown("---")
    if st.button("🚪 Se déconnecter", use_container_width=True):
        log_connexion(CUR_LOGIN, "LOGOUT")
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    st.caption("SocGen CI · 2026")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page in ("📊 Dashboard Global", "📊 Mon Dashboard"):
    st.markdown(f"# {'📊 Dashboard Global' if IS_ADMIN else f'📊 Mon Dashboard – {CUR_DISPLAY}'}")

    df_all      = load_saisies(CUR_LOGIN)
    total_kpis  = len(df_mes_kpis)
    kpis_saisis = df_all["kpi"].nunique() if not df_all.empty else 0
    tx_compl    = round(kpis_saisis / total_kpis * 100) if total_kpis else 0
    nb_saisies  = len(df_all)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="kpi-card"><div class="kpi-label">KPIs assignés</div><div class="kpi-val">{total_kpis}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="kpi-card"><div class="kpi-label">KPIs saisis</div><div class="kpi-val">{kpis_saisis}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Complétion</div><div class="kpi-val">{tx_compl}%</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total saisies</div><div class="kpi-val">{nb_saisies}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    if df_all.empty:
        st.info("Aucune donnée saisie. Allez dans **Saisie KPI** pour commencer.")
    else:
        col_l, col_r = st.columns(2)

        with col_l:
            st.markdown('<div class="section-header">Complétion par catégorie</div>', unsafe_allow_html=True)
            cat_t = df_mes_kpis.groupby("categorie")["kpi"].count().reset_index(name="total")
            cat_s = df_all.groupby("categorie")["kpi"].nunique().reset_index(name="saisis")
            cat_m = cat_t.merge(cat_s, on="categorie", how="left").fillna(0)
            cat_m["pct"] = (cat_m["saisis"] / cat_m["total"] * 100).round(0)
            fig = px.bar(cat_m, x="pct", y="categorie", orientation="h",
                         color="pct", color_continuous_scale=["#ffcdd2","#cc0000"],
                         range_color=[0,100], text="pct", labels={"pct":"%","categorie":""})
            fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
            fig.update_layout(showlegend=False, coloraxis_showscale=False,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              margin=dict(l=0,r=50,t=10,b=10), height=280,
                              yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            if IS_ADMIN:
                st.markdown('<div class="section-header">Saisies par responsable</div>', unsafe_allow_html=True)
                by_r = df_all.groupby("nom_resp").size().reset_index(name="nb")
                fig2 = px.pie(by_r, values="nb", names="nom_resp",
                              color_discrete_sequence=px.colors.sequential.Reds_r, hole=0.45)
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                   margin=dict(l=0,r=0,t=10,b=10), height=280)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.markdown('<div class="section-header">Mes dernières saisies</div>', unsafe_allow_html=True)
                st.dataframe(
                    df_all[["kpi","periode","valeur","unite","date_saisie"]].head(8)
                    .rename(columns={"kpi":"KPI","periode":"Période","valeur":"Valeur",
                                     "unite":"Unité","date_saisie":"Date"}),
                    use_container_width=True, hide_index=True
                )

        st.markdown('<div class="section-header">Évolution des saisies</div>', unsafe_allow_html=True)
        df_all["dt"] = pd.to_datetime(df_all["date_saisie"])
        df_tl = df_all.groupby(df_all["dt"].dt.date).size().reset_index(name="nb")
        df_tl.columns = ["date","nb"]
        fig3 = px.area(df_tl, x="date", y="nb", color_discrete_sequence=["#cc0000"],
                       labels={"nb":"Saisies","date":""})
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           margin=dict(l=0,r=0,t=10,b=10), height=190)
        st.plotly_chart(fig3, use_container_width=True)

        manquants = df_mes_kpis[~df_mes_kpis["kpi"].isin(df_all["kpi"].unique())]
        if not manquants.empty:
            st.markdown('<div class="section-header">⚠️ KPIs non encore saisis</div>', unsafe_allow_html=True)
            for _, row in manquants.iterrows():
                st.markdown(
                    f'<div class="alert-box">📍 <b>{row["categorie"]}</b> — {row["kpi"]} '
                    f'<span style="color:#888">· {row["periodicite"]}</span></div>',
                    unsafe_allow_html=True
                )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : SAISIE KPI
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📝 Saisie KPI":
    st.markdown("# 📝 Formulaire de saisie KPI")

    if df_mes_kpis.empty:
        st.warning("Aucun KPI assigné à votre compte. Contactez l'administrateur.")
        st.stop()

    cats = df_mes_kpis["categorie"].unique().tolist()

    with st.form("form_saisie", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Identification**")
            categorie  = st.selectbox("Catégorie *", cats)
            kpis_liste = df_mes_kpis[df_mes_kpis["categorie"] == categorie]["kpi"].tolist()
            kpi        = st.selectbox("KPI *", kpis_liste)
        with col2:
            st.markdown("**Données**")
            periode     = st.text_input("Période *", value=datetime.now().strftime("%B %Y"),
                                        placeholder="ex: Avril 2026")
            valeur      = st.number_input("Valeur *", value=0.0, format="%.4f")
            unite       = st.text_input("Unité", placeholder="%, FCFA, nombre…")
            commentaire = st.text_area("Commentaire", height=80)

        info_kpi = df_mes_kpis[df_mes_kpis["kpi"] == kpi].iloc[0] if kpi else None
        if info_kpi is not None:
            st.info(f"📧 **{info_kpi['nom']}** ({info_kpi['email']}) · Périodicité : **{info_kpi['periodicite']}**")

        submitted = st.form_submit_button("✅ Enregistrer", use_container_width=True, type="primary")
        if submitted:
            if not periode.strip():
                st.error("La période est obligatoire.")
            else:
                insert_saisie({
                    "login":       CUR_LOGIN,
                    "nom_resp":    CUR_NOM_REF or CUR_DISPLAY,
                    "categorie":   categorie,
                    "kpi":         kpi,
                    "periodicite": info_kpi["periodicite"] if info_kpi is not None else "",
                    "periode":     periode.strip(),
                    "valeur":      valeur,
                    "unite":       unite,
                    "commentaire": commentaire,
                })
                st.success(f"✅ **{kpi}** – période **{periode}** enregistré !")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : HISTORIQUE / MES SAISIES
# ═══════════════════════════════════════════════════════════════════════════════
elif page in ("🗃️ Historique", "🗃️ Mes saisies"):
    st.markdown(f"# {'🗃️ Historique global' if IS_ADMIN else '🗃️ Mes saisies'}")

    df_h = load_saisies(CUR_LOGIN)

    if df_h.empty:
        st.info("Aucune donnée disponible.")
    else:
        col1, col2, col3 = st.columns(3)
        cats_uniq = df_h["categorie"].unique().tolist()
        with col1:
            f_cat = st.multiselect("Catégorie", cats_uniq, default=cats_uniq)
        with col2:
            f_per = st.text_input("Période (texte libre)")
        with col3:
            f_resp = None
            if IS_ADMIN:
                resps  = df_h["nom_resp"].unique().tolist()
                f_resp = st.multiselect("Responsable", resps, default=resps)

        df_f = df_h[df_h["categorie"].isin(f_cat)]
        if f_per:
            df_f = df_f[df_f["periode"].str.contains(f_per, case=False, na=False)]
        if IS_ADMIN and f_resp:
            df_f = df_f[df_f["nom_resp"].isin(f_resp)]

        cols_show = (
            ["id","nom_resp","categorie","kpi","periodicite","periode","valeur","unite","commentaire","date_saisie"]
            if IS_ADMIN else
            ["id","categorie","kpi","periodicite","periode","valeur","unite","commentaire","date_saisie"]
        )
        rename_map = {
            "id":"ID","nom_resp":"Responsable","categorie":"Catégorie","kpi":"KPI",
            "periodicite":"Périodicité","periode":"Période","valeur":"Valeur",
            "unite":"Unité","commentaire":"Commentaire","date_saisie":"Date saisie"
        }
        st.dataframe(df_f[cols_show].rename(columns=rename_map),
                     use_container_width=True, height=420)
        st.caption(f"{len(df_f)} enregistrement(s)")

        csv = df_f.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exporter CSV", data=csv,
                           file_name=f"kpi_{CUR_LOGIN}.csv", mime="text/csv")

        with st.expander("🗑️ Supprimer un enregistrement"):
            del_id = st.number_input("ID à supprimer", min_value=1, step=1)
            if st.button("Supprimer", type="secondary"):
                delete_saisie(int(del_id), CUR_LOGIN)
                st.success(f"Ligne #{del_id} supprimée.")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : RÉFÉRENTIEL
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Référentiel":
    st.markdown("# 📋 Référentiel des KPIs")
    if not IS_ADMIN:
        st.info(f"Affichage filtré : KPIs assignés à **{CUR_DISPLAY}**")

    search  = st.text_input("🔍 Rechercher un KPI, responsable…")
    df_show = df_mes_kpis.copy()
    if search:
        mask    = df_show.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)
        df_show = df_show[mask]

    for cat in df_show["categorie"].unique():
        st.markdown(f'<div class="section-header">{cat}</div>', unsafe_allow_html=True)
        sub = (df_show[df_show["categorie"] == cat][["kpi","periodicite","nom","email"]]
               .rename(columns={"kpi":"KPI","periodicite":"Périodicité","nom":"Responsable","email":"Email"}))
        st.dataframe(sub, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : LOGS CONNEXION (admin)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔐 Logs connexion":
    if not IS_ADMIN:
        st.error("Accès réservé à l'administrateur.")
        st.stop()

    st.markdown("# 🔐 Logs de connexion")
    df_logs = load_logs()
    if df_logs.empty:
        st.info("Aucun log disponible.")
    else:
        st.dataframe(
            df_logs.rename(columns={"id":"ID","login":"Login","action":"Action","timestamp":"Horodatage"}),
            use_container_width=True, height=400
        )
        csv_l = df_logs.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exporter logs CSV", data=csv_l,
                           file_name="logs_connexion.csv", mime="text/csv")
