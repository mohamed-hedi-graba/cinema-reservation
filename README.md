# Cinema Ticket Reservation — TP Processus Unifié & Agile

> Système de réservation de places de cinéma avec gestion de concurrence (UC à risque : réservation siège)

## Stack
- **FastAPI** (Python 3.11+) — API REST async
- **SQLAlchemy 2.0** + **asyncpg** — ORM async, PostgreSQL
- **Pydantic v2** — Validation, settings
- **Pytest** + **httpx** — Tests unitaires & intégration
- **Ruff** — Lint/format
- **GitHub Actions** — CI (lint, test, coverage)
- **PlantUML** — Diagrammes (cas d'utilisation, classes, séquence)

## Architecture en couches
```
app/
├── api/           # Contrôleurs (routes FastAPI)
│   └── reservations.py
├── services/      # Métier (logique, concurrence)
│   └── reservation.py
├── repositories/  # Accès données (SQLAlchemy)
│   └── __init__.py
├── models/        # Entités domaine + BD
│   └── __init__.py
├── core/          # Config, DB, sécurité
│   ├── config.py
│   └── database.py
└── main.py        # Entry point
```

## UC couverts
| UC | Endpoint | Statut |
|----|----------|--------|
| UC-01 Consulter films | `GET /films` | 🔜 Itération 2 |
| UC-02 Consulter séances | `GET /seances` | 🔜 Itération 2 |
| **UC-03 Réserver une place** ★ | `POST /reservations` | ✅ **Implémenté + test concurrence** |
| UC-04 Effectuer paiement | `POST /reservations/{id}/payer` | ✅ Squelette (mock Stripe) |
| UC-05 Recevoir confirmation | Async (Celery/RQ) | 🔜 Itération 3 |
| UC-06 Annuler réservation | `DELETE /reservations/{id}` | ✅ Implémenté |

## Démarrage local

```bash
# 1. Dépendances
docker compose up -d postgres postgres_test mailhog

# 2. Env
cp .env.example .env
# Éditer DATABASE_URL si besoin

# 3. Installer
pip install -e ".[dev]"

# 4. Lancer API
uvicorn app.main:app --reload

# 5. Tests
pytest -v --cov=app
```

### URLs utiles
- API : http://localhost:8000
- Docs Swagger : http://localhost:8000/docs
- Health : http://localhost:8000/health
- Mailhog UI : http://localhost:8025

## Gestion de la concurrence (UC-03)

**Problème** : Deux utilisateurs tentent de réserver le même siège en même temps.

**Solution** : Contrainte `UNIQUE` au niveau BDD sur `(seance_id, siege_id, statut)` + `INSERT` atomique.

```sql
-- Dans la migration / modèle
UniqueConstraint("seance_id", "siege_id", "statut", name="uq_reservation_siege_seance_statut")
```

- Transaction 1 : `INSERT` → OK → `201 Created`
- Transaction 2 (simultanée) : `INSERT` → `IntegrityError` (unique violation) → `409 Conflict`

**Test d'intégration** : `tests/test_reservation_integration.py::TestUC03ReservationConcurrente::test_deux_utilisateurs_meme_siege_premier_gagne`

## Diagrammes PlantUML

```bash
# Générer images (nécessite plantuml / java)
cd diagrams
plantuml *.puml
```

| Fichier | Description |
|---------|-------------|
| `use_case.puml` | Diagramme cas d'utilisation (acteurs, UC, include/extend) |
| `classes.puml` | Diagramme de classes (domaine, repositories, services, API) |
| `sequence_uc03.puml` | Diagramme de séquence UC-03 (nominal + concurrence) |

## Git Flow imposé par le TP

- **Branches** : `feature/uc-XX-description` (1 par UC)
- **Milestones GitHub** : Inception, Élaboration, Construction, Transition
- **Tags** : `v0.0-inception`, `v0.1-elaboration`, `v0.2-construction`, `v1.0-release`
- **PR obligatoire** + review croisée (Itération 3) + CI verte

## Jalons (Tags)

```bash
# Inception
git tag v0.0-inception

# Élaboration (architecture de base qui tourne + UC-03 + CI verte)
git tag v0.1-elaboration

# Construction (UC-01,02,04,06 + tests)
git tag v0.2-construction

# Transition (UC-05 notifs + recette + déploiement)
git tag v1.0-release
```

## CI GitHub Actions

Pipeline sur chaque push/PR :
1. `ruff check .` — Lint
2. `ruff format --check .` — Format
3. `pytest -v --cov=app` — Tests + couverture
4. Upload coverage → Codecov

## Auteur
TP Processus Unifié & Approches Agiles — Équipe [VOTRE NOM]