from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Reservation, Salle, Seance, Siege, StatutReservation


class SiegeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, siege_id: int) -> Siege | None:
        return await self.session.get(Siege, siege_id)

    async def get_disponibles_pour_seance(self, seance_id: int) -> list[Siege]:
        # Sièges de la salle qui n'ont PAS de réservation CONFIRMEE ou EN_ATTENTE sur cette séance
        stmt = (
            select(Siege)
            .join(Siege.salle)
            .join(Salle.seances)
            .where(Seance.id == seance_id)
            .where(
                ~Siege.reservations.any(
                    (Reservation.seance_id == seance_id)
                    & (
                        Reservation.statut.in_(
                            [StatutReservation.CONFIRMEE, StatutReservation.EN_ATTENTE]
                        )
                    )
                )
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ReservationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, reservation: Reservation) -> Reservation:
        self.session.add(reservation)
        await self.session.flush()
        return reservation

    async def get_by_id(self, reservation_id: int) -> Reservation | None:
        stmt = (
            select(Reservation)
            .options(selectinload(Reservation.siege), selectinload(Reservation.seance))
            .where(Reservation.id == reservation_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_siege_seance(
        self, siege_id: int, seance_id: int, statuts: list[StatutReservation]
    ) -> Reservation | None:
        stmt = select(Reservation).where(
            Reservation.siege_id == siege_id,
            Reservation.seance_id == seance_id,
            Reservation.statut.in_(statuts),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_statut(
        self, reservation_id: int, statut: StatutReservation
    ) -> Reservation | None:
        reservation = await self.get_by_id(reservation_id)
        if reservation:
            reservation.statut = statut
            await self.session.flush()
        return reservation
