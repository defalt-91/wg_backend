import logging
import pathlib

from alembic import command, config
from sqlalchemy import Engine, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.db.session import SessionFactory


# from alembic import migration,op,command,env,config,util,operations,runtime,script,ddl,Operations,autogenerate

BASE_DIR = pathlib.Path(__file__).parent.absolute()
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
        # alembic upgrade head
        alembic_config = config.Config(BASE_DIR / 'alembic.ini')
        command.upgrade(config=alembic_config, revision='head')
        with SessionFactory() as session:
            # Try to create session to check if DB is awake
            session.execute(select(1))
            # breakpoint()

    except Exception as e:
        logger.error('Alembic upgrade error: {}'.format(e))
        raise e


def main() -> None:
    logger.info("Initializing service")
    init()
    logger.info("Service finished initializing")


if __name__=="__main__":
    main()
