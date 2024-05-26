import logging

from sqlalchemy import select
import sqlalchemy
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from alembic import command, config
from wg_backend.core.settings import get_settings
from wg_backend.db.session import SessionFactory

settings = get_settings()

logging.basicConfig(level = settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


def create_necessary_dirs_with():
    try:
        settings.DIST_DIR.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
        settings.TMP_DIR.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct)
        settings.WG_CONFIG_DIR_PATH.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
        # settings.SQLITE_DIR_PATH.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
        settings.PID_FILE_DIR.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
        if not settings.DEBUG:
            settings.LOGS_DIR_PATH.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
            settings.RUN_DIR.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
    except Exception as e:
        raise Exception(f'Could not create necessary directories: {e}')


def create_necessary_files():
    try:
        (settings.SQLITE_DIR_PATH / settings.SQLITE_FILE_NAME).touch(exist_ok = True, mode = settings.app_umask_oct)
        # settings.gunicorn_pid_file.touch(exist_ok = True, mode = settings.app_umask_oct)
        settings.wg_if_config_file_path.touch(exist_ok = True, mode = settings.app_umask_oct)
        settings.wg_if_peers_config_file_path.touch(exist_ok = True, mode = settings.app_umask_oct)
        if not settings.DEBUG:
            settings.gunicorn_access_log_path.touch(exist_ok = True, mode = settings.app_umask_oct)
            settings.gunicorn_error_log_path.touch(exist_ok = True, mode = settings.app_umask_oct)
    except Exception as e:
        raise Exception(f'Could not create necessary files: {e}')


@retry(
    stop = stop_after_attempt(max_tries),
    wait = wait_fixed(wait_seconds),
    before = before_log(logger, logging.INFO),
    after = after_log(logger, logging.INFO),
)
def init() -> None:
    try:
        logger.info('Creating necessary directories and files with needed permissions (exist_ok=True).')
        create_necessary_dirs_with()
        # create_necessary_files()
        logger.info('Directories and files are ready to rock.')
        """ [alembic upgrade head] 
        this command will create db if not created, and apply alembic migrations to it to HEAD or last migration,
        migrations will upgrade database in multiple steps from '/alembic/versions/' dir
        """
        # alembic_config = config.Config(settings.ALEMBIC_CONFIG_PATH)
        # command.upgrade(config = alembic_config, revision = 'head')
        with SessionFactory() as session:
            session.execute(select(1))
        logger.debug('Database is healthy and ready for transactions')
    except sqlalchemy.exc.OperationalError as e:
        logger.critical('Error when trying to access database', e)
    except Exception as e:
        logger.critical('Error when trying to create dirs and files or select db', e)
        raise e


def main():
    logger.info("Initializing service.")
    init()
    logger.info("Service finished initializing.")
    return


if __name__ == "__main__":
    main()
