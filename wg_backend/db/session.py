from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from wg_backend.core.configs.Settings import get_settings

settings = get_settings()

engine = create_engine(
    url = settings.sqlalchemy_db_uri,
    pool_pre_ping = True,
    echo = settings.SQLALCHEMY_ECHO_CREATED_QUERIES,
    future = True,
)

SessionFactory = sessionmaker(
    bind = engine,
    future = True,
    autoflush = True,
    autocommit = False,
    expire_on_commit = False
)


def get_session() -> Generator:
    session = SessionFactory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    else:
        session.commit()
    finally:
        session.close()


SessionDep = Annotated[Session, Depends(get_session)]


class SessionContextManager:
    def __init__(self):
        self.session = SessionFactory()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


# async def get_session2():
# 	with SessionContextManager() as session:
# 		yield session
