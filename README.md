# Dashboard KPI – SocGen CI (v2 avec Login)

## Installation & lancement

```bash
pip install -r requirements.txt
streamlit run app.py
```
→ http://localhost:8501

---

## Comptes utilisateurs (à changer en production)

| Identifiant     | Mot de passe      | Rôle        | KPIs visibles                        |
|-----------------|-------------------|-------------|--------------------------------------|
| admin           | Admin@2026        | Admin       | Tous les KPIs + logs connexion       |
| jacques         | Jacques@2026      | Responsable | Encours dépôts retail & corporate    |
| yssouf          | Yssouf@2026       | Responsable | Crédits + Commissions                |
| hafsatou        | Hafsatou@2026     | Responsable | Dossiers échus + Décaissements       |
| aymard          | Aymard@2026       | Responsable | Crédits échus Retail + PDI           |
| jean-joseph     | JeanJoseph@2026   | Responsable | Suspens Comptable                    |
| esther          | Esther@2026       | Responsable | CNR global, retail, corporate        |
| nicanor         | Nicanor@2026      | Responsable | Ressources humaines                  |
| isabelle        | Isabelle@2026     | Responsable | Gouvernance et Conformité            |
| serge-francois  | Serge@2026        | Responsable | Disponibilité GAB                    |

---

## Architecture

### Base de données SQLite : `kpi_socgen.db`

**Table `saisies`** — Historique complet de toutes les saisies
| Colonne      | Type    | Description                        |
|--------------|---------|------------------------------------|
| id           | INTEGER | Clé primaire auto-incrémentée      |
| login        | TEXT    | Identifiant de l'utilisateur       |
| nom_resp     | TEXT    | Nom affiché du responsable         |
| categorie    | TEXT    | Catégorie du KPI                   |
| kpi          | TEXT    | Libellé du KPI                     |
| periodicite  | TEXT    | Mensuelle / Trimestrielle          |
| periode      | TEXT    | Ex: "Avril 2026"                   |
| valeur       | REAL    | Valeur numérique saisie            |
| unite        | TEXT    | Unité (%, FCFA, nombre…)           |
| commentaire  | TEXT    | Commentaire libre                  |
| date_saisie  | TEXT    | Horodatage ISO de la saisie        |

**Table `logs_connexion`** — Traçabilité des connexions
| Colonne   | Type    | Description          |
|-----------|---------|----------------------|
| id        | INTEGER | Clé primaire         |
| login     | TEXT    | Identifiant          |
| action    | TEXT    | LOGIN / LOGOUT       |
| timestamp | TEXT    | Horodatage           |

---

## Règles d'accès

- **Responsable** : voit uniquement ses KPIs assignés, son historique personnel
- **Admin** : voit tout (tous les KPIs, tout l'historique, les logs de connexion)
- Un responsable **ne peut pas** voir ni modifier les saisies d'un autre responsable
