import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
import io

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Dashboard KPI – SocGen CI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = "kpi_socgen.db"
ROUGE   = "#cc0000"
LAYOUT  = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
               margin=dict(l=0, r=40, t=10, b=10))


def _hash(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()


import base64 as _b64, os as _os

def _get_logo_b64() -> str:
    path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "logo_socgen.png")
    with open(path, "rb") as f:
        return _b64.b64encode(f.read()).decode()

_LOGO_B64  = _get_logo_b64()
_LOGO_HTML = f'<img src="data:image/png;base64,{_LOGO_B64}" width="110" style="border-radius:6px;">'


# ══════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES
# ══════════════════════════════════════════════════════════════════════════════
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS kpi_ref (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            categorie   TEXT NOT NULL,
            kpi         TEXT NOT NULL,
            periodicite TEXT NOT NULL DEFAULT 'Mensuelle',
            email       TEXT,
            nom         TEXT,
            UNIQUE(categorie, kpi)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            login     TEXT NOT NULL UNIQUE,
            password  TEXT NOT NULL,
            role      TEXT NOT NULL DEFAULT 'user',
            nom_ref   TEXT,
            display   TEXT NOT NULL,
            email     TEXT,
            actif     INTEGER NOT NULL DEFAULT 1
        )
    """)
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

    # Seed KPIs
    if c.execute("SELECT COUNT(*) FROM kpi_ref").fetchone()[0] == 0:
        seed_kpi = [
            ("Activite Commerciale","Encours de depots retail","Mensuelle","jacques.akponi@socgen.com","jacques"),
            ("Activite Commerciale","Encours de depots corporate","Mensuelle","jacques.akponi@socgen.com","jacques"),
            ("Activite Commerciale","Taux de credit corporate","Mensuelle","yssouf.soumahoro@socgen.com","yssouf"),
            ("Activite Commerciale","Taux de credit Retail","Mensuelle","yssouf.soumahoro@socgen.com","yssouf"),
            ("Activite Commerciale","Taux de dossiers de credits echus Corporate","Mensuelle","Hafsatou.THIAM@socgen.com","Hafsatou"),
            ("Activite Commerciale","Taux de dossiers de credits echus Retail","Mensuelle","aymard.konan@socgen.com","aymard"),
            ("Activite Commerciale","Nombre de forcage Corporate","Mensuelle","Hafsatou.THIAM@socgen.com","Hafsatou"),
            ("Activite Commerciale","Nombre de Decaissement Non Conforme Corporate","Mensuelle","Hafsatou.THIAM@socgen.com","Hafsatou"),
            ("Performance Financiere","Commissions sur les produits Retail","Mensuelle","yssouf.soumahoro@socgen.com","yssouf"),
            ("Performance Financiere","Commissions sur les produits Corporate","Mensuelle","yssouf.soumahoro@socgen.com","yssouf"),
            ("Performance Financiere","Suspens Comptable","Trimestrielle","Jean-Joseph.KOUASSI@socgen.com","Jean-Joseph"),
            ("Qualite de portefeuille et risque","Nombre de PDI retail","Mensuelle","aymard.konan@socgen.com","aymard"),
            ("Qualite de portefeuille et risque","CNR global","Mensuelle","esther.toure@socgen.com","esther"),
            ("Qualite de portefeuille et risque","CNR retail","Mensuelle","esther.toure@socgen.com","esther"),
            ("Qualite de portefeuille et risque","CNR Corporate","Mensuelle","esther.toure@socgen.com","esther"),
            ("Ressources humaines","Taux de chaises vides par direction","Mensuelle","Nicanor.ANDJU@socgen.com","Nicanor"),
            ("Ressources humaines","Taux d'absenteisme par direction","Mensuelle","Nicanor.ANDJU@socgen.com","Nicanor"),
            ("Ressources humaines","Taux de turn over par direction","Mensuelle","Nicanor.ANDJU@socgen.com","Nicanor"),
            ("Gouvernance et Conformite","Nombre d'incidents financiers eleves et tres eleves","Mensuelle","Isabelle.Dirabou@socgen.com","Isabelle"),
            ("Gouvernance et Conformite","Nombre d'incidents operationnels","Mensuelle","Isabelle.Dirabou@socgen.com","Isabelle"),
            ("Gouvernance et Conformite","Montant des incidents Operationnels","Mensuelle","Isabelle.Dirabou@socgen.com","Isabelle"),
            ("Digitalisation","Disponibilite des GAB (Gobla et Top 5)","Mensuelle","Serge-francois.KOFFI@socgen.com","Serge-francois"),
        ]
        c.executemany("INSERT OR IGNORE INTO kpi_ref (categorie,kpi,periodicite,email,nom) VALUES (?,?,?,?,?)", seed_kpi)

    # Seed utilisateurs
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        seed_users = [
            ("admin",         _hash("Admin@2026"),      "admin","None","Administrateur","admin@socgen.com"),
            ("dg",            _hash("DG@2026"),         "dg",  "None","Directeur General","dg@socgen.com"),
            ("jacques",       _hash("Jacques@2026"),    "user","jacques","Jacques Akponi","jacques.akponi@socgen.com"),
            ("yssouf",        _hash("Yssouf@2026"),     "user","yssouf","Yssouf Soumahoro","yssouf.soumahoro@socgen.com"),
            ("hafsatou",      _hash("Hafsatou@2026"),   "user","Hafsatou","Hafsatou Thiam","Hafsatou.THIAM@socgen.com"),
            ("aymard",        _hash("Aymard@2026"),     "user","aymard","Aymard Konan","aymard.konan@socgen.com"),
            ("jean-joseph",   _hash("JeanJoseph@2026"), "user","Jean-Joseph","Jean-Joseph Kouassi","Jean-Joseph.KOUASSI@socgen.com"),
            ("esther",        _hash("Esther@2026"),     "user","esther","Esther Toure","esther.toure@socgen.com"),
            ("nicanor",       _hash("Nicanor@2026"),    "user","Nicanor","Nicanor Andju","Nicanor.ANDJU@socgen.com"),
            ("isabelle",      _hash("Isabelle@2026"),   "user","Isabelle","Isabelle Dirabou","Isabelle.Dirabou@socgen.com"),
            ("serge-francois",_hash("Serge@2026"),      "user","Serge-francois","Serge-Francois Koffi","Serge-francois.KOFFI@socgen.com"),
        ]
        c.executemany("INSERT OR IGNORE INTO users (login,password,role,nom_ref,display,email) VALUES (?,?,?,?,?,?)", seed_users)

    conn.commit()
    conn.close()


# ── Helpers DB ────────────────────────────────────────────────────────────────
def load_kpi_ref() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM kpi_ref ORDER BY categorie, kpi", conn)
    conn.close()
    return df


def add_kpi(categorie, kpi, periodicite, email, nom):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO kpi_ref (categorie,kpi,periodicite,email,nom) VALUES (?,?,?,?,?)",
                     (categorie, kpi, periodicite, email, nom))
        conn.commit()
        return True, "KPI ajouté avec succès."
    except sqlite3.IntegrityError:
        return False, "Ce KPI existe déjà dans cette catégorie."
    finally:
        conn.close()


def delete_kpi(kpi_id):
    conn = get_conn()
    conn.execute("DELETE FROM kpi_ref WHERE id=?", (kpi_id,))
    conn.commit()
    conn.close()


def get_user(login: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE login=? AND actif=1", (login,)).fetchone()
    conn.close()
    if row:
        return dict(zip(["id","login","password","role","nom_ref","display","email","actif"], row))
    return None


def load_users() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql("SELECT id,login,role,nom_ref,display,email,actif FROM users ORDER BY role,login", conn)
    conn.close()
    return df


def add_user(login, password, role, nom_ref, display, email):
    conn = get_conn()
    try:
        nom_ref_db = None if (not nom_ref or nom_ref == "None") else nom_ref
        conn.execute("INSERT INTO users (login,password,role,nom_ref,display,email) VALUES (?,?,?,?,?,?)",
                     (login.lower().strip(), _hash(password), role, nom_ref_db, display, email))
        conn.commit()
        return True, "Utilisateur créé."
    except sqlite3.IntegrityError:
        return False, "Cet identifiant existe déjà."
    finally:
        conn.close()


def toggle_user(uid, actif):
    conn = get_conn()
    conn.execute("UPDATE users SET actif=? WHERE id=?", (actif, uid))
    conn.commit()
    conn.close()


def log_connexion(login, action):
    conn = get_conn()
    conn.execute("INSERT INTO logs_connexion (login,action,timestamp) VALUES (?,?,?)",
                 (login, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def insert_saisie(data):
    conn = get_conn()
    conn.execute("""
        INSERT INTO saisies (login,nom_resp,categorie,kpi,periodicite,periode,valeur,unite,commentaire,date_saisie)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (data["login"],data["nom_resp"],data["categorie"],data["kpi"],
          data["periodicite"],data["periode"],data["valeur"],
          data["unite"],data["commentaire"],
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def load_saisies(login=None) -> pd.DataFrame:
    conn = get_conn()
    if login and login not in ("admin","dg"):
        df = pd.read_sql("SELECT * FROM saisies WHERE login=? ORDER BY date_saisie DESC", conn, params=(login,))
    else:
        df = pd.read_sql("SELECT * FROM saisies ORDER BY date_saisie DESC", conn)
    conn.close()
    return df


def delete_saisie(row_id, login):
    conn = get_conn()
    if login == "admin":
        conn.execute("DELETE FROM saisies WHERE id=?", (row_id,))
    else:
        conn.execute("DELETE FROM saisies WHERE id=? AND login=?", (row_id, login))
    conn.commit()
    conn.close()


def load_logs() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM logs_connexion ORDER BY timestamp DESC LIMIT 300", conn)
    conn.close()
    return df


def to_xlsx(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="KPI")
    return buf.getvalue()


init_db()


# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;600;700&family=IBM+Plex+Mono&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.main{background:#f5f6fa;}
.kpi-card{background:white;border-left:4px solid #cc0000;border-radius:6px;
    padding:16px 20px;margin-bottom:12px;box-shadow:0 1px 6px rgba(0,0,0,0.08);}
.kpi-val{font-size:2rem;font-weight:700;color:#1a1a2e;font-family:'IBM Plex Mono';}
.kpi-label{font-size:.75rem;color:#888;text-transform:uppercase;letter-spacing:.1em;}
.section-header{font-size:1rem;font-weight:700;color:#cc0000;
    border-bottom:2px solid #cc0000;padding-bottom:4px;margin:22px 0 12px;
    text-transform:uppercase;letter-spacing:.07em;}
.alert-box{background:#fff8e1;border-left:4px solid #ffc107;
    padding:10px 16px;border-radius:4px;font-size:.88rem;margin-bottom:6px;}
.badge-admin{background:#1a1a2e;color:white;padding:3px 12px;border-radius:20px;font-size:.78rem;font-weight:600;}
.badge-dg{background:#7b1fa2;color:white;padding:3px 12px;border-radius:20px;font-size:.78rem;font-weight:600;}
.badge-user{background:#cc0000;color:white;padding:3px 12px;border-radius:20px;font-size:.78rem;font-weight:600;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def show_login():
    logo_large = _LOGO_HTML.replace('width="110"', 'width="140"')
    st.markdown(
        f"""<div style="text-align:center;margin-top:40px;">
      {logo_large}
      <h2 style="color:#cc0000;margin-top:16px;">Dashboard KPI – SocGen CI</h2>
      <p style="color:#888;font-size:.9rem;">Saisie &amp; suivi des indicateurs de performance</p>
    </div>""",
        unsafe_allow_html=True
    )

    _, cf, _ = st.columns([1, 1.1, 1])
    with cf:
        with st.form("lf"):
            st.markdown("#### 🔐 Connexion")
            li = st.text_input("Identifiant")
            pw = st.text_input("Mot de passe", type="password")
            ok = st.form_submit_button("Se connecter", use_container_width=True, type="primary")
        if ok:
            u = get_user(li.strip().lower())
            if u and u["password"] == _hash(pw):
                st.session_state.update({"logged_in":True,"login":u["login"],
                    "role":u["role"],"nom_ref":u["nom_ref"],"display":u["display"]})
                log_connexion(u["login"], "LOGIN")
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")
        st.caption("⚠️ Accès restreint – SocGen CI 2026")


if not st.session_state.get("logged_in"):
    show_login()
    st.stop()

CUR_LOGIN   = st.session_state["login"]
CUR_ROLE    = st.session_state["role"]
CUR_NOM_REF = st.session_state["nom_ref"]
CUR_DISPLAY = st.session_state["display"]
IS_ADMIN    = CUR_ROLE == "admin"
IS_DG       = CUR_ROLE == "dg"
IS_USER     = CUR_ROLE == "user"

df_ref = load_kpi_ref()
if IS_ADMIN or IS_DG:
    df_mes_kpis = df_ref.copy()
elif IS_USER and CUR_NOM_REF and CUR_NOM_REF != "None":
    df_mes_kpis = df_ref[df_ref["nom"] == CUR_NOM_REF].copy()
else:
    df_mes_kpis = pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(_LOGO_HTML, unsafe_allow_html=True)
    st.markdown("---")
    badge = "badge-admin" if IS_ADMIN else ("badge-dg" if IS_DG else "badge-user")
    label = {"admin":"Admin","dg":"DG","user":"Responsable"}.get(CUR_ROLE,"")
    st.markdown(f'<span class="{badge}">{label}</span> &nbsp;<b>{CUR_DISPLAY}</b>', unsafe_allow_html=True)
    st.markdown("---")

    if IS_ADMIN:
        menus = ["📊 Dashboard de saisies","📈 Dashboard Global","📝 Saisie KPI",
                 "🗃️ Historique","📋 Référentiel","⚙️ Administration","🔐 Logs connexion"]
    elif IS_DG:
        menus = ["📈 Dashboard Global"]
    else:
        menus = ["📊 Mon Dashboard","📝 Saisie KPI","🗃️ Mes saisies","📋 Référentiel"]

    page = st.radio("Navigation", menus)
    st.markdown("---")
    if st.button("🚪 Se déconnecter", use_container_width=True):
        log_connexion(CUR_LOGIN, "LOGOUT")
        for k in list(st.session_state): del st.session_state[k]
        st.rerun()
    st.caption("SocGen CI · 2026")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : DASHBOARD DE SAISIES (admin) / MON DASHBOARD (user)
# ══════════════════════════════════════════════════════════════════════════════
if page in ("📊 Dashboard de saisies", "📊 Mon Dashboard"):
    titre = "📊 Dashboard de saisies" if IS_ADMIN else f"📊 Mon Dashboard – {CUR_DISPLAY}"
    st.markdown(f"# {titre}")

    df_all     = load_saisies(CUR_LOGIN)
    tot_kpis   = len(df_mes_kpis)
    saisis     = df_all["kpi"].nunique() if not df_all.empty else 0
    tx         = round(saisis/tot_kpis*100) if tot_kpis else 0
    nb         = len(df_all)

    c1,c2,c3,c4 = st.columns(4)
    for col,lbl,val in zip([c1,c2,c3,c4],
        ["KPIs assignés","KPIs saisis","Complétion","Total saisies"],
        [tot_kpis, saisis, f"{tx}%", nb]):
        col.markdown(f'<div class="kpi-card"><div class="kpi-label">{lbl}</div>'
                     f'<div class="kpi-val">{val}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    if df_all.empty:
        st.info("Aucune donnée saisie. Allez dans **Saisie KPI** pour commencer.")
    else:
        cl, cr = st.columns(2)

        with cl:
            st.markdown('<div class="section-header">Complétion par catégorie</div>', unsafe_allow_html=True)
            ct = df_mes_kpis.groupby("categorie")["kpi"].count().reset_index(name="total")
            cs = df_all.groupby("categorie")["kpi"].nunique().reset_index(name="saisis")
            cm = ct.merge(cs, on="categorie", how="left").fillna(0)
            cm["pct"] = (cm["saisis"]/cm["total"]*100).round(0)
            f1 = px.bar(cm, x="pct", y="categorie", orientation="h",
                        color="pct", color_continuous_scale=["#ffcdd2",ROUGE],
                        range_color=[0,100], text="pct", labels={"pct":"%","categorie":""})
            f1.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
            f1.update_layout(**LAYOUT, showlegend=False, coloraxis_showscale=False,
                             height=280, yaxis=dict(autorange="reversed"))
            st.plotly_chart(f1, use_container_width=True)

        with cr:
            if IS_ADMIN:
                st.markdown('<div class="section-header">Saisies par responsable</div>', unsafe_allow_html=True)
                br = df_all.groupby("nom_resp").size().reset_index(name="nb")
                f2 = px.pie(br, values="nb", names="nom_resp",
                            color_discrete_sequence=px.colors.sequential.Reds_r, hole=0.45)
                f2.update_layout(**LAYOUT, height=280)
                st.plotly_chart(f2, use_container_width=True)
            else:
                st.markdown('<div class="section-header">Mes dernières saisies</div>', unsafe_allow_html=True)
                st.dataframe(df_all[["kpi","periode","valeur","unite","date_saisie"]].head(8)
                    .rename(columns={"kpi":"KPI","periode":"Période","valeur":"Valeur","unite":"Unité","date_saisie":"Date"}),
                    use_container_width=True, hide_index=True)

        st.markdown('<div class="section-header">Évolution des saisies</div>', unsafe_allow_html=True)
        df_all["dt"] = pd.to_datetime(df_all["date_saisie"])
        dtl = df_all.groupby(df_all["dt"].dt.date).size().reset_index(name="nb")
        dtl.columns = ["date","nb"]
        f3 = px.area(dtl, x="date", y="nb", color_discrete_sequence=[ROUGE], labels={"nb":"Saisies","date":""})
        f3.update_layout(**LAYOUT, height=190)
        st.plotly_chart(f3, use_container_width=True)

        # KPIs non saisis — avec nom du responsable devant
        manquants = df_mes_kpis[~df_mes_kpis["kpi"].isin(df_all["kpi"].unique())]
        if not manquants.empty:
            st.markdown('<div class="section-header">⚠️ KPIs non encore saisis</div>', unsafe_allow_html=True)
            for _, row in manquants.iterrows():
                st.markdown(
                    f'<div class="alert-box">'
                    f'👤 <b>{row["nom"]}</b> &nbsp;·&nbsp; '
                    f'📍 <b>{row["categorie"]}</b> — {row["kpi"]} '
                    f'<span style="color:#888">· {row["periodicite"]}</span>'
                    f'</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : DASHBOARD GLOBAL (DG + admin) — stats sur historique
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Dashboard Global":
    st.markdown("# 📈 Dashboard Global")
    st.caption("Vue consolidée et statistiques sur l'ensemble des indicateurs")

    df_all = load_saisies()  # tout l'historique
    df_ref2 = load_kpi_ref()

    if df_all.empty:
        st.info("Aucune donnée disponible dans la base.")
        st.stop()

    # Filtres
    cf1, cf2, cf3 = st.columns(3)
    with cf1:
        f_cats  = st.multiselect("Catégorie", sorted(df_all["categorie"].unique()), default=sorted(df_all["categorie"].unique()))
    with cf2:
        f_resps = st.multiselect("Responsable", sorted(df_all["nom_resp"].unique()), default=sorted(df_all["nom_resp"].unique()))
    with cf3:
        f_pers  = st.multiselect("Période", sorted(df_all["periode"].unique()), default=sorted(df_all["periode"].unique()))

    df_f = df_all[df_all["categorie"].isin(f_cats) & df_all["nom_resp"].isin(f_resps) & df_all["periode"].isin(f_pers)]
    st.markdown("---")

    # Métriques
    c1,c2,c3,c4 = st.columns(4)
    for col,lbl,val in zip([c1,c2,c3,c4],
        ["KPIs référentiel","KPIs saisis","Périodes couvertes","Responsables actifs"],
        [len(df_ref2), df_f["kpi"].nunique(), df_f["periode"].nunique(), df_f["nom_resp"].nunique()]):
        col.markdown(f'<div class="kpi-card"><div class="kpi-label">{lbl}</div>'
                     f'<div class="kpi-val">{val}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    r1l, r1r = st.columns(2)
    with r1l:
        st.markdown('<div class="section-header">Saisies par catégorie</div>', unsafe_allow_html=True)
        bc = df_f.groupby("categorie").size().reset_index(name="nb").sort_values("nb")
        fc = px.bar(bc, x="nb", y="categorie", orientation="h",
                    color_discrete_sequence=[ROUGE], text="nb", labels={"nb":"Nb","categorie":""})
        fc.update_traces(textposition="outside")
        fc.update_layout(**LAYOUT, height=300, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fc, use_container_width=True)

    with r1r:
        st.markdown('<div class="section-header">Saisies par responsable</div>', unsafe_allow_html=True)
        br2 = df_f.groupby("nom_resp").size().reset_index(name="nb").sort_values("nb", ascending=False)
        fr2 = px.bar(br2, x="nom_resp", y="nb", color_discrete_sequence=[ROUGE],
                     text="nb", labels={"nb":"Nb","nom_resp":""})
        fr2.update_traces(textposition="outside")
        fr2.update_layout(**LAYOUT, height=300)
        st.plotly_chart(fr2, use_container_width=True)

    r2l, r2r = st.columns(2)
    with r2l:
        st.markdown('<div class="section-header">Évolution temporelle</div>', unsafe_allow_html=True)
        df_f2 = df_f.copy()
        df_f2["dt"] = pd.to_datetime(df_f2["date_saisie"])
        dtl2 = df_f2.groupby(df_f2["dt"].dt.date).size().reset_index(name="nb")
        dtl2.columns = ["date","nb"]
        ftl = px.area(dtl2, x="date", y="nb", color_discrete_sequence=[ROUGE], labels={"nb":"Saisies","date":""})
        ftl.update_layout(**LAYOUT, height=260)
        st.plotly_chart(ftl, use_container_width=True)

    with r2r:
        st.markdown('<div class="section-header">Complétion par responsable</div>', unsafe_allow_html=True)
        ref_r = df_ref2.groupby("nom")["kpi"].count().reset_index(name="total").rename(columns={"nom":"nom_resp"})
        sai_r = df_f.groupby("nom_resp")["kpi"].nunique().reset_index(name="saisis")
        comp  = ref_r.merge(sai_r, on="nom_resp", how="left").fillna(0)
        comp["pct"] = (comp["saisis"]/comp["total"]*100).round(0)
        fcp = px.bar(comp, x="pct", y="nom_resp", orientation="h",
                     color="pct", color_continuous_scale=["#ffcdd2",ROUGE],
                     range_color=[0,100], text="pct", labels={"pct":"%","nom_resp":""})
        fcp.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fcp.update_layout(**LAYOUT, showlegend=False, coloraxis_showscale=False,
                          height=260, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fcp, use_container_width=True)

    # Tableau dernière valeur par KPI
    st.markdown('<div class="section-header">Dernière valeur saisie par KPI</div>', unsafe_allow_html=True)
    df_last = (df_f.sort_values("date_saisie", ascending=False)
               .groupby(["categorie","kpi","nom_resp"]).first().reset_index()
               [["categorie","kpi","nom_resp","periode","valeur","unite","date_saisie"]])
    st.dataframe(df_last.rename(columns={
        "categorie":"Catégorie","kpi":"KPI","nom_resp":"Responsable",
        "periode":"Période","valeur":"Valeur","unite":"Unité","date_saisie":"Dernière saisie"}),
        use_container_width=True, height=380, hide_index=True)

    # Alertes manquants
    manq = df_ref2[~df_ref2["kpi"].isin(df_f["kpi"].unique())]
    if not manq.empty:
        st.markdown('<div class="section-header">⚠️ KPIs absents de la sélection</div>', unsafe_allow_html=True)
        for _, row in manq.iterrows():
            st.markdown(
                f'<div class="alert-box">👤 <b>{row["nom"]}</b> &nbsp;·&nbsp; '
                f'📍 <b>{row["categorie"]}</b> — {row["kpi"]}</div>',
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : SAISIE KPI
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📝 Saisie KPI":
    st.markdown("# 📝 Formulaire de saisie KPI")

    if df_mes_kpis.empty:
        st.warning("Aucun KPI assigné à votre compte. Contactez l'administrateur.")
        st.stop()

    cats = df_mes_kpis["categorie"].unique().tolist()
    with st.form("fs", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Identification**")
            cat  = st.selectbox("Catégorie *", cats)
            kpis = df_mes_kpis[df_mes_kpis["categorie"]==cat]["kpi"].tolist()
            kpi  = st.selectbox("KPI *", kpis)
        with c2:
            st.markdown("**Données**")
            per = st.text_input("Période *", value=datetime.now().strftime("%B %Y"))
            val = st.number_input("Valeur *", value=0.0, format="%.4f")
            uni = st.text_input("Unité", placeholder="%, FCFA, nombre…")
            com = st.text_area("Commentaire", height=80)

        ik = df_mes_kpis[df_mes_kpis["kpi"]==kpi].iloc[0] if kpi else None
        if ik is not None:
            st.info(f"📧 **{ik['nom']}** ({ik['email']}) · Périodicité : **{ik['periodicite']}**")

        sub = st.form_submit_button("✅ Enregistrer", use_container_width=True, type="primary")
        if sub:
            if not per.strip():
                st.error("La période est obligatoire.")
            else:
                insert_saisie({"login":CUR_LOGIN,"nom_resp":CUR_NOM_REF or CUR_DISPLAY,
                               "categorie":cat,"kpi":kpi,
                               "periodicite":ik["periodicite"] if ik is not None else "",
                               "periode":per.strip(),"valeur":val,"unite":uni,"commentaire":com})
                st.success(f"✅ **{kpi}** – période **{per}** enregistré !")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : HISTORIQUE / MES SAISIES
# ══════════════════════════════════════════════════════════════════════════════
elif page in ("🗃️ Historique","🗃️ Mes saisies"):
    st.markdown(f"# {'🗃️ Historique global' if IS_ADMIN else '🗃️ Mes saisies'}")
    df_h = load_saisies(CUR_LOGIN)

    if df_h.empty:
        st.info("Aucune donnée disponible.")
    else:
        cf1, cf2, cf3 = st.columns(3)
        with cf1: f_cat = st.multiselect("Catégorie", df_h["categorie"].unique().tolist(), default=df_h["categorie"].unique().tolist())
        with cf2: f_per = st.text_input("Période")
        with cf3:
            f_resp = None
            if IS_ADMIN:
                f_resp = st.multiselect("Responsable", df_h["nom_resp"].unique().tolist(), default=df_h["nom_resp"].unique().tolist())

        df_f = df_h[df_h["categorie"].isin(f_cat)]
        if f_per: df_f = df_f[df_f["periode"].str.contains(f_per, case=False, na=False)]
        if IS_ADMIN and f_resp: df_f = df_f[df_f["nom_resp"].isin(f_resp)]

        cols = (["id","nom_resp","categorie","kpi","periodicite","periode","valeur","unite","commentaire","date_saisie"]
                if IS_ADMIN else
                ["id","categorie","kpi","periodicite","periode","valeur","unite","commentaire","date_saisie"])
        rmap = {"id":"ID","nom_resp":"Responsable","categorie":"Catégorie","kpi":"KPI",
                "periodicite":"Périodicité","periode":"Période","valeur":"Valeur",
                "unite":"Unité","commentaire":"Commentaire","date_saisie":"Date saisie"}

        st.dataframe(df_f[cols].rename(columns=rmap), use_container_width=True, height=420)
        st.caption(f"{len(df_f)} enregistrement(s)")

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button("⬇️ Exporter CSV", data=df_f.to_csv(index=False).encode(),
                               file_name=f"kpi_{CUR_LOGIN}.csv", mime="text/csv")
        with dl2:
            if IS_ADMIN:
                st.download_button("⬇️ Exporter Excel (.xlsx)",
                                   data=to_xlsx(df_f[cols].rename(columns=rmap)),
                                   file_name="historique_kpi.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        with st.expander("🗑️ Supprimer un enregistrement"):
            did = st.number_input("ID à supprimer", min_value=1, step=1)
            if st.button("Supprimer", type="secondary"):
                delete_saisie(int(did), CUR_LOGIN)
                st.success(f"Ligne #{did} supprimée.")
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : RÉFÉRENTIEL
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Référentiel":
    st.markdown("# 📋 Référentiel des KPIs")
    if not IS_ADMIN:
        st.info(f"Affichage filtré : KPIs de **{CUR_DISPLAY}**")

    srch = st.text_input("🔍 Rechercher")
    dfs  = df_mes_kpis.copy()
    if srch:
        dfs = dfs[dfs.apply(lambda r: r.astype(str).str.contains(srch, case=False).any(), axis=1)]

    for cat in dfs["categorie"].unique():
        st.markdown(f'<div class="section-header">{cat}</div>', unsafe_allow_html=True)
        sub = (dfs[dfs["categorie"]==cat][["kpi","periodicite","nom","email"]]
               .rename(columns={"kpi":"KPI","periodicite":"Périodicité","nom":"Responsable","email":"Email"}))
        st.dataframe(sub, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : ADMINISTRATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Administration":
    if not IS_ADMIN:
        st.error("Accès réservé à l'administrateur.")
        st.stop()

    st.markdown("# ⚙️ Administration")
    tab_k, tab_u = st.tabs(["📋 Gestion des KPIs", "👤 Gestion des utilisateurs"])

    # ─ KPIs ─
    with tab_k:
        st.markdown("### ➕ Ajouter un KPI")
        df_rc = load_kpi_ref()
        cats_e = sorted(df_rc["categorie"].unique().tolist())
        noms_e = sorted(df_rc["nom"].dropna().unique().tolist())

        with st.form("add_kpi", clear_on_submit=True):
            k1, k2 = st.columns(2)
            with k1:
                cm  = st.radio("Catégorie", ["Existante","Nouvelle"], horizontal=True)
                ncat = st.selectbox("Catégorie existante", cats_e) if cm=="Existante" else st.text_input("Nouvelle catégorie")
                nkpi = st.text_input("Libellé du KPI *")
                nper = st.selectbox("Périodicité", ["Mensuelle","Trimestrielle","Annuelle","Hebdomadaire"])
            with k2:
                rm   = st.radio("Responsable", ["Existant","Nouveau"], horizontal=True)
                nnom = st.selectbox("Responsable existant", noms_e) if rm=="Existant" else st.text_input("Nom du responsable")
                neml = st.text_input("Email du responsable")

            if st.form_submit_button("➕ Ajouter", type="primary", use_container_width=True):
                if not ncat or not nkpi or not nnom:
                    st.error("Catégorie, KPI et responsable obligatoires.")
                else:
                    ok, msg = add_kpi(ncat.strip(), nkpi.strip(), nper, neml.strip(), nnom.strip())
                    st.success(msg) if ok else st.error(msg)
                    if ok: st.rerun()

        st.markdown("### KPIs existants")
        df_rc2 = load_kpi_ref()
        st.dataframe(df_rc2[["id","categorie","kpi","periodicite","nom","email"]]
            .rename(columns={"id":"ID","categorie":"Catégorie","kpi":"KPI",
                             "periodicite":"Périodicité","nom":"Responsable","email":"Email"}),
            use_container_width=True, height=340, hide_index=True)

        with st.expander("🗑️ Supprimer un KPI par ID"):
            dkid = st.number_input("ID KPI", min_value=1, step=1, key="dkid")
            if st.button("Supprimer ce KPI", type="secondary"):
                delete_kpi(int(dkid))
                st.success(f"KPI #{dkid} supprimé.")
                st.rerun()

    # ─ Utilisateurs ─
    with tab_u:
        st.markdown("### ➕ Ajouter un utilisateur")
        df_rc3 = load_kpi_ref()
        noms_u = sorted(df_rc3["nom"].dropna().unique().tolist())

        with st.form("add_user", clear_on_submit=True):
            u1, u2 = st.columns(2)
            with u1:
                ulg  = st.text_input("Identifiant (login) *")
                udn  = st.text_input("Nom complet *")
                ueml = st.text_input("Email")
            with u2:
                urol = st.selectbox("Rôle *", ["user","admin","dg"])
                unr  = st.selectbox("Référentiel responsable (si rôle 'user')", ["(aucun)"] + noms_u)
                upw  = st.text_input("Mot de passe *", type="password")
                upw2 = st.text_input("Confirmer mot de passe *", type="password")

            if st.form_submit_button("➕ Créer", type="primary", use_container_width=True):
                if not ulg or not udn or not upw:
                    st.error("Login, nom et mot de passe obligatoires.")
                elif upw != upw2:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    nr = None if unr == "(aucun)" else unr
                    ok2, msg2 = add_user(ulg, upw, urol, nr, udn, ueml)
                    st.success(msg2) if ok2 else st.error(msg2)
                    if ok2: st.rerun()

        st.markdown("### Utilisateurs")
        st.dataframe(load_users().rename(columns={
            "id":"ID","login":"Login","role":"Rôle","nom_ref":"Réf. KPI",
            "display":"Nom","email":"Email","actif":"Actif"}),
            use_container_width=True, height=300, hide_index=True)

        with st.expander("🔒 Activer / Désactiver"):
            uid2  = st.number_input("ID utilisateur", min_value=1, step=1, key="uid2")
            stat  = st.radio("Action", ["Activer","Désactiver"], horizontal=True)
            if st.button("Appliquer", type="secondary"):
                toggle_user(int(uid2), 1 if stat=="Activer" else 0)
                st.success(f"Utilisateur #{uid2} → {stat.lower()}.")
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : LOGS CONNEXION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔐 Logs connexion":
    if not IS_ADMIN:
        st.error("Accès réservé à l'administrateur.")
        st.stop()

    st.markdown("# 🔐 Logs de connexion")
    df_logs = load_logs()
    if df_logs.empty:
        st.info("Aucun log.")
    else:
        st.dataframe(df_logs.rename(columns={"id":"ID","login":"Login","action":"Action","timestamp":"Horodatage"}),
                     use_container_width=True, height=420)
        lc1, lc2 = st.columns(2)
        with lc1:
            st.download_button("⬇️ CSV", data=df_logs.to_csv(index=False).encode(),
                               file_name="logs.csv", mime="text/csv")
        with lc2:
            st.download_button("⬇️ Excel (.xlsx)", data=to_xlsx(df_logs),
                               file_name="logs.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
