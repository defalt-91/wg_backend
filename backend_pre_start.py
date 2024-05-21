import logging

from sqlalchemy import select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from alembic import command, config
from app.db.session import SessionFactory
from app.core.Settings import get_settings
settings = get_settings()

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.INFO),
)
def init() -> None:
    global session
    try:
        """     
        alembic upgrade head
        """
        alembic_config = config.Config(settings.ALEMBIC_CONFIG_PATH)
        command.upgrade(config=alembic_config, revision='head')
        with SessionFactory() as session:
            session.execute(select(1))
        # Try to create session to check if DB is awake
        logger.debug('Database is ready for transactions')
        # breakpoint()

    except Exception as e:
        logger.error('Alembic upgrade error: {}'.format(e))
        raise e

    finally:
        session.close()


def main():
    logger.info("Initializing service")
    init()
    logger.info("Service finished initializing")
    return


if __name__=="__main__":
    main()
