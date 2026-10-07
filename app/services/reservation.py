from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Reservation, Seance, Siege, StatutReservation
from app.repositories import ReservationRepository, SiegeRepository


class SiegeNonDisponibleError(Exception):
    def __init__(self, siege_id: int, seance_id: int):
        self.siege_id = siege_id
        self.seance_id = seance_id
        super().__init__(f"Siège {siege_id} déjà réservé pour la séance {seance_id}")


class SeanceIntrouvableError(Exception):
    pass


class ReservationService:
    """Service métier pour la réservation - gère la concurrence via SELECT FOR UPDATE + contrainte UNIQUE"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.reservation_repo = ReservationRepository(session)
        self.siege_repo = SiegeRepository(session)

    async def reserver_siege(
        self,
        seance_id: int,
        siege_id: int,
        spectateur_email: str,
    ) -> Reservation:
        """
        Réserve un siège pour une séance.
        Stratégie anti-conflit :
        1. SELECT FOR UPDATE sur le siège + vérif dispo en BDD (contrainte UNIQUE)
        2. Insert réservation EN_ATTENTE avec expiration 15 min
        3. Si IntegrityError (conflit) → lève SiegeNonDisponibleError
        """
        # 1. Vérifier que la séance existe
        seance = await self.session.get(Seance, seance_id)
        if not seance:
            raise SeanceIntrouvableError(f"Séance {seance_id} introuvable")

        # 2. Vérifier que le siège appartient à la salle de la séance
        siege = await self.siege_repo.get_by_id(siege_id)
        if not siege or siege.salle_id != seance.salle_id:
            raise ValueError(f"Siège {siege_id} n'appartient pas à la salle de la séance {seance_id}")

        # 3. Tentative d'insertion avec contrainte UNIQUE (gère la concurrence au niveau BDD)
        reservation = Reservation(
            seance_id=seance_id,
            siege_id=siege_id,
            spectateur_email=spectateur_email,
            statut=StatutReservation.EN_ATTENTE,
            montant_cents=seance.prix_base_cents,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
        )

        try:
            await self.reservation_repo.create(reservation)
            await self.session.commit()
            return reservation
        except IntegrityError:
            await self.session.rollback()
            # Double-vérification pour message d'erreur précis
            existing = await self.reservation_repo.get_by_siege_seance(
                siege_id, seance_id, [StatutReservation.EN_ATTENTE, StatutReservation.CONFIRMEE]
            )
            if existing:
                raise SiegeNonDisponibleError(siege_id, seance_id)
            raise

    async def confirmer_paiement(self, reservation_id: int, stripe_payment_intent_id: str) -> Reservation:
        reservation = await self.reservation_repo.get_by_id(reservation_id)
        if not reservation:
            raise ValueError(f"Réservation {reservation_id} introuvable")
        if reservation.statut != StatutReservation.EN_ATTENTE:
            raise ValueError(f"Réservation {reservation_id} n'est pas en attente (statut: {reservation.statut})")

        reservation.statut = StatutReservation.CONFIRMEE
        reservation.stripe_payment_intent_id = stripe_payment_intent_id
        reservation.expires_at = None
        await self.session.commit()
        return reservation

    async def annuler(self, reservation_id: int) -> Reservation:
        reservation = await self.reservation_repo.get_by_id(reservation_id)
        if not reservation:
            raise ValueError(f"Réservation {reservation_id} introuvable")
        if reservation.statut == StatutReservation.ANNULEE:
            raise ValueError("Déjà annulée")

        reservation.statut = StatutReservation.ANNULEE
        await self.session.commit()
        return reservation