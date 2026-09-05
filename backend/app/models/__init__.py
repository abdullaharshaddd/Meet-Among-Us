from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base. Every ORM model in every phase inherits from this."""


# Imported after Base is defined (models subclass it) and re-exported so a single
# `from app.models import Base` in alembic/env.py registers every table on
# Base.metadata for autogenerate — importing a model module for its side effect only.
from app.models.user import User  # noqa: E402,F401
from app.models.refresh_token import RefreshToken  # noqa: E402,F401

