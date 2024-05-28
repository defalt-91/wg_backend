import logging
from subprocess import SubprocessError

from gunicorn.app.wsgiapp import WSGIApplication
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, exc as sqlalchemy_exceptions
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed
from uvicorn import run as uvicorn_run
from wg_backend.core.settings import execute, get_settings
from wg_backend.crud.crud_user_fn import authenticate, create_user
from wg_backend.crud.crud_wgserver import crud_wg_interface
from wg_backend.db.session import SessionFactory
from wg_backend.main import app as wg_backend_app
from wg_backend.models.wg_interface import WGInterface
from wg_backend.schemas.user import UserCreate
from wg_backend.schemas.wg_interface import WGInterfaceCreate

settings = get_settings()

logging.basicConfig(level = settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


def init_db(session: Session) -> None:
    """creating superuser if there is not one"""
    user = authenticate(
        session = session,
        username = settings.FIRST_SUPERUSER,
        password = settings.FIRST_SUPERUSER_PASSWORD,
    )
    if not user:
        logger.debug("No superuser,creating one from provided environments ...")
        user_in = UserCreate(
            username = settings.FIRST_SUPERUSER,
            password = settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser = True,
        )
        super_user = create_user(session = session, user_create = user_in)
        logger.debug(f"newly created superuser is: {super_user.username}")
        logger.debug("Superuser created.")
    else:
        logger.debug("superuser already exists.")
    """ load peer config from db or create one"""
    try:
        interface = session.query(WGInterface).one()
        logger.debug(f"loading existing {interface.interface} config from database.")
    except sqlalchemy_exceptions.NoResultFound:
        logger.debug("No interface configuration found in database, creating one ...")
        obj_in = WGInterfaceCreate(interface = settings.WG_INTERFACE_NAME).model_dump()
        created_orm_wg_if = crud_wg_interface.create(session, obj_in = obj_in)
        logger.info("Wireguard db interface created.")
        logger.info(f"newly created interface in db is => {created_orm_wg_if.interface}.")
    except sqlalchemy_exceptions.MultipleResultsFound:
        logger.debug("there are multiple interfaces in database.")
    finally:
        logger.debug("everything is ready for wg_backend to start.")


@retry(
    stop = stop_after_attempt(max_tries),
    wait = wait_fixed(wait_seconds),
    before = before_log(logger, logging.INFO),
    after = after_log(logger, logging.INFO),
)
def init(session: Session) -> None:
    try:
        logger.info('Creating necessary directories and files with needed permissions (exist_ok=True).')
        create_necessary_dirs_with()
        create_necessary_files()
        logger.info('Directories and files are ready to rock.')
        """ [alembic upgrade head] 
        this command will create db if not created, and apply alembic migrations to it to HEAD or last migration,
        migrations will upgrade database in multiple steps from '/alembic/versions/' dir
        """
        execute(["alembic", "upgrade", "head"])
        session.execute(select(1))
        logger.debug('Database is healthy and ready for transactions')
    except SubprocessError as e:
        logger.critical("couldn't upgrade data base:", e)
    except OperationalError as e:
        logger.critical('Error when trying to access database', e)
    except Exception as e:
        logger.critical('Error when trying to create dirs and files or select db', e)
        raise e


def create_necessary_dirs_with():
    try:
        settings.DIST_DIR.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
        settings.tmp_dir_path.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct)
        settings.wg_config_dir_path.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
        settings.sqlite_dir_path.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
        settings.pid_file_dir_path.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
        if not settings.DEBUG:
            settings.gunicorn_logs_dir_path.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
            settings.run_dir_path.mkdir(exist_ok = True, mode = settings.app_umask_dirs_oct, parents = True)
    except Exception as e:
        raise Exception(f'Could not create necessary directories: {e}')


def create_necessary_files():
    try:
        (settings.sqlite_dir_path / settings.SQLITE_FILE_NAME).touch(exist_ok = True, mode = settings.app_umask_oct)
        # settings.gunicorn_pid_file.touch(exist_ok = True, mode = settings.app_umask_oct)
        settings.wg_if_config_file_path.touch(exist_ok = True, mode = settings.app_umask_oct)
        settings.wg_if_peers_config_file_path.touch(exist_ok = True, mode = settings.app_umask_oct)
        if not settings.DEBUG:
            settings.gunicorn_access_log_path.touch(exist_ok = True, mode = settings.app_umask_oct)
            settings.gunicorn_error_log_path.touch(exist_ok = True, mode = settings.app_umask_oct)
    except Exception as e:
        raise Exception(f'Could not create necessary files: {e}')


class StandaloneApplication(WSGIApplication):
    def __init__(self, app, *args, **kwargs) -> None:
        # self.options = options or {}
        self.application = app
        super().__init__(*args, **kwargs)

    def load_config(self):
        self.load_config_from_file("gunicorn_conf.py")

    def load(self):
        return self.application


def run_uvicorn():
    with SessionFactory() as session:
        logger.info("Initializing service.")
        init(session)
        logger.info("Service finished initializing.")
        logger.info("Creating initial data")
        init_db(session)
        logger.info("Initial data created")
    uvicorn_run(
        app = "wg_backend.main:app",
        port = settings.UVICORN_PORT,
        host = str(settings.UVICORN_HOST),
        reload = True,
        workers = 1
    )


def run_gunicorn():
    with SessionFactory() as session:
        logger.info("Initializing service.")
        init(session)
        logger.info("Service finished initializing.")
        logger.info("Creating initial data")
        init_db(session)
        logger.info("Initial data created")
    app_ = StandaloneApplication(wg_backend_app)
    # run(prog="gunicorn")
    app_.run()
