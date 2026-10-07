from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StatutReservation(PyEnum):
    EN_ATTENTE = "EN_ATTENTE"
    CONFIRMEE = "CONFIRMEE"
    ANNULEE = "ANNULEE"
    EXPIREE = "EXPIREE"


class Film(Base):
    __tablename__ = "films"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titre: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=True)
    duree_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    affiche_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    seances: Mapped[list["Seance"]] = relationship(
        back_populates="film", cascade="all, delete-orphan"
    )


class Salle(Base):
    __tablename__ = "salles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    capacite: Mapped[int] = mapped_column(Integer, nullable=False)

    seances: Mapped[list["Seance"]] = relationship(back_populates="salle")
    sieges: Mapped[list["Siege"]] = relationship(
        back_populates="salle", cascade="all, delete-orphan"
    )


class Seance(Base):
    __tablename__ = "seances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    film_id: Mapped[int] = mapped_column(ForeignKey("films.id", ondelete="CASCADE"), nullable=False)
    salle_id: Mapped[int] = mapped_column(
        ForeignKey("salles.id", ondelete="CASCADE"), nullable=False
    )
    debut: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    prix_base_cents: Mapped[int] = mapped_column(Integer, nullable=False)  # en centimes

    film: Mapped["Film"] = relationship(back_populates="seances")
    salle: Mapped["Salle"] = relationship(back_populates="seances")
    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="seance", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_seances_film_debut", "film_id", "debut"),)


class Siege(Base):
    __tablename__ = "sieges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    salle_id: Mapped[int] = mapped_column(
        ForeignKey("salles.id", ondelete="CASCADE"), nullable=False
    )
    rang: Mapped[str] = mapped_column(String(2), nullable=False)  # A, B, C...
    numero: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3...

    salle: Mapped["Salle"] = relationship(back_populates="sieges")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="siege")

    __table_args__ = (
        UniqueConstraint("salle_id", "rang", "numero", name="uq_siege_salle_rang_numero"),
    )


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seance_id: Mapped[int] = mapped_column(
        ForeignKey("seances.id", ondelete="CASCADE"), nullable=False
    )
    siege_id: Mapped[int] = mapped_column(
        ForeignKey("sieges.id", ondelete="CASCADE"), nullable=False
    )
    spectateur_email: Mapped[str] = mapped_column(String(255), nullable=False)
    statut: Mapped[StatutReservation] = mapped_column(
        Enum(StatutReservation), default=StatutReservation.EN_ATTENTE, nullable=False
    )
    montant_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    stripe_payment_intent_id: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    seance: Mapped["Seance"] = relationship(back_populates="reservations")
    siege: Mapped["Siege"] = relationship(back_populates="reservations")

    __table_args__ = (
        UniqueConstraint(
            "seance_id", "siege_id", "statut", name="uq_reservation_siege_seance_statut"
        ),
        Index("ix_reservations_spectateur", "spectateur_email"),
    )
