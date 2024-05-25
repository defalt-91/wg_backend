import logging

from sqlalchemy import select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from alembic import command, config
from wg_backend.core.settings import get_settings
from wg_backend.db.session import SessionFactory

settings = get_settings()

logging.basicConfig(level = settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


def create_necessary_dirs():
    try:
        settings.DIST_DIR.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
        settings.TMP_DIR.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct)
        settings.WG_CONFIG_DIR_PATH.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
        settings.SQLITE_DIR_PATH.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
        settings.PID_FILE_DIR.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
        if not settings.DEBUG:
            settings.LOGS_DIR_PATH.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
            settings.RUN_DIR.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
    except Exception as e:
        raise Exception('Could not create necessary directories: {}'.format(e))


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
        raise Exception('Could not create necessary files: {}'.format(e))


@retry(
    stop = stop_after_attempt(max_tries),
    wait = wait_fixed(wait_seconds),
    before = before_log(logger, logging.INFO),
    after = after_log(logger, logging.INFO),
)
def init() -> None:
    try:
        logger.info('Creating necessary directories and files with needed permissions (exist_ok).')
        create_necessary_dirs()
        create_necessary_files()
        # (settings.BASE_DIR / 'sqlite.db').touch(exist_ok = True, mode = settings.app_umask_oct)
        logger.info('dirs and files are ready to rock.')
        """
        alembic upgrade head
        """
        alembic_config = config.Config(settings.ALEMBIC_CONFIG_PATH)
        command.upgrade(config = alembic_config, revision = 'head')
        with SessionFactory() as session:
            session.execute(select(1))
        logger.debug('Database is ready for transactions')

    except Exception as e:
        logger.error('Error when trying to select db', e)
        raise e

    finally:
        session.close()


def main():
    logger.info("Initializing service and creating needed directories and files(exist_ok=True).")
    init()
    logger.info("Service finished initializing.")
    return


if __name__ == "__main__":
    main()
