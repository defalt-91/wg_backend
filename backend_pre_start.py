import logging, pathlib
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed
from sqlalchemy.sql import text
from app.db.session import SessionFactory
from alembic import command, config

# from alembic import migration,op,command,env,config,util,operations,runtime,script,ddl,Operations,autogenerate

BASE_DIR = pathlib.Path(__file__).parent.absolute()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1
try:
    alembic_config = config.Config(BASE_DIR / 'alembic.ini')
    command.upgrade(config=alembic_config, revision='head')
except Exception as err:
    logger.critical('Alembic upgrade error: {}'.format(err))
logger.debug("Alembic upgraded database to last revision.")


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


def main() -> None:
    logger.info("Initializing service")
    init()
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
