import logging

from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from wg_backend.core.configs.Settings import get_settings

settings = get_settings()

logging.basicConfig(level = settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop = stop_after_attempt(max_tries),
    wait = wait_fixed(wait_seconds),
    before = before_log(logger, logging.INFO),
    after = after_log(logger, logging.INFO),
)
def init() -> None:
    print(settings.APP_FILES_DIR)
    print(settings.BASE_DIR / 'wg_config' / "var/lib/wireguard")
    print(settings.WG_CONFIG_DIR_PATH)
    print(settings.wg_if_config_file_path)
    print(settings.wg_if_peers_config_file_path)
    print(settings.ACCESS_LOG)
    print(settings.ERROR_LOG)
    # print(Path("/var/lib/wireguard"))
    # print(Path("/var/lib/wireguard"))
    # print(Path("/var/lib/wireguard"))
    # try:
    #     logger.info('Creating necessary directories and files with needed permissions (exist_ok).')
    #     # os.umask(0)
    #     settings.WG_CONFIG_DIR_PATH.mkdir(exist_ok = True, mode = settings.umask_dirs)
    #     settings.wg_if_config_file_path.touch(exist_ok = True, mode = settings.umask_files)
    #     settings.wg_if_peers_config_file_path.touch(exist_ok = True, mode = settings.umask_files)
    #     # (settings.BASE_DIR / 'sqlite.db').touch(exist_ok = True, mode = settings.umask_files)
    #     settings.SQLITE_DATABASE_LOCATION.mkdir(exist_ok = True, mode = settings.umask_dirs, parents = True)
    #     (settings.SQLITE_DATABASE_LOCATION / 'sqlite.db').touch(exist_ok = True, mode = settings.umask_files)
    #     logger.info('dirs and files are ready to rock.')
    #     """
    #     alembic upgrade head
    #     """
    #     # alembic_config = config.Config(settings.ALEMBIC_CONFIG_PATH)
    #     # command.upgrade(config = alembic_config, revision = 'head')
    #     with SessionFactory() as session:
    #         session.execute(select(1))
    #     logger.debug('Database is ready for transactions')
    #
    # except Exception as e:
    #     logger.error('Error when trying to select db',e)
    #     raise e
    #
    # finally:
    #     session.close()


def main():
    logger.info("Initializing service and creating needed directories and files(exist_ok=True).")
    init()
    logger.info("Service finished initializing.")
    return


if __name__ == "__main__":
    main()
