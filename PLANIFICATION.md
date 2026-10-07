# Planification — 3 Itérations / 4 Phases (Processus Unifié)

## Phases & Jalons (Tags Git)

| Phase | Jalon (Tag) | Description |
|-------|-------------|-------------|
| **Inception** | `v0.0-inception` | Vision, UC, priorisation, architecture cible, risques |
| **Élaboration** | `v0.1-elaboration` | Arch de base qui tourne : UC-03 bout en bout + test CI |
| **Construction** | `v0.2-construction` | UC-01,02,04,06 implémentés + tests unitaires/intégration |
| **Transition** | `v1.0-release` | UC-05 (notifications), recette, doc, déploiement |

---

## Itération 1 (2 semaines) — **Inception → Élaboration (début)**

| Jour | Livrable |
|------|----------|
| J1-J2 | Dépôt Git + GitHub Projects (milestones, issues UC, branches) |
| J3-J4 | Diagramme cas d'utilisation PlantUML (committé) |
| J5-J6 | **Squelette FastAPI** : config, modèles SQLAlchemy, DB, route health |
| J7-J8 | **UC-03 Réserver une place** : Controller → Service → Repo + **test intégration concurrence** |
| J9-J10 | CI GitHub Actions (lint, test, build) — **pipeline vert** |
| **Fin** | Tag `v0.1-elaboration` + fermer milestone "Élaboration" |

---

## Itération 2 (2 semaines) — **Construction (cœur métier)**

| Semaine | UC | Livrables |
|---------|-----|-----------|
| S1 | UC-01 Films, UC-02 Séances | Diagrammes classes/séquence PlantUML, implémentation couches, tests unitaires |
| S2 | UC-04 Paiement (Stripe mock), UC-06 Annulation | Idem + test intégration nominal par UC |
| **Fin** | Tag `v0.2-construction` + fermer milestone "Construction" |

---

## Itération 3 (1-2 semaines) — **Transition**

| Semaine | Livrables |
|---------|-----------|
| S1 | UC-05 Notification (email/SMS async, Celery/RQ), tests bout en bout |
| S2 | Revue croisée (équipe externe), corrections, doc utilisateur, déploiement staging |
| **Fin** | Tag `v1.0-release` + fermer milestone "Transition" |

---

## Règles Git (imposées par l'énoncé)

- **1 branche par UC** : `feature/uc-03-reservation`, `feature/uc-04-paiement`, etc.
- **Milestones GitHub** = 4 phases (Inception, Élaboration, Construction, Transition)
- **Tags** = jalons de phase (`v0.0-inception`, `v0.1-elaboration`, `v0.2-construction`, `v1.0-release`)
- **Merge** : PR obligatoire, review croisée (Itération 3), CI verte