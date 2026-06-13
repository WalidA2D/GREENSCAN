"""Connexion SQLAlchemy + session + base déclarative."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.config import settings

# pool_pre_ping : évite les connexions mortes après inactivité.
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles ORM."""


def get_db() -> Generator[Session, None, None]:
    """Dépendance FastAPI : fournit une session DB par requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crée toutes les tables si elles n'existent pas (idempotent)."""
    # Import nécessaire pour enregistrer les modèles sur Base.metadata.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
