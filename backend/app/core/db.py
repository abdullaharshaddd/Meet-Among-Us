from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Supabase's transaction pooler hands each transaction a different backend connection,
# so server-side prepared statements from a previous transaction won't exist. psycopg3
# prepares automatically after 5 identical queries; prepare_threshold=None turns that off.
# NullPool because pgbouncer is already the pool — a second pool on top just holds
# client slots open against the free tier's cap. See docs/adr/0001.
engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
    connect_args={"prepare_threshold": None},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
