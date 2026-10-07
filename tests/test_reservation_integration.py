import asyncio
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import get_session
from app.main import app
from app.models import Base, Film, Salle, Seance, Siege


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine and tables once per session"""
    engine = create_async_engine(
        settings.test_database_url,
        echo=False,
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def session(test_engine):
    """Create a new session for each test"""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(test_engine):
    """Create test client with overridden database dependency"""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_session():
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_data(session: AsyncSession):
    """Crée un film, une salle, une séance, des sièges"""
    film = Film(titre="Inception", description="Rêve dans un rêve", duree_minutes=148)
    salle = Salle(nom="Salle 1", capacite=10)
    session.add_all([film, salle])
    await session.flush()

    seance = Seance(
        film_id=film.id,
        salle_id=salle.id,
        debut=datetime(2025, 12, 25, 20, 0, 0, tzinfo=UTC),
        fin=datetime(2025, 12, 25, 22, 30, 0, tzinfo=UTC),
        prix_base_cents=1200,
    )
    session.add(seance)
    await session.flush()

    sieges = [Siege(salle_id=salle.id, rang="A", numero=i) for i in range(1, 6)]
    session.add_all(sieges)
    await session.commit()

    return {"film": film, "salle": salle, "seance": seance, "sieges": sieges}


class TestUC03ReservationConcurrente:
    """Tests d'intégration pour UC-03: Réserver une place (conflit siège)"""

    async def test_reserver_siege_disponible_succes(self, client: AsyncClient, sample_data):
        seance_id = sample_data["seance"].id
        siege_id = sample_data["sieges"][0].id

        response = await client.post(
            "/reservations",
            json={
                "seance_id": seance_id,
                "siege_id": siege_id,
                "spectateur_email": "alice@example.com",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["statut"] == "EN_ATTENTE"
        assert data["siege_id"] == siege_id
        assert data["montant_cents"] == 1200

    async def test_deux_utilisateurs_meme_siege_premier_gagne(
        self, client: AsyncClient, sample_data
    ):
        """TEST CLÉ: Concurrence - deux requêtes simultanées sur le même siège"""
        seance_id = sample_data["seance"].id
        siege_id = sample_data["sieges"][0].id

        # Requêtes simultanées
        responses = await asyncio.gather(
            client.post(
                "/reservations",
                json={
                    "seance_id": seance_id,
                    "siege_id": siege_id,
                    "spectateur_email": "alice@example.com",
                },
            ),
            client.post(
                "/reservations",
                json={
                    "seance_id": seance_id,
                    "siege_id": siege_id,
                    "spectateur_email": "bob@example.com",
                },
            ),
            return_exceptions=True,
        )

        # Un seul doit réussir (201), l'autre échouer (409 Conflict)
        status_codes = [r.status_code for r in responses if not isinstance(r, Exception)]
        assert 201 in status_codes
        assert 409 in status_codes
        assert status_codes.count(201) == 1
        assert status_codes.count(409) == 1

    async def test_reserver_siege_inexistant_404(self, client: AsyncClient, sample_data):
        response = await client.post(
            "/reservations",
            json={"seance_id": 99999, "siege_id": 1, "spectateur_email": "alice@example.com"},
        )
        assert response.status_code == 404

    async def test_reserver_siege_mauvaise_salle_400(
        self, client: AsyncClient, sample_data, session: AsyncSession
    ):
        # Créer une 2e salle avec ses propres sièges
        salle2 = Salle(nom="Salle 2", capacite=5)
        session.add(salle2)
        await session.flush()
        siege_salle2 = Siege(salle_id=salle2.id, rang="A", numero=1)
        session.add(siege_salle2)
        await session.commit()

        response = await client.post(
            "/reservations",
            json={
                "seance_id": sample_data["seance"].id,
                "siege_id": siege_salle2.id,
                "spectateur_email": "alice@example.com",
            },
        )
        assert response.status_code == 400


class TestUC04Paiement:
    async def test_confirmer_paiement_reservation_en_attente(
        self, client: AsyncClient, sample_data
    ):
        seance_id = sample_data["seance"].id
        siege_id = sample_data["sieges"][1].id

        # Créer réservation
        resp = await client.post(
            "/reservations",
            json={
                "seance_id": seance_id,
                "siege_id": siege_id,
                "spectateur_email": "alice@example.com",
            },
        )
        assert resp.status_code == 201
        reservation_id = resp.json()["id"]

        # Confirmer paiement
        resp = await client.post(
            f"/reservations/{reservation_id}/payer",
            json={"stripe_payment_intent_id": "pi_mock_123"},
        )
        assert resp.status_code == 200
        assert resp.json()["statut"] == "CONFIRMEE"
        assert resp.json()["stripe_payment_intent_id"] == "pi_mock_123"

    async def test_payer_reservation_inexistante_400(self, client: AsyncClient):
        resp = await client.post(
            "/reservations/99999/payer", json={"stripe_payment_intent_id": "pi_mock"}
        )
        assert resp.status_code == 400


class TestUC06Annulation:
    async def test_annuler_reservation_en_attente(self, client: AsyncClient, sample_data):
        seance_id = sample_data["seance"].id
        siege_id = sample_data["sieges"][2].id

        resp = await client.post(
            "/reservations",
            json={
                "seance_id": seance_id,
                "siege_id": siege_id,
                "spectateur_email": "alice@example.com",
            },
        )
        reservation_id = resp.json()["id"]

        resp = await client.delete(f"/reservations/{reservation_id}")
        assert resp.status_code == 204

        # Vérifier que le siège est libéré (nouvelle réservation possible)
        resp2 = await client.post(
            "/reservations",
            json={
                "seance_id": seance_id,
                "siege_id": siege_id,
                "spectateur_email": "bob@example.com",
            },
        )
        assert resp2.status_code == 201
