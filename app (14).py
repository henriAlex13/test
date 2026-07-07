"""
Dashboard KPI — Suivi des indicateurs (modèle SGCI)
====================================================

Stockage 100% SQLite (kpi_data.db). Tables : referentiel, users, saisies, historique.
L'affectation est portée par la colonne « username » du référentiel
(un indicateur = un responsable). Plus de fichier/table « affectations ».

Rôles :
  - saisie : formulaires de SES indicateurs + tableau de bord + historique
  - admin  : vue « Pilotage » (Vue d'ensemble + Analyse + Historique + Saisie) + Référentiel + Comptes
  - dg     : vue dédiée (à venir)

Lancement :
    pip install -r requirements.txt
    streamlit run app.py
"""

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "kpi_data.db"
REFERENTIEL_PATH = APP_DIR / "referentiel_kpi.csv"  # amorçage initial
USERS_PATH = APP_DIR / "users.csv"                  # amorçage initial

SALT = "SGCI-KPI-2026"  # À CHANGER en production (st.secrets / variable d'env.)

MOIS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
ANNEES = [2027, 2026, 2025, 2024]

st.set_page_config(page_title="Dashboard KPI", page_icon="📊", layout="wide")


# --------------------------------------------------------------------------- #
# Habillage
# --------------------------------------------------------------------------- #
def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        html, body, [class*="css"], .stMarkdown, .stText { font-family:'Inter',system-ui,Segoe UI,sans-serif; }
        .block-container { padding-top:1.4rem; padding-bottom:2rem; max-width:1200px; }
        .app-header{ background:linear-gradient(135deg,#C8102E 0%,#7d0a1c 100%); color:#fff;
            border-radius:16px;padding:22px 28px;margin-bottom:22px;box-shadow:0 8px 22px rgba(200,16,46,.22);}
        .app-header h1{font-size:1.5rem;margin:0;font-weight:800;color:#fff;letter-spacing:-.3px;}
        .app-header p{margin:.3rem 0 0;opacity:.92;font-size:.92rem;color:#fff;}
        div[data-testid="stMetric"]{ background:#fff;border:1px solid #ECEEF3;border-left:4px solid #C8102E;
            border-radius:14px;padding:14px 18px;box-shadow:0 1px 3px rgba(16,24,40,.06);}
        div[data-testid="stMetricLabel"] p{font-size:.78rem;color:#6B7280;font-weight:600;
            text-transform:uppercase;letter-spacing:.4px;}
        div[data-testid="stMetricValue"]{font-size:1.4rem;font-weight:800;color:#1F2430;}
        section[data-testid="stSidebar"]{background:#14161D;}
        section[data-testid="stSidebar"] *{color:#E5E7EB;}
        section[data-testid="stSidebar"] h1{color:#fff;}
        .user-badge{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);
            border-radius:12px;padding:12px 14px;margin:6px 0 4px;}
        .user-badge .nm{font-weight:700;font-size:.98rem;color:#fff;}
        .user-badge .rl{font-size:.78rem;color:#C8102E;font-weight:600;background:rgba(200,16,46,.16);
            padding:2px 8px;border-radius:20px;display:inline-block;margin-top:4px;}
        .stButton>button, .stDownloadButton>button, div[data-testid="stFormSubmitButton"]>button{
            border-radius:10px;font-weight:600; }
        hr{margin:1.1rem 0;}
        .stDataFrame{border-radius:12px;overflow:hidden;border:1px solid #ECEEF3;}
        .section-title{font-size:1.05rem;font-weight:700;color:#1F2430;margin:.2rem 0 .6rem;}
        .soon-card{max-width:560px;margin:3rem auto;text-align:center;background:#fff;border:1px dashed #C8102E;
            border-radius:18px;padding:46px 30px;box-shadow:0 8px 24px rgba(16,24,40,.06);}
        .soon-card .emoji{font-size:3rem;} .soon-card h2{margin:.4rem 0 .2rem;color:#1F2430;font-weight:800;}
        .soon-card p{color:#6B7280;margin:0;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def header(titre, sous_titre=""):
    st.markdown(f'<div class="app-header"><h1>{titre}</h1>'
                f'{f"<p>{sous_titre}</p>" if sous_titre else ""}</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Base de données
# --------------------------------------------------------------------------- #
def get_conn():
    return sqlite3.connect(DB_PATH)


def _lire_csv(path):
    """Lecture robuste : détecte le séparateur (',' ou ';'), gère le BOM/accents."""
    df = pd.read_csv(path, dtype=str, sep=None, engine="python",
                     encoding="utf-8-sig").fillna("")
    df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]
    return df


def _seed_depuis_csv(conn, table, csv_path, colonnes):
    vide = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    if vide and csv_path.exists():
        df = _lire_csv(csv_path)
        df = df[[c for c in colonnes if c in df.columns]]
        if not df.empty and len(df.columns) > 0:
            df.to_sql(table, conn, if_exists="append", index=False)


def init_db():
    with get_conn() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS saisies (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   kpi TEXT NOT NULL, periode TEXT NOT NULL, periode_sort TEXT NOT NULL,
                   valeur REAL, commentaire TEXT, saisi_par TEXT, date_saisie TEXT,
                   UNIQUE (kpi, periode))""")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS historique (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   kpi TEXT NOT NULL, periode TEXT NOT NULL, periode_sort TEXT,
                   valeur REAL, commentaire TEXT, saisi_par TEXT, date_saisie TEXT)""")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS referentiel (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   categorie TEXT, kpi TEXT UNIQUE, periodicite TEXT,
                   direction TEXT, contact TEXT, username TEXT)""")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
                   username TEXT PRIMARY KEY, password_hash TEXT, nom TEXT, role TEXT)""")

        # Compat : colonne username si absente sur une base antérieure
        cols = [r[1] for r in conn.execute("PRAGMA table_info(referentiel)").fetchall()]
        if "username" not in cols:
            conn.execute("ALTER TABLE referentiel ADD COLUMN username TEXT")

        # Amorçage initial depuis CSV (si tables vides)
        _seed_depuis_csv(conn, "referentiel", REFERENTIEL_PATH,
                         ["categorie", "kpi", "periodicite", "direction", "contact", "username"])
        _seed_depuis_csv(conn, "users", USERS_PATH,
                         ["username", "password_hash", "nom", "role"])

        # Migration d'une ancienne colonne 'affectations' (pipe) -> username (1er responsable)
        if "affectations" in cols:
            for rid, a in conn.execute(
                "SELECT id, affectations FROM referentiel "
                "WHERE (username IS NULL OR username='') AND affectations IS NOT NULL "
                "AND affectations<>''").fetchall():
                premier = str(a).split("|")[0].strip()
                if premier:
                    conn.execute("UPDATE referentiel SET username=? WHERE id=?", (premier, rid))

        # Migration d'une ancienne table 'affectations' -> username, puis suppression
        if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='affectations'").fetchone():
            deja = conn.execute("SELECT COUNT(*) FROM referentiel "
                                "WHERE username IS NOT NULL AND username<>''").fetchone()[0]
            if deja == 0:
                conn.execute(
                    """UPDATE referentiel SET username=(
                           SELECT a.username FROM affectations a WHERE a.kpi=referentiel.kpi LIMIT 1)
                       WHERE EXISTS (SELECT 1 FROM affectations a WHERE a.kpi=referentiel.kpi)""")
            conn.execute("DROP TABLE affectations")

        conn.execute("UPDATE referentiel SET username='' WHERE username IS NULL")


def enregistrer_saisie(kpi, periode, periode_sort, valeur, commentaire, saisi_par):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO saisies (kpi, periode, periode_sort, valeur, commentaire, saisi_par, date_saisie)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(kpi, periode) DO UPDATE SET
                   valeur=excluded.valeur, commentaire=excluded.commentaire,
                   saisi_par=excluded.saisi_par, date_saisie=excluded.date_saisie""",
            (kpi, periode, periode_sort, valeur, commentaire, saisi_par, ts))
        conn.execute(
            """INSERT INTO historique (kpi, periode, periode_sort, valeur, commentaire, saisi_par, date_saisie)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (kpi, periode, periode_sort, valeur, commentaire, saisi_par, ts))


def lire_saisies():
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM saisies", conn)


def lire_historique():
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM historique", conn)


def etat_courant_depuis_historique():
    h = lire_historique()
    if h.empty:
        return h
    return h.sort_values("date_saisie").drop_duplicates(["kpi", "periode"], keep="last")


# --------------------------------------------------------------------------- #
# Comptes & référentiel
# --------------------------------------------------------------------------- #
def hash_mdp(mdp: str) -> str:
    return hashlib.sha256((SALT + mdp).encode("utf-8")).hexdigest()


def charger_users() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query("SELECT username, password_hash, nom, role FROM users", conn).fillna("")


def ajouter_user(username, mdp, nom, role):
    with get_conn() as conn:
        conn.execute("INSERT INTO users (username, password_hash, nom, role) VALUES (?, ?, ?, ?)",
                     (username, hash_mdp(mdp), nom, role))


def modifier_user(username, nom, role, mdp=None):
    with get_conn() as conn:
        if mdp:
            conn.execute("UPDATE users SET nom=?, role=?, password_hash=? WHERE username=?",
                         (nom, role, hash_mdp(mdp), username))
        else:
            conn.execute("UPDATE users SET nom=?, role=? WHERE username=?", (nom, role, username))


def supprimer_user(username):
    with get_conn() as conn:
        conn.execute("UPDATE referentiel SET username='' WHERE username=?", (username,))
        conn.execute("DELETE FROM users WHERE username=?", (username,))
    charger_referentiel.clear()


def _norm(s):
    """Normalise un intitulé : espaces insécables -> espace, espaces multiples réduits, trim."""
    return " ".join(str(s).replace("\u00a0", " ").split())


@st.cache_data
def charger_referentiel():
    with get_conn() as conn:
        ref = pd.read_sql_query(
            "SELECT categorie, kpi, periodicite, direction, contact, username "
            "FROM referentiel ORDER BY id", conn)
    ref = ref.fillna("")
    ref["kpi"] = ref["kpi"].map(_norm)
    return ref


def ajouter_kpi(categorie, kpi, periodicite, direction, contact="", username=""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO referentiel (categorie, kpi, periodicite, direction, contact, username) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (categorie, _norm(kpi), periodicite, direction, contact, username))
    charger_referentiel.clear()


def affecter_kpis(username, kpis):
    """Affecte un ensemble de KPIs à un utilisateur (un KPI = un responsable).

    La correspondance se fait sur l'intitulé NORMALISÉ (insensible aux espaces
    superflus / insécables) puis par identifiant de ligne, pour éviter qu'un KPI
    ne soit ignoré à cause d'un espace parasite en base.
    """
    cible = {_norm(k) for k in kpis}
    with get_conn() as conn:
        rows = conn.execute("SELECT id, kpi FROM referentiel").fetchall()
        ids = [rid for rid, k in rows if _norm(k) in cible]
        conn.execute("UPDATE referentiel SET username='' WHERE username = ?", (username,))
        if ids:
            conn.executemany("UPDATE referentiel SET username = ? WHERE id = ?",
                             [(username, i) for i in ids])
    charger_referentiel.clear()


def kpis_autorises(auth, ref) -> list:
    if auth["role"] in ("admin", "dg"):
        return ref["kpi"].tolist()
    return ref.loc[ref["username"] == auth["username"], "kpi"].tolist()


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def type_kpi(nom: str) -> str:
    n = nom.lower()
    if any(m in n for m in ("taux", "pourcentage", "%", "disponibilité")):
        return "pct"
    if any(m in n for m in ("montant", "encours")):
        return "fcfa"
    return "nombre"


def formater(valeur, nom):
    if valeur is None or pd.isna(valeur):
        return "—"
    t = type_kpi(nom)
    if t == "pct":
        return f"{valeur:,.2f} %".replace(",", " ")
    if t == "fcfa":
        return f"{valeur:,.0f} FCFA".replace(",", " ")
    return f"{valeur:,.0f}".replace(",", " ")


def construire_periode(periodicite, annee, mois_idx=None, trimestre=None):
    if periodicite == "Mensuelle":
        m = mois_idx + 1
        return f"{MOIS[mois_idx]} {annee}", f"{annee}-{m:02d}", f"{annee}-{m:02d}"
    q = int(trimestre[1])
    fin = q * 3
    return f"{trimestre} {annee}", f"{annee}-{trimestre}", f"{annee}-{fin:02d}"


# --------------------------------------------------------------------------- #
# PAGE : Connexion
# --------------------------------------------------------------------------- #
def page_login(users):
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown('<div class="app-header" style="text-align:center"><h1>📊 Dashboard KPI</h1>'
                    '<p>Suivi des indicateurs de pilotage</p></div>', unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Identifiant")
            p = st.text_input("Mot de passe", type="password")
            ok = st.form_submit_button("Se connecter", type="primary", use_container_width=True)
        if ok:
            row = users[users["username"] == u.strip()]
            if not row.empty and row.iloc[0]["password_hash"] == hash_mdp(p):
                st.session_state.auth = {"username": u.strip(), "nom": row.iloc[0]["nom"],
                                         "role": row.iloc[0]["role"]}
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")


# --------------------------------------------------------------------------- #
# CORPS : Saisie
# --------------------------------------------------------------------------- #
def corps_saisie(ref_user, auth, prefix="sa"):
    if ref_user.empty:
        st.info("Aucun KPI ne vous est affecté. Contactez l'administrateur.")
        return
    periodicites = sorted(ref_user["periodicite"].unique())
    c0, c3, c4 = st.columns(3)
    periodicite = c0.selectbox("Périodicité", periodicites, key=f"{prefix}_periodicite")
    annee = c3.selectbox("Année", ANNEES, index=1, key=f"{prefix}_annee")
    if periodicite == "Mensuelle":
        mois = c4.selectbox("Mois", MOIS, index=min(datetime.now().month - 1, 11), key=f"{prefix}_mois")
        p_aff, p_sto, p_sort = construire_periode(periodicite, annee, mois_idx=MOIS.index(mois))
    else:
        trimestre = c4.selectbox("Trimestre", ["T1", "T2", "T3", "T4"], key=f"{prefix}_trim")
        p_aff, p_sto, p_sort = construire_periode(periodicite, annee, trimestre=trimestre)

    ref_sel = ref_user[ref_user["periodicite"] == periodicite]
    deja = lire_saisies().pipe(lambda d: d[d["periode"] == p_sto]).set_index("kpi")["valeur"].to_dict()

    st.markdown(f'<div class="section-title">Indicateurs · {p_aff}</div>', unsafe_allow_html=True)
    with st.form(f"form_saisie_{prefix}"):
        valeurs = {}
        for domaine, grp in ref_sel.groupby("categorie"):
            st.markdown(f"**{domaine}**")
            lignes = list(grp.iterrows())
            cols = st.columns(2)
            for i, (_, row) in enumerate(lignes):
                kpi = row["kpi"]
                unite = {"pct": "%", "fcfa": "FCFA", "nombre": "Nombre"}[type_kpi(kpi)]
                with cols[i % 2]:
                    valeurs[kpi] = st.number_input(
                        f"{kpi} ({unite})",
                        value=float(deja[kpi]) if kpi in deja and pd.notna(deja[kpi]) else None,
                        step=1.0, format="%.2f", key=f"in_{prefix}_{kpi}_{p_sto}",
                        help=f"Direction : {row['direction']}")
        commentaire = st.text_area("Commentaire (optionnel)", height=70, key=f"{prefix}_comm")
        submit = st.form_submit_button("💾 Enregistrer", type="primary")
    if submit:
        n = 0
        for kpi, val in valeurs.items():
            if val is not None:
                enregistrer_saisie(kpi, p_sto, p_sort, val, commentaire, auth["nom"])
                n += 1
        st.success(f"{n} valeur(s) enregistrée(s) pour {p_aff}.")
        st.rerun()


def page_saisie(ref_user, auth):
    header("Saisie des indicateurs", "Renseignez les valeurs de la période sélectionnée")
    corps_saisie(ref_user, auth)


# --------------------------------------------------------------------------- #
# CORPS : Analyse (tableau de bord)
# --------------------------------------------------------------------------- #
def corps_dashboard(ref_user, auth, prefix="db"):
    if ref_user.empty:
        st.info("Aucun KPI dans le périmètre.")
        return
    data = lire_saisies().merge(ref_user, on="kpi", how="inner")
    if data.empty:
        st.info("Aucune donnée saisie pour ce périmètre.")
        return

    f1, f2 = st.columns(2)
    doms = f1.multiselect("Domaine(s)", sorted(ref_user["categorie"].unique()),
                          default=sorted(ref_user["categorie"].unique()), key=f"{prefix}_doms")
    dirs_dispo = sorted(ref_user[ref_user["categorie"].isin(doms)]["direction"].unique())
    dirs = f2.multiselect("Direction(s)", dirs_dispo, default=dirs_dispo, key=f"{prefix}_dirs")

    perim = ref_user[ref_user["categorie"].isin(doms) & ref_user["direction"].isin(dirs)]
    data = data[data["categorie"].isin(doms) & data["direction"].isin(dirs)]
    if data.empty:
        st.warning("Aucune donnée pour ces filtres.")
        return

    nb_total = perim.shape[0]
    nb_renseignes = data["kpi"].nunique()
    taux = nb_renseignes / nb_total if nb_total else 0
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("KPIs au périmètre", nb_total)
    m2.metric("KPIs renseignés", nb_renseignes)
    m3.metric("Taux de remplissage", f"{taux*100:.0f} %")
    m4.metric("Dernière mise à jour", data["date_saisie"].max() or "—")
    st.progress(taux, text=f"Complétude : {nb_renseignes}/{nb_total} KPIs")

    st.divider()
    periodes = (data[["periode", "periode_sort"]].drop_duplicates()
                .sort_values("periode_sort", ascending=False))
    p_ref = st.selectbox("Période de référence", periodes["periode"].tolist(), key=f"{prefix}_per")
    p_ref_sort = periodes[periodes["periode"] == p_ref]["periode_sort"].iloc[0]

    lignes = []
    for _, row in perim.iterrows():
        kpi = row["kpi"]
        s = data[data["kpi"] == kpi].sort_values("periode_sort")
        s_upto = s[s["periode_sort"] <= p_ref_sort]
        val = s_upto["valeur"].iloc[-1] if len(s_upto) else None
        lignes.append({"KPI": kpi, "Domaine": row["categorie"], "Direction": row["direction"],
                       "Valeur": formater(val, kpi)})
    st.markdown(f'<div class="section-title">Valeurs — {p_ref}</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(lignes), use_container_width=True, hide_index=True)

    st.divider()
    st.markdown('<div class="section-title">Évolution d\'un indicateur</div>', unsafe_allow_html=True)
    kpi_choisi = st.selectbox("Choisir un KPI", sorted(data["kpi"].unique()), key=f"{prefix}_kpi")
    serie = (data[data["kpi"] == kpi_choisi].sort_values("periode_sort")
             [["periode", "valeur"]].set_index("periode"))
    if not serie.empty:
        st.line_chart(serie, y="valeur", color="#C8102E")

    st.download_button("⬇️ Exporter (CSV)", data.to_csv(index=False).encode("utf-8-sig"),
                       file_name="export_saisies_kpi.csv", mime="text/csv", key=f"{prefix}_dl")


def page_dashboard(ref_user, auth):
    header("Tableau de bord", "Suivi et analyse de vos indicateurs")
    corps_dashboard(ref_user, auth)


# --------------------------------------------------------------------------- #
# CORPS : Historique
# --------------------------------------------------------------------------- #
def corps_historique(ref_user, auth, prefix="hi"):
    if ref_user.empty:
        st.info("Aucun KPI dans le périmètre.")
        return
    hist = lire_historique().merge(ref_user, on="kpi", how="inner")
    if hist.empty:
        st.info("Aucun enregistrement pour le moment. Les saisies apparaîtront ici.")
        return
    hist = hist.sort_values("date_saisie", ascending=False)

    c1, c2, c3 = st.columns(3)
    c1.metric("Enregistrements", len(hist))
    c2.metric("Contributeurs", hist["saisi_par"].nunique())
    c3.metric("Dernière saisie", hist["date_saisie"].max())

    st.divider()
    f1, f2, f3 = st.columns(3)
    doms = f1.multiselect("Domaine(s)", sorted(hist["categorie"].unique()), key=f"{prefix}_doms")
    auteurs = f2.multiselect("Contributeur(s)", sorted(hist["saisi_par"].dropna().unique()), key=f"{prefix}_aut")
    periodes = f3.multiselect("Période(s)", sorted(hist["periode"].unique()), key=f"{prefix}_per")
    vue = hist.copy()
    if doms:
        vue = vue[vue["categorie"].isin(doms)]
    if auteurs:
        vue = vue[vue["saisi_par"].isin(auteurs)]
    if periodes:
        vue = vue[vue["periode"].isin(periodes)]
    if vue.empty:
        st.warning("Aucun enregistrement pour ces filtres.")
        return

    affichage = pd.DataFrame({
        "Date & heure": vue["date_saisie"], "KPI": vue["kpi"], "Domaine": vue["categorie"],
        "Direction": vue["direction"], "Période": vue["periode"],
        "Valeur": [formater(v, k) for v, k in zip(vue["valeur"], vue["kpi"])],
        "Saisi par": vue["saisi_par"], "Commentaire": vue["commentaire"].fillna(""),
    })
    st.markdown(f'<div class="section-title">{len(affichage)} enregistrement(s)</div>', unsafe_allow_html=True)
    st.dataframe(affichage, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Exporter l'historique (CSV)",
                       affichage.to_csv(index=False).encode("utf-8-sig"),
                       file_name="historique_saisies.csv", mime="text/csv", key=f"{prefix}_dl")


def page_historique(ref_user, auth):
    header("Historique des saisies", "Journal complet des enregistrements de formulaires")
    corps_historique(ref_user, auth)


# --------------------------------------------------------------------------- #
# CORPS : Vue d'ensemble (consolidée — tous les indicateurs)
# --------------------------------------------------------------------------- #
def corps_vue_ensemble(ref, prefix="ve"):
    etat = etat_courant_depuis_historique()
    if etat.empty:
        st.info("Aucune donnée enregistrée pour le moment.")
        return
    data = etat.merge(ref, on="kpi", how="inner")
    hist = lire_historique()

    nb_total = ref.shape[0]
    nb_renseignes = data["kpi"].nunique()
    taux = nb_renseignes / nb_total if nb_total else 0
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Indicateurs suivis", nb_total)
    m2.metric("Renseignés", nb_renseignes)
    m3.metric("Complétude", f"{taux*100:.0f} %")
    m4.metric("Contributeurs", hist["saisi_par"].nunique())
    m5.metric("Dernière saisie", hist["date_saisie"].max())
    st.progress(taux, text=f"Couverture globale : {nb_renseignes}/{nb_total} indicateurs")

    st.divider()
    st.markdown('<div class="section-title">Complétude par domaine</div>', unsafe_allow_html=True)
    syn = []
    for dom, grp in ref.groupby("categorie"):
        total = grp["kpi"].nunique()
        rens = data[data["categorie"] == dom]["kpi"].nunique()
        syn.append({"Domaine": dom, "Renseignés": rens, "Total": total,
                    "Taux (%)": round(rens / total * 100, 0) if total else 0})
    syn_df = pd.DataFrame(syn)
    cc1, cc2 = st.columns([1.2, 1])
    cc1.bar_chart(syn_df.set_index("Domaine")["Taux (%)"], color="#C8102E", height=300)
    cc2.dataframe(syn_df, use_container_width=True, hide_index=True)

    st.divider()
    periodes = (data[["periode", "periode_sort"]].drop_duplicates()
                .sort_values("periode_sort", ascending=False))
    p_ref = st.selectbox("Période de référence", periodes["periode"].tolist(), key=f"{prefix}_per")
    p_ref_sort = periodes[periodes["periode"] == p_ref]["periode_sort"].iloc[0]

    st.markdown(f'<div class="section-title">Indicateurs au {p_ref}</div>', unsafe_allow_html=True)
    domaines = sorted(ref["categorie"].unique())
    for dom in domaines:
        kpis_dom = ref[ref["categorie"] == dom]
        lignes = []
        for _, row in kpis_dom.iterrows():
            kpi = row["kpi"]
            s = data[data["kpi"] == kpi].sort_values("periode_sort")
            s_upto = s[s["periode_sort"] <= p_ref_sort]
            val = s_upto["valeur"].iloc[-1] if len(s_upto) else None
            lignes.append({"KPI": kpi, "Direction": row["direction"], "Valeur": formater(val, kpi)})
        renseignes = sum(1 for x in lignes if x["Valeur"] != "—")
        with st.expander(f"{dom}  ·  {renseignes}/{len(lignes)} renseignés", expanded=(dom == domaines[0])):
            st.dataframe(pd.DataFrame(lignes), use_container_width=True, hide_index=True)

    st.divider()
    st.markdown('<div class="section-title">Évolution d\'un indicateur</div>', unsafe_allow_html=True)
    kpi_choisi = st.selectbox("Choisir un indicateur", sorted(data["kpi"].unique()), key=f"{prefix}_kpi")
    serie = (data[data["kpi"] == kpi_choisi].sort_values("periode_sort")
             [["periode", "valeur"]].set_index("periode"))
    if not serie.empty:
        st.line_chart(serie, y="valeur", color="#C8102E")

    st.download_button("⬇️ Exporter la vue consolidée (CSV)",
                       data.to_csv(index=False).encode("utf-8-sig"),
                       file_name="vue_consolidee.csv", mime="text/csv", key=f"{prefix}_dl")


# --------------------------------------------------------------------------- #
# PAGE : Pilotage (admin)
# --------------------------------------------------------------------------- #
def page_pilotage(ref, auth):
    header("Pilotage", "Vue consolidée, analyse, historique et saisie en un seul endroit")
    t1, t2, t3, t4 = st.tabs(["📌 Vue d'ensemble", "📈 Analyse", "🕑 Historique", "✏️ Saisie"])
    with t1:
        corps_vue_ensemble(ref, prefix="pil_ve")
    with t2:
        corps_dashboard(ref, auth, prefix="pil_db")
    with t3:
        corps_historique(ref, auth, prefix="pil_hi")
    with t4:
        corps_saisie(ref, auth, prefix="pil_sa")


# --------------------------------------------------------------------------- #
# PAGE : Direction Générale — à venir
# --------------------------------------------------------------------------- #
def page_dg(auth):
    header("Direction Générale", "Espace dédié à la Direction Générale")
    st.markdown('<div class="soon-card"><div class="emoji">🚧</div><h2>Bientôt disponible</h2>'
                '<p>Cette vue est en cours de conception.</p></div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# PAGE : Référentiel (admin)
# --------------------------------------------------------------------------- #
def page_referentiel(ref, users):
    header("Référentiel des KPIs", "Catalogue des indicateurs et de leurs responsables")
    c1, c2, c3 = st.columns(3)
    c1.metric("Nombre de KPIs", ref.shape[0])
    c2.metric("Domaines", ref["categorie"].nunique())
    c3.metric("Directions", ref["direction"].nunique())

    cat = st.multiselect("Filtrer par domaine", sorted(ref["categorie"].unique()))
    vue = ref[ref["categorie"].isin(cat)] if cat else ref
    st.dataframe(vue, use_container_width=True, hide_index=True, column_config={
        "categorie": "Domaine", "kpi": "KPI", "periodicite": "Périodicité", "direction": "Direction",
        "contact": "Contact (email / matricule)", "username": "Responsable (compte)"})

    st.divider()
    st.markdown('<div class="section-title">➕ Ajouter un indicateur</div>', unsafe_allow_html=True)
    domaines = sorted(ref["categorie"].unique())
    directions = sorted(ref["direction"].unique())
    comptes_saisie = ["(aucun)"] + users[users["role"] == "saisie"]["username"].tolist()
    with st.form("ajout_kpi"):
        kpi = st.text_input("Intitulé de l'indicateur")
        c1, c2 = st.columns(2)
        dom_sel = c1.selectbox("Domaine existant", domaines)
        dom_new = c2.text_input("…ou nouveau domaine", placeholder="laisser vide pour la sélection")
        c3, c4 = st.columns(2)
        dir_sel = c3.selectbox("Direction existante", directions)
        dir_new = c4.text_input("…ou nouvelle direction", placeholder="laisser vide pour la sélection")
        c5, c6, c7 = st.columns(3)
        periodicite = c5.selectbox("Périodicité", ["Mensuelle", "Trimestrielle"])
        contact = c6.text_input("Contact (email / matricule)")
        responsable = c7.selectbox("Responsable (compte)", comptes_saisie)
        ok = st.form_submit_button("Ajouter l'indicateur", type="primary")
    if ok:
        categorie = dom_new.strip() or dom_sel
        direction = dir_new.strip() or dir_sel
        username = "" if responsable == "(aucun)" else responsable
        if not kpi.strip():
            st.error("L'intitulé de l'indicateur est obligatoire.")
        elif kpi.strip() in ref["kpi"].values:
            st.error("Cet indicateur existe déjà dans le référentiel.")
        else:
            ajouter_kpi(categorie, kpi.strip(), periodicite, direction, contact.strip(), username)
            st.success(f"Indicateur « {kpi.strip()} » ajouté au domaine « {categorie} ».")
            st.rerun()


# --------------------------------------------------------------------------- #
# PAGE : Comptes (admin)
# --------------------------------------------------------------------------- #
def page_comptes(ref, users, auth):
    header("Comptes & affectations", "Création des accès et attribution des KPIs")

    cnt = ref[ref["username"] != ""].groupby("username").size().rename("KPIs affectés")
    recap = (users[["username", "nom", "role"]].merge(cnt, on="username", how="left")
             .fillna({"KPIs affectés": 0}))
    recap["KPIs affectés"] = recap["KPIs affectés"].astype(int)
    st.dataframe(recap, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown('<div class="section-title">➕ Créer un compte et affecter ses KPIs</div>', unsafe_allow_html=True)
    filtre_dom_new = st.multiselect("Filtrer les KPIs par domaine (optionnel)",
                                    sorted(ref["categorie"].unique()), key="filtre_new")
    options_new = (ref[ref["categorie"].isin(filtre_dom_new)]["kpi"].tolist()
                   if filtre_dom_new else ref["kpi"].tolist())
    with st.form("ajout_user"):
        c1, c2 = st.columns(2)
        username = c1.text_input("Identifiant")
        nom = c2.text_input("Nom affiché")
        c3, c4 = st.columns(2)
        role = c3.selectbox("Rôle", ["saisie", "dg", "admin"],
                            help="saisie : KPIs affectés · dg : vue dédiée · admin : tout")
        mdp = c4.text_input("Mot de passe", type="password")
        kpis_new = st.multiselect("KPIs à affecter", sorted(options_new),
                                  help="Utile uniquement pour le rôle « saisie ».")
        ok = st.form_submit_button("Créer le compte", type="primary")
    if ok:
        if not username or not mdp:
            st.error("Identifiant et mot de passe obligatoires.")
        elif username.strip() in users["username"].values:
            st.error("Cet identifiant existe déjà.")
        elif role == "saisie" and not kpis_new:
            st.error("Sélectionnez au moins un KPI pour un compte de saisie.")
        else:
            ajouter_user(username.strip(), mdp, nom, role)
            if role == "saisie":
                affecter_kpis(username.strip(), kpis_new)
            st.success(f"Compte « {username} » créé.")
            st.rerun()

    st.divider()
    st.markdown('<div class="section-title">✏️ Modifier ou supprimer un compte</div>',
                unsafe_allow_html=True)
    if users.empty:
        st.caption("Aucun compte enregistré.")
    else:
        u_mod = st.selectbox("Compte à modifier", users["username"].tolist(), key="mod_sel")
        row = users[users["username"] == u_mod].iloc[0]
        roles = ["saisie", "dg", "admin"]
        nb_admins = int((users["role"] == "admin").sum())
        with st.form("modif_user"):
            nom = st.text_input("Nom affiché", value=row["nom"], key=f"mod_nom_{u_mod}")
            role = st.selectbox("Rôle", roles,
                                index=roles.index(row["role"]) if row["role"] in roles else 0,
                                key=f"mod_role_{u_mod}")
            new_mdp = st.text_input("Nouveau mot de passe (laisser vide pour conserver)",
                                    type="password", key=f"mod_mdp_{u_mod}")
            confirm = st.checkbox("Confirmer la suppression de ce compte", key=f"mod_conf_{u_mod}")
            c1, c2 = st.columns(2)
            save = c1.form_submit_button("💾 Enregistrer", type="primary")
            suppr = c2.form_submit_button("🗑️ Supprimer le compte")
        if save:
            if row["role"] == "admin" and role != "admin" and nb_admins <= 1:
                st.error("Impossible : c'est le dernier administrateur.")
            else:
                modifier_user(u_mod, nom.strip() or row["nom"], role, new_mdp or None)
                st.success(f"Compte « {u_mod} » mis à jour.")
                st.rerun()
        if suppr:
            if not confirm:
                st.warning("Cochez « Confirmer la suppression » avant de supprimer.")
            elif u_mod == auth["username"]:
                st.error("Vous ne pouvez pas supprimer votre propre compte connecté.")
            elif row["role"] == "admin" and nb_admins <= 1:
                st.error("Impossible : c'est le dernier administrateur.")
            else:
                supprimer_user(u_mod)
                st.success(f"Compte « {u_mod} » supprimé.")
                st.rerun()

    st.divider()
    st.markdown('<div class="section-title">🎯 Modifier les affectations d\'un compte existant</div>',
                unsafe_allow_html=True)
    saisie_users = users[users["role"] == "saisie"]["username"].tolist()
    if not saisie_users:
        st.caption("Aucun compte de saisie à configurer.")
        return
    u_cible = st.selectbox("Utilisateur", saisie_users)
    actuels = ref.loc[ref["username"] == u_cible, "kpi"].tolist()
    filtre_dom = st.multiselect("Filtrer la liste par domaine (optionnel)",
                                sorted(ref["categorie"].unique()), key="filtre_edit")
    options = (ref[ref["categorie"].isin(filtre_dom)]["kpi"].tolist()
               if filtre_dom else ref["kpi"].tolist())
    options = sorted(set(options) | set(actuels))
    with st.form("affectation"):
        choix = st.multiselect("KPIs affectés", options, default=actuels)
        ok2 = st.form_submit_button("💾 Enregistrer les affectations", type="primary")
    if ok2:
        affecter_kpis(u_cible, choix)
        st.success(f"{len(choix)} KPI(s) affecté(s) à « {u_cible} ».")
        st.rerun()


# --------------------------------------------------------------------------- #
# Application
# --------------------------------------------------------------------------- #
def main():
    inject_css()
    init_db()
    ref = charger_referentiel()
    users = charger_users()

    if "auth" not in st.session_state:
        page_login(users)
        return

    auth = st.session_state.auth
    role = auth["role"]
    is_admin, is_dg = role == "admin", role == "dg"
    kpis_ok = kpis_autorises(auth, ref)
    ref_user = ref[ref["kpi"].isin(kpis_ok)]

    st.sidebar.markdown("# 📊 Dashboard KPI")
    role_label = {"admin": "Administrateur", "dg": "Direction Générale"}.get(role, "Saisie")
    portee = ("Tous les KPIs" if is_admin else
              "Vue dédiée" if is_dg else f"{len(kpis_ok)} KPI(s) affecté(s)")
    st.sidebar.markdown(
        f'<div class="user-badge"><div class="nm">{auth["nom"]}</div>'
        f'<span class="rl">{role_label}</span>'
        f'<div style="font-size:.78rem;margin-top:6px;opacity:.7">{portee}</div></div>',
        unsafe_allow_html=True)

    if is_dg:
        pages = ["Direction Générale"]
    elif is_admin:
        pages = ["Pilotage", "Référentiel", "Comptes"]
    else:
        pages = ["Saisie", "Tableau de bord", "Historique"]
    page = st.sidebar.radio("Navigation", pages)

    st.sidebar.divider()
    if st.sidebar.button("Se déconnecter", use_container_width=True):
        del st.session_state.auth
        st.rerun()

    if page == "Saisie":
        page_saisie(ref_user, auth)
    elif page == "Tableau de bord":
        page_dashboard(ref_user, auth)
    elif page == "Historique":
        page_historique(ref_user, auth)
    elif page == "Pilotage":
        page_pilotage(ref, auth)
    elif page == "Direction Générale":
        page_dg(auth)
    elif page == "Référentiel":
        page_referentiel(ref, users)
    elif page == "Comptes":
        page_comptes(ref, users, auth)


if __name__ == "__main__":
    main()
