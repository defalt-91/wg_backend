import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.Settings import get_settings

settings=get_settings()

engine = create_engine(
	url=settings.SQLALCHEMY_DATABASE_URL,
	pool_pre_ping=True,
	echo=True,
	future=True,
)

SessionFactory = sessionmaker(
	bind=engine,
	future=True,
	autoflush=True,
	autocommit=False,
	expire_on_commit=False
)
from init_db import init_db


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    with SessionFactory() as session:
        init_db(session)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()