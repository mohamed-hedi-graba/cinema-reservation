from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import StatutReservation
from app.services.reservation import (
    ReservationService,
    SeanceIntrouvableError,
    SiegeNonDisponibleError,
)

router = APIRouter(prefix="/reservations", tags=["Réservations"])


class ReservationRequest(BaseModel):
    seance_id: int
    siege_id: int
    spectateur_email: EmailStr


class ReservationResponse(BaseModel):
    id: int
    seance_id: int
    siege_id: int
    spectateur_email: str
    statut: StatutReservation
    montant_cents: int
    stripe_payment_intent_id: str | None
    expires_at: str | None

    class Config:
        from_attributes = True


class PaiementConfirmationRequest(BaseModel):
    stripe_payment_intent_id: str


@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def creer_reservation(
    data: ReservationRequest,
    session: AsyncSession = Depends(get_session),
):
    """UC-03: Réserver une place - crée une réservation EN_ATTENTE (15 min pour payer)"""
    service = ReservationService(session)
    try:
        reservation = await service.reserver_siege(
            seance_id=data.seance_id,
            siege_id=data.siege_id,
            spectateur_email=data.spectateur_email,
        )
    except SeanceIntrouvableError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SiegeNonDisponibleError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ReservationResponse(
        id=reservation.id,
        seance_id=reservation.seance_id,
        siege_id=reservation.siege_id,
        spectateur_email=reservation.spectateur_email,
        statut=reservation.statut,
        montant_cents=reservation.montant_cents,
        stripe_payment_intent_id=reservation.stripe_payment_intent_id,
        expires_at=reservation.expires_at.isoformat() if reservation.expires_at else None,
    )


@router.post("/{reservation_id}/payer", response_model=ReservationResponse)
async def confirmer_paiement(
    reservation_id: int,
    data: PaiementConfirmationRequest,
    session: AsyncSession = Depends(get_session),
):
    """UC-04: Effectuer un paiement - confirme la réservation après paiement Stripe"""
    service = ReservationService(session)
    try:
        reservation = await service.confirmer_paiement(
            reservation_id, data.stripe_payment_intent_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ReservationResponse(
        id=reservation.id,
        seance_id=reservation.seance_id,
        siege_id=reservation.siege_id,
        spectateur_email=reservation.spectateur_email,
        statut=reservation.statut,
        montant_cents=reservation.montant_cents,
        stripe_payment_intent_id=reservation.stripe_payment_intent_id,
        expires_at=reservation.expires_at.isoformat() if reservation.expires_at else None,
    )


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def annuler_reservation(
    reservation_id: int,
    session: AsyncSession = Depends(get_session),
):
    """UC-06: Annuler une réservation"""
    service = ReservationService(session)
    try:
        await service.annuler(reservation_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
