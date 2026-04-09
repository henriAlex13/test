# Dashboard KPI – SocGen CI (v3)

## Installation & lancement

```bash
pip install -r requirements.txt
streamlit run app.py
```
→ http://localhost:8501

---

## Nouveautés v3

| Fonctionnalité | Détail |
|---|---|
| KPIs manquants | Nom du responsable affiché devant chaque KPI manquant |
| Gestion référentiel | Admin peut ajouter/désactiver catégories et KPIs |
| Dashboard Analytique | Vue DG/Admin avec stats approfondies sur l'historique |
| Renommage | "Dashboard Global" → "Dashboard de saisies" |
| Export Excel | Admin & DG peuvent télécharger l'historique en .xlsx formaté |
| Export PowerPoint | Admin & DG peuvent télécharger le dashboard en .pptx (5 slides) |

---

## Comptes utilisateurs

| Identifiant     | Mot de passe      | Rôle        | Accès                                  |
|-----------------|-------------------|-------------|----------------------------------------|
| admin           | Admin@2026        | Admin       | Tout + gestion référentiel + logs      |
| dg              | DG@2026           | DG          | Dashboard analytique + exports         |
| jacques         | Jacques@2026      | Responsable | Ses KPIs uniquement                    |
| yssouf          | Yssouf@2026       | Responsable | Ses KPIs uniquement                    |
| hafsatou        | Hafsatou@2026     | Responsable | Ses KPIs uniquement                    |
| aymard          | Aymard@2026       | Responsable | Ses KPIs uniquement                    |
| jean-joseph     | JeanJoseph@2026   | Responsable | Ses KPIs uniquement                    |
| esther          | Esther@2026       | Responsable | Ses KPIs uniquement                    |
| nicanor         | Nicanor@2026      | Responsable | Ses KPIs uniquement                    |
| isabelle        | Isabelle@2026     | Responsable | Ses KPIs uniquement                    |
| serge-francois  | Serge@2026        | Responsable | Ses KPIs uniquement                    |

---

## Structure de la base `kpi_socgen.db`

### Table `kpi_ref` — Référentiel dynamique des KPIs
| Colonne     | Description                        |
|-------------|------------------------------------|
| id          | Clé primaire                       |
| categorie   | Catégorie du KPI                   |
| kpi         | Libellé du KPI                     |
| periodicite | Mensuelle / Trimestrielle / etc.   |
| email       | Email du responsable               |
| nom         | Nom du responsable                 |
| actif       | 1=actif, 0=désactivé               |

### Table `saisies` — Historique complet
| Colonne      | Description                        |
|--------------|------------------------------------|
| id           | Clé primaire auto                  |
| login        | Identifiant de connexion           |
| nom_resp     | Nom affiché du responsable         |
| categorie    | Catégorie du KPI                   |
| kpi          | Libellé du KPI                     |
| periodicite  | Fréquence                          |
| periode      | Ex: "Avril 2026"                   |
| valeur       | Valeur numérique                   |
| unite        | Unité (%, FCFA, nombre…)           |
| commentaire  | Commentaire libre                  |
| date_saisie  | Horodatage ISO                     |

### Table `logs_connexion` — Traçabilité
| Colonne   | Description          |
|-----------|----------------------|
| login     | Identifiant          |
| action    | LOGIN / LOGOUT       |
| timestamp | Horodatage           |

---

## Export PowerPoint (5 slides)
1. Slide titre
2. Vue d'ensemble (métriques + barres de complétion)
3. Saisies par responsable
4. Tableau des 20 dernières saisies
5. KPIs manquants avec responsables
