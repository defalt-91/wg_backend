import logging
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed
from sqlalchemy.sql import text
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init() -> None:
    try:
        db = SessionFactory()
        # Try to create session to check if DB is awake
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(e)
        raise e
    logger.error(db.in_transaction())


def main() -> None:
    logger.info("Initializing service")
    init()
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
