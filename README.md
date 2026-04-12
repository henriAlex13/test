# Dashboard KPI – SocGen CI (v3)

## Installation & lancement
```bash
pip install -r requirements.txt
streamlit run app.py
```
→ http://localhost:8501

---

## Comptes par défaut

| Login           | Mot de passe      | Rôle  | Accès                                      |
|-----------------|-------------------|-------|--------------------------------------------|
| admin           | Admin@2026        | admin | Tout + Administration + Logs               |
| dg              | DG@2026           | dg    | Dashboard Global uniquement                |
| jacques         | Jacques@2026      | user  | Ses KPIs uniquement                        |
| yssouf          | Yssouf@2026       | user  | Ses KPIs uniquement                        |
| hafsatou        | Hafsatou@2026     | user  | Ses KPIs uniquement                        |
| aymard          | Aymard@2026       | user  | Ses KPIs uniquement                        |
| jean-joseph     | JeanJoseph@2026   | user  | Ses KPIs uniquement                        |
| esther          | Esther@2026       | user  | Ses KPIs uniquement                        |
| nicanor         | Nicanor@2026      | user  | Ses KPIs uniquement                        |
| isabelle        | Isabelle@2026     | user  | Ses KPIs uniquement                        |
| serge-francois  | Serge@2026        | user  | Ses KPIs uniquement                        |

---

## Nouveautés v3

- ✅ KPIs non saisis : nom du responsable affiché en premier
- ✅ Dashboard de saisies (admin) renommé (était "Dashboard Global")
- ✅ Dashboard Global (DG) : vue stats consolidées sur l'historique
  - Le DG ne voit QUE cette page
- ✅ Administration : ajouter/supprimer des KPIs, des catégories, des utilisateurs
- ✅ Export Excel (.xlsx) disponible pour l'admin dans Historique et Logs
- ✅ Utilisateurs gérables en base de données (plus de code à modifier)

---

## Base de données SQLite : `kpi_socgen.db`

| Table            | Contenu                                      |
|------------------|----------------------------------------------|
| kpi_ref          | Référentiel dynamique des KPIs               |
| users            | Utilisateurs avec rôles et mots de passe     |
| saisies          | Historique de toutes les saisies             |
| logs_connexion   | Traçabilité LOGIN/LOGOUT                     |
